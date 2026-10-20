"""compare: 같은 구간을 여러 모델/설정으로 만든 후보를 나란히 붙인 비교 영상.

패널 라벨은 cv2.putText 한계로 ASCII 만 표시한다 (모델명, take 번호, seed, 라벨의 ASCII 부분).
"""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Optional, Sequence

import cv2
import numpy as np

from .generate import existing_takes
from .utils import (FrameWriter, PipelineError, Workspace, find_binary, iter_frames, log, read_json, run,
                    timestamp, video_stream_info)


def _ascii(s: str) -> str:
    return re.sub(r"[^\x20-\x7e]", "", s)


def compose_grid(panels: Sequence[np.ndarray], cols: int) -> np.ndarray:
    rows = math.ceil(len(panels) / cols)
    h, w = panels[0].shape[:2]
    canvas = np.zeros((rows * h, cols * w, 3), np.uint8)
    for i, p in enumerate(panels):
        r, c = divmod(i, cols)
        canvas[r * h:(r + 1) * h, c * w:(c + 1) * w] = p
    return canvas


def run_compare(ws: Workspace, segment: int, takes: Optional[Sequence[int]] = None, include_input: bool = True,
                cols: int = 3, panel_size: int = 384) -> Path:
    plan = read_json(ws.p("segments.json"))
    d = ws.p(f"segments/{segment:03d}")
    if not d.is_dir():
        raise PipelineError(f"구간 {segment} 폴더가 없습니다: {d}")
    avail = existing_takes(d)
    takes = list(takes) if takes else avail
    bad = [t for t in takes if t not in avail]
    if bad or not takes:
        raise PipelineError(f"구간 {segment} 에서 사용할 수 없는 후보: {bad or '후보 없음'} (있는 후보: {avail})")
    items = [("input", d / "input.mp4")] if include_input else []
    for t in takes:
        meta = read_json(d / f"take_{t}.json") if (d / f"take_{t}.json").exists() else {}
        items.append((_ascii(f"take_{t} {meta.get('model', '')} s{meta.get('seed', '')} {meta.get('label', '')}").strip(), d / f"take_{t}.mp4"))
    streams = []
    for label, path in items:
        v = video_stream_info(path)
        streams.append((label, iter_frames(path, v["width"], v["height"])))
    out_dir = ws.p("compare"); out_dir.mkdir(exist_ok=True)
    out = out_dir / f"cmp_seg{segment:03d}_{timestamp()}.mp4"     # 항상 새 파일
    cols = min(cols, len(items))
    grid_w = cols * panel_size
    grid_h = math.ceil(len(items) / cols) * panel_size
    tmp = out.with_suffix(".silent.mp4")
    n = 0
    with FrameWriter(tmp, grid_w, grid_h, plan["fps_rational"], crf=12) as w:
        while True:
            panels = []
            for label, it in streams:
                f = next(it, None)
                if f is None:
                    break
                f = cv2.resize(f, (panel_size, panel_size), interpolation=cv2.INTER_AREA)
                cv2.putText(f, label[:40], (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(f, label[:40], (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                panels.append(f)
            if len(panels) < len(streams):
                break
            w.write(compose_grid(panels, cols))
            n += 1
    run([find_binary("ffmpeg"), "-y", "-v", "error", "-i", tmp, "-i", d / "audio.wav", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "256k", "-shortest", out], "비교 영상 오디오 결합")
    tmp.unlink(missing_ok=True)
    log(f"[compare] {n}프레임, 패널 {len(items)}개 -> {out}")
    return out
