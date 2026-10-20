"""CodeFormer 얼굴 복원 어댑터 (스켈레톤, TODO 미검증).

사용법: git clone https://github.com/sczhou/CodeFormer && pip install -r requirements.txt &&
        python scripts/download_pretrained_models.py CodeFormer ; export CODEFORMER_DIR=...
입력: 정렬된 512x512 얼굴 크롭 영상 -> 프레임 PNG -> `inference_codeformer.py --has_aligned` -> 다시 영상.
w(충실도 가중치): 낮을수록 품질/복원 강함, 높을수록 원본 identity 유지. 기본 0.7.
TODO: 출력 폴더 구조(restored_faces / final_results)와 플래그를 설치 버전에서 확인할 것.
"""
import shutil
import tempfile
from pathlib import Path

from ..utils import PipelineError, video_stream_info
from .base import (BasePostProcessor, extract_frames, frames_to_video, py, register, resolve_tool_dir, run_tool)


@register("codeformer")
class CodeFormer(BasePostProcessor):
    kind = "restore"
    TOOL_ENV = "CODEFORMER_DIR"

    def build_command(self, frames: Path, out: Path, weight: float) -> list:
        return [str(c) for c in (py(), "inference_codeformer.py", "-w", weight, "--has_aligned",
                                 "--input_path", frames, "--output_path", out)]

    def process(self, src: Path, dst: Path, opts: dict) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, opts.get("tool_dir"), "CodeFormer")
        info = video_stream_info(src)
        tmp = Path(tempfile.mkdtemp(prefix="codeformer_"))
        try:
            extract_frames(src, tmp / "in")
            run_tool(self.build_command(tmp / "in", tmp / "out", opts.get("weight", 0.7)), repo, "CodeFormer 얼굴 복원")  # TODO
            res = next((d for d in (tmp / "out" / "restored_faces", tmp / "out" / "final_results") if d.is_dir()), None)
            if res is None or not list(res.glob("*.png")):
                raise PipelineError("CodeFormer 결과 프레임을 찾지 못했습니다 (출력 폴더 구조 확인 필요).")
            # 결과 파일명이 원본과 다를 수 있어 순서대로 다시 번호를 매긴다
            ordered = tmp / "ordered"; ordered.mkdir()
            for i, f in enumerate(sorted(res.glob("*.png")), 1):
                shutil.copyfile(f, ordered / f"{i:08d}.png")
            frames_to_video(ordered, dst, info["fps_rational"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return dst
