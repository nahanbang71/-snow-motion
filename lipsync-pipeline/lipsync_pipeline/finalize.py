"""7단계 finalize: 선택된 후보 조립(크로스페이드) -> 얼굴 복원 -> 원본에 합성 -> 업스케일 -> 프레임 보간 -> 오디오 재결합.

원칙
  * 얼굴 복원(CodeFormer) / 업스케일(Real-ESRGAN) / 프레임 보간(RIFE)은 각각 켜고 끌 수 있고 기본은 모두 켬.
  * 최종 영상은 원본(prepare 결과)의 해상도 / FPS / 길이를 유지한다. 단, 켜 둔 옵션 때문에 달라지는 것은 예외이며
    정확히 그만큼만 달라졌는지 검증한다: 업스케일 -> 해상도 x배율, 프레임 보간 -> FPS x배수 (길이는 항상 동일).
  * 립싱크 불가 구간(얼굴 없음/너무 작음/입 가려짐/측면)은 원본 프레임을 그대로 쓴다. 경계는 부드럽게 알파 램프.
  * 모든 중간 결과는 work/<이름>/finalize/<tag>/ 에 단계별로 보존하고 덮어쓰지 않는다 (다른 후보 조합으로 재합성 가능).
"""
from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from .emotion import apply_motion
from .face import crop_square, feather_mask, match_color, mouth_mask, mouth_relative, paste_back
from .models import get_post_processor
from .selection import resolve_selection
from .segments import segment_weights
from .utils import (FrameWriter, PipelineError, Workspace, find_binary, iter_frames, log, read_json, run, timestamp,
                    video_stream_info, write_json)


@dataclass
class FinalizeOptions:
    tag: Optional[str] = None
    fill_missing: str = "error"          # error | first | score
    restore: bool = True                 # CodeFormer (기본 켬)
    upscale: bool = True                 # Real-ESRGAN, 전체 프레임 (기본 켬: 720p 소스)
    interpolate: bool = True             # RIFE (기본 켬: FPS 가 interp_multi 배가 됨. 원본 FPS 유지는 --no-interpolate)
    interp_multi: int = 2
    restore_weight: float = 0.7
    upscale_scale: float = 2.0
    precision: str = "fp32"              # 후처리 정밀도 (fp16 이상)
    paste_mode: str = "face"             # face | mouth
    color_match: bool = True
    apply_emotion: bool = False
    crf: int = 12
    tool_dirs: dict = field(default_factory=dict)    # {"restore": ..., "upscale": ..., "interpolate": ...}
    restore_name: str = "codeformer"
    upscale_name: str = "realesrgan"
    interpolate_name: str = "rife"


def assemble_patches(ws: Workspace, plan: dict, track: dict, selection: dict[int, Path], dst: Path, crf: int = 8) -> None:
    """선택된 take 들을 프레임 시간축으로 이어 붙인다. 겹침 구간은 선형 크로스페이드, 구간 밖은 원본 크롭."""
    S, n, half = plan["crop_size"], plan["n_frames"], plan["half_overlap"]
    segs = [s for s in plan["segments"] if s["index"] in selection]
    its, last = {}, {}
    with FrameWriter(dst, S, S, plan["fps_rational"], crf=crf, preset="slow") as w:
        for i, base in enumerate(iter_frames(ws.face_crop, S, S)):
            acc, wsum = np.zeros((S, S, 3), np.float32), 0.0
            for sg in segs:
                rs, re = sg["range"]
                if not (rs <= i < re):
                    continue
                if sg["index"] not in its:
                    v = video_stream_info(selection[sg["index"]])
                    its[sg["index"]] = iter_frames(selection[sg["index"]], v["width"], v["height"])
                fr = next(its[sg["index"]], None)
                if fr is None:
                    fr = last.get(sg["index"])
                    if fr is None:
                        raise PipelineError(f"구간 {sg['index']} 후보 영상이 비어 있습니다.")
                last[sg["index"]] = fr
                if fr.shape[0] != S:
                    fr = cv2.resize(fr, (S, S), interpolation=cv2.INTER_CUBIC)
                wt = segment_weights(sg, i, max(half, 1))
                acc += fr.astype(np.float32) * wt
                wsum += wt
            w.write(np.clip(acc / wsum, 0, 255).astype(np.uint8) if wsum > 0 else base)
            if i >= n - 1:
                break


def frame_alphas(track: dict, edge_ramp_s: float = 0.25) -> np.ndarray:
    """프레임별 패치 합성 비율. 립싱크 가능 구간은 1, 아니면 0. 컷 경계가 아닌 끝점은 램프로 부드럽게."""
    n, fps = track["n_frames"], track["fps"]
    mask = np.array([f["eligible"] for f in track["frames"]], bool)
    alpha = mask.astype(np.float64)
    cut_starts = {r[0] for r in track.get("cuts", [])}
    cut_ends = {r[1] for r in track.get("cuts", [])}
    edges = np.flatnonzero(np.diff(np.r_[False, mask, False].astype(int)))
    for s, e in zip(edges[::2], edges[1::2]):
        r = min(int(round(edge_ramp_s * fps)), (e - s) // 2)
        if r > 0 and s not in cut_starts and s > 0:
            alpha[s:s + r] = (np.arange(r) + 1) / (r + 1)
        if r > 0 and e not in cut_ends and e < n:
            alpha[e - r:e] = (np.arange(r, 0, -1)) / (r + 1)
    return alpha


def composite(ws: Workspace, track: dict, patch_video: Path, dst: Path, opts: FinalizeOptions, emotion: Optional[dict]) -> None:
    v = video_stream_info(ws.video_noaudio)
    pv = video_stream_info(patch_video)
    P = pv["width"]
    alpha = frame_alphas(track)
    base_mask = feather_mask(P) if opts.paste_mode == "face" else None
    patches = iter_frames(patch_video, P, pv["height"])
    with FrameWriter(dst, v["width"], v["height"], v["fps_rational"], crf=8, preset="slow") as w:
        for i, frame in enumerate(iter_frames(ws.video_noaudio, v["width"], v["height"])):
            patch = next(patches, None)
            a = float(alpha[i]) if i < len(alpha) else 0.0
            if patch is None or a <= 0:
                w.write(frame)
                continue
            x, y, s = track["frames"][i]["crop"]
            if emotion is not None:
                patch = apply_motion(patch, emotion["dx"][i], emotion["dy"][i], emotion["rot"][i], emotion["scale"][i])
            mask = base_mask if base_mask is not None else mouth_mask(P, mouth_relative(track["frames"][i]))
            if opts.color_match:
                ref = crop_square(frame, x, y, s, P)
                patch = match_color(patch, ref, mask)
            w.write(paste_back(frame, patch, x, y, s, mask * a))


def verify_matches_source(ws: Workspace, final: Path, opts: Optional[FinalizeOptions] = None) -> dict:
    """최종 영상이 원본(prepare 결과)과 맞는지 검증. 켜 둔 업스케일/보간으로 인한 변화만 허용한다."""
    opts = opts or FinalizeOptions(upscale=False, interpolate=False)
    ref, out = video_stream_info(ws.video_noaudio), video_stream_info(final)
    scale = opts.upscale_scale if opts.upscale else 1.0
    mult = opts.interp_multi if opts.interpolate else 1
    exp_w, exp_h, exp_fps = ref["width"] * scale, ref["height"] * scale, ref["fps"] * mult
    problems = []
    if abs(out["width"] - exp_w) > 2 or abs(out["height"] - exp_h) > 2:
        problems.append(f"해상도 {out['width']}x{out['height']} (기대 {exp_w:.0f}x{exp_h:.0f})")
    if abs(out["fps"] - exp_fps) > 0.01 * mult:
        problems.append(f"FPS {out['fps']:.3f} (기대 {exp_fps:.3f})")
    if ref["frames"] and abs(out["frames"] - ref["frames"] * mult) > mult:
        problems.append(f"프레임 수 {out['frames']} (기대 약 {ref['frames'] * mult})")
    if abs(ref["duration"] - out["duration"]) > 2.0 / ref["fps"]:
        problems.append(f"길이 {out['duration']:.3f}s (기대 {ref['duration']:.3f}s)")
    if problems:
        raise PipelineError("최종 영상이 기대와 다릅니다: " + "; ".join(problems))
    return {"width": out["width"], "height": out["height"], "fps": out["fps"], "frames": out["frames"],
            "duration": out["duration"], "source_width": ref["width"], "source_height": ref["height"],
            "source_fps": ref["fps"], "matches_expectation": True}


def run_finalize(ws: Workspace, opts: FinalizeOptions = FinalizeOptions()) -> Path:
    ws.require(ws.video_noaudio, ws.audio_44k, ws.face_track, hint="`prepare`, `scan` 단계를 먼저 실행해 주세요.")
    track = read_json(ws.face_track)
    tag = opts.tag or timestamp()
    run_dir = ws.p("finalize") / tag
    if run_dir.exists():
        raise PipelineError(f"이미 있는 결과 폴더입니다(덮어쓰기 금지): {run_dir}. 다른 --tag 를 지정하세요.")
    run_dir.mkdir(parents=True)

    plan_path = ws.p("segments.json")
    selection: dict[int, Path] = {}
    plan = None
    if plan_path.exists() and any(f["eligible"] for f in track["frames"]):
        plan = read_json(plan_path)
        selection = resolve_selection(ws, opts.fill_missing)
    stages: dict[str, str] = {}
    emotion = read_json(ws.emotion) if opts.apply_emotion and ws.emotion.exists() else None
    if opts.apply_emotion and emotion is None:
        raise PipelineError("--emotion 을 켰지만 emotion.json 이 없습니다. `emotion` 단계를 먼저 실행해 주세요.")

    if not selection:
        log("[finalize] 립싱크를 적용할 구간이 없어 원본 영상을 그대로 사용합니다.")
        composed = ws.video_noaudio
    else:
        patch = run_dir / "01_assembled_crop.mp4"
        assemble_patches(ws, plan, track, selection, patch)
        stages["assembled_crop"] = patch.name
        td = opts.tool_dirs
        if opts.restore:
            log("[finalize] 얼굴 복원...")
            nxt = run_dir / "02_restored_crop.mp4"
            get_post_processor("restore", opts.restore_name).process(
                patch, nxt, {"weight": opts.restore_weight, "tool_dir": td.get("restore")})
            patch, stages["restored_crop"] = nxt, nxt.name
        composed = run_dir / "03_composited.mp4"
        log("[finalize] 원본에 합성...")
        composite(ws, track, patch, composed, opts, emotion)
        stages["composited"] = composed.name

    if opts.upscale:
        log("[finalize] 전체 프레임 업스케일...")
        nxt = run_dir / "04_upscaled.mp4"
        get_post_processor("upscale", opts.upscale_name).process(
            composed, nxt, {"scale": opts.upscale_scale, "precision": opts.precision, "tool_dir": opts.tool_dirs.get("upscale")})
        composed, stages["upscaled"] = nxt, nxt.name
    if opts.interpolate:
        log(f"[finalize] 프레임 보간 x{opts.interp_multi}...")
        nxt = run_dir / "05_interpolated.mp4"
        get_post_processor("interpolate", opts.interpolate_name).process(
            composed, nxt, {"multi": opts.interp_multi, "tool_dir": opts.tool_dirs.get("interpolate")})
        composed, stages["interpolated"] = nxt, nxt.name

    final = run_dir / "final.mp4"
    run([find_binary("ffmpeg"), "-y", "-v", "error", "-i", composed, "-i", ws.audio_44k, "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "libx264", "-crf", str(opts.crf), "-preset", "slow", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", final], "최종 인코딩/오디오 결합")
    check = verify_matches_source(ws, final, opts)
    write_json(run_dir / "render.json", {
        "options": asdict(opts), "selection": {str(k): str(v.relative_to(ws.root).as_posix()) for k, v in selection.items()},
        "stages": stages, "verification": check, "lipsync_applied": bool(selection),
        "exceptions": {"scale": opts.upscale_scale if opts.upscale else 1, "fps_multiplier": opts.interp_multi if opts.interpolate else 1}})
    log(f"[finalize] 완료: {final}  ({check['width']}x{check['height']}, {check['fps']:.3f}fps, {check['duration']:.2f}초)")
    return final
