"""CLI: python -m lipsync_pipeline <서브커맨드> ...  (각 단계는 독립 실행 가능)

흐름: prepare -> separate -> analyze -> scan -> emotion -> segments -> lipsync(GPU) -> (review) -> finalize
일괄: run(한 작업 전체/일부 단계), batch(CSV)   보조: compare, select, pack, unpack, models
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .utils import PipelineError, Workspace, log


def _add_work(p):
    p.add_argument("--work-root", default="work", help="작업 폴더 루트 (기본: ./work)")


def _add_name(p):
    p.add_argument("name", help="작업 이름 (work/<이름>/)")
    _add_work(p)


def _add_gen_options(p):
    g = p.add_argument_group("생성 옵션 (기본값은 모두 최대 품질)")
    g.add_argument("--seed", type=int, default=1234, help="기준 seed (후보마다 자동으로 달라짐)")
    g.add_argument("--steps", type=int, default=None, help="샘플링 스텝 (기본: 모델 최대값)")
    g.add_argument("--guidance", type=float, default=None)
    g.add_argument("--precision", choices=["fp16", "bf16", "fp32"], default="fp16")
    g.add_argument("--offload", choices=["none", "model", "sequential"], default="none",
                   help="작은 VRAM 용: model=CPU offload, sequential=레이어 단위(가장 느리고 VRAM 최소)")
    g.add_argument("--device", default="cuda")
    g.add_argument("--tool-dir", default=None, help="모델 저장소 폴더 (환경변수로도 지정 가능)")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="lipsync-pipeline", description="완성된 영상 + 완성된 음원에 립싱크만 적용하는 파이프라인")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare", help="1. 메타데이터 확인, 오디오 제거 영상 / 44.1kHz WAV / 16kHz WAV 생성")
    p.add_argument("video"); p.add_argument("audio"); _add_work(p)
    p.add_argument("--name", default=None); p.add_argument("--audio-start", type=float, default=0.0, help="음원에서 사용할 시작 위치(초)")

    p = sub.add_parser("separate", help="2. Demucs 보컬 분리"); _add_name(p)
    p.add_argument("--backend", choices=["demucs", "passthrough"], default="demucs")
    p.add_argument("--model", default="htdemucs"); p.add_argument("--device", default="cpu")
    p.add_argument("--chunk-sec", type=float, default=60.0); p.add_argument("--overlap-sec", type=float, default=2.0)

    p = sub.add_parser("analyze", help="3. F0/RMS/무음 구간/비트 -> analysis.json"); _add_name(p)
    p.add_argument("--hop-ms", type=float, default=10.0); p.add_argument("--fps", type=float, default=None)

    p = sub.add_parser("cuts", help="4a. 장면 전환(컷) 감지만 실행 -> cuts.json"); _add_name(p)
    p.add_argument("--threshold", type=float, default=0.15)

    p = sub.add_parser("scan", aliases=["face"], help="4. 영상 사전 점검: 컷/얼굴/각도/눈/입 가림/워터마크 경고 -> cuts_report.csv"); _add_name(p)
    p.add_argument("--backend", choices=["auto", "mediapipe", "haar", "fixed"], default="auto")
    p.add_argument("--box", default=None, help="fixed 용 x,y,w,h")
    p.add_argument("--stride", type=int, default=1); p.add_argument("--crop-scale", type=float, default=1.6)
    p.add_argument("--size", type=int, default=512, help="얼굴 크롭 해상도 (기본 512 = 최대 품질)")
    p.add_argument("--min-face-px", type=int, default=96, help="이보다 작은 얼굴은 립싱크 건너뜀")
    p.add_argument("--apply-bad-cuts", action="store_true", help="입 가림/측면/각도 문제 컷도 건너뛰지 않고 립싱크 적용 (얼굴 없음/작음은 항상 건너뜀)")
    p.add_argument("--no-export-crop", action="store_true")

    p = sub.add_parser("segments", help="5a. 무음 기준 문장 단위 구간 분할 (0.5초 겹침) + 입력 자르기"); _add_name(p)
    p.add_argument("--overlap-sec", type=float, default=0.5); p.add_argument("--min-len-sec", type=float, default=2.0)
    p.add_argument("--max-len-sec", type=float, default=12.0); p.add_argument("--replan", action="store_true")

    p = sub.add_parser("lipsync", help="5b. 구간별 후보(take) 생성 (GPU 필요, 기존 후보는 보존)"); _add_name(p)
    p.add_argument("--model", default="latentsync", help="models 서브커맨드로 목록 확인")
    p.add_argument("--takes", type=int, default=3); p.add_argument("--segments", default=None, help="예: 3,5 (기본 전체)")
    p.add_argument("--label", default="", help="설정 메모 (compare 라벨에 표시)"); p.add_argument("--no-score", action="store_true")
    _add_gen_options(p)

    p = sub.add_parser("emotion", help="6. 고개 끄덕임/미세 움직임 파라미터 -> emotion.json"); _add_name(p)
    p.add_argument("--nod-amp", type=float, default=0.012); p.add_argument("--seed", type=int, default=0)

    p = sub.add_parser("review", help="후보 비교/선택 웹 UI (selection.json 저장)"); _add_name(p)
    p.add_argument("--port", type=int, default=8765); p.add_argument("--no-browser", action="store_true")
    p.add_argument("--model", default="latentsync", help="UI 의 재생성 기본 모델"); _add_gen_options(p)

    p = sub.add_parser("select", help="UI 없이 구간 후보 선택"); _add_name(p)
    p.add_argument("--segment", type=int, required=True); p.add_argument("--take", type=int, required=True)

    p = sub.add_parser("compare", help="같은 구간의 후보들을 나란히 붙인 비교 영상"); _add_name(p)
    p.add_argument("--segment", type=int, required=True); p.add_argument("--takes", default=None, help="예: 1,2,4 (기본 전체)")
    p.add_argument("--no-input", action="store_true"); p.add_argument("--cols", type=int, default=3)

    p = sub.add_parser("finalize", help="7. 후보 조립 -> 복원 -> 업스케일 -> 합성 -> 오디오 결합 -> final.mp4"); _add_name(p)
    p.add_argument("--tag", default=None, help="결과 폴더 이름 (기본 시각, 덮어쓰기 금지)")
    p.add_argument("--fill-missing", choices=["error", "first", "score"], default="error")
    for flag, helptxt, default in (("restore", "얼굴 복원(CodeFormer)", True), ("upscale", "전체 프레임 업스케일(Real-ESRGAN)", True),
                                   ("interpolate", "프레임 보간(RIFE, FPS 가 배수만큼 증가)", True)):
        p.add_argument(f"--{flag}", dest=flag, action="store_true", default=default, help=f"{helptxt} 켜기" + (" (기본)" if default else ""))
        p.add_argument(f"--no-{flag}", dest=flag, action="store_false", help=f"{helptxt} 끄기")
    p.add_argument("--restore-weight", type=float, default=0.7); p.add_argument("--upscale-scale", type=float, default=2.0)
    p.add_argument("--interp-multi", type=int, default=2)
    p.add_argument("--paste-mode", choices=["face", "mouth"], default="face"); p.add_argument("--no-color-match", action="store_true")
    p.add_argument("--emotion", action="store_true", help="emotion.json 의 움직임 적용")
    p.add_argument("--restore-dir"); p.add_argument("--upscale-dir"); p.add_argument("--interpolate-dir")

    p = sub.add_parser("run", help="한 작업의 여러 단계를 이어서 실행 (state.json 으로 이어하기)"); _add_name(p)
    _add_run_args(p)
    p.add_argument("--video"); p.add_argument("--audio")

    p = sub.add_parser("batch", help="CSV(영상경로,음원경로,이름,프리셋) 일괄 처리"); p.add_argument("csv"); _add_work(p)
    _add_run_args(p)

    p = sub.add_parser("pack", help="PC<->GPU 전달용 zip 만들기"); _add_name(p)
    p.add_argument("--kind", choices=["upload", "result", "full"], required=True,
                   help="upload=GPU 로 보낼 입력, result=GPU 에서 돌려받을 후보, full=작업 폴더 전체(후처리를 GPU 에서 할 때)")
    p = sub.add_parser("unpack", help="GPU 결과 zip 을 작업 폴더에 병합 (덮어쓰지 않음)"); _add_name(p); p.add_argument("zip")
    sub.add_parser("models", help="등록된 어댑터 목록")
    return ap


def _add_run_args(p):
    p.add_argument("--preset", default="quality", help="presets/<이름>.yaml (기본 quality)")
    p.add_argument("--preset-dir", default=None)
    p.add_argument("--stages", default=None, help="실행할 단계만 쉼표로 (예: lipsync,emotion)")
    p.add_argument("--from", dest="start", default=None); p.add_argument("--until", default=None)
    p.add_argument("--force", action="store_true", help="완료된 단계도 다시 실행 (기존 결과는 보존)")
    p.add_argument("--offload", choices=["none", "model", "sequential"], default=None, help="프리셋의 offload 덮어쓰기")
    p.add_argument("--takes", type=int, default=None, help="프리셋의 takes 덮어쓰기")
    p.add_argument("--lipsync-device", default=None)


def _opts(a):
    from .models import GenerationOptions
    return GenerationOptions(seed=a.seed, steps=a.steps, guidance=a.guidance, precision=a.precision,
                             offload=a.offload, device=a.device, tool_dir=a.tool_dir)


def _stage_list(a):
    return [x.strip() for x in a.stages.split(",") if x.strip()] if a.stages else None


def dispatch(a) -> None:
    c = a.cmd
    if c == "scan" or c == "face":
        c = "scan"
    if c == "models":
        from .models import available_models
        for k, v in available_models().items():
            print(f"{k}: {', '.join(v)}")
        return
    if c == "prepare":
        from .prepare import prepare
        prepare(Path(a.video), Path(a.audio), a.work_root, a.name, a.audio_start)
        return
    if c == "batch":
        from .batch import run_batch
        res = run_batch(Path(a.csv), a.work_root, _stage_list(a), a.start, a.until, a.force, a.preset,
                        Path(a.preset_dir) if a.preset_dir else None,
                        {"offload": a.offload, "takes": a.takes, "lipsync_device": a.lipsync_device})
        if any(r["status"] != "done" for r in res):
            raise PipelineError("실패한 작업이 있습니다 (위의 배치 결과 목록 참고).")
        return
    ws = Workspace.open(a.name, a.work_root, must_exist=c not in ("unpack", "run"))
    if c == "run":
        from .pipeline import Job, run_job
        from .presets import load_preset
        pr = load_preset(a.preset, [Path(a.preset_dir)] if a.preset_dir else None)
        for k, v in (("offload", a.offload), ("takes", a.takes), ("lipsync_device", a.lipsync_device)):
            if v is not None:
                setattr(pr, k, v)
        run_job(Job(a.name, Path(a.video) if a.video else None, Path(a.audio) if a.audio else None, a.preset), pr,
                a.work_root, _stage_list(a), a.start, a.until, a.force)
        return
    if c == "separate":
        from .separate import separate
        separate(ws, a.backend, a.model, a.device, a.chunk_sec, a.overlap_sec)
    elif c == "analyze":
        from .analyze import analyze
        analyze(ws, a.hop_ms, a.fps)
    elif c == "cuts":
        from .cuts import run_cuts
        run_cuts(ws, a.threshold)
    elif c == "scan":
        from .face import run_scan
        box = tuple(float(v) for v in a.box.split(",")) if a.box else None
        if box and len(box) != 4:
            raise PipelineError("--box 는 x,y,w,h 네 값이어야 합니다.")
        run_scan(ws, a.backend, box, a.stride, a.crop_scale, a.size, not a.no_export_crop, a.min_face_px, a.apply_bad_cuts)
    elif c == "segments":
        from .segments import run_segments
        run_segments(ws, a.overlap_sec, a.min_len_sec, a.max_len_sec, a.replan)
    elif c == "lipsync":
        from .generate import generate_takes
        only = [int(x) for x in a.segments.split(",")] if a.segments else None
        generate_takes(ws, a.model, a.takes, _opts(a), only, a.label, not a.no_score)
    elif c == "emotion":
        from .emotion import EmotionConfig, run_emotion
        run_emotion(ws, EmotionConfig(nod_amp=a.nod_amp, seed=a.seed))
    elif c == "review":
        from .review import serve
        serve(ws, a.port, a.model, _opts(a), not a.no_browser)
    elif c == "select":
        from .selection import set_selection
        set_selection(ws, a.segment, a.take)
        log(f"[select] 구간 {a.segment} -> take_{a.take}")
    elif c == "compare":
        from .compare import run_compare
        takes = [int(x) for x in a.takes.split(",")] if a.takes else None
        run_compare(ws, a.segment, takes, not a.no_input, a.cols)
    elif c == "finalize":
        from .finalize import FinalizeOptions, run_finalize
        run_finalize(ws, FinalizeOptions(
            tag=a.tag, fill_missing=a.fill_missing, restore=a.restore, upscale=a.upscale, interpolate=a.interpolate,
            restore_weight=a.restore_weight, upscale_scale=a.upscale_scale, interp_multi=a.interp_multi, paste_mode=a.paste_mode,
            color_match=not a.no_color_match, apply_emotion=a.emotion,
            tool_dirs={"restore": a.restore_dir, "upscale": a.upscale_dir, "interpolate": a.interpolate_dir}))
    elif c == "pack":
        from .bundle import pack
        pack(ws, a.kind)
    elif c == "unpack":
        from .bundle import unpack
        unpack(ws, Path(a.zip))


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):                  # Windows 콘솔에서도 한글이 깨지지 않도록
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    args = build_parser().parse_args(argv)
    try:
        dispatch(args)
    except PipelineError as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("중단되었습니다.", file=sys.stderr)
        return 130
    return 0
