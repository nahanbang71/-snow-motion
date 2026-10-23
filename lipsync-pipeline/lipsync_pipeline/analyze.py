"""3단계 analyze: 보컬에서 F0(음높이), RMS 에너지, 발성/무음 구간, 비트를 추출해 analysis.json 으로 저장.

librosa 없이 numpy/scipy 만 사용 (Windows/Colab 어디서나 설치 부담 없음).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from scipy import signal
from scipy.ndimage import median_filter, uniform_filter1d

from .utils import PipelineError, archive_existing, Workspace, log, read_json, read_wav, to_mono, write_json

ANALYSIS_SR = 16000


def _resample(x: np.ndarray, sr: int, target: int = ANALYSIS_SR) -> np.ndarray:
    if sr == target:
        return x
    from math import gcd
    g = gcd(sr, target)
    return signal.resample_poly(x, target // g, sr // g).astype(np.float32)


def _frames(x: np.ndarray, size: int, hop: int) -> np.ndarray:
    """중심 정렬 프레임 (n_frames, size). 양끝은 0 으로 패딩."""
    pad = size // 2
    xp = np.pad(x, (pad, pad + hop))
    n = 1 + len(x) // hop
    idx = np.arange(size)[None, :] + hop * np.arange(n)[:, None]
    return xp[idx]


def compute_rms(x: np.ndarray, hop: int, size: int = 400) -> np.ndarray:
    fr = _frames(x, size, hop)
    return np.sqrt((fr.astype(np.float64) ** 2).mean(axis=1)).astype(np.float32)


def compute_f0(x: np.ndarray, sr: int, hop: int, rms: np.ndarray, fmin: float = 70.0,
               fmax: float = 1100.0, frame: int = 1024, voicing_thr: float = 0.45,
               silence_db: float = -50.0) -> tuple[np.ndarray, np.ndarray]:
    """정규화 자기상관 기반 F0. 반환: (f0 Hz, 무성음은 0), 확신도."""
    lag_min, lag_max = int(sr / fmax), int(sr / fmin)
    fr = _frames(x, frame, hop).astype(np.float32)
    n = len(fr)
    f0 = np.zeros(n, dtype=np.float32)
    conf = np.zeros(n, dtype=np.float32)
    nfft = 1 << int(np.ceil(np.log2(frame * 2)))
    win = np.hanning(frame).astype(np.float32)
    norm = np.arange(frame, 0, -1, dtype=np.float32) / frame       # 겹치는 샘플 수 보정
    r_win = np.fft.irfft(np.abs(np.fft.rfft(win, nfft)) ** 2)[:frame] / norm   # 창함수 자기상관 보정
    r_win = np.maximum(r_win / r_win[0], 1e-3)
    for s in range(0, n, 2048):
        blk = fr[s:s + 2048]
        blk = (blk - blk.mean(axis=1, keepdims=True)) * win
        r = np.fft.irfft(np.abs(np.fft.rfft(blk, nfft, axis=1)) ** 2, axis=1)[:, :lag_max + 2]
        e0 = r[:, 0:1] + 1e-12
        rn = r / e0 / r_win[None, :lag_max + 2]
        seg = rn[:, lag_min - 1:lag_max + 2]
        # 국소 최대점 후보 중 최대값의 90% 이상인 첫 번째(가장 짧은 주기) -> 옥타브 오류 억제
        is_peak = (seg[:, 1:-1] > seg[:, :-2]) & (seg[:, 1:-1] >= seg[:, 2:])
        cand = np.where(is_peak, seg[:, 1:-1], -np.inf)
        mx = cand.max(axis=1)
        ok = np.isfinite(mx) & (mx > 0)
        first = np.argmax(cand >= (0.9 * mx)[:, None], axis=1)
        k = first + 1                                                # seg 내 인덱스
        rows = np.arange(len(blk))
        a, b, c = seg[rows, k - 1], seg[rows, k], seg[rows, k + 1]
        denom = a - 2 * b + c
        shift = 0.5 * (a - c) / np.where(np.abs(denom) > 1e-9, denom, np.inf)
        lag = (lag_min - 1) + k + np.clip(shift, -1, 1)
        f = sr / lag
        f0[s:s + len(blk)] = np.where(ok, f, 0)
        conf[s:s + len(blk)] = np.where(ok, np.clip(mx, 0, 1), 0)
    rms_db = 20 * np.log10(rms[:n] + 1e-9)
    voiced = (conf >= voicing_thr) & (rms_db > silence_db) & (f0 >= fmin) & (f0 <= fmax)
    f0 = np.where(voiced, f0, 0.0)
    # 튀는 값 제거 (유성음 구간에서만 중앙값 필터)
    sm = median_filter(f0, size=5, mode="nearest")
    f0 = np.where(voiced & (sm > 0), sm, 0.0).astype(np.float32)
    return f0, conf


def find_segments(rms_db: np.ndarray, hop_s: float, thr_db: Optional[float] = None,
                  min_gap_s: float = 0.25, min_dur_s: float = 0.12) -> list[dict]:
    """에너지 기반 발성/무음 구간. 짧은 틈은 메우고 짧은 발성은 버린다."""
    if thr_db is None:
        thr_db = max(-55.0, float(np.percentile(rms_db, 95)) - 30.0)
    active = rms_db > thr_db
    # 경계 찾기
    edges = np.flatnonzero(np.diff(np.r_[False, active, False].astype(int)))
    runs = [[int(a), int(b)] for a, b in zip(edges[::2], edges[1::2])]
    merged: list[list[int]] = []
    for r in runs:
        if merged and (r[0] - merged[-1][1]) * hop_s < min_gap_s:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    merged = [r for r in merged if (r[1] - r[0]) * hop_s >= min_dur_s]
    total = len(rms_db)
    segs, cur = [], 0
    for a, b in merged:
        if a > cur:
            segs.append({"start": round(cur * hop_s, 3), "end": round(a * hop_s, 3), "type": "silence"})
        segs.append({"start": round(a * hop_s, 3), "end": round(b * hop_s, 3), "type": "voiced"})
        cur = b
    if cur < total:
        segs.append({"start": round(cur * hop_s, 3), "end": round(total * hop_s, 3), "type": "silence"})
    return segs


def onset_envelope(x: np.ndarray, sr: int, hop: int) -> np.ndarray:
    """로그 압축 스펙트럼 플럭스. 프레임 i 는 시간 i*hop/sr 에 대응."""
    nper = 1024
    _, _, Z = signal.stft(x, fs=sr, nperseg=nper, noverlap=nper - hop, boundary="zeros", padded=True)
    mag = np.log1p(10.0 * np.abs(Z))
    flux = np.maximum(np.diff(mag, axis=1, prepend=mag[:, :1]), 0).sum(axis=0)
    flux = flux - uniform_filter1d(flux, size=int(0.5 * sr / hop) | 1)   # 지역 평균 제거
    flux = np.maximum(flux, 0)
    sd = flux.std()
    return (flux / sd if sd > 0 else flux).astype(np.float32)


def estimate_tempo(env: np.ndarray, hop_s: float, bpm_min: float = 50, bpm_max: float = 200,
                   prior_bpm: float = 120.0) -> float:
    if len(env) < int(2.0 / hop_s) or env.max() <= 0:
        return 0.0
    e = env - env.mean()
    ac = signal.correlate(e, e, mode="full", method="fft")[len(e) - 1:]
    lags = np.arange(int(60 / bpm_max / hop_s), int(60 / bpm_min / hop_s) + 1)
    lags = lags[lags < len(ac)]
    bpm = 60.0 / (lags * hop_s)
    weight = np.exp(-0.5 * (np.log2(bpm / prior_bpm) / 1.0) ** 2)    # 120bpm 부근 선호
    best = lags[np.argmax(ac[lags] * weight)]
    # 포물선 보간
    if 1 <= best < len(ac) - 1:
        a, b, c = ac[best - 1], ac[best], ac[best + 1]
        d = a - 2 * b + c
        best = best + (0.5 * (a - c) / d if abs(d) > 1e-12 else 0.0)
    return float(60.0 / (best * hop_s))


def track_beats(env: np.ndarray, hop_s: float, bpm: float, tightness: float = 100.0) -> np.ndarray:
    """Ellis(2007) 동적계획 비트 추적. 반환: 비트 프레임 인덱스."""
    if bpm <= 0 or len(env) == 0:
        return np.zeros(0, dtype=int)
    period = 60.0 / bpm / hop_s
    n = len(env)
    score = env.astype(np.float64).copy()
    back = -np.ones(n, dtype=int)
    for i in range(n):
        lo, hi = int(i - 2 * period), int(i - period / 2)
        if hi < 0:
            continue
        lo = max(lo, 0)
        if hi < lo:
            continue
        js = np.arange(lo, hi + 1)
        pen = -tightness * np.log((i - js) / period) ** 2
        cand = score[js] + pen
        k = int(np.argmax(cand))
        if cand[k] > 0:
            score[i] = env[i] + cand[k]
            back[i] = js[k]
    tail = max(int(n - period), 0)
    i = tail + int(np.argmax(score[tail:]))
    beats = [i]
    while back[i] >= 0:
        i = back[i]
        beats.append(i)
    beats = np.array(beats[::-1], dtype=int)
    # 에너지가 거의 없는 비트(무음 구간)는 제거
    keep = env[beats] > 0.25 * np.median(env[beats]) if len(beats) else np.zeros(0, bool)
    return beats[keep]


def to_video_frames(fps: float, n_frames: int, hop_s: float, rms_db: np.ndarray, f0: np.ndarray,
                    beats_s: np.ndarray) -> dict:
    """분석 프레임(hop) -> 영상 프레임 단위 요약. emotion 단계의 입력."""
    t0 = np.arange(n_frames) / fps
    t1 = (np.arange(n_frames) + 1) / fps
    i0 = np.clip((t0 / hop_s).astype(int), 0, len(rms_db) - 1)
    i1 = np.clip(np.ceil(t1 / hop_s).astype(int), i0 + 1, len(rms_db))
    r_out, f_out, v_out = np.zeros(n_frames), np.zeros(n_frames), np.zeros(n_frames, dtype=bool)
    for k in range(n_frames):
        r_out[k] = rms_db[i0[k]:i1[k]].mean()
        seg = f0[i0[k]:i1[k]]
        seg = seg[seg > 0]
        if len(seg) * 2 >= (i1[k] - i0[k]):
            f_out[k], v_out[k] = float(np.median(seg)), True
    beat_flag = np.zeros(n_frames, dtype=bool)
    bi = np.floor(beats_s * fps).astype(int)
    beat_flag[bi[(bi >= 0) & (bi < n_frames)]] = True
    return {"fps": fps, "n": n_frames, "rms_db": np.round(r_out, 2).tolist(),
            "f0": np.round(f_out, 2).tolist(), "voiced": v_out.astype(int).tolist(),
            "beat": beat_flag.astype(int).tolist()}


def analyze_audio(x: np.ndarray, sr: int, fps: float, n_frames: int, hop_ms: float = 10.0) -> dict:
    x = _resample(x.astype(np.float32), sr)
    sr = ANALYSIS_SR
    hop = int(round(sr * hop_ms / 1000))
    hop_s = hop / sr
    rms = compute_rms(x, hop)
    rms_db = 20 * np.log10(rms + 1e-9)
    f0, conf = compute_f0(x, sr, hop, rms)
    n = min(len(rms), len(f0))
    rms, rms_db, f0, conf = rms[:n], rms_db[:n], f0[:n], conf[:n]
    segments = find_segments(rms_db, hop_s)
    env = onset_envelope(x, sr, hop)
    bpm = estimate_tempo(env, hop_s)
    beat_idx = track_beats(env, hop_s, bpm)
    beats_s = beat_idx * hop_s
    voiced_f0 = f0[f0 > 0]
    return {
        "hop_s": hop_s, "duration": len(x) / sr, "sample_rate": sr,
        "summary": {
            "tempo_bpm": round(bpm, 2), "n_beats": int(len(beats_s)),
            "f0_median_hz": round(float(np.median(voiced_f0)), 2) if len(voiced_f0) else 0.0,
            "voiced_ratio": round(float((f0 > 0).mean()), 3),
            "rms_db_p95": round(float(np.percentile(rms_db, 95)), 2),
        },
        "segments": segments,
        "beats": np.round(beats_s, 3).tolist(),
        "rms": np.round(rms, 5).tolist(),
        "rms_db": np.round(rms_db, 2).tolist(),
        "f0": np.round(f0, 2).tolist(),
        "f0_confidence": np.round(conf, 3).tolist(),
        "per_frame": to_video_frames(fps, n_frames, hop_s, rms_db, f0, beats_s),
    }


def analyze(ws: Workspace, hop_ms: float = 10.0, fps: Optional[float] = None) -> dict:
    src = next((p for p in (ws.vocals_16k, ws.vocals, ws.audio_16k) if p.exists()), None)
    if src is None:
        raise PipelineError("분석할 오디오가 없습니다. `prepare` (및 `separate`) 단계를 먼저 실행해 주세요.")
    if src == ws.audio_16k:
        log("[경고] 보컬 분리 결과가 없어 전체 믹스로 분석합니다. 정확도가 떨어질 수 있습니다.")
    if ws.info.exists():
        v = read_json(ws.info)["video"]
        fps, n_frames = fps or v["fps"], v["frames"]
    else:
        if fps is None:
            raise PipelineError("info.json 이 없어 --fps 를 직접 지정해야 합니다.")
        n_frames = None
    sr, data = read_wav(src)
    x = to_mono(data)
    if n_frames is None:
        n_frames = int(len(x) / sr * fps)
    log(f"[analyze] {src.name} 분석 중 ({len(x) / sr:.1f}초)...")
    result = analyze_audio(x, sr, fps, n_frames, hop_ms)
    result["source"] = src.name
    archive_existing(ws, ws.analysis)
    write_json(ws.analysis, result)
    s = result["summary"]
    log(f"[analyze] 완료: 템포 {s['tempo_bpm']}bpm, 비트 {s['n_beats']}개, "
        f"F0 중앙값 {s['f0_median_hz']}Hz, 발성 비율 {s['voiced_ratio']:.0%}")
    return result
