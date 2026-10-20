"""Wan2.2-S2V 어댑터 (얼굴 전체 생성 계열).

근거: Wan-Video/Wan2.2 @ 1ea34ff48f87168174e12956e200b1d908b1c5ff 의 실제 코드를 읽고 대조함 (GPU 실행은 하지 않음).
  - 진입점: 저장소 루트의 `python generate.py --task s2v-14B ...` (README.md:264 단일 GPU 예시):
      python generate.py --task s2v-14B --size 1024*704 --ckpt_dir ./Wan2.2-S2V-14B/ --offload_model True --convert_model_dtype
                         --prompt "..." --image <참조 이미지> --audio <음성>
  - 주의 1 (기본값 함정): --prompt/--image/--audio 를 안 주면 예제 값(흰 고양이 프롬프트, examples/i2v_input.JPG, examples/talk.wav)으로
      조용히 채워진다 (generate.py:68-73, EXAMPLE_PROMPT["s2v-14B"] generate.py:45-52). => 어댑터는 세 값을 항상 명시한다.
  - 주의 2: --save_file 은 확장자까지 포함한 전체 파일명이다 (generate.py:551-558 save_video(save_file=args.save_file); 안 주면 .mp4 를
      붙인 이름을 만든다). InfiniteTalk 은 확장자 없는 접두사라서 다르다. 생성 후 같은 파일에 오디오를 합친다
      (generate.py:559-560 merge_video_audio(video_path=args.save_file, audio_path=args.audio)).
  - 해상도: --size 는 "생성 영상의 면적"이고 종횡비는 참조 이미지를 따른다 (README.md:285; wan/configs/__init__.py:21-40 SIZE_CONFIGS/MAX_AREA_CONFIGS). 표에서 가장 큰 면적은 720*1280 / 1280*720 (921,600) -> 품질 우선 기본값으로 1280*720.
      정사각 크롭이면 약 960x960 이 나오므로 어댑터가 resize_to_source 로 입력 크롭 해상도에 맞춘다.
  - 품질 설정: --sample_steps 기본 40, --sample_guide_scale 기본 4.5, --sample_shift 3 (wan/configs/wan_s2v_14B.py:57-59;
      generate.py:84-91 에서 None 이면 cfg 값 사용) -> MAX_STEPS=40 (문서에 더 큰 값 안내 없음, TODO). 정밀도 인자는 없다
      (파라미터 dtype 은 bfloat16 고정: wan/configs/shared_config.py:14) -> precision 옵션은 무시된다.
  - fps/길이: 출력 fps 는 cfg.sample_fps = 16 (wan/configs/shared_config.py:18, generate.py:554 fps=cfg.sample_fps). 24fps 입력이면
      base.run() 의 conform_to_source 가 프레임을 복제해 맞추므로 움직임이 끊겨 보일 수 있다 (품질 저하 - 필요하면 RIFE 보간 고려).
      --num_clip 을 안 주면 오디오 전체 길이를 생성한다 (generate.py:250 --num_clip help). --infer_frames 기본 80 (generate.py:292, 한 클립 프레임 수, 4의 배수).
  - 저VRAM: README.md:148-150 "최소 80GB VRAM", 152 "OOM 이면 --offload_model True, --convert_model_dtype, --t5_cpu 를 쓰라".
      어댑터: offload=none -> --offload_model False, model -> --offload_model True --convert_model_dtype,
              sequential -> 위 + --t5_cpu.  (--offload_model 미지정 시 단일 GPU 에서 True: generate.py:322-324)
  - --start_from_ref: 참조 이미지를 시작 프레임으로 쓴다 (generate.py:286). 입력 크롭의 첫 프레임을 참조로 쓰므로 켠다.
  - --pose_video(generate.py:281, DWPose 시퀀스로 자세를 구동)는 RGB 영상이 아니라 포즈 시각화 영상이 필요해서 사용하지 않는다 (TODO 미검증).
  - 가중치: `hf download Wan-AI/Wan2.2-S2V-14B --local-dir ./Wan2.2-S2V-14B` (README.md 의 모델 표 + 다운로드 절차; 표에는 S2V-14B 링크,
      절차는 T2V 예시 `huggingface-cli download ... --local-dir ./Wan2.2-T2V-A14B`).  *.safetensors 대용량 (수십 GB).
  - 환경: README.md:97-103 (requirements.txt, flash_attn 은 마지막에 설치). TTS(CosyVoice) 용 requirements_s2v.txt 는 필요 없다.

TODO(미검증): 소스를 읽어 확인한 것이고 GPU 실행은 해 보지 못했다. 입력 크롭의 표정/구도를 얼마나 유지하는지(참조 이미지 1장 기반)는 실행해 봐야 안다.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from ..utils import PipelineError, find_binary, log, run
from .base import (BaseLipSyncModel, LipSyncRequest, py, register, resize_to_source, resolve_tool_dir, run_tool)

WEIGHT_DOWNLOADS = [("Wan-AI/Wan2.2-S2V-14B", [], "Wan2.2-S2V-14B", None)]
CKPT_DIR = "Wan2.2-S2V-14B"
SIZES = ("720*1280", "1280*720", "480*832", "832*480", "704*1280", "1280*704", "1024*704", "704*1024")   # wan/configs/__init__.py:21-30
DEFAULT_SIZE = "1280*720"          # 면적 921,600 = 표에서 가장 큼
DEFAULT_PROMPT = "a person is singing"      # README.md:282 의 예시 프롬프트
SAMPLE_FPS = 16
EXTRA_FLAGS = {"infer_frames": int, "sample_shift": float, "num_clip": int}


@register("wan_s2v")
class WanS2VModel(BaseLipSyncModel):
    MODE = "face_generation"
    MAX_STEPS = 40
    DEFAULT_GUIDANCE = 4.5      # --sample_guide_scale (wan_s2v_14B.py:59)
    NATIVE_RESOLUTION = 960
    TOOL_ENV = "WAN22_DIR"

    def build_command(self, req: LipSyncRequest, ref_image: Path, save_file: Path) -> list:
        o = req.options
        size = o.extra.get("size", DEFAULT_SIZE)
        if size not in SIZES:
            raise PipelineError(f"Wan2.2-S2V --size 는 {SIZES} 중 하나입니다: {size}")
        cmd = [py("wan_s2v"), "generate.py", "--task", "s2v-14B", "--size", size, "--ckpt_dir", o.extra.get("ckpt_dir", CKPT_DIR),
               "--prompt", o.extra.get("prompt", DEFAULT_PROMPT), "--image", ref_image, "--audio", req.audio,
               "--save_file", save_file, "--sample_steps", o.steps, "--sample_guide_scale", o.guidance,
               "--base_seed", o.seed, "--start_from_ref",
               "--offload_model", "False" if o.offload == "none" else "True"]
        if o.offload in ("model", "sequential"):
            cmd.append("--convert_model_dtype")
        if o.offload == "sequential":
            cmd.append("--t5_cpu")
        for k in sorted(EXTRA_FLAGS):
            if k in o.extra:
                cmd += [f"--{k}", EXTRA_FLAGS[k](o.extra[k])]
        return [str(c) for c in cmd]

    def check_environment(self, opts):
        repo = resolve_tool_dir(self.TOOL_ENV, opts.tool_dir, "Wan2.2")
        ckpt = repo / opts.extra.get("ckpt_dir", CKPT_DIR)
        if not ckpt.is_dir():
            raise PipelineError(f"Wan2.2-S2V 체크포인트 폴더가 없습니다: {ckpt} (gpu/runpod_setup.sh wan_s2v 참고)")

    def generate(self, req: LipSyncRequest) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, req.options.tool_dir, "Wan2.2")
        if req.options.precision != "fp16":
            log("[경고] Wan2.2-S2V 에는 정밀도 인자가 없어 precision 은 무시됩니다 (bfloat16 고정).")
        work = Path(tempfile.mkdtemp(prefix="wan_s2v_")).resolve()
        try:
            ref, audio, out = work / "ref.png", work / "audio.wav", work / "result.mp4"
            run([find_binary("ffmpeg"), "-y", "-v", "error", "-i", req.video, "-frames:v", "1", ref], "참조 프레임 추출")
            shutil.copyfile(req.audio, audio)
            req_in = LipSyncRequest(req.video, audio, req.output, req.fps, req.options)
            proc = run_tool(self.build_command(req_in, ref, out), repo, "Wan2.2-S2V 추론")      # TODO: GPU 에서 검증
            if not out.is_file():
                tail = "\n".join(((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()[-12:])
                raise PipelineError(f"Wan2.2-S2V 결과 파일이 없습니다: {out.name}\n{tail}")
            shutil.move(str(out), req.output)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        resize_to_source(req.video, req.output)       # fps(16)/프레임 수는 base.run() 의 conform_to_source 가 맞춘다
        return req.output
