"""RIFE 프레임 보간 어댑터 (스켈레톤, TODO 미검증).

사용법: git clone https://github.com/hzwer/Practical-RIFE && pip install -r requirements.txt, train_log/ 가중치 배치
        export RIFE_DIR=...
`inference_video.py --multi=2 --video=입력 --output=출력` 형태를 사용한다.
fps 가 배로 늘어나므로 finalize 는 보간된 영상의 fps 를 그대로 유지하고 오디오를 재결합한다 (길이 동일).
TODO: 플래그/출력 규칙을 설치 버전에서 확인할 것. 보간 후 오디오는 항상 새로 mux 한다.
"""
from pathlib import Path

from .base import BasePostProcessor, py, register, resolve_tool_dir, run_tool


@register("rife")
class RIFE(BasePostProcessor):
    kind = "interpolate"
    TOOL_ENV = "RIFE_DIR"

    def build_command(self, src: Path, dst: Path, multi: int) -> list:
        return [str(c) for c in (py(), "inference_video.py", f"--multi={multi}", f"--video={src}", f"--output={dst}")]

    def process(self, src: Path, dst: Path, opts: dict) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, opts.get("tool_dir"), "RIFE")
        run_tool(self.build_command(src, dst, int(opts.get("multi", 2))), repo, "RIFE 프레임 보간")   # TODO
        return dst
