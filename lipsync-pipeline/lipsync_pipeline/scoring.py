"""후보 자동 점수 (참고용 — 최종 선택은 사용자가 한다).

- sync_proxy : 입 영역 움직임과 오디오 에너지의 상관(±6프레임 지연 탐색). CPU 에서 계산되는 간이 지표.
- SyncNetScorer: SyncNet 방식(LSE-D/LSE-C) 점수. 외부 저장소가 필요한 스켈레톤 (TODO 미검증).
- flicker    : 프레임 간 떨림. 입 아래쪽이 아닌 얼굴 윗부분이 원본 대비 얼마나 흔들렸는지 + 입 영역 가속도.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np

from .utils import PipelineError, iter_frames, read_wav, to_mono, video_stream_info

MOUTH_REGION = (0.55, 0.92, 0.25, 0.75)    # y0, y1, x0, x1 (크롭 대비 비율)


def _gray_frames(path: Path) -> np.ndarray:
    v = video_stream_info(path)
    fr = [f.astype(np.float32).mean(axis=2) for f in iter_frames(path, v["width"], v["height"])]
    if not fr:
        raise PipelineError(f"프레임을 읽을 수 없습니다: {path}")
    return np.stack(fr)


def audio_envelope(audio: Path, fps: float, n: int) -> np.ndarray:
    sr, data = read_wav(audio)
    x = to_mono(data)
    out = np.zeros(n)
    for i in range(n):
        seg = x[int(i / fps * sr):int((i + 1) / fps * sr)]
        out[i] = np.sqrt((seg ** 2).mean()) if len(seg) else 0.0
    return out


def sync_proxy(gray: np.ndarray, audio: Path, fps: float, max_lag: int = 6,
               region: tuple = MOUTH_REGION) -> dict:
    h, w = gray.shape[1:]
    y0, y1, x0, x1 = region
    roi = gray[:, int(h * y0):int(h * y1), int(w * x0):int(w * x1)]
    motion = np.abs(np.diff(roi, axis=0)).mean(axis=(1, 2))           # n-1
    env = audio_envelope(audio, fps, len(gray))[1:]
    best = (-2.0, 0)
    for lag in range(-max_lag, max_lag + 1):
        a, b = (motion[lag:], env[:len(env) - lag]) if lag >= 0 else (motion[:lag], env[-lag:])
        m = min(len(a), len(b))
        if m < 4 or a[:m].std() < 1e-9 or b[:m].std() < 1e-9:
            continue
        c = float(np.corrcoef(a[:m], b[:m])[0, 1])
        if c > best[0]:
            best = (c, lag)
    corr = best[0] if best[0] > -2 else 0.0
    return {"corr": round(corr, 3), "lag_frames": best[1]}


def flicker(take_gray: np.ndarray, ref_gray: np.ndarray, region: tuple = MOUTH_REGION) -> dict:
    n = min(len(take_gray), len(ref_gray))
    t, r = take_gray[:n], ref_gray[:n]
    h = t.shape[1]
    top = slice(0, int(h * region[0]))
    d_t, d_r = np.diff(t[:, top], axis=0), np.diff(r[:, top], axis=0)
    upper = float(np.abs(d_t - d_r).mean())
    y0, y1, x0, x1 = region
    w = t.shape[2]
    m = t[:, int(h * y0):int(h * y1), int(w * x0):int(w * x1)]
    accel = float(np.abs(np.diff(m, n=2, axis=0)).mean()) if n > 2 else 0.0
    return {"flicker_upper": round(upper, 3), "mouth_accel": round(accel, 3),
            "stable_pct": round(100 * float(np.exp(-upper / 4.0)), 1)}


class SyncNetScorer:
    """TODO(미검증): syncnet_python(joonson/syncnet_python) 의 LSE-D / LSE-C.

    사용법(공식 README 기억 기반, 설치 버전과 대조할 것):
      python run_pipeline.py --videofile X.mp4 --reference name --data_dir tmp
      python run_syncnet.py  --videofile X.mp4 --reference name --data_dir tmp
    SYNCNET_DIR 환경변수가 없으면 None 을 돌려주고 점수 표시에서 빠진다.
    """

    def available(self) -> bool:
        return bool(os.environ.get("SYNCNET_DIR"))

    def score(self, video: Path, audio: Path) -> Optional[dict]:
        if not self.available():
            return None
        raise NotImplementedError("SyncNet 점수 계산은 GPU 환경에서 구현/검증이 필요합니다 (TODO).")


def score_take(take: Path, ref: Path, audio: Path, fps: float) -> dict:
    tg, rg = _gray_frames(take), _gray_frames(ref)
    out = {"sync_proxy": sync_proxy(tg, audio, fps), **flicker(tg, rg)}
    try:
        sn = SyncNetScorer().score(take, audio)
    except NotImplementedError:
        sn = None
    if sn:
        out["syncnet"] = sn
    return out
