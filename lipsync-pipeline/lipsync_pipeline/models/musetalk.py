"""MuseTalk 어댑터 (스켈레톤).

TODO(미검증): GPU 가 없어 실행해 보지 못했다. 인자/설정 파일 형식은 MuseTalk README(v1.5) 기억에 의존한 것이므로
설치한 버전과 대조할 것.

사용법
  1) git clone https://github.com/TMElyralab/MuseTalk && cd MuseTalk && pip install -r requirements.txt
  2) 저장소의 download_weights 스크립트로 가중치(models/) 내려받기
  3) export MUSETALK_DIR=/path/to/MuseTalk   (또는 --tool-dir)
  4) python -m lipsync_pipeline lipsync <이름> --model musetalk

MuseTalk 은 추론 설정을 YAML 로 받는다 (task_0: video_path / audio_path). 어댑터가 임시 YAML 을 만들어 넘긴다.
MuseTalk 은 확산 샘플링 스텝 개념이 없으므로 steps 는 무시된다. 출력은 result_dir 아래에 생기며, 어댑터가 req.output 으로 옮긴다.
"""
import shutil
from pathlib import Path

from .base import BaseLipSyncModel, LipSyncRequest, py, register, resolve_tool_dir, run_tool


@register("musetalk")
class MuseTalkModel(BaseLipSyncModel):
    MAX_STEPS = 1
    NATIVE_RESOLUTION = 256
    TOOL_ENV = "MUSETALK_DIR"

    def build_config(self, req: LipSyncRequest) -> str:
        # 경로에 공백/한글이 있어도 되도록 JSON 문자열 표기(YAML 호환)로 감싼다
        import json
        return ("task_0:\n"
                f"  video_path: {json.dumps(str(req.video), ensure_ascii=False)}\n"
                f"  audio_path: {json.dumps(str(req.audio), ensure_ascii=False)}\n")

    def build_command(self, req: LipSyncRequest, cfg_path: Path, result_dir: Path) -> list:
        cmd = [py(), "-m", "scripts.inference", "--inference_config", cfg_path,
               "--result_dir", result_dir, "--version", "v15"]       # TODO: 플래그 확인
        return [str(c) for c in cmd]

    def check_environment(self, opts):
        resolve_tool_dir(self.TOOL_ENV, opts.tool_dir, "MuseTalk")

    def generate(self, req: LipSyncRequest) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, req.options.tool_dir, "MuseTalk")
        work = req.output.parent / f".musetalk_{req.output.stem}"
        work.mkdir(exist_ok=True)
        cfg = work / "inference.yaml"
        cfg.write_text(self.build_config(req), encoding="utf-8")
        run_tool(self.build_command(req, cfg, work / "result"), repo, "MuseTalk 추론")   # TODO: GPU 에서 검증
        produced = sorted((work / "result").rglob("*.mp4"))
        if not produced:
            from ..utils import PipelineError
            raise PipelineError("MuseTalk 결과 mp4 를 찾지 못했습니다 (result_dir 구조 확인 필요).")
        shutil.move(str(produced[-1]), req.output)     # TODO: 해상도/오디오 트랙 정리 필요할 수 있음
        shutil.rmtree(work, ignore_errors=True)
        return req.output
