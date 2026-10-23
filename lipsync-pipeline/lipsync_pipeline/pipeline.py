"""단계 실행기: state.json 으로 완료 상태를 기록하고, 중단/에러 후 이어서 실행한다. 단계별 시간은 report.csv 로 남긴다."""
from __future__ import annotations

import csv
import os
import shutil
import subprocess
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

from .models import GenerationOptions
from .presets import Preset
from .utils import PipelineError, Workspace, log, read_json, sanitize_name, timestamp, write_json

STAGES = ["prepare", "separate", "analyze", "scan", "emotion", "segments", "lipsync", "finalize"]
REPORT_COLUMNS = ["time", "name", "preset", "stage", "status", "seconds", "video_seconds", "frames", "model", "device", "gpu", "error"]


@dataclass
class Job:
    name: str
    video: Optional[Path] = None
    audio: Optional[Path] = None
    preset: str = "quality"


class State:
    def __init__(self, ws: Workspace):
        self.path = ws.p("state.json")
        self.data = read_json(self.path) if self.path.exists() else {"version": 1, "stages": {}}

    def get(self, stage: str) -> dict:
        return self.data["stages"].get(stage, {"status": "pending"})

    def set(self, stage: str, **kw) -> None:
        self.data["stages"][stage] = {**self.data["stages"].get(stage, {}), **kw}
        tmp = self.path.with_suffix(".tmp")
        write_json(tmp, self.data)
        os.replace(tmp, self.path)                # 중간에 끊겨도 state.json 이 깨지지 않도록 원자적으로 교체

    def invalidate_after(self, stage: str) -> None:
        for s in STAGES[STAGES.index(stage) + 1:]:
            if self.get(s).get("status") == "done":
                self.set(s, status="stale")


def gpu_name() -> str:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return ""
    try:
        return subprocess.run([exe, "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True,
                              timeout=10).stdout.strip().splitlines()[0]
    except Exception:
        return ""


def append_report(ws: Workspace, row: dict) -> None:
    p = ws.p("report.csv")
    new = not p.exists()
    with open(p, "a", newline="", encoding="utf-8-sig") as f:       # 이력은 지우지 않고 계속 덧붙인다
        w = csv.DictWriter(f, fieldnames=REPORT_COLUMNS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in REPORT_COLUMNS})


def _gen_options(pr: Preset) -> GenerationOptions:
    return GenerationOptions(seed=pr.seed, steps=pr.steps, guidance=pr.guidance, precision=pr.precision,
                             offload=pr.offload, device=pr.lipsync_device, tool_dir=pr.tool_dirs.get("lipsync"))


def _stage_funcs(ws: Workspace, job: Job, pr: Preset, force: bool, work_root) -> dict[str, tuple[Callable[[], dict], Callable[[], bool]]]:
    """stage -> (실행 함수, 산출물 확인 함수)."""
    from .analyze import analyze
    from .emotion import run_emotion
    from .face import run_scan
    from .finalize import FinalizeOptions, run_finalize
    from .generate import existing_takes, generate_takes
    from .prepare import prepare
    from .segments import run_segments
    from .separate import separate

    def do_prepare():
        if job.video is None or job.audio is None:
            if ws.info.exists():
                return {"note": "기존 prepare 결과 사용"}
            raise PipelineError("prepare 에는 영상/음원 경로가 필요합니다.")
        prepare(job.video, job.audio, work_root, ws.name)
        return {}

    def do_lipsync():
        generate_takes(ws, pr.model, pr.takes, _gen_options(pr))
        return {"model": pr.model, "takes": pr.takes}

    def lipsync_ok():
        if not ws.p("segments.json").exists():
            return False
        return all(len(existing_takes(ws.p(s["dir"]))) >= pr.takes for s in read_json(ws.p("segments.json"))["segments"])

    def do_finalize():
        tag = f"auto_{timestamp()}"
        out = run_finalize(ws, FinalizeOptions(
            tag=tag, fill_missing=pr.fill_missing, restore=pr.restore, upscale=pr.upscale, interpolate=pr.interpolate,
            restore_weight=pr.restore_weight, upscale_scale=pr.upscale_scale, interp_multi=pr.interp_multi,
            paste_mode=pr.paste_mode, apply_emotion=pr.emotion,
            tool_dirs={"restore": pr.tool_dirs.get("restore"), "upscale": pr.tool_dirs.get("upscale"),
                       "interpolate": pr.tool_dirs.get("interpolate")}))
        return {"output": str(out.relative_to(ws.root).as_posix()), "tag": tag}

    return {
        "prepare": (do_prepare, lambda: ws.info.exists() and ws.video_noaudio.exists() and ws.audio_16k.exists()),
        "separate": (lambda: (separate(ws, pr.separate_backend, pr.separate_model, pr.separate_device), {})[1],
                     lambda: ws.vocals.exists() and ws.vocals_16k.exists()),
        "analyze": (lambda: (analyze(ws), {})[1], lambda: ws.analysis.exists()),
        "scan": (lambda: (run_scan(ws, pr.face_backend, None, 1, 1.6, pr.face_size, True, pr.min_face_px, pr.apply_bad_cuts), {})[1],
                 lambda: ws.face_track.exists() and ws.face_crop.exists()),
        "emotion": (lambda: (run_emotion(ws), {})[1], lambda: ws.emotion.exists()),
        "segments": (lambda: (run_segments(ws, pr.overlap_sec, pr.min_len_sec, pr.max_len_sec, replan=force), {})[1],
                     lambda: ws.p("segments.json").exists()),
        "lipsync": (do_lipsync, lipsync_ok),
        "finalize": (do_finalize, lambda: bool(ws.p("finalize").is_dir() and list(ws.p("finalize").glob("*/final.mp4")))),
    }


def select_stages(stages: Optional[Sequence[str]] = None, start: Optional[str] = None, until: Optional[str] = None) -> list[str]:
    for s in [*(stages or []), *( [start] if start else []), *([until] if until else [])]:
        if s not in STAGES:
            raise PipelineError(f"알 수 없는 단계 '{s}'. 사용 가능: {', '.join(STAGES)}")
    sel = list(stages) if stages else list(STAGES)
    i0 = STAGES.index(start) if start else 0
    i1 = STAGES.index(until) if until else len(STAGES) - 1
    return [s for s in STAGES if s in sel and i0 <= STAGES.index(s) <= i1]


def run_job(job: Job, pr: Preset, work_root: Path | str = "work", stages: Optional[Sequence[str]] = None,
            start: Optional[str] = None, until: Optional[str] = None, force: bool = False) -> dict:
    """한 작업을 단계별로 실행. 끝난 단계는 건너뛰고(--force 제외), 실패하면 state.json 에 기록한 뒤 예외를 다시 던진다."""
    name = sanitize_name(job.name)
    ws = Workspace.open(name, work_root, must_exist=False)
    state = State(ws)
    funcs = _stage_funcs(ws, job, pr, force, work_root)
    ran, skipped = [], []
    for stage in select_stages(stages, start, until):
        run_fn, ok_fn = funcs[stage]
        cur = state.get(stage)
        if not force and cur.get("status") == "done" and ok_fn():
            log(f"[{name}] {stage}: 이미 완료되어 건너뜁니다.")
            skipped.append(stage)
            continue
        log(f"[{name}] ===== {stage} 시작 =====")
        t0 = time.time()
        state.set(stage, status="running", started=time.strftime("%Y-%m-%d %H:%M:%S"), error="")
        row = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "name": name, "preset": pr.name, "stage": stage,
               "model": pr.model if stage == "lipsync" else "", "device": pr.lipsync_device if stage == "lipsync" else
               (pr.separate_device if stage == "separate" else ""), "gpu": gpu_name()}
        try:
            details = run_fn() or {}
        except BaseException as e:
            secs = round(time.time() - t0, 2)
            msg = str(e) if isinstance(e, PipelineError) else f"{type(e).__name__}: {e}"
            state.set(stage, status="failed", seconds=secs, error=msg, finished=time.strftime("%Y-%m-%d %H:%M:%S"),
                      traceback="" if isinstance(e, PipelineError) else traceback.format_exc()[-2000:])
            append_report(ws, {**row, "status": "failed", "seconds": secs, "error": msg[:300].replace("\n", " ")})
            raise
        secs = round(time.time() - t0, 2)
        info = read_json(ws.info)["video"] if ws.info.exists() else {}
        state.set(stage, status="done", seconds=secs, finished=time.strftime("%Y-%m-%d %H:%M:%S"), error="", **details)
        state.invalidate_after(stage)
        append_report(ws, {**row, "status": "done", "seconds": secs, "video_seconds": round(info.get("duration", 0), 2),
                           "frames": info.get("frames", "")})
        ran.append(stage)
    return {"name": name, "ran": ran, "skipped": skipped}
