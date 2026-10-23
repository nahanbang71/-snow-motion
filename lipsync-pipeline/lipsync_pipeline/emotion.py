"""6단계 emotion: analysis.json 의 에너지/F0/비트로 고개 끄덕임·미세 움직임 파라미터를 만든다.

출력 단위: dx, dy 는 얼굴 크롭 한 변 대비 비율, rot 는 도(deg), scale 은 1 기준 증감.
numpy 만 사용하므로 GPU 없이 어디서나 실행/검증 가능.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d

from .utils import PipelineError, Workspace, archive_existing, log, read_json, write_json


@dataclass
class EmotionConfig:
    nod_amp: float = 0.012       # 비트당 끄덕임 세기 (크롭 대비)
    nod_peak_s: float = 0.09     # 끄덕임이 최대가 되는 시간
    sway_amp: float = 0.006      # 좌우 흔들림
    sway_period_s: float = 3.6
    tilt_deg: float = 1.2        # F0 에 따른 고개 기울임 최대각
    scale_amp: float = 0.006     # 에너지에 따른 미세 확대
    micro_amp: float = 0.0015    # 무작위 미세 움직임
    silence_gain: float = 0.3    # 무음 구간에서의 움직임 비율
    seed: int = 0


def _norm_energy(rms_db: np.ndarray, voiced: np.ndarray) -> np.ndarray:
    if not voiced.any():
        return np.zeros_like(rms_db)
    lo, hi = np.percentile(rms_db[voiced], [10, 95])
    return np.clip((rms_db - lo) / max(hi - lo, 1e-6), 0, 1)


def generate_params(pf: dict, cfg: EmotionConfig = EmotionConfig()) -> dict:
    fps, n = float(pf["fps"]), int(pf["n"])
    rms_db = np.array(pf["rms_db"], float)
    f0 = np.array(pf["f0"], float)
    voiced = np.array(pf["voiced"], bool)
    beat = np.array(pf["beat"], bool)
    sm = max(fps * 0.1, 0.5)
    energy = gaussian_filter1d(_norm_energy(rms_db, voiced), sm)
    gain = np.where(gaussian_filter1d(voiced.astype(float), fps * 0.3) > 0.3, 1.0, cfg.silence_gain)
    t = np.arange(n) / fps

    # 끄덕임: 비트마다 감마 모양 펄스 (peak 에서 최대 후 자연스럽게 복귀)
    impulses = np.zeros(n); impulses[beat] = 0.4 + 0.6 * energy[beat]
    klen = max(int(fps * cfg.nod_peak_s * 8), 3)
    tk = np.arange(klen) / fps / cfg.nod_peak_s
    kernel = tk * np.exp(1 - tk)
    nod = np.convolve(impulses, kernel)[:n]
    dy = cfg.nod_amp * nod * gain

    # 좌우 sway / 에너지 기반 확대
    dx = cfg.sway_amp * np.sin(2 * np.pi * t / cfg.sway_period_s) * (0.3 + 0.7 * energy) * gain
    scale = cfg.scale_amp * (energy - 0.5) * gain

    # F0: 음정이 중앙값보다 높을수록 고개를 살짝 들고(dy 감소) 기울임
    if voiced.any():
        med = np.median(f0[voiced])
        st = np.zeros(n); st[voiced] = 12 * np.log2(f0[voiced] / med)
        w = gaussian_filter1d(voiced.astype(float), sm) + 1e-6
        st = gaussian_filter1d(st, sm * 2) / w
        st = np.clip(st / 6.0, -1, 1) * (gaussian_filter1d(voiced.astype(float), sm) > 0.3)
    else:
        st = np.zeros(n)
    rot = cfg.tilt_deg * st * gain
    dy = dy - 0.3 * cfg.nod_amp * st

    rng = np.random.default_rng(cfg.seed)
    micro = gaussian_filter1d(rng.standard_normal((n, 3)), fps * 0.25, axis=0)
    micro /= max(micro.std(), 1e-9)
    amp = cfg.micro_amp * (0.5 + energy)
    dx = dx + amp * micro[:, 0]
    dy = dy + amp * micro[:, 1]
    rot = rot + 0.3 * cfg.tilt_deg * amp / max(cfg.micro_amp, 1e-9) * 0.1 * micro[:, 2]

    return {"fps": fps, "n": n, "config": asdict(cfg),
            "dx": np.round(dx, 6).tolist(), "dy": np.round(dy, 6).tolist(),
            "rot": np.round(rot, 4).tolist(), "scale": np.round(scale, 6).tolist()}


def apply_motion(patch: np.ndarray, dx: float, dy: float, rot: float, scale: float) -> np.ndarray:
    """정사각 패치에 이동/회전/확대를 적용 (경계는 반사)."""
    if dx == 0 and dy == 0 and rot == 0 and scale == 0:
        return patch
    h, w = patch.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), rot, 1.0 + scale)
    m[0, 2] += dx * w
    m[1, 2] += dy * h
    return cv2.warpAffine(patch, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def run_emotion(ws: Workspace, cfg: EmotionConfig = EmotionConfig()) -> dict:
    if not ws.analysis.exists():
        raise PipelineError("analysis.json 이 없습니다. `analyze` 단계를 먼저 실행해 주세요.")
    params = generate_params(read_json(ws.analysis)["per_frame"], cfg)
    archive_existing(ws, ws.emotion)
    write_json(ws.emotion, params)
    log(f"[emotion] {params['n']}프레임 파라미터 저장: {ws.emotion.name}")
    return params
