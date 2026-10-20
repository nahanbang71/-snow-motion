"""MuseTalk 어댑터 (v1.5).

근거: TMElyralab/MuseTalk @ 0a89dec45a0192b824e3cf4daf96c239440c5ed8 의 실제 코드를 읽고 대조함 (GPU 실행은 하지 않음).
  - 진입점/인자:  scripts/inference.py:253-274 (argparse)  /  inference.sh:46-66 (v1.5 일 때 인자 조합)
      `python -m scripts.inference --inference_config <yaml> --result_dir <dir> --unet_model_path models/musetalkV15/unet.pth
       --unet_config models/musetalkV15/musetalk.json --version v15`   (README.md:287 의 Windows 예시도 동일)
      * --unet_config 기본값(scripts/inference.py:256 "./models/musetalk/config.json")은 다운로드되는 파일명
        (download_weights.sh:15-18 -> models/musetalkV15/musetalk.json)과 달라서 반드시 명시해야 한다.
      * --use_float16 은 store_true 플래그 (scripts/inference.py:270, 53-56). README.md:341 은 "플래그를 빼면 품질이 좋아지지만
        VRAM/시간이 늘어난다"고 안내한다 -> 품질 우선이면 precision=fp32 로 실행(어댑터: fp16 -> 플래그, fp32 -> 플래그 없음).
      * 샘플링 스텝/가이던스 인자는 없다(한 번에 예측) -> steps/guidance 는 무시. offload 옵션도 코드에 없다
        (grep offload 결과 없음; README.md:336 은 4GB VRAM + fp16 으로 동작한다고만 안내).
  - 설정 yaml:  configs/inference/test.yaml:1-9  =>  task_0:\n video_path: ...\n audio_path: ...  (선택 키 result_name, bbox_shift)
      * result_name 키는 scripts/inference.py:89-90 에서 읽힘 -> 출력 파일명을 고정할 수 있다.
      * bbox_shift 는 v15 에서 무시됨 (scripts/inference.py:93-94, v15 는 0 고정).
  - 출력 경로 규칙: scripts/inference.py:104-116  =>  <result_dir>/<version>/<result_name>   (여기서는 <result_dir>/v15/take.mp4)
      result_name 이 없으면 <입력파일명(첫 '.' 앞)>_<오디오파일명>.mp4 (scripts/inference.py:99-101, 114).
  - 주의 1: 영상/오디오 경로가 따옴표 없이 셸 명령에 들어간다 (scripts/inference.py:123, 231, 235 의 f-string + os.system).
      => 공백/한글 공백이 있는 경로는 깨진다. 어댑터는 입력을 공백 없는 임시 폴더로 복사해서 넘긴다.
  - 주의 2: 처리 중 예외는 try/except 로 삼켜서 "Error occurred during processing:" 만 출력하고 종료 코드 0 으로 끝난다
      (scripts/inference.py:248-249). => 종료 코드를 믿지 말고 출력 파일의 존재로 성공을 판단하고, 로그 끝부분을 오류에 붙인다.
  - 주의 3: 영상 입력이면 fps 는 입력 파일에서 읽는다 (scripts/inference.py:126). --fps 는 이미지 입력용. README.md:320 은 25fps 입력을
      권장. 출력의 fps/프레임 수는 base.run() 의 conform_to_source 가 입력과 맞춘다.
  - 가중치:  download_weights.sh:1-45 (아래 WEIGHT_DOWNLOADS 참고). gpu/runpod_setup.sh 가 같은 목록을 쓴다.
      * 스크립트는 `huggingface-cli` 를 쓰지만 최신 huggingface_hub 에서는 CLI 이름이 `hf` 로 바뀌었다 -> `hf download <repo> <파일...> --local-dir`.
  - 환경: README.md:148-184 는 Python 3.10 + torch 2.0.1 + mmcv 2.0.1/mmdet/mmpose 를 요구한다 -> 현재 파이썬이 3.13 인 Colab 등에서는
      별도 가상환경을 만들고 LIPSYNC_TOOL_PYTHON 으로 그 파이썬을 지정한다 (models/base.py py()).

TODO(미검증): 위 내용은 소스를 읽어 확인한 것이고, 실제 GPU 실행은 해 보지 못했다. 출력 mp4 의 오디오 트랙/길이는 실행해 봐야 안다.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from ..utils import PipelineError, log
from .base import BaseLipSyncModel, LipSyncRequest, py, register, resolve_tool_dir, run_tool

# download_weights.sh 와 같은 내용: (HF repo, 파일들, 저장 위치(저장소 기준))
# `hf download` 는 파일명을 위치 인자로 받는다 (--include/--exclude 를 쓰지 않는다).
WEIGHT_DOWNLOADS = [
    ("TMElyralab/MuseTalk", ["musetalkV15/musetalk.json", "musetalkV15/unet.pth"], "models"),
    ("stabilityai/sd-vae-ft-mse", ["config.json", "diffusion_pytorch_model.bin"], "models/sd-vae"),
    ("openai/whisper-tiny", ["config.json", "pytorch_model.bin", "preprocessor_config.json"], "models/whisper"),
    ("yzd-v/DWPose", ["dw-ll_ucoco_384.pth"], "models/dwpose"),
    ("ByteDance/LatentSync", ["latentsync_syncnet.pt"], "models/syncnet"),
]
# 위 목록으로 받을 수 없는 것 (download_weights.sh:37-40): Google Drive 의 face-parse-bisent 79999_iter.pth + torchvision resnet18
OTHER_WEIGHTS = {
    "models/face-parse-bisent/79999_iter.pth": "gdown --id 154JgKpzCPW82qINcVieuPH3fZ2e0P812",
    "models/face-parse-bisent/resnet18-5c106cde.pth": "https://download.pytorch.org/models/resnet18-5c106cde.pth",
}

UNET_MODEL = "models/musetalkV15/unet.pth"
UNET_CONFIG = "models/musetalkV15/musetalk.json"
RESULT_NAME = "take.mp4"
# opts.extra 로 넘길 수 있는 scripts/inference.py 인자 (scripts/inference.py:260-274)
EXTRA_FLAGS = {"batch_size": int, "extra_margin": int, "left_cheek_width": int, "right_cheek_width": int,
               "audio_padding_length_left": int, "audio_padding_length_right": int, "parsing_mode": str}


@register("musetalk")
class MuseTalkModel(BaseLipSyncModel):
    MAX_STEPS = 1               # 샘플링 스텝 개념 없음 (steps 는 무시됨)
    NATIVE_RESOLUTION = 256     # README.md:32 "face region of 256 x 256"
    TOOL_ENV = "MUSETALK_DIR"

    @staticmethod
    def check_shell_safe(*paths: Path) -> None:
        """MuseTalk 는 경로를 따옴표 없이 셸에 넣으므로 공백/셸 특수문자가 있으면 깨진다 (scripts/inference.py:123,231,235)."""
        for p in paths:
            if any(c.isspace() or c in "\"'`$&|;<>()*?!#" for c in str(p)):
                raise PipelineError(f"MuseTalk 는 공백/특수문자가 있는 경로를 처리하지 못합니다: {p}")

    def build_config(self, video: Path, audio: Path, result_name: str = RESULT_NAME) -> str:
        """configs/inference/test.yaml 형식. 값은 JSON 문자열 표기(YAML 호환)로 감싼다."""
        q = lambda v: json.dumps(str(v), ensure_ascii=False)
        return ("task_0:\n"
                f"  video_path: {q(video)}\n"
                f"  audio_path: {q(audio)}\n"
                f"  result_name: {q(result_name)}\n")

    def build_command(self, req: LipSyncRequest, cfg_path: Path, result_dir: Path) -> list:
        o = req.options
        if o.precision == "bf16":
            raise PipelineError("MuseTalk 는 bf16 을 지원하지 않습니다 (fp16 은 --use_float16, fp32 는 플래그 없음).")
        cmd = [py(), "-m", "scripts.inference", "--inference_config", cfg_path, "--result_dir", result_dir,
               "--unet_model_path", UNET_MODEL, "--unet_config", UNET_CONFIG, "--version", "v15"]
        if o.precision == "fp16":
            cmd.append("--use_float16")
        for k, v in sorted(o.extra.items()):
            if k not in EXTRA_FLAGS:
                raise PipelineError(f"MuseTalk 에서 지원하지 않는 extra 옵션: {k} (가능: {', '.join(sorted(EXTRA_FLAGS))})")
            cmd += [f"--{k}", EXTRA_FLAGS[k](v)]
        return [str(c) for c in cmd]

    @staticmethod
    def expected_output(result_dir: Path, result_name: str = RESULT_NAME) -> Path:
        return Path(result_dir) / "v15" / result_name        # scripts/inference.py:104,116

    def check_environment(self, opts):
        repo = resolve_tool_dir(self.TOOL_ENV, opts.tool_dir, "MuseTalk")
        missing = [f for f in (UNET_MODEL, UNET_CONFIG, "models/whisper/config.json") if not (repo / f).exists()]
        if missing:
            raise PipelineError("MuseTalk 가중치가 없습니다: " + ", ".join(missing) +
                                " (gpu/runpod_setup.sh musetalk 또는 저장소의 download_weights.sh 참고)")

    def generate(self, req: LipSyncRequest) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, req.options.tool_dir, "MuseTalk")
        if req.options.offload != "none":
            log("[경고] MuseTalk 에는 offload 옵션이 없어 무시합니다 (VRAM 이 작으면 precision=fp16 으로 실행하세요).")
        work = Path(tempfile.mkdtemp(prefix="musetalk_")).resolve()      # 공백 없는 임시 경로
        try:
            video, audio = work / "input.mp4", work / "audio.wav"
            shutil.copyfile(req.video, video)
            shutil.copyfile(req.audio, audio)
            result_dir, cfg = work / "result", work / "inference.yaml"
            self.check_shell_safe(video, audio, result_dir)
            cfg.write_text(self.build_config(video, audio), encoding="utf-8")
            proc = run_tool(self.build_command(req, cfg, result_dir), repo, "MuseTalk 추론")   # TODO: GPU 에서 검증
            produced = self.expected_output(result_dir)
            if not produced.is_file():
                tail = "\n".join(((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()[-12:])
                raise PipelineError("MuseTalk 가 결과를 만들지 않았습니다 (처리 중 오류는 종료 코드 0 으로 삼켜집니다: "
                                    f"scripts/inference.py:248). 로그 끝부분:\n{tail}")
            shutil.move(str(produced), req.output)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        return req.output
