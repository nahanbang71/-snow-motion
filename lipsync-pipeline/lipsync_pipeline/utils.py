"""공용 유틸: 외부 명령 실행, 작업 폴더, WAV/JSON 입출력, ffmpeg 프레임 파이프.

OpenCV 의 VideoCapture/imread 는 Windows 에서 한글 경로를 못 읽는 경우가 있어서,
영상 입출력은 모두 ffmpeg 파이프(인자 리스트 방식)로 처리한다.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterator, Optional, Sequence

import numpy as np


class PipelineError(Exception):
    """사용자에게 한국어로 보여줄 오류."""


def find_binary(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise PipelineError(
            f"'{name}' 를 찾을 수 없습니다. ffmpeg 를 설치하고 PATH 에 추가해 주세요 "
            "(Windows: winget install Gyan.FFmpeg)."
        )
    return path


def run(cmd: Sequence[str], what: str, cwd: Optional[Path] = None, env=None) -> subprocess.CompletedProcess:
    """외부 명령 실행. 실패하면 stderr 끝부분을 포함한 한국어 오류를 낸다."""
    try:
        proc = subprocess.run(
            [str(c) for c in cmd], capture_output=True, text=True,
            encoding="utf-8", errors="replace", cwd=str(cwd) if cwd else None, env=env,
        )
    except FileNotFoundError as e:
        raise PipelineError(f"{what} 실행 실패: 실행 파일을 찾을 수 없습니다 ({e}).") from e
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or proc.stdout or "").strip().splitlines()[-15:])
        raise PipelineError(f"{what} 실패 (종료 코드 {proc.returncode}):\n{tail}")
    return proc


# ---------------------------------------------------------------- 작업 폴더

_BAD_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_name(name: str) -> str:
    cleaned = _BAD_CHARS.sub("_", name).strip().strip(".")
    if not cleaned:
        raise PipelineError("작업 이름이 비어 있습니다. --name 으로 이름을 지정해 주세요.")
    return cleaned


@dataclass
class Workspace:
    """work/<이름>/ 아래의 표준 파일 위치."""

    root: Path
    name: str

    @classmethod
    def open(cls, name: str, work_root: Path | str = "work", must_exist: bool = True) -> "Workspace":
        name = sanitize_name(name)
        # 절대경로로 고정한다: 외부 모델(LatentSync 등)은 자기 저장소 폴더를 cwd 로 실행되므로 상대경로면 입력 파일을 못 찾는다.
        root = (Path(work_root) / name).resolve()
        if must_exist and not root.is_dir():
            raise PipelineError(
                f"작업 폴더 '{root}' 가 없습니다. 먼저 `prepare` 단계를 실행해 주세요."
            )
        root.mkdir(parents=True, exist_ok=True)
        return cls(root=root, name=name)

    def p(self, filename: str) -> Path:
        return self.root / filename

    info = property(lambda s: s.p("info.json"))
    video_noaudio = property(lambda s: s.p("video_noaudio.mp4"))
    audio_44k = property(lambda s: s.p("audio_44k.wav"))
    audio_16k = property(lambda s: s.p("audio_16k.wav"))
    vocals = property(lambda s: s.p("vocals.wav"))
    vocals_16k = property(lambda s: s.p("vocals_16k.wav"))
    analysis = property(lambda s: s.p("analysis.json"))
    face_track = property(lambda s: s.p("face_track.json"))
    face_crop = property(lambda s: s.p("face_crop.mp4"))
    lipsync_crop = property(lambda s: s.p("lipsync_crop.mp4"))
    emotion = property(lambda s: s.p("emotion.json"))
    final = property(lambda s: s.p("final.mp4"))

    def require(self, *files: Path, hint: str) -> None:
        missing = [f.name for f in files if not f.exists()]
        if missing:
            raise PipelineError(f"필요한 파일이 없습니다: {', '.join(missing)}. {hint}")


def read_json(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise PipelineError(f"파일이 없습니다: {path}") from e
    except json.JSONDecodeError as e:
        raise PipelineError(f"JSON 형식이 올바르지 않습니다 ({path}): {e}") from e


def write_json(path: Path, data: dict) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- WAV

def read_wav(path: Path) -> tuple[int, np.ndarray]:
    """PCM/float WAV -> (샘플레이트, float32 배열 (n, ch), -1~1)."""
    from scipy.io import wavfile

    try:
        sr, data = wavfile.read(str(path))
    except FileNotFoundError as e:
        raise PipelineError(f"오디오 파일이 없습니다: {path}") from e
    except ValueError as e:
        raise PipelineError(f"WAV 를 읽을 수 없습니다 ({path}): {e}") from e
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float32) / 2147483648.0
    elif data.dtype == np.uint8:
        data = (data.astype(np.float32) - 128.0) / 128.0
    else:
        data = data.astype(np.float32)
    if data.ndim == 1:
        data = data[:, None]
    return int(sr), data


def write_wav(path: Path, sr: int, data: np.ndarray) -> None:
    """float 배열 (n, ch) 또는 (n,) -> 16bit PCM WAV."""
    from scipy.io import wavfile

    pcm = np.clip(np.asarray(data, dtype=np.float32), -1.0, 1.0)
    pcm = (pcm * 32767.0).round().astype(np.int16)
    wavfile.write(str(path), int(sr), pcm)


def to_mono(data: np.ndarray) -> np.ndarray:
    return data.mean(axis=1) if data.ndim == 2 else data


# ---------------------------------------------------------------- ffprobe / 프레임 IO

def ffprobe(path: Path) -> dict:
    out = run(
        [find_binary("ffprobe"), "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        f"ffprobe ({Path(path).name})",
    )
    return json.loads(out.stdout)


def parse_rate(text: str) -> float:
    try:
        v = Fraction(text)
        return float(v)
    except (ValueError, ZeroDivisionError):
        return 0.0


def video_stream_info(path: Path) -> dict:
    """영상 첫 비디오 스트림의 width/height/fps/프레임수/길이."""
    probe = ffprobe(path)
    vs = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), None)
    if vs is None:
        raise PipelineError(f"비디오 스트림이 없습니다: {path}")
    rate_txt = vs.get("avg_frame_rate", "0/0")
    if parse_rate(rate_txt) <= 0:
        rate_txt = vs.get("r_frame_rate", "0/0")
    fps = parse_rate(rate_txt)
    duration = float(vs.get("duration") or probe.get("format", {}).get("duration") or 0.0)
    nb = vs.get("nb_frames")
    frames = int(nb) if nb and str(nb).isdigit() else int(round(duration * fps))
    return {"width": int(vs["width"]), "height": int(vs["height"]), "fps": fps,
            "fps_rational": rate_txt, "frames": frames, "duration": duration,
            "codec": vs.get("codec_name")}


def iter_frames(path: Path, width: int, height: int) -> Iterator[np.ndarray]:
    """ffmpeg 파이프로 BGR24 프레임을 하나씩 읽는다 (한글 경로 안전)."""
    cmd = [find_binary("ffmpeg"), "-v", "error", "-i", str(path),
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    size = width * height * 3
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        while True:
            buf = proc.stdout.read(size)
            if len(buf) < size:
                break
            yield np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 3).copy()
    finally:
        proc.stdout.close()
        err = proc.stderr.read().decode("utf-8", errors="replace")
        proc.stderr.close()
        proc.wait()
    if proc.returncode not in (0, None) and err.strip():
        # 소비자가 중간에 제너레이터를 닫아 SIGPIPE 가 난 경우는 무시한다
        if "Broken pipe" not in err:
            raise PipelineError(f"프레임 읽기 실패 ({Path(path).name}): {err.strip()[-300:]}")


class FrameWriter:
    """BGR24 프레임을 ffmpeg 로 mp4(H.264) 인코딩. audio 를 주면 같이 mux 한다."""

    def __init__(self, path: Path, width: int, height: int, fps_rational: str,
                 crf: int = 18, audio: Optional[Path] = None, preset: str = "medium"):
        self.path, self.width, self.height = Path(path), width, height
        cmd = [find_binary("ffmpeg"), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
               "-s", f"{width}x{height}", "-r", fps_rational, "-i", "-"]
        if audio is not None:
            cmd += ["-i", str(audio)]
        cmd += ["-c:v", "libx264", "-crf", str(crf), "-preset", preset, "-pix_fmt", "yuv420p"]
        if audio is not None:
            cmd += ["-c:a", "aac", "-b:a", "256k", "-shortest"]
        cmd += ["-movflags", "+faststart", str(path)]
        self._proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        self.count = 0

    def write(self, frame: np.ndarray) -> None:
        if frame.shape != (self.height, self.width, 3) or frame.dtype != np.uint8:
            raise PipelineError(
                f"프레임 규격이 맞지 않습니다: {frame.shape}/{frame.dtype}, "
                f"기대값 ({self.height}, {self.width}, 3)/uint8"
            )
        try:
            self._proc.stdin.write(frame.tobytes())
        except BrokenPipeError as e:
            raise PipelineError("ffmpeg 인코딩이 중단되었습니다: " + self._close_err()) from e
        self.count += 1

    def _close_err(self) -> str:
        try:
            self._proc.stdin.close()
        except Exception:
            pass
        err = self._proc.stderr.read().decode("utf-8", errors="replace")
        self._proc.wait()
        return err.strip()[-400:]

    def close(self) -> None:
        err = self._close_err()
        if self._proc.returncode != 0:
            raise PipelineError(f"영상 인코딩 실패 ({self.path.name}): {err}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *a):
        if exc_type is None:
            self.close()
        else:
            self._close_err()


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- 덮어쓰기 금지 지원

def timestamp() -> str:
    import time
    return time.strftime("%Y%m%d-%H%M%S")


def archive_existing(ws: "Workspace", *paths: Path) -> Optional[Path]:
    """이미 있는 산출물을 지우지 않고 work/<이름>/_archive/<시각>/ 로 옮겨 보존한다."""
    existing = [Path(p) for p in paths if Path(p).exists()]
    if not existing:
        return None
    dest = ws.p("_archive") / timestamp()
    n = 1
    while dest.exists():
        dest = ws.p("_archive") / f"{timestamp()}_{n}"
        n += 1
    dest.mkdir(parents=True)
    for p in existing:
        shutil.move(str(p), str(dest / p.name))
    log(f"[보존] 기존 결과를 {dest} 로 옮겼습니다: {', '.join(p.name for p in existing)}")
    return dest
