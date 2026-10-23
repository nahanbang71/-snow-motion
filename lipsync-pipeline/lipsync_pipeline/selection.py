"""selection.json: 구간별로 사용자가 고른 후보. 갱신할 때마다 이전 버전을 selection_history/ 에 보존한다."""
from __future__ import annotations

import time
from pathlib import Path

from .generate import existing_takes
from .utils import PipelineError, Workspace, read_json, write_json


def load_selection(ws: Workspace) -> dict:
    p = ws.p("selection.json")
    return read_json(p) if p.exists() else {"version": 1, "segments": {}}


def set_selection(ws: Workspace, segment: int, take: int) -> dict:
    plan = read_json(ws.p("segments.json"))
    if segment not in {s["index"] for s in plan["segments"]}:
        raise PipelineError(f"구간 {segment} 는 없습니다.")
    if take not in existing_takes(ws.p(f"segments/{segment:03d}")):
        raise PipelineError(f"구간 {segment} 에 take_{take} 후보가 없습니다.")
    sel = load_selection(ws)
    p = ws.p("selection.json")
    if p.exists():
        hist = ws.p("selection_history"); hist.mkdir(exist_ok=True)
        (hist / f"selection_{time.strftime('%Y%m%d-%H%M%S')}_{time.time_ns() % 10**6:06d}.json").write_text(
            p.read_text(encoding="utf-8"), encoding="utf-8")
    sel["segments"][str(segment)] = take
    sel["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    write_json(p, sel)
    return sel


def resolve_selection(ws: Workspace, fill_missing: str = "error") -> dict[int, Path]:
    """구간번호 -> 사용할 take mp4. 선택 안 된 구간은 fill_missing(error|first|score)에 따라 처리."""
    plan = read_json(ws.p("segments.json"))
    sel = load_selection(ws)["segments"]
    out, missing = {}, []
    for sg in plan["segments"]:
        d = ws.p(sg["dir"])
        k = sel.get(str(sg["index"]))
        takes = existing_takes(d)
        if k is None:
            if fill_missing == "first" and takes:
                k = takes[0]
            elif fill_missing == "score" and takes:
                def key(t):
                    sc = (read_json(d / f"take_{t}.json").get("scores") or {})
                    return (sc.get("sync_proxy", {}).get("corr", -1), sc.get("stable_pct", 0))
                k = max(takes, key=key)
            else:
                missing.append(sg["index"])
                continue
        path = d / f"take_{k}.mp4"
        if not path.exists():
            raise PipelineError(f"선택된 후보 파일이 없습니다: {path}")
        out[sg["index"]] = path
    if missing:
        raise PipelineError(
            f"아직 후보를 선택하지 않은 구간이 있습니다: {missing}. `review` 로 고르거나 "
            "`select`, 또는 --fill-missing first|score 를 지정하세요.")
    return out
