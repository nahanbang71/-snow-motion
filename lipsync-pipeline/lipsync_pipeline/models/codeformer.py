"""CodeFormer 얼굴 복원 어댑터.

근거: sczhou/CodeFormer @ b33cc7d639d6545bfcccc7e0bc6ae51f24e79c2b 의 실제 코드를 읽고 대조함 (GPU 실행은 하지 않음).
  - 진입점/인자: `python inference_codeformer.py -w 0.5 --has_aligned --input_path <폴더> --output_path <폴더>`
      (README.md:109 정렬된 얼굴용 예시; 인자 정의 inference_codeformer.py:60-80)
      * -w/--fidelity_weight 기본 0.5, 작을수록 화질, 클수록 원본 충실 (README.md:103). 우리 기본 0.7 은 README.md:117 의
        전체 이미지 예시 값 - 립싱크 모델이 만든 입 모양을 덜 바꾸도록 충실도 쪽으로 잡았다 (finalize --restore-weight 로 조절).
      * --has_aligned: 입력이 이미 잘라 정렬된 얼굴이면 얼굴 검출을 건너뛰고 512x512 로 리사이즈해서 복원한다
        (inference_codeformer.py:180-186). 따라서 출력은 항상 512x512 이다.
  - 입력 규칙: --input_path 가 jpg/png/mp4 등으로 "끝나면" 단일 파일로 취급한다 (inference_codeformer.py:87-90).
      => 프레임 폴더 이름이 그런 문자열로 끝나면 안 된다 (어댑터는 폴더를 `frames` 로 만든다). 폴더 안에서는 jpg/png 를 정렬해서 읽는다 (:107-109).
  - 출력 규칙: has_aligned 일 때는 `<output_path>/restored_faces/<입력 파일명 stem>.png` 만 생긴다 (:238-245).
      `final_results/` 는 has_aligned 가 아닐 때만 생기고 (:248-252), mp4 합성도 영상 입력일 때만 (:255-270) -> 어댑터는 프레임 PNG 폴더를 넣고
      restored_faces 를 다시 영상으로 만든다. 입력 프레임 수와 결과 수가 다르면 오류로 처리한다.
  - 가중치: 실행 시 `weights/CodeFormer/codeformer.pth` 를 자동 다운로드 (inference_codeformer.py:138-140). 미리 받으려면
      `python scripts/download_pretrained_models.py facelib` / `... CodeFormer` (README.md:83,89). 설치는 `python basicsr/setup.py develop`
      (README.md:73).  환경: README.md:68 은 Python 3.8 -> LIPSYNC_TOOL_PYTHON 으로 별도 가상환경 지정.

TODO(미검증): 소스를 읽어 확인한 것이고 GPU/CPU 실행은 해 보지 못했다.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from ..utils import PipelineError, video_stream_info
from .base import (BasePostProcessor, extract_frames, frames_to_video, py, register, resolve_tool_dir, run_tool)

WEIGHT_SCRIPTS = ["python scripts/download_pretrained_models.py facelib", "python scripts/download_pretrained_models.py CodeFormer"]
_SINGLE_FILE_SUFFIXES = ("jpg", "jpeg", "png", "JPG", "JPEG", "PNG", "mp4", "mov", "avi", "MP4", "MOV", "AVI")


@register("codeformer")
class CodeFormer(BasePostProcessor):
    kind = "restore"
    TOOL_ENV = "CODEFORMER_DIR"

    def build_command(self, frames: Path, out: Path, weight: float) -> list:
        if str(frames).endswith(_SINGLE_FILE_SUFFIXES):
            raise PipelineError(f"CodeFormer 는 이름이 이미지/영상 확장자로 끝나는 폴더를 파일로 오인합니다: {frames}")
        return [str(c) for c in (py("codeformer"), "inference_codeformer.py", "-w", weight, "--has_aligned",
                                 "--input_path", frames, "--output_path", out)]

    @staticmethod
    def restored_dir(out: Path) -> Path:
        return Path(out) / "restored_faces"            # inference_codeformer.py:244

    def process(self, src: Path, dst: Path, opts: dict) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, opts.get("tool_dir"), "CodeFormer")
        info = video_stream_info(src)
        tmp = Path(tempfile.mkdtemp(prefix="codeformer_"))
        try:
            n = extract_frames(src, tmp / "frames")
            proc = run_tool(self.build_command(tmp / "frames", tmp / "out", opts.get("weight", 0.7)), repo, "CodeFormer 얼굴 복원")  # TODO: 실행 검증
            res = sorted(self.restored_dir(tmp / "out").glob("*.png"))
            if len(res) != n:
                tail = "\n".join(((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()[-8:])
                raise PipelineError(f"CodeFormer 결과 프레임 수({len(res)})가 입력({n})과 다릅니다.\n{tail}")
            ordered = tmp / "ordered"; ordered.mkdir()
            for i, f in enumerate(res, 1):                 # 파일명 stem 이 입력과 같으므로 정렬 순서 = 프레임 순서
                shutil.copyfile(f, ordered / f"{i:08d}.png")
            frames_to_video(ordered, dst, info["fps_rational"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return dst
