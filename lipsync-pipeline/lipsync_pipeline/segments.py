"""구간 분할: 립싱크 적용 가능 구간(span)을 무음 기준 문장/프레이즈 단위로 나누고, 이웃 구간은 0.5초 겹치게 한다.

- 구간은 컷 경계와 '적용 불가' 프레임을 절대 넘지 않는다 (span 단위로 먼저 자름).
- 이웃 구간 경계(=무음 중앙)를 기준으로 앞뒤 0.25초씩 확장해서 총 0.5초 겹치고, finalize 에서 크로스페이드한다.
- 생성 입력(segments/NNN/input.mp4, audio.wav)은 PC(CPU)에서 미리 잘라 두므로 GPU 쪽은 이 폴더만 있으면 된다.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

from .cuts import eligible_spans
from .utils import (FrameWriter, PipelineError, Workspace, archive_existing, iter_frames, log, read_json,
                    read_wav, video_stream_info, write_json, write_wav)


def phrase_cuts(span: tuple[int, int], silence_frames: Sequence[int], rms_db: np.ndarray, fps: float,
                min_len_s: float = 2.0, max_len_s: float = 12.0) -> list[int]:
    """span 안의 내부 경계 프레임들. 무음 후보에서 자르고, 짧으면 합치고, 너무 길면 에너지가 낮은 곳에서 나눈다."""
    s, e = span
    cuts = sorted(c for c in set(silence_frames) if s < c < e)
    min_len, max_len = int(min_len_s * fps), int(max_len_s * fps)
    # 1) 너무 짧은 구간은 다음 구간과 합치기
    merged, prev = [], s
    for c in cuts:
        if c - prev >= min_len:
            merged.append(c)
            prev = c
    if merged and e - merged[-1] < min_len:
        merged.pop()
    # 2) 너무 긴 구간은 균등 분할점 근처의 최소 에너지 프레임에서 분할
    out, bounds = [], [s, *merged, e]
    for a, b in zip(bounds[:-1], bounds[1:]):
        parts = int(np.ceil((b - a) / max_len)) if max_len > 0 else 1
        for k in range(1, parts):
            target = a + (b - a) * k // parts
            lo, hi = max(a + min_len // 2, target - int(0.15 * (b - a) / parts)), min(b - min_len // 2, target + int(0.15 * (b - a) / parts))
            hi = max(hi, lo + 1)
            win = np.asarray(rms_db[lo:hi]) if len(rms_db) >= hi else np.zeros(hi - lo)
            pen = 1e-4 * np.abs(np.arange(lo, hi) - target)       # 에너지가 같으면 균등 분할점에 가까운 쪽
            out.append(lo + int(np.argmin(win + pen)))
        out.append(b)
    return sorted(set(c for c in out if s < c < e))


def plan_segments(spans: Sequence[tuple[int, int]], analysis: dict, fps: float, overlap_s: float = 0.5,
                  min_len_s: float = 2.0, max_len_s: float = 12.0, min_silence_s: float = 0.35) -> list[dict]:
    half = max(int(round(overlap_s * fps / 2)), 0)
    silences = [int(round((g["start"] + g["end"]) / 2 * fps)) for g in analysis["segments"]
                if g["type"] == "silence" and g["end"] - g["start"] >= min_silence_s]
    rms_db = np.array(analysis["per_frame"]["rms_db"], float)
    segs, idx = [], 1
    for s, e in spans:
        bounds = [s, *phrase_cuts((s, e), silences, rms_db, fps, min_len_s, max_len_s), e]
        for a, b in zip(bounds[:-1], bounds[1:]):
            rs = a - half if a > s else a
            re = b + half if b < e else b
            segs.append({"index": idx, "core": [a, b], "range": [rs, re], "dir": f"segments/{idx:03d}"})
            idx += 1
    return segs


def slice_audio(src: Path, dst: Path, start_f: int, end_f: int, fps: float) -> None:
    sr, data = read_wav(src)
    a, b = int(round(start_f / fps * sr)), int(round(end_f / fps * sr))
    chunk = data[a:b]
    need = b - a
    if len(chunk) < need:
        chunk = np.pad(chunk, ((0, need - len(chunk)), (0, 0)))
    write_wav(dst, sr, chunk)


def run_segments(ws: Workspace, overlap_s: float = 0.5, min_len_s: float = 2.0, max_len_s: float = 12.0,
                 replan: bool = False) -> dict:
    ws.require(ws.face_track, ws.face_crop, ws.analysis, hint="`analyze`, `scan` 단계를 먼저 실행해 주세요.")
    plan_path = ws.p("segments.json")
    if plan_path.exists():
        if not replan:
            raise PipelineError("이미 구간 계획(segments.json)이 있습니다. 기존 후보를 보존하려면 그대로 두고, "
                                "새로 나누려면 --replan 을 주세요 (기존 segments/ 는 _archive 로 보관됩니다).")
        archive_existing(ws, plan_path, ws.p("segments"), ws.p("selection.json"))
    track, analysis = read_json(ws.face_track), read_json(ws.analysis)
    fps, n = track["fps"], track["n_frames"]
    mask = np.array([f["eligible"] for f in track["frames"]], bool)
    spans = eligible_spans(mask)
    segs = plan_segments(spans, analysis, fps, overlap_s, min_len_s, max_len_s)
    audio_src = ws.vocals_16k if ws.vocals_16k.exists() else ws.audio_16k
    if audio_src == ws.audio_16k:
        log("[경고] 보컬 분리본이 없어 전체 믹스 오디오를 립싱크 입력으로 씁니다 (품질 저하 가능).")
    ws.p("segments").mkdir(exist_ok=True)

    size = track["out_size"]
    v = video_stream_info(ws.face_crop)
    writers = {}
    for sg in segs:
        d = ws.p(sg["dir"]); d.mkdir(parents=True, exist_ok=True)
        slice_audio(audio_src, d / "audio.wav", sg["range"][0], sg["range"][1], fps)
        writers[sg["index"]] = FrameWriter(d / "input.mp4", size, size, v["fps_rational"], crf=8, preset="slow")
    try:
        for i, frame in enumerate(iter_frames(ws.face_crop, size, size)):
            for sg in segs:
                if sg["range"][0] <= i < sg["range"][1]:
                    writers[sg["index"]].write(frame)
    finally:
        for w in writers.values():
            w.close()
    plan = {"fps": fps, "fps_rational": v["fps_rational"], "n_frames": n,
            "half_overlap": max(int(round(overlap_s * fps / 2)), 0), "overlap_s": overlap_s,
            "crop_size": size, "audio_source": audio_src.name, "spans": [list(s) for s in spans], "segments": segs}
    write_json(plan_path, plan)
    log(f"[segments] 적용 구간 {len(spans)}개 -> 생성 구간 {len(segs)}개 (겹침 {overlap_s}초)")
    return plan


def segment_weights(sg: dict, i: int, half: int) -> float:
    """프레임 i 에서 구간 sg 의 크로스페이드 가중치 (이웃과 겹치는 곳에서 합이 1)."""
    rs, re = sg["range"]; a, b = sg["core"]
    w = 1.0
    if rs < a:
        w *= min(1.0, (i - rs + 0.5) / (2 * half))
    if re > b:
        w *= min(1.0, (re - i - 0.5) / (2 * half))
    return w
