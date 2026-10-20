"""LatentSync 어댑터 (스켈레톤).

TODO(미검증): 이 환경에는 GPU 가 없어 실행해 보지 못했다. 아래 CLI 형태는 LatentSync 공식 README 의
`python -m scripts.inference ...` 예시를 기억에 의존해 옮긴 것이므로, 설치한 버전의 README/inference.sh 와
인자 이름을 반드시 대조할 것.

사용법
  1) git clone https://github.com/bytedance/LatentSync  && cd LatentSync && pip install -r requirements.txt
  2) 체크포인트(latentsync_unet.pt, whisper/tiny.pt)를 LatentSync/checkpoints/ 에 내려받기
  3) export LATENTSYNC_DIR=/path/to/LatentSync   (또는 --tool-dir)
  4) python -m lipsync_pipeline lipsync <이름> --model latentsync

입출력 규격은 base.py 상단 참고. LatentSync 는 자체 얼굴 검출/정렬을 하고 256px(v1.5) 또는 512px(v1.6) 모델이므로
출력 해상도가 입력 크롭과 다르면 TODO 부분에서 리사이즈해야 한다.
offload: TODO — 공식 코드에 offload 옵션이 없으면 diffusers 파이프라인에
  `pipeline.enable_model_cpu_offload()` / `enable_sequential_cpu_offload()` 를 넣는 패치가 필요하다.
"""
from pathlib import Path

from .base import BaseLipSyncModel, LipSyncRequest, py, register, resolve_tool_dir, run_tool


@register("latentsync")
class LatentSyncModel(BaseLipSyncModel):
    MAX_STEPS = 50
    DEFAULT_GUIDANCE = 2.0
    NATIVE_RESOLUTION = 256
    TOOL_ENV = "LATENTSYNC_DIR"

    def build_command(self, req: LipSyncRequest, repo: Path) -> list:
        o = req.options
        cmd = [py(), "-m", "scripts.inference",
               "--unet_config_path", "configs/unet/stage2.yaml",       # TODO: 버전에 맞는 설정 파일
               "--inference_ckpt_path", "checkpoints/latentsync_unet.pt",
               "--inference_steps", o.steps, "--guidance_scale", o.guidance,
               "--seed", o.seed,
               "--video_path", req.video, "--audio_path", req.audio, "--video_out_path", req.output]
        # TODO: precision / offload 를 넘기는 공식 인자가 없다면 환경변수나 패치로 전달
        return [str(c) for c in cmd]

    def check_environment(self, opts):
        resolve_tool_dir(self.TOOL_ENV, opts.tool_dir, "LatentSync")

    def generate(self, req: LipSyncRequest) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, req.options.tool_dir, "LatentSync")
        run_tool(self.build_command(req, repo), repo, "LatentSync 추론")   # TODO: GPU 에서 검증
        return req.output
