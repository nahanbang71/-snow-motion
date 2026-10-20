"""장면 전환(컷) 감지 + 컷별 얼굴 리포트(cuts_report.csv) + 립싱크 적용 가능 프레임 판정.

범위: 이 프로그램은 완성된 영상/음원에 "립싱크만" 적용한다. 영상·음원 생성 기능은 없다.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional, Sequence

import cv2
import numpy as np

from .utils import (PipelineError, Workspace, archive_existing, iter_frames, log, read_json,
                    video_stream_info, write_json)

THUMB = (64, 36)


def frame_signature(frame: np.ndarray) -> np.ndarray:
    return cv2.resize(frame, THUMB, interpolation=cv2.INTER_AREA)


def _hist(t: np.ndarray, bins: int = 8) -> np.ndarray:
    h = np.concatenate([np.bincount((t[..., c] // (256 // bins)).ravel(), minlength=bins) for c in range(3)])
    return h / max(h.sum(), 1)


def signature_distances(sigs: Sequence[np.ndarray]) -> np.ndarray:
    """연속 프레임 간 거리 (0~1). d[i] = sig[i-1] 과 sig[i] 의 차이, d[0]=0."""
    d = np.zeros(len(sigs))
    hs = [_hist(s) for s in sigs]
    for i in range(1, len(sigs)):
        pix = np.abs(sigs[i].astype(np.int16) - sigs[i - 1].astype(np.int16)).mean() / 255.0
        hist = 0.5 * np.abs(hs[i] - hs[i - 1]).sum()
        d[i] = 0.5 * pix + 0.5 * hist
    return d


def cuts_from_distances(d: np.ndarray, fps: float, abs_thr: float = 0.15, peak_ratio: float = 2.0,
                        window: int = 5, min_len_s: float = 0.4) -> list[int]:
    """컷이 시작되는 프레임 인덱스 목록(0 제외). 주변보다 뚜렷하게 튀는 변화만 컷으로 본다."""
    n = len(d)
    found: list[int] = []
    for i in range(1, n):
        if d[i] < abs_thr:
            continue
        lo, hi = max(0, i - window), min(n, i + window + 1)
        others = np.concatenate([d[lo:i], d[i + 1:hi]])
        if len(others) == 0 or d[i] > peak_ratio * others.max():
            found.append(i)
    min_len = max(int(round(min_len_s * fps)), 1)
    kept: list[int] = []
    for i in found:
        if kept and i - kept[-1] < min_len:
            if d[i] > d[kept[-1]]:
                kept[-1] = i
            continue
        kept.append(i)
    return [i for i in kept if i >= min_len]


def cut_ranges(starts: Sequence[int], n_frames: int) -> list[tuple[int, int]]:
    """컷 시작 인덱스 -> [(start, end) 반열린 구간] 목록."""
    b = [0, *sorted(set(starts)), n_frames]
    return [(b[i], b[i + 1]) for i in range(len(b) - 1) if b[i + 1] > b[i]]


def run_cuts(ws: Workspace, abs_thr: float = 0.15, min_len_s: float = 0.4) -> dict:
    ws.require(ws.video_noaudio, hint="먼저 `prepare` 단계를 실행해 주세요.")
    v = video_stream_info(ws.video_noaudio)
    sigs = [frame_signature(f) for f in iter_frames(ws.video_noaudio, v["width"], v["height"])]
    d = signature_distances(sigs)
    starts = cuts_from_distances(d, v["fps"], abs_thr, min_len_s=min_len_s)
    ranges = cut_ranges(starts, len(sigs))
    result = {"fps": v["fps"], "n_frames": len(sigs), "cuts": [list(r) for r in ranges],
              "cut_starts": starts, "params": {"abs_thr": abs_thr, "min_len_s": min_len_s}}
    archive_existing(ws, ws.p("cuts.json"))
    write_json(ws.p("cuts.json"), result)
    log(f"[cuts] 장면 전환 {len(starts)}회 -> 컷 {len(ranges)}개 (cuts.json)")
    return result


# ---------------------------------------------------------------- 립싱크 적용 가능 프레임 판정

def eligible_mask(frames: Sequence[dict], ranges: Sequence[tuple[int, int]], fps: float,
                  min_face_px: int = 96, max_yaw: float = 45.0, max_pitch: float = 40.0,
                  skip_occluded: bool = True, max_gap_s: float = 0.3, min_run_s: float = 0.5) -> np.ndarray:
    """프레임별 '립싱크를 적용해도 되는가'. 얼굴 없음/너무 작음/측면/입 가려짐은 제외.
    컷을 넘지 않고, 짧은 검출 끊김은 메우고, 짧은 구간은 버린다."""
    n = len(frames)
    ok = np.zeros(n, bool)
    for i, f in enumerate(frames):
        if not f["detected"]:
            continue
        w, h = f["face"][2], f["face"][3]
        yaw, pitch = f.get("yaw"), f.get("pitch")
        good = max(w, h) >= min_face_px
        good = good and (yaw is None or abs(yaw) <= max_yaw) and (pitch is None or abs(pitch) <= max_pitch)
        if skip_occluded:
            good = good and not f.get("occluded", False)
        ok[i] = good
    gap, min_run = int(round(max_gap_s * fps)), max(int(round(min_run_s * fps)), 1)
    out = np.zeros(n, bool)
    for s, e in ranges:
        seg = ok[s:e].copy()
        idx = np.flatnonzero(seg)
        for a, b in zip(idx[:-1], idx[1:]):          # 짧은 끊김 메우기
            if 1 < b - a <= gap + 1:
                seg[a:b] = True
        edges = np.flatnonzero(np.diff(np.r_[False, seg, False].astype(int)))
        for a, b in zip(edges[::2], edges[1::2]):
            if b - a >= min_run:
                out[s + a:s + b] = True
    return out


def eligible_spans(mask: np.ndarray) -> list[tuple[int, int]]:
    edges = np.flatnonzero(np.diff(np.r_[False, mask, False].astype(int)))
    return [(int(a), int(b)) for a, b in zip(edges[::2], edges[1::2])]


# ---------------------------------------------------------------- 컷별 리포트

REPORT_COLUMNS = ["cut", "start_frame", "end_frame", "start_s", "end_s", "frames", "face_ratio",
                  "face_px_median", "face_size_ratio", "yaw_deg_median", "pitch_deg_median", "roll_deg_median",
                  "eye_closed_ratio", "mouth_occluded_ratio", "lipsync_ratio", "decision", "warnings"]


def _med(vals: list) -> Optional[float]:
    vals = [v for v in vals if v is not None]
    return float(np.median(vals)) if vals else None


def make_report(frames: Sequence[dict], ranges: Sequence[tuple[int, int]], fps: float, frame_w: int,
                frame_h: int, mask: np.ndarray, min_face_px: int = 96, warn_yaw: float = 25.0,
                warn_pitch: float = 25.0, warn_roll: float = 20.0, max_occluded: float = 0.15,
                max_eye_closed: float = 0.3) -> list[dict]:
    rows = []
    r1 = lambda v, k=1: "" if v is None else round(v, k)
    for ci, (s, e) in enumerate(ranges, 1):
        fr = frames[s:e]
        det = [f for f in fr if f["detected"]]
        n = e - s
        face_ratio = len(det) / n
        px = _med([max(f["face"][2], f["face"][3]) for f in det])
        yaw, pitch, roll = (_med([f.get(k) for f in det]) for k in ("yaw", "pitch", "roll"))
        eyes = [f.get("eye_closed") for f in det if f.get("eye_closed") is not None]
        eye_ratio = (sum(eyes) / len(eyes)) if eyes else None
        occ_ratio = (sum(1 for f in det if f.get("occluded")) / len(det)) if det else 0.0
        lip_ratio = float(mask[s:e].mean())
        warns = []
        if not det:
            warns.append("얼굴 미검출")
        else:
            if px < min_face_px:
                warns.append(f"얼굴이 너무 작음({px:.0f}px)")
            if face_ratio < 0.8:
                warns.append(f"얼굴 검출 불안정({face_ratio:.0%})")
            if yaw is not None and abs(yaw) > warn_yaw:
                warns.append(f"정면 아님(좌우 회전 {yaw:+.0f}°)")
            if pitch is not None and abs(pitch) > warn_pitch:
                warns.append(f"정면 아님(상하 각도 {pitch:+.0f}°)")
            if roll is not None and abs(roll) > warn_roll:
                warns.append(f"고개 기울어짐({roll:+.0f}°)")
            if occ_ratio > max_occluded:
                warns.append(f"입 가려짐 의심(마이크/손/머리카락 등, {occ_ratio:.0%} 프레임)")
            if eye_ratio is not None and eye_ratio > max_eye_closed:
                warns.append(f"눈 감김 많음({eye_ratio:.0%} 프레임)")
        decision = "skip" if lip_ratio == 0 else ("apply_with_warning" if warns else "apply")
        rows.append({
            "cut": ci, "start_frame": s, "end_frame": e, "start_s": round(s / fps, 3), "end_s": round(e / fps, 3),
            "frames": n, "face_ratio": round(face_ratio, 3), "face_px_median": r1(px),
            "face_size_ratio": "" if px is None else round(px / min(frame_w, frame_h), 3),
            "yaw_deg_median": r1(yaw), "pitch_deg_median": r1(pitch), "roll_deg_median": r1(roll),
            "eye_closed_ratio": "" if eye_ratio is None else round(eye_ratio, 3),
            "mouth_occluded_ratio": round(occ_ratio, 3), "lipsync_ratio": round(lip_ratio, 3),
            "decision": decision, "warnings": " | ".join(warns),
        })
    return rows


def write_report_csv(path: Path, rows: list[dict]) -> None:
    # utf-8-sig: Windows Excel 에서 한글이 깨지지 않도록 BOM 포함
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=REPORT_COLUMNS)
        w.writeheader()
        w.writerows(rows)
