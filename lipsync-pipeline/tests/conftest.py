import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg 필요")


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *map(str, args)], check=True)


@pytest.fixture(scope="session")
def samples(tmp_path_factory):
    """합성 샘플: testsrc(4초) + smptebars(4초) 이어붙인 8초 영상(= 장면 전환 1회), 무음 구간이 있는 sine 음원.
    한글 + 공백 파일명으로 만들어 경로 처리도 함께 검증한다."""
    d = tmp_path_factory.mktemp("샘플 폴더")
    video, audio = d / "내 영상 샘플.mp4", d / "내 노래 음원.wav"
    _ff("-f", "lavfi", "-i", "testsrc=size=320x240:rate=25:duration=4",
        "-f", "lavfi", "-i", "smptebars=size=320x240:rate=25:duration=4",
        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]", "-map", "[v]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", video)
    # 0~3초 발성, 3~3.8 무음, 3.8~6.8 발성, 6.8~7.6 무음, 7.6~8 발성
    _ff("-f", "lavfi", "-i", "sine=frequency=220:sample_rate=44100:duration=8",
        "-af", "volume=enable='between(t,3,3.8)+between(t,6.8,7.6)':volume=0,aformat=channel_layouts=stereo",
        audio)
    return {"video": video, "audio": audio, "dir": d}


@pytest.fixture()
def work(tmp_path):
    return tmp_path / "work"
