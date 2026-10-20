"""2단계 separate: Demucs 로 보컬 분리. 긴 곡은 겹치는 구간으로 나눠 처리한 뒤 크로스페이드로 이어 붙인다."""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Callable

import numpy as np

from .utils import (PipelineError, Workspace, archive_existing, find_binary, log, read_wav, run, write_wav)

# (구간 오디오 (n, 2) float32, 샘플레이트) -> 보컬 (n, 2)
ChunkSeparator = Callable[[np.ndarray, int], np.ndarray]


def plan_chunks(n: int, sr: int, chunk_sec: float, overlap_sec: float) -> list[tuple[int, int]]:
    """전체 길이 n 샘플을 (start, end) 구간들로 나눈다. 인접 구간은 overlap 만큼 겹친다."""
    if chunk_sec <= 0 or overlap_sec < 0 or overlap_sec * 2 >= chunk_sec:
        raise PipelineError("구간 길이는 0보다 크고, 겹침(overlap)의 2배보다 커야 합니다.")
    size, ov = int(chunk_sec * sr), int(overlap_sec * sr)
    if n <= size:
        return [(0, n)]
    step = size - ov
    spans, start = [], 0
    while True:
        end = min(start + size, n)
        spans.append((start, end))
        if end >= n:
            break
        start += step
    # 마지막 구간이 겹침보다 짧으면 앞 구간에 흡수
    if len(spans) > 1 and spans[-1][1] - spans[-1][0] <= ov:
        spans.pop()
        spans[-1] = (spans[-1][0], n)
    return spans


def separate_in_chunks(audio: np.ndarray, sr: int, separator: ChunkSeparator,
                       chunk_sec: float = 60.0, overlap_sec: float = 2.0) -> np.ndarray:
    """audio (n, ch) 를 구간별로 separator 에 넣고 겹침 구간을 선형 크로스페이드로 합친다."""
    n = len(audio)
    spans = plan_chunks(n, sr, chunk_sec, overlap_sec)
    out = np.zeros_like(audio, dtype=np.float32)
    ov = int(overlap_sec * sr)
    for i, (s, e) in enumerate(spans):
        log(f"[separate] 구간 {i + 1}/{len(spans)} ({s / sr:.1f}s ~ {e / sr:.1f}s)")
        part = np.asarray(separator(audio[s:e], sr), dtype=np.float32)
        if part.shape != audio[s:e].shape:
            raise PipelineError(f"분리 결과 길이가 입력과 다릅니다: {part.shape} != {audio[s:e].shape}")
        w = np.ones(e - s, dtype=np.float32)
        if i > 0:
            k = min(ov, e - s)
            w[:k] = np.linspace(0.0, 1.0, k, endpoint=False, dtype=np.float32) if k else w[:0]
        if i < len(spans) - 1:
            k = min(ov, e - s)
            w[-k:] = np.minimum(w[-k:], np.linspace(1.0, 0.0, k, endpoint=False, dtype=np.float32))
        out[s:e] += part * w[:, None]
    return out


def demucs_separator(model: str, device: str, workdir: Path) -> ChunkSeparator:
    """Demucs CLI(`python -m demucs`)를 구간마다 호출하는 분리기."""

    def _run(chunk: np.ndarray, sr: int) -> np.ndarray:
        inp, outdir = workdir / "chunk_in.wav", workdir / "chunk_out"
        shutil.rmtree(outdir, ignore_errors=True)
        write_wav(inp, sr, chunk)
        run([sys.executable, "-m", "demucs", "-n", model, "--two-stems=vocals", "-d", device,
             "-o", outdir, "--filename", "{stem}.{ext}", inp], "Demucs 보컬 분리")
        found = list(outdir.rglob("vocals.wav"))
        if not found:
            raise PipelineError("Demucs 출력에서 vocals.wav 를 찾을 수 없습니다.")
        vsr, vocals = read_wav(found[0])
        if vsr != sr or len(vocals) != len(chunk):
            n = min(len(vocals), len(chunk))   # Demucs 가 1~2샘플 차이를 낼 수 있음
            fixed = np.zeros_like(chunk)
            fixed[:n] = vocals[:n, : chunk.shape[1]]
            return fixed
        return vocals

    return _run


def separate(ws: Workspace, backend: str = "demucs", model: str = "htdemucs", device: str = "cpu",
             chunk_sec: float = 60.0, overlap_sec: float = 2.0) -> Path:
    ws.require(ws.audio_44k, hint="먼저 `prepare` 단계를 실행해 주세요.")
    sr, audio = read_wav(ws.audio_44k)
    if audio.shape[1] == 1:
        audio = np.repeat(audio, 2, axis=1)

    if backend == "demucs":
        try:
            import demucs  # noqa: F401
        except ImportError as e:
            raise PipelineError(
                "demucs 가 설치되어 있지 않습니다. `pip install demucs` (torch 포함) 후 다시 실행하세요. "
                "테스트용으로 보컬 분리를 건너뛰려면 --backend passthrough 를 사용하세요."
            ) from e
        tmp = Path(tempfile.mkdtemp(prefix="demucs_"))
        try:
            sep = demucs_separator(model, device, tmp)
            vocals = separate_in_chunks(audio, sr, sep, chunk_sec, overlap_sec)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    elif backend == "passthrough":
        log("[separate] passthrough: 분리 없이 원본을 그대로 보컬로 사용합니다 (테스트용).")
        vocals = separate_in_chunks(audio, sr, lambda a, _sr: a, chunk_sec, overlap_sec)
    else:
        raise PipelineError(f"알 수 없는 backend: {backend} (demucs | passthrough)")

    archive_existing(ws, ws.vocals, ws.vocals_16k)
    write_wav(ws.vocals, sr, vocals)
    run([find_binary("ffmpeg"), "-y", "-v", "error", "-i", ws.vocals, "-ar", "16000", "-ac", "1",
         "-c:a", "pcm_s16le", ws.vocals_16k], "보컬 16kHz 변환")
    log(f"[separate] 완료: {ws.vocals.name}, {ws.vocals_16k.name}")
    return ws.vocals
