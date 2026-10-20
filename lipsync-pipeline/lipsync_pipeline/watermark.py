"""서비스 워터마크(Meta AI, sync.so, Flow 마크 등) '경고'용 탐지. 제거 기능은 만들지 않는다.

원리: 로고/글자 워터마크는 프레임이 움직여도 같은 자리에 같은 픽셀로 남는다.
  -> 샘플 프레임들의 시간축 표준편차가 매우 낮으면서(정지) 공간적으로 윤곽(에지)이 뚜렷한 작은 덩어리를 후보로 본다.
카메라가 완전히 고정된 영상은 배경도 정지라 오탐이 날 수 있다 -> 후보가 화면 일부(기본 12% 이하)일 때만 보고한다.
"""
from __future__ import annotations

from typing import Optional, Sequence

import cv2
import numpy as np


def detect_static_overlays(frames: Sequence[np.ndarray], max_area_ratio: float = 0.12,
                           static_std: float = 3.0, edge_thr: float = 40.0) -> list[dict]:
    if len(frames) < 5:
        return []
    g = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in frames])
    h, w = g.shape[1:]
    tstd = g.std(axis=0)
    mean = g.mean(axis=0)
    gx = cv2.Sobel(mean, cv2.CV_32F, 1, 0); gy = cv2.Sobel(mean, cv2.CV_32F, 0, 1)
    edges = np.sqrt(gx ** 2 + gy ** 2)
    cand = ((tstd < static_std) & (edges > edge_thr)).astype(np.uint8)
    if cand.sum() == 0 or tstd.mean() < static_std:        # 영상 전체가 정지면 판단 불가
        return []
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (max(w // 40, 5), max(h // 60, 5)))
    cand = cv2.morphologyEx(cand, cv2.MORPH_CLOSE, k)
    n, _, stats, _ = cv2.connectedComponentsWithStats(cand, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if bw * bh < 0.0005 * w * h or bw * bh > max_area_ratio * w * h or area < 0.15 * bw * bh:
            continue
        out.append({"box": [int(x), int(y), int(bw), int(bh)], "area_ratio": round(bw * bh / (w * h), 4)})
    return out


def box_distance(a: Sequence[float], b: Sequence[float]) -> float:
    """두 bbox(x,y,w,h) 사이의 최소 거리 (겹치면 0)."""
    dx = max(a[0] - (b[0] + b[2]), b[0] - (a[0] + a[2]), 0)
    dy = max(a[1] - (b[1] + b[3]), b[1] - (a[1] + a[3]), 0)
    return float((dx * dx + dy * dy) ** 0.5)


def watermark_warnings(overlays: Sequence[dict], face_boxes: Sequence[Sequence[float]]) -> list[str]:
    if not overlays:
        return []
    msgs = [f"고정 오버레이(워터마크 의심) {len(overlays)}곳: " +
            ", ".join(f"(x={o['box'][0]}, y={o['box'][1]}, {o['box'][2]}x{o['box'][3]})" for o in overlays)]
    if face_boxes:
        fb = np.median(np.array(face_boxes, float), axis=0)
        near = [o for o in overlays if box_distance(o["box"], fb) < 0.5 * max(fb[2], fb[3])]
        if near:
            msgs.append("워터마크가 얼굴 근처에 있습니다 -> 립싱크 결과 품질에 영향을 줄 수 있습니다 (제거 기능은 제공하지 않습니다).")
    return msgs
