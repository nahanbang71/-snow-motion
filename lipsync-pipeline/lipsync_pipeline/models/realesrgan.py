"""Real-ESRGAN 업스케일 어댑터 (스켈레톤, TODO 미검증).

사용법: git clone https://github.com/xinntao/Real-ESRGAN && pip install basicsr facexlib gfpgan -r requirements.txt && python setup.py develop
        export REALESRGAN_DIR=...
`inference_realesrgan_video.py -i 입력 -o 출력폴더 -n RealESRGAN_x4plus --outscale 2 --fp32` 형태를 사용한다.
품질 우선이므로 기본은 x4plus 모델 + outscale 2, fp32 (fp16 이상 요구사항 충족).
TODO: 출력 파일명 규칙(<이름>_out.mp4)과 플래그를 설치 버전에서 확인할 것.
"""
import shutil
import tempfile
from pathlib import Path

from ..utils import PipelineError
from .base import BasePostProcessor, py, register, resolve_tool_dir, run_tool


@register("realesrgan")
class RealESRGAN(BasePostProcessor):
    kind = "upscale"
    TOOL_ENV = "REALESRGAN_DIR"

    def build_command(self, src: Path, outdir: Path, scale: float, model: str, fp32: bool) -> list:
        cmd = [py(), "inference_realesrgan_video.py", "-i", src, "-o", outdir, "-n", model,
               "--outscale", scale, "--suffix", "out"]
        if fp32:
            cmd.append("--fp32")
        return [str(c) for c in cmd]

    def process(self, src: Path, dst: Path, opts: dict) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, opts.get("tool_dir"), "Real-ESRGAN")
        tmp = Path(tempfile.mkdtemp(prefix="realesrgan_"))
        try:
            cmd = self.build_command(src, tmp, opts.get("scale", 2), opts.get("model", "RealESRGAN_x4plus"),
                                     opts.get("precision", "fp32") == "fp32")
            run_tool(cmd, repo, "Real-ESRGAN 업스케일")      # TODO: GPU 에서 검증
            out = sorted(tmp.glob("*.mp4"))
            if not out:
                raise PipelineError("Real-ESRGAN 결과 mp4 를 찾지 못했습니다.")
            shutil.move(str(out[0]), dst)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return dst
