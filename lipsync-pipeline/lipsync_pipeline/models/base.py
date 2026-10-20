"""모델 어댑터 인터페이스 + 레지스트리.

새 모델이 나오면 이 폴더에 파일 하나를 추가하고 클래스에 `@register("이름")` 만 붙이면 된다
(models/__init__.py 가 폴더 안의 모듈을 자동으로 import 한다).

두 종류의 어댑터:
  - BaseLipSyncModel   : (얼굴 크롭 영상 + 오디오) -> 립싱크된 얼굴 크롭 영상      [kind="lipsync"]
  - BasePostProcessor  : 영상 -> 영상 (얼굴 복원 / 업스케일 / 프레임 보간)          [kind="restore"|"upscale"|"interpolate"]

──────────────── 립싱크 입출력 규격 ────────────────
입력  video : 정사각 얼굴 크롭 mp4 (H.264, 보통 512x512, 원본 fps, 오디오 없음)
      audio : 16kHz 모노 PCM WAV (보컬 분리본), 영상과 같은 길이
      (face_generation 계열은 video 의 첫 프레임을 참조 이미지로 쓰거나 video 자체를 구동 영상으로 쓴다 -
       어느 쪽이든 출력은 아래 규격으로 맞춘다)
출력  output: 입력 video 와 "같은 해상도 / 같은 fps / 같은 프레임 수" 의 mp4.
      (모델이 다른 해상도로 내놓으면 어댑터가 리사이즈하고, 프레임 수가 ±2 이상 다르면 오류)
주의  GPU 가 필요한 어댑터의 run() 은 이 저장소에서 검증되지 않았다. TODO 표시를 확인할 것.
"""
from __future__ import annotations

import os
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, ClassVar, Optional

from ..utils import PipelineError, find_binary, run, video_stream_info

OFFLOAD_MODES = ("none", "model", "sequential")
PRECISIONS = ("fp16", "bf16", "fp32")


@dataclass
class GenerationOptions:
    """품질 우선 기본값. steps=None 이면 어댑터의 MAX_STEPS(최대)를 쓴다."""

    seed: int = 1234
    steps: Optional[int] = None
    guidance: Optional[float] = None
    precision: str = "fp16"          # fp16 이상 (fp32 도 가능)
    offload: str = "none"            # none | model(CPU offload) | sequential(레이어 단위, 가장 느리고 VRAM 최소)
    device: str = "cuda"
    tool_dir: Optional[str] = None   # 모델 저장소 위치 (환경변수로도 지정 가능)
    extra: dict = field(default_factory=dict)

    def validate(self) -> None:
        if self.offload not in OFFLOAD_MODES:
            raise PipelineError(f"--offload 는 {OFFLOAD_MODES} 중 하나여야 합니다: {self.offload}")
        if self.precision not in PRECISIONS:
            raise PipelineError(f"--precision 은 {PRECISIONS} 중 하나여야 합니다: {self.precision}")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LipSyncRequest:
    video: Path
    audio: Path
    output: Path
    fps: float
    options: GenerationOptions


_LIPSYNC: dict[str, type["BaseLipSyncModel"]] = {}
_POST: dict[str, dict[str, type["BasePostProcessor"]]] = {"restore": {}, "upscale": {}, "interpolate": {}}


def register(name: str) -> Callable[[type], type]:
    def deco(cls):
        cls.name = name
        if issubclass(cls, BaseLipSyncModel):
            _LIPSYNC[name] = cls
        elif issubclass(cls, BasePostProcessor):
            _POST[cls.kind][name] = cls
        else:
            raise TypeError("BaseLipSyncModel 또는 BasePostProcessor 를 상속해야 합니다.")
        return cls
    return deco


def get_lipsync_model(name: str) -> "BaseLipSyncModel":
    if name not in _LIPSYNC:
        raise PipelineError(f"알 수 없는 립싱크 모델 '{name}'. 사용 가능: {', '.join(sorted(_LIPSYNC))}")
    return _LIPSYNC[name]()


def get_post_processor(kind: str, name: str) -> "BasePostProcessor":
    if name not in _POST[kind]:
        raise PipelineError(f"알 수 없는 {kind} 어댑터 '{name}'. 사용 가능: {', '.join(sorted(_POST[kind]))}")
    return _POST[kind][name]()


def available_models() -> dict[str, list[str]]:
    return {"lipsync": sorted(_LIPSYNC), **{k: sorted(v) for k, v in _POST.items()}}


def resolve_tool_dir(env_var: str, explicit: Optional[str], what: str) -> Path:
    d = explicit or os.environ.get(env_var)
    if not d:
        raise PipelineError(
            f"{what} 저장소 위치를 알 수 없습니다. --tool-dir 또는 환경변수 {env_var} 로 "
            f"{what} 를 clone 한 폴더를 지정해 주세요 (gpu/colab_notebook.ipynb, gpu/runpod_setup.sh 참고)."
        )
    p = Path(d)
    if not p.is_dir():
        raise PipelineError(f"{what} 폴더가 없습니다: {p}")
    return p


class BaseLipSyncModel(ABC):
    name: ClassVar[str] = "base"
    MAX_STEPS: ClassVar[int] = 50          # 최대 품질 샘플링 스텝 (기본값으로 사용)
    DEFAULT_GUIDANCE: ClassVar[Optional[float]] = None
    NATIVE_RESOLUTION: ClassVar[Optional[int]] = None    # 모델 고유 해상도 (참고용)
    TOOL_ENV: ClassVar[str] = ""
    # "inpaint_mouth": 입(하관)만 다시 그리는 계열 (LatentSync, MuseTalk)
    # "face_generation": 얼굴 전체/표정까지 새로 생성하는 계열 (Wan2.2-S2V, InfiniteTalk 등)
    MODE: ClassVar[str] = "inpaint_mouth"

    def resolve(self, opts: GenerationOptions) -> GenerationOptions:
        """None 인 항목을 최대 품질 기본값으로 채운 복사본."""
        opts.validate()
        out = GenerationOptions(**{**opts.to_dict()})
        out.steps = opts.steps or self.MAX_STEPS
        out.guidance = opts.guidance if opts.guidance is not None else self.DEFAULT_GUIDANCE
        return out

    def check_environment(self, opts: GenerationOptions) -> None:
        """실행 전 점검. 문제가 있으면 PipelineError(한국어)."""

    @abstractmethod
    def generate(self, req: LipSyncRequest) -> Path:
        """req.output 에 결과를 쓰고 그 경로를 돌려준다. 이미 req.options 는 resolve() 된 상태."""

    def run(self, req: LipSyncRequest) -> Path:
        req.options = self.resolve(req.options)
        self.check_environment(req.options)
        out = self.generate(req)
        self.validate_output(req.video, out)
        return out

    @staticmethod
    def validate_output(src: Path, out: Path, frame_tolerance: int = 2) -> None:
        if not Path(out).is_file():
            raise PipelineError(f"모델이 결과 파일을 만들지 않았습니다: {out}")
        a, b = video_stream_info(src), video_stream_info(out)
        if (a["width"], a["height"]) != (b["width"], b["height"]):
            raise PipelineError(
                f"출력 해상도 {b['width']}x{b['height']} 가 입력 {a['width']}x{a['height']} 와 다릅니다 (어댑터에서 리사이즈 필요)."
            )
        if abs(a["frames"] - b["frames"]) > frame_tolerance:
            raise PipelineError(f"출력 프레임 수({b['frames']})가 입력({a['frames']})과 다릅니다.")


class BasePostProcessor(ABC):
    name: ClassVar[str] = "base"
    kind: ClassVar[str] = "restore"
    TOOL_ENV: ClassVar[str] = ""

    @abstractmethod
    def process(self, src: Path, dst: Path, opts: dict) -> Path:
        """src 영상을 처리해 dst(mp4)에 쓴다. 오디오는 다루지 않는다(마지막에 재결합)."""


# ---------------------------------------------------------------- 공용 헬퍼

def run_tool(cmd: list, cwd: Path, what: str) -> None:
    """외부 모델 저장소의 스크립트를 실행 (현재 파이썬 인터프리터 사용)."""
    run([str(c) for c in cmd], what, cwd=cwd)


def py() -> str:
    return sys.executable


def extract_frames(video: Path, outdir: Path) -> int:
    outdir.mkdir(parents=True, exist_ok=True)
    run([find_binary("ffmpeg"), "-y", "-v", "error", "-i", video, str(outdir / "%08d.png")], "프레임 추출")
    return len(list(outdir.glob("*.png")))


def frames_to_video(framedir: Path, dst: Path, fps_rational: str, crf: int = 8, pattern: str = "%08d.png") -> None:
    run([find_binary("ffmpeg"), "-y", "-v", "error", "-framerate", fps_rational, "-i", str(framedir / pattern),
         "-c:v", "libx264", "-crf", str(crf), "-preset", "slow", "-pix_fmt", "yuv420p", dst], "프레임 -> 영상 변환")
