import json
import subprocess

import numpy as np
import pytest

from lipsync_pipeline import analyze as an
from lipsync_pipeline import separate as sp
from lipsync_pipeline.prepare import prepare
from lipsync_pipeline.utils import (PipelineError, Workspace, archive_existing, read_wav, sanitize_name,
                                    video_stream_info, write_wav)


def test_sanitize_name_keeps_korean_and_blocks_separators():
    assert sanitize_name("내 영상: 1/2") == "내 영상_ 1_2"
    with pytest.raises(PipelineError, match="비어"):
        sanitize_name("  ..  ")


def test_wav_roundtrip(tmp_path):
    x = (0.5 * np.sin(np.linspace(0, 100, 4410))).astype(np.float32)[:, None]
    write_wav(tmp_path / "a b.wav", 44100, x)
    sr, y = read_wav(tmp_path / "a b.wav")
    assert sr == 44100 and np.allclose(x, y, atol=1e-3)


def test_archive_existing_preserves(work):
    ws = Workspace.open("t", work, must_exist=False)
    f = ws.p("a.txt"); f.write_text("old")
    dest = archive_existing(ws, f)
    assert not f.exists() and (dest / "a.txt").read_text() == "old"


def test_prepare_outputs(samples, work):
    info = prepare(samples["video"], samples["audio"], work)          # 한글+공백 경로
    ws = Workspace.open("내 영상 샘플", work)
    v = video_stream_info(ws.video_noaudio)
    assert (v["width"], v["height"]) == (320, 240) and abs(v["fps"] - 25) < 0.01 and v["frames"] == 200
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(ws.video_noaudio)],
                         capture_output=True, text=True).stdout
    assert "audio" not in out                                           # 오디오 제거됨
    sr44, a44 = read_wav(ws.audio_44k); sr16, a16 = read_wav(ws.audio_16k)
    assert (sr44, a44.shape[1], sr16, a16.shape[1]) == (44100, 2, 16000, 1)
    assert abs(len(a44) / sr44 - 8.0) < 0.05 and abs(len(a16) / sr16 - 8.0) < 0.05
    assert json.loads(ws.info.read_text(encoding="utf-8"))["video"]["frames"] == info["video"]["frames"]


def test_prepare_errors_are_korean(work, tmp_path):
    with pytest.raises(PipelineError, match="영상 파일을 찾을 수 없습니다"):
        prepare(tmp_path / "없음.mp4", tmp_path / "없음.wav", work)


def test_prepare_rerun_archives_instead_of_overwriting(samples, work):
    prepare(samples["video"], samples["audio"], work)
    prepare(samples["video"], samples["audio"], work)
    assert any((work / "내 영상 샘플" / "_archive").iterdir())


# ------------------------------------------------------------ separate
def test_plan_chunks_cover_all_with_overlap():
    sr, n = 1000, 10_500
    spans = sp.plan_chunks(n, sr, chunk_sec=4, overlap_sec=0.5)
    assert spans[0][0] == 0 and spans[-1][1] == n
    for (a, b), (c, d) in zip(spans[:-1], spans[1:]):
        assert b - c == 500
    with pytest.raises(PipelineError):
        sp.plan_chunks(n, sr, chunk_sec=1, overlap_sec=0.6)


def test_chunked_separation_reconstructs_signal():
    sr = 8000
    t = np.arange(sr * 23) / sr
    x = np.stack([np.sin(2 * np.pi * 300 * t), np.sin(2 * np.pi * 500 * t)], 1).astype(np.float32)
    y = sp.separate_in_chunks(x, sr, lambda a, _: a * 0.5 + 0.0, chunk_sec=5, overlap_sec=1)
    assert np.allclose(y, x * 0.5, atol=1e-5)          # 크로스페이드 가중치 합이 1


def test_separate_passthrough_cli(samples, work):
    prepare(samples["video"], samples["audio"], work)
    ws = Workspace.open("내 영상 샘플", work)
    sp.separate(ws, backend="passthrough", chunk_sec=3, overlap_sec=0.5)
    assert ws.vocals.exists() and ws.vocals_16k.exists()
    with pytest.raises(PipelineError, match="demucs"):
        import sys
        if "demucs" in sys.modules or __import__("importlib").util.find_spec("demucs"):
            pytest.skip("demucs 설치됨")
        sp.separate(ws, backend="demucs")


# ------------------------------------------------------------ analyze
def test_f0_sine_and_silence():
    sr = 16000
    t = np.arange(sr * 2) / sr
    x = (0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    x[sr:] = 0
    hop = 160
    rms = an.compute_rms(x, hop)
    f0, conf = an.compute_f0(x, sr, hop, rms)
    voiced = f0[: 90]
    assert abs(np.median(voiced[voiced > 0]) - 220) < 2.2
    assert (voiced > 0).mean() > 0.9
    assert (f0[110:] == 0).all()


def test_segments_voiced_and_silence():
    sr, hop = 16000, 160
    x = np.zeros(sr * 8, np.float32)
    t = np.arange(sr * 8) / sr
    tone = 0.3 * np.sin(2 * np.pi * 220 * t)
    for a, b in ((0, 3), (3.8, 6.8), (7.6, 8)):
        x[int(a * sr):int(b * sr)] = tone[int(a * sr):int(b * sr)]
    rms_db = 20 * np.log10(an.compute_rms(x, hop) + 1e-9)
    segs = an.find_segments(rms_db, hop / sr)
    types = [s["type"] for s in segs]
    assert types == ["voiced", "silence", "voiced", "silence", "voiced"]
    assert abs(segs[1]["start"] - 3.0) < 0.1 and abs(segs[1]["end"] - 3.8) < 0.1


def test_beats_120bpm():
    sr = 16000
    x = np.zeros(sr * 12, np.float32)
    clicks = np.arange(0.25, 11.5, 0.5)
    tt = np.arange(int(0.03 * sr)) / sr
    burst = (np.sin(2 * np.pi * 1000 * tt) * np.exp(-tt * 150)).astype(np.float32)
    for c in clicks:
        i = int(c * sr); x[i:i + len(burst)] += burst
    res = an.analyze_audio(x, sr, fps=25, n_frames=300)
    assert abs(res["summary"]["tempo_bpm"] - 120) < 4
    beats = np.array(res["beats"])
    hit = np.mean([np.abs(beats - c).min() < 0.06 for c in clicks[2:-2]])
    assert hit >= 0.8
    pf = res["per_frame"]
    assert pf["n"] == 300 and len(pf["rms_db"]) == 300 and sum(pf["beat"]) >= 15


def test_analyze_stage_writes_json(samples, work):
    prepare(samples["video"], samples["audio"], work)
    ws = Workspace.open("내 영상 샘플", work)
    res = an.analyze(ws)
    data = json.loads(ws.analysis.read_text(encoding="utf-8"))
    assert data["per_frame"]["n"] == 200 and abs(data["summary"]["f0_median_hz"] - 220) < 3
    assert [s["type"] for s in data["segments"]] == ["voiced", "silence", "voiced", "silence", "voiced"]
