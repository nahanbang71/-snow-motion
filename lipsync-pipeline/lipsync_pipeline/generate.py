"""구간별 다중 후보(take) 생성. 기존 후보는 절대 덮어쓰지 않고 번호를 이어서 붙인다.

segments/<번호>/take_<k>.mp4  + take_<k>.json(모델/seed/옵션/점수)  + segments/generation_log.jsonl
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Optional, Sequence

from .models import GenerationOptions, LipSyncRequest, get_lipsync_model
from .scoring import score_take
from .utils import PipelineError, Workspace, log, read_json, write_json

_TAKE = re.compile(r"^take_(\d+)\.(mp4|json)$")


def existing_takes(seg_dir: Path) -> list[int]:
    return sorted({int(m.group(1)) for f in seg_dir.glob("take_*") if (m := _TAKE.match(f.name))})


def next_take_number(seg_dir: Path) -> int:
    t = existing_takes(seg_dir)
    return (t[-1] + 1) if t else 1


def generate_takes(ws: Workspace, model_name: str, takes: int = 3, options: Optional[GenerationOptions] = None,
                   only: Optional[Sequence[int]] = None, label: str = "", score: bool = True) -> list[Path]:
    plan_path = ws.p("segments.json")
    if not plan_path.exists():
        raise PipelineError("구간 계획(segments.json)이 없습니다. `segments` 단계를 먼저 실행해 주세요.")
    if takes < 1:
        raise PipelineError("--takes 는 1 이상이어야 합니다.")
    plan = read_json(plan_path)
    model = get_lipsync_model(model_name)
    base_opts = options or GenerationOptions()
    model.check_environment(model.resolve(base_opts))
    made: list[Path] = []
    segs = [s for s in plan["segments"] if only is None or s["index"] in set(only)]
    if only and len(segs) != len(set(only)):
        raise PipelineError(f"존재하지 않는 구간 번호가 있습니다: {sorted(set(only) - {s['index'] for s in segs})}")
    for sg in segs:
        d = ws.p(sg["dir"])
        video, audio = d / "input.mp4", d / "audio.wav"
        if not video.exists() or not audio.exists():
            raise PipelineError(f"구간 {sg['index']} 입력(input.mp4/audio.wav)이 없습니다: {d}")
        for _ in range(takes):
            k = next_take_number(d)
            seed = base_opts.seed + (sg["index"] - 1) * 100 + (k - 1)    # 후보마다 다른 seed
            opts = GenerationOptions(**{**base_opts.to_dict(), "seed": seed})
            tmp = d / f".tmp_take_{k}.mp4"
            req = LipSyncRequest(video=video, audio=audio, output=tmp, fps=plan["fps"], options=opts)
            log(f"[lipsync] 구간 {sg['index']}/{len(plan['segments'])} take_{k} ({model_name}, seed={seed})")
            t0 = time.time()
            try:
                model.run(req)
            except Exception:
                tmp.unlink(missing_ok=True)
                raise
            out = d / f"take_{k}.mp4"
            os.replace(tmp, out)                      # 완성된 파일만 take_k.mp4 로 등장
            meta = {"segment": sg["index"], "take": k, "model": model_name, "label": label, "seed": seed,
                    "options": req.options.to_dict(), "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "seconds": round(time.time() - t0, 1), "scores": None}
            if score:
                try:
                    meta["scores"] = score_take(out, video, audio, plan["fps"])
                except Exception as e:                # 점수는 참고용이므로 실패해도 후보는 보존
                    log(f"[경고] 점수 계산 실패(후보는 저장됨): {e}")
            write_json(d / f"take_{k}.json", meta)
            with open(ws.p("segments") / "generation_log.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(meta, ensure_ascii=False) + "\n")
            made.append(out)
    return made
