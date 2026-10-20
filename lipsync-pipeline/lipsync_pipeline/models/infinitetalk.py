"""InfiniteTalk 어댑터 (얼굴 전체 생성 계열).

근거: MeiGen-AI/InfiniteTalk @ 50aa0a94184315407a991ae804d9b58d6d311ba8 의 실제 코드를 읽고 대조함 (GPU 실행은 하지 않음).
  - 진입점: 저장소 루트의 `python generate_infinitetalk.py` (모듈 실행 `-m` 이 아님). README.md:210-226 의 단일 GPU 예시:
      --ckpt_dir weights/Wan2.1-I2V-14B-480P  --wav2vec_dir weights/chinese-wav2vec2-base
      --infinitetalk_dir weights/InfiniteTalk/single/infinitetalk.safetensors  --input_json <json>
      --size infinitetalk-480  --sample_steps 40  --mode streaming  --motion_frame 9  --save_file <이름>
    * --ckpt_dir 는 필수 (generate_infinitetalk.py:39 assert).
  - 입력 JSON: examples/single_example_video.json:1-7 =>
      {"prompt": "...", "cond_video": "<영상>", "cond_audio": {"person1": "<wav>"}}   (cond_video 가 영상이면 영상->영상 더빙)
      generate_infinitetalk.py:548-575 가 이 키를 읽는다. 한 사람이므로 person1 만 쓴다.
  - 출력: `--save_file X` 는 확장자 없는 접두사이고 결과는 `X.mp4` (generate_infinitetalk.py:657 로그,
      wan/utils/multitalk_utils.py:279 `save_path = save_path + ".mp4"`; 임시 `X-temp.mp4`, `X-cropaudio.wav` 도 같은 접두사로 생긴다).
  - fps/해상도: fps 는 25 고정 (generate_infinitetalk.py:325 `audio_duration * 25`, multitalk_utils.py:237 `fps=25`) -> 24fps 입력이면
      프레임 수가 달라지므로 base.run() 의 conform_to_source 가 필요. 해상도는 버킷 `infinitetalk-480` = 640x640,
      `infinitetalk-720` = 960x960 (wan/configs/__init__.py:38-39) 이고 종횡비는 입력을 따른다 -> 입력 크롭(예: 512x512)과 달라서
      어댑터가 resize_to_source 로 입력 해상도에 맞춘다.
  - 품질 설정: --sample_steps 기본 40 (generate_infinitetalk.py:43-44), README 도 40 -> MAX_STEPS=40 (더 큰 값에 대한 안내는 없음, TODO).
      --sample_text_guide_scale 기본 5.0 / --sample_audio_guide_scale 기본 4.0, README.md:203-205 "LoRA 없이는 5 / 4 가 최적".
      --size 는 infinitetalk-720 이 더 높은 품질(README.md:186,230) -> 기본 720. 정밀도 인자는 없다 (모델이 bfloat16 고정:
      wan/configs/shared_config.py:10-14) -> precision 옵션은 무시된다.
  - 저VRAM: `--offload_model` (str2bool, 지정 안 하면 단일 GPU 에서 True: generate_infinitetalk.py:460-461),
      `--num_persistent_param_in_dit 0` ("very low VRAM", README.md:246-262), `--quant int8|fp8` + `--quant_dir`(양자화 가중치 필요).
      어댑터: offload=none -> --offload_model False, model -> --offload_model True,
              sequential -> --offload_model True --num_persistent_param_in_dit 0.
  - 긴 구간: --mode clip 은 한 덩어리(--frame_num 기본 81프레임 = 3.2초)만 만들고, streaming 이 긴 영상용 (generate_infinitetalk.py:187-190,
      README.md:196-197). 구간이 길 수 있어 streaming 으로 실행하고 --max_frame_num(기본 1000)을 구간 길이에 맞춰 키운다.
  - 가중치(README.md:175-180, huggingface-cli 대신 현재 CLI 인 `hf download`):
      Wan-AI/Wan2.1-I2V-14B-480P -> weights/Wan2.1-I2V-14B-480P,  TencentGameMate/chinese-wav2vec2-base -> weights/chinese-wav2vec2-base
      (+ model.safetensors 는 --revision refs/pr/1),  MeiGen-AI/InfiniteTalk -> weights/InfiniteTalk
  - 환경: README.md:133-147 Python 3.10 + torch 2.4.1 + xformers 0.0.28 + flash_attn 2.7.4.post1 -> 현재 파이썬이 다르면
      LIPSYNC_TOOL_PYTHON 으로 별도 가상환경의 파이썬을 지정한다.

TODO(미검증): 소스를 읽어 확인한 것이고 GPU 실행은 해 보지 못했다. 생성 결과가 입력 크롭의 구도/표정을 얼마나 따르는지는 실행해 봐야 안다.
"""
from __future__ import annotations

import json
import math
import shutil
import tempfile
from pathlib import Path

from ..utils import PipelineError, log, video_stream_info
from .base import (BaseLipSyncModel, LipSyncRequest, py, register, resize_to_source, resolve_tool_dir, run_tool)

# README.md:175-180 (hf download <repo> [파일...] --local-dir <저장 위치>)
WEIGHT_DOWNLOADS = [
    ("Wan-AI/Wan2.1-I2V-14B-480P", [], "weights/Wan2.1-I2V-14B-480P", None),
    ("TencentGameMate/chinese-wav2vec2-base", [], "weights/chinese-wav2vec2-base", None),
    ("TencentGameMate/chinese-wav2vec2-base", ["model.safetensors"], "weights/chinese-wav2vec2-base", "refs/pr/1"),
    ("MeiGen-AI/InfiniteTalk", [], "weights/InfiniteTalk", None),
]
CKPT_DIR = "weights/Wan2.1-I2V-14B-480P"
WAV2VEC_DIR = "weights/chinese-wav2vec2-base"
INFINITETALK_WEIGHTS = "weights/InfiniteTalk/single/infinitetalk.safetensors"
FPS = 25                        # 모델 고정 fps
SIZES = ("infinitetalk-480", "infinitetalk-720")
EXTRA_FLAGS = {"motion_frame": int, "sample_audio_guide_scale": float, "sample_shift": float,
               "color_correction_strength": float, "size": str, "prompt": str}


@register("infinitetalk")
class InfiniteTalkModel(BaseLipSyncModel):
    MODE = "face_generation"
    MAX_STEPS = 40
    DEFAULT_GUIDANCE = 5.0      # --sample_text_guide_scale (LoRA 없을 때 최적값, README.md:203)
    NATIVE_RESOLUTION = 960     # infinitetalk-720 버킷
    TOOL_ENV = "INFINITETALK_DIR"

    def build_input_json(self, video: Path, audio: Path, prompt: str = "A person is singing") -> str:
        return json.dumps({"prompt": prompt, "cond_video": str(video), "cond_audio": {"person1": str(audio)}},
                          ensure_ascii=False, indent=1)

    def build_command(self, req: LipSyncRequest, input_json: Path, save_prefix: Path, audio_dir: Path,
                      max_frame_num: int = 1000) -> list:
        o = req.options
        size = o.extra.get("size", "infinitetalk-720")
        if size not in SIZES:
            raise PipelineError(f"InfiniteTalk --size 는 {SIZES} 중 하나입니다: {size}")
        cmd = [py(), "generate_infinitetalk.py", "--ckpt_dir", CKPT_DIR, "--wav2vec_dir", WAV2VEC_DIR,
               "--infinitetalk_dir", INFINITETALK_WEIGHTS, "--input_json", input_json,
               "--size", size, "--sample_steps", o.steps, "--sample_text_guide_scale", o.guidance,
               "--mode", "streaming", "--max_frame_num", max(1000, max_frame_num),
               "--base_seed", o.seed, "--save_file", save_prefix, "--audio_save_dir", audio_dir,
               "--offload_model", "False" if o.offload == "none" else "True"]
        if o.offload == "sequential":
            cmd += ["--num_persistent_param_in_dit", 0]
        for k in ("motion_frame", "sample_audio_guide_scale", "sample_shift", "color_correction_strength"):
            if k in o.extra:
                cmd += [f"--{k}", EXTRA_FLAGS[k](o.extra[k])]
        return [str(c) for c in cmd]

    @staticmethod
    def expected_output(save_prefix: Path) -> Path:
        return Path(str(save_prefix) + ".mp4")          # multitalk_utils.py:279

    def check_environment(self, opts):
        repo = resolve_tool_dir(self.TOOL_ENV, opts.tool_dir, "InfiniteTalk")
        missing = [f for f in (CKPT_DIR, WAV2VEC_DIR, INFINITETALK_WEIGHTS) if not (repo / f).exists()]
        if missing:
            raise PipelineError("InfiniteTalk 가중치가 없습니다: " + ", ".join(missing) + " (gpu/runpod_setup.sh infinitetalk 참고)")

    def generate(self, req: LipSyncRequest) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, req.options.tool_dir, "InfiniteTalk")
        if req.options.precision != "fp16":
            log("[경고] InfiniteTalk 에는 정밀도 인자가 없어 precision 은 무시됩니다 (모델은 bfloat16 고정).")
        info = video_stream_info(req.video)
        work = Path(tempfile.mkdtemp(prefix="infinitetalk_")).resolve()
        try:
            video, audio = work / "input.mp4", work / "audio.wav"
            shutil.copyfile(req.video, video)
            shutil.copyfile(req.audio, audio)
            cfg, prefix = work / "input.json", work / "result"
            cfg.write_text(self.build_input_json(video, audio), encoding="utf-8")
            frames = math.ceil(info["duration"] * FPS) + 8
            proc = run_tool(self.build_command(req, cfg, prefix, work / "audio_embeds", frames), repo, "InfiniteTalk 추론")   # TODO: GPU 에서 검증
            produced = self.expected_output(prefix)
            if not produced.is_file():
                tail = "\n".join(((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()[-12:])
                raise PipelineError(f"InfiniteTalk 결과 파일이 없습니다: {produced.name}\n{tail}")
            shutil.move(str(produced), req.output)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        resize_to_source(req.video, req.output)       # fps/프레임 수는 base.run() 의 conform_to_source 가 맞춘다
        return req.output
