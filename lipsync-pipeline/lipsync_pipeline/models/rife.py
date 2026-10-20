"""RIFE 프레임 보간 어댑터 (Practical-RIFE).

근거: hzwer/Practical-RIFE @ bbfd2ea90910789a860ea3e2b32a240cd577b75e 의 실제 코드를 읽고 대조함 (GPU 실행은 하지 않음).
  - 진입점/인자: `python inference_video.py --multi=2 --video=<영상>` (README.md:50, 인자 정의 inference_video.py:57-70)
      * --multi 는 프레임레이트 배수 (README.md:82), --exp 는 multi = 2^exp (inference_video.py:73-74). --model 기본 `train_log` (:61).
      * --fp16 은 "Tensor Core 카드에서 빠르고 가벼운 추론" 용 옵션 (:62) -> 품질 우선이므로 기본은 켜지 않는다 (opts["fp16"] 로 켤 수 있음).
      * --scale 은 [0.25, 0.5, 1.0, 2.0, 4.0] 만 허용 (:80), 4K 는 0.5 권장 (README.md:58-60).
  - 출력 (기존 어댑터의 가정이 틀렸던 부분):
      * 기본 모드는 cv2.VideoWriter 의 'mp4v' 코덱으로 쓴다 (inference_video.py:113, 140) -> MPEG-4 Part 2 라서 H.264 보다 화질이 나쁘고 한 번 더 손실.
        어댑터는 `--png` 로 무손실 PNG 를 `vid_out/{:0>7d}.png` (cwd 기준, 0부터: inference_video.py:132-134, 148-150) 로 받아서 ffmpeg 로 H.264 인코딩한다.
      * 오디오 합성(transferAudio, :16-45, :284-290)은 moviepy.editor(moviepy 2.x 에는 없음)와 ./temp 폴더를 쓴다. png 모드에서는 건너뛴다 (:284 조건).
        우리 입력은 무음이고 오디오는 마지막에 따로 재결합하므로 필요 없다.
      * 프레임 수는 입력 n 프레임 -> (n-1)*multi + 1 (쌍마다 원본 1 + 중간 multi-1, 마지막 원본 1: :241-253, 마지막 put). finalize 의 검증 허용 오차(±multi) 안.
  - 입력: skvideo.io.vreader 로 읽고 (:111) 해상도가 128 배수가 아니면 내부에서 패딩한다 (:193-195).
  - 가중치/환경: "모델 목록에서 받아 *.py 와 flownet.pkl 을 train_log/ 에 넣는다" (README.md:45). 링크는 Google Drive/Baidu 뿐이라 자동 다운로드가
      없다 (README.md:19-34) -> check_environment 가 train_log/flownet.pkl 존재를 확인한다. 파이썬 <= 3.11 (README.md:39), requirements.txt 는
      numpy<=1.23.5 로 고정 -> LIPSYNC_TOOL_PYTHON 으로 별도 가상환경 지정.

TODO(미검증): 소스를 읽어 확인한 것이고 실행은 해 보지 못했다. 가중치 zip 의 내부 구성(어느 폴더에 풀어야 하는지)도 확인하지 못했다.
"""
from __future__ import annotations

import shutil
import tempfile
from fractions import Fraction
from pathlib import Path

from ..utils import PipelineError, video_stream_info
from .base import BasePostProcessor, frames_to_video, py, register, resolve_tool_dir, run_tool

SCALES = (0.25, 0.5, 1.0, 2.0, 4.0)       # inference_video.py:80


@register("rife")
class RIFE(BasePostProcessor):
    kind = "interpolate"
    TOOL_ENV = "RIFE_DIR"

    def build_command(self, repo: Path, src: Path, multi: int, scale: float = 1.0, fp16: bool = False) -> list:
        """png 모드: cwd 는 임시 폴더(vid_out/ 이 거기 생김). 스크립트와 모델은 절대경로로 지정."""
        if multi < 2:
            raise PipelineError("RIFE --multi 는 2 이상이어야 합니다.")
        if scale not in SCALES:
            raise PipelineError(f"RIFE --scale 은 {SCALES} 중 하나입니다: {scale}")
        cmd = [py(), repo / "inference_video.py", f"--multi={multi}", f"--video={src}", "--png",
               f"--model={repo / 'train_log'}", f"--scale={scale}"]
        if fp16:
            cmd.append("--fp16")
        return [str(c) for c in cmd]

    @staticmethod
    def output_fps(fps_rational: str, multi: int) -> str:
        f = Fraction(fps_rational) * multi
        return f"{f.numerator}/{f.denominator}"

    @staticmethod
    def expected_frames(n: int, multi: int) -> int:
        return (n - 1) * multi + 1

    def check_environment(self, opts: dict) -> None:
        repo = resolve_tool_dir(self.TOOL_ENV, opts.get("tool_dir"), "RIFE")
        if not (repo / "train_log" / "flownet.pkl").is_file():
            raise PipelineError("RIFE 가중치가 없습니다: train_log/flownet.pkl (README 의 모델 목록에서 직접 받아 train_log/ 에 넣어야 합니다).")

    def process(self, src: Path, dst: Path, opts: dict) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, opts.get("tool_dir"), "RIFE")
        multi = int(opts.get("multi", 2))
        info = video_stream_info(src)
        tmp = Path(tempfile.mkdtemp(prefix="rife_"))
        try:
            safe_src = tmp / "input.mp4"
            shutil.copyfile(src, safe_src)
            work = tmp / "work"; work.mkdir()           # 이 안에 vid_out/*.png 가 생긴다
            self.check_environment(opts)
            proc = run_tool(self.build_command(repo, safe_src, multi, float(opts.get("scale", 1.0)), bool(opts.get("fp16", False))),
                            work, "RIFE 프레임 보간")        # TODO: 실행 검증
            out = work / "vid_out"
            got = len(list(out.glob("*.png"))) if out.is_dir() else 0
            want = self.expected_frames(info["frames"], multi)
            if got == 0 or abs(got - want) > multi:
                tail = "\n".join(((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()[-8:])
                raise PipelineError(f"RIFE 결과 프레임 수({got})가 기대({want})와 다릅니다.\n{tail}")
            frames_to_video(out, dst, self.output_fps(info["fps_rational"], multi), pattern="%07d.png")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return dst
