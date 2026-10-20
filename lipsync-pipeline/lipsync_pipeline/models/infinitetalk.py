"""InfiniteTalk 어댑터 (얼굴 전체 생성 계열, 스켈레톤).

TODO(미검증): GPU 가 없어 실행하지 못했다. InfiniteTalk(MeiGen-AI/InfiniteTalk)은 Wan 기반의 audio-driven
영상 생성 모델로, 영상->영상(dubbing) 또는 이미지->영상 입력 JSON 을 받는 생성 스크립트를 쓴다.
아래 인자/JSON 키는 기억에 의존한 것이므로 설치한 버전의 README 와 반드시 대조할 것.

사용법
  1) git clone https://github.com/MeiGen-AI/InfiniteTalk, 의존성/가중치(Wan2.1 I2V 계열 + InfiniteTalk + wav2vec2) 설치
  2) export INFINITETALK_DIR=/path/to/InfiniteTalk   (또는 --tool-dir)
  3) python -m lipsync lipsync <이름> --model infinitetalk --offload sequential   # VRAM 이 작으면

입출력: base.py 규격. 이 계열은 표정/고개까지 새로 만들기 때문에 입력 크롭과 모양이 달라질 수 있어,
어댑터가 출력을 (크롭 해상도, 원본 fps, 같은 프레임 수) 로 리사이즈/리타이밍해야 한다 (TODO).
오디오는 보컬 분리본(16kHz). 해상도는 모델 지원 범위(예: 480p/720p) 중 최대를 쓰는 것이 기본(품질 우선).
"""
import json
from pathlib import Path

from .base import BaseLipSyncModel, LipSyncRequest, py, register, resolve_tool_dir, run_tool


@register("infinitetalk")
class InfiniteTalkModel(BaseLipSyncModel):
    MODE = "face_generation"
    MAX_STEPS = 40            # TODO: 공식 권장 최대 스텝 확인
    DEFAULT_GUIDANCE = 4.0
    NATIVE_RESOLUTION = 512   # TODO
    TOOL_ENV = "INFINITETALK_DIR"

    def build_input_json(self, req: LipSyncRequest) -> str:
        return json.dumps({"prompt": "a person singing, natural expressions",
                           "cond_video": str(req.video), "cond_audio": {"person1": str(req.audio)}},
                          ensure_ascii=False, indent=1)      # TODO: 실제 JSON 스키마 확인

    def build_command(self, req: LipSyncRequest, input_json: Path) -> list:
        o = req.options
        cmd = [py(), "generate_infinitetalk.py", "--input_json", input_json, "--save_file", req.output.with_suffix(""),
               "--sample_steps", o.steps, "--sample_text_guide_scale", o.guidance, "--base_seed", o.seed]
        if o.offload != "none":
            cmd += ["--num_persistent_param_in_dit", 0]      # TODO: 공식 저VRAM 옵션 이름 확인
        return [str(c) for c in cmd]

    def check_environment(self, opts):
        resolve_tool_dir(self.TOOL_ENV, opts.tool_dir, "InfiniteTalk")

    def generate(self, req: LipSyncRequest) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, req.options.tool_dir, "InfiniteTalk")
        cfg = req.output.parent / f".infinitetalk_{req.output.stem}.json"
        cfg.write_text(self.build_input_json(req), encoding="utf-8")
        run_tool(self.build_command(req, cfg), repo, "InfiniteTalk 추론")        # TODO: GPU 에서 검증
        cfg.unlink(missing_ok=True)
        # TODO: 모델 출력 mp4 를 req.output 규격(해상도/fps/프레임 수)으로 정리
        return req.output
