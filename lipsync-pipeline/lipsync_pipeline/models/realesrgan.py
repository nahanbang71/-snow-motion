"""Real-ESRGAN 업스케일 어댑터.

근거: xinntao/Real-ESRGAN @ a4abfb2979a7bbff3f69f58f58ae324608821e27 의 실제 코드를 읽고 대조함 (GPU 실행은 하지 않음).
  - 영상 스크립트: `python inference_realesrgan_video.py -i <영상> -o <폴더> -n <모델> -s <배율> --suffix out [--fp32]`
      (인자 정의 inference_realesrgan_video.py:332-371)
      * 출력은 `<output>/<입력파일명 stem>_<suffix>.mp4` (:279-281). fps 는 입력을 따르고 (:98-103), 입력에 오디오가 있으면 복사한다 (:145-151).
      * -n 기본값은 `realesr-animevideov3` (애니메이션용, :334-340) 이므로 실사에서는 반드시 명시해야 한다. 실사용으로 RealESRGAN_x4plus
        (README.md:188 의 이미지 스크립트 기본 모델과 같음) 를 쓰고, -s 2 는 x4 모델을 2배로 줄여 쓴다 (-s 는 임의 배율 :349).
      * 정밀도: 기본이 fp16(half) 이고 `--fp32` 가 fp32 (:355-356). finalize 는 fp32 를 기본으로 넘긴다 (fp16 이상).
      * --tile 0 = 타일 없음 (:351). CUDA OOM 이 나면 코드가 `--tile` 을 줄이라고 안내한다 (:268) -> opts["tile"] 로 전달 가능.
  - 주의 (CPU 전용 PC): 영상 스크립트는 `num_process = torch.cuda.device_count() * num_process_per_gpu` 가 1 이 아니면 multiprocessing 경로로
      가는데 (:289-296), GPU 가 없으면 0 이라 Pool(0) 에서 ValueError 가 난다 -> 영상 스크립트는 GPU 가 없으면 실행되지 않는다.
      어댑터는 도구 파이썬으로 CUDA 개수를 확인하고, 0 이면 프레임 단위 스크립트로 폴백한다 (아래).
  - 프레임 스크립트: `python inference_realesrgan.py -i <프레임폴더> -o <폴더> -n <모델> -s <배율> --suffix "" --ext png --fp32`
      (인자 inference_realesrgan.py:16-53). suffix 가 빈 문자열이면 파일명이 그대로 (:158-159). 장치는 cuda 가 없으면 cpu (realesrgan/utils.py:48-52),
      CPU 에서 half 는 불가하므로 --fp32 를 강제한다. 매우 느리다.
  - 설치/가중치: README.md:106-111 (basicsr, facexlib, gfpgan, requirements.txt, `python setup.py develop`), 모델 가중치는 `weights/<모델>.pth` 가
      없으면 릴리스 URL 에서 자동 다운로드 (inference_realesrgan_video.py:203-212; 직접 받으려면 README.md:202 의 wget).
      영상 스크립트는 `ffmpeg-python` 이 필요하다 (:19-23, 없으면 pip 로 설치 시도).

TODO(미검증): 소스를 읽어 확인한 것이고 실행은 해 보지 못했다.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from ..utils import PipelineError, find_binary, run, video_stream_info
from .base import (BasePostProcessor, extract_frames, frames_to_video, py, register, resolve_tool_dir, run_tool)

DEFAULT_MODEL = "RealESRGAN_x4plus"


def cuda_device_count() -> int:
    """도구 파이썬(LIPSYNC_TOOL_PYTHON 또는 현재 인터프리터)에서 보이는 CUDA 장치 수. 확인 실패 시 -1."""
    try:
        out = subprocess.run([py(), "-c", "import torch; print(torch.cuda.device_count())"], capture_output=True,
                             text=True, timeout=120).stdout.strip().splitlines()
        return int(out[-1])
    except Exception:
        return -1


@register("realesrgan")
class RealESRGAN(BasePostProcessor):
    kind = "upscale"
    TOOL_ENV = "REALESRGAN_DIR"

    def build_command(self, src: Path, outdir: Path, scale: float, model: str, fp32: bool, tile: int = 0) -> list:
        """영상 스크립트 (GPU 필요)."""
        cmd = [py(), "inference_realesrgan_video.py", "-i", src, "-o", outdir, "-n", model,
               "--outscale", scale, "--suffix", "out"]
        if tile:
            cmd += ["--tile", tile]
        if fp32:
            cmd.append("--fp32")
        return [str(c) for c in cmd]

    def build_frames_command(self, framedir: Path, outdir: Path, scale: float, model: str, tile: int = 0) -> list:
        """프레임 스크립트 (CPU 폴백). CPU 에서는 half 가 불가하므로 항상 --fp32."""
        cmd = [py(), "inference_realesrgan.py", "-i", framedir, "-o", outdir, "-n", model, "--outscale", scale,
               "--suffix", "", "--ext", "png", "--fp32"]
        if tile:
            cmd += ["--tile", tile]
        return [str(c) for c in cmd]

    @staticmethod
    def expected_video(outdir: Path, src: Path, suffix: str = "out") -> Path:
        return Path(outdir) / f"{Path(src).stem}_{suffix}.mp4"          # inference_realesrgan_video.py:281

    def process(self, src: Path, dst: Path, opts: dict) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, opts.get("tool_dir"), "Real-ESRGAN")
        scale, model, tile = opts.get("scale", 2), opts.get("model", DEFAULT_MODEL), int(opts.get("tile", 0))
        fp32 = opts.get("precision", "fp32") == "fp32"
        tmp = Path(tempfile.mkdtemp(prefix="realesrgan_"))
        try:
            gpus = opts.get("cuda_devices", cuda_device_count())
            if gpus == 0:
                self._process_frames(repo, src, dst, tmp, scale, model, tile)
            else:                                   # GPU 가 있거나(>0) 확인 불가(-1) 이면 영상 스크립트
                safe_src = tmp / "input.mp4"        # 한글/공백 경로를 피하려고 임시 폴더로 복사
                shutil.copyfile(src, safe_src)
                proc = run_tool(self.build_command(safe_src, tmp / "out", scale, model, fp32, tile), repo, "Real-ESRGAN 업스케일")   # TODO: 실행 검증
                produced = self.expected_video(tmp / "out", safe_src)
                if not produced.is_file():
                    tail = "\n".join(((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()[-8:])
                    raise PipelineError(f"Real-ESRGAN 결과 파일이 없습니다: {produced.name}\n{tail}")
                shutil.move(str(produced), dst)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return dst

    def _process_frames(self, repo: Path, src: Path, dst: Path, tmp: Path, scale, model, tile) -> None:
        from ..utils import log
        log("[경고] GPU 가 없어 Real-ESRGAN 을 프레임 단위(CPU)로 처리합니다 (영상 스크립트는 CUDA 가 필요). 매우 느립니다.")
        info = video_stream_info(src)
        n = extract_frames(src, tmp / "frames")
        proc = run_tool(self.build_frames_command(tmp / "frames", tmp / "out", scale, model, tile), repo, "Real-ESRGAN 업스케일(프레임)")
        res = sorted((tmp / "out").glob("*.png"))
        if len(res) != n:
            tail = "\n".join(((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()[-8:])
            raise PipelineError(f"Real-ESRGAN 결과 프레임 수({len(res)})가 입력({n})과 다릅니다.\n{tail}")
        frames_to_video(tmp / "out", dst, info["fps_rational"], pattern="%08d.png")
