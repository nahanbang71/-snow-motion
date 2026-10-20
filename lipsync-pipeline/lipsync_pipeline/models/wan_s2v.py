"""Wan2.2-S2V 어댑터 (얼굴 전체 생성 계열, 스켈레톤).

TODO(미검증): GPU 가 없어 실행하지 못했다. Wan2.2 저장소(Wan-Video/Wan2.2)의 speech-to-video 태스크는
참조 이미지 + 오디오(+ 선택적 포즈 영상)로 영상을 생성한다. 명령행은 기억에 의존한 것이므로 README 와 대조할 것:
  python generate.py --task s2v-14B --size 1024*704 --ckpt_dir ./Wan2.2-S2V-14B/ --offload_model True --convert_model_dtype \
         --image 참조.png --audio 음원.wav --prompt "..."

사용법
  1) Wan2.2 저장소 clone + Wan2.2-S2V-14B 가중치 내려받기
  2) export WAN22_DIR=/path/to/Wan2.2   (또는 --tool-dir)
  3) python -m lipsync lipsync <이름> --model wan_s2v --offload model

입력 영상의 첫 프레임을 참조 이미지로 쓴다 (ffmpeg 로 추출). 생성 길이/fps 가 입력과 다를 수 있으므로
어댑터가 출력을 입력 크롭 규격(해상도, fps, 프레임 수)에 맞춰야 한다 (TODO).
"""
from pathlib import Path

from ..utils import find_binary, run
from .base import BaseLipSyncModel, LipSyncRequest, py, register, resolve_tool_dir, run_tool


@register("wan_s2v")
class WanS2VModel(BaseLipSyncModel):
    MODE = "face_generation"
    MAX_STEPS = 40            # TODO: 공식 기본/권장 스텝 확인
    DEFAULT_GUIDANCE = 4.5
    TOOL_ENV = "WAN22_DIR"

    def build_command(self, req: LipSyncRequest, ref_image: Path, ckpt_dir: Path) -> list:
        o = req.options
        cmd = [py(), "generate.py", "--task", "s2v-14B", "--size", "1024*704", "--ckpt_dir", ckpt_dir,
               "--image", ref_image, "--audio", req.audio, "--save_file", req.output,
               "--sample_steps", o.steps, "--sample_guide_scale", o.guidance, "--base_seed", o.seed]
        if o.offload != "none":
            cmd += ["--offload_model", "True", "--convert_model_dtype"]
        return [str(c) for c in cmd]

    def check_environment(self, opts):
        resolve_tool_dir(self.TOOL_ENV, opts.tool_dir, "Wan2.2")

    def generate(self, req: LipSyncRequest) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, req.options.tool_dir, "Wan2.2")
        ref = req.output.parent / f".ref_{req.output.stem}.png"
        run([find_binary("ffmpeg"), "-y", "-v", "error", "-i", req.video, "-frames:v", "1", ref], "참조 프레임 추출")
        run_tool(self.build_command(req, ref, repo / "Wan2.2-S2V-14B"), repo, "Wan2.2-S2V 추론")    # TODO: GPU 에서 검증
        ref.unlink(missing_ok=True)
        # TODO: 출력 규격 정리 (리사이즈/리타이밍)
        return req.output
