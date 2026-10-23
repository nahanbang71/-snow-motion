#!/usr/bin/env bash
# 외부 GPU(RunPod 등)에서 5~6단계(lipsync/emotion)와, 원하면 후처리(finalize)를 돌리기 위한 환경 세팅.
#
# 사용:  bash gpu/runpod_setup.sh <대상...>
#   대상: latentsync musetalk infinitetalk wan_s2v codeformer realesrgan rife   (예: bash gpu/runpod_setup.sh latentsync musetalk)
#
# ── Colab 에서 실제로 부딪힌 문제를 반영한 원칙 ────────────────────────────────────────────
#  1) 파이썬 버전: 코랩/최신 이미지의 파이썬은 3.13 이라 LatentSync 의 torch==2.5.1 이 설치되지 않는다.
#     -> `uv` 로 파이썬 3.10 가상환경을 따로 만들고, 그 파이썬을 환경변수 LIPSYNC_TOOL_PYTHON 으로 지정한다.
#        (모델마다 요구 환경이 달라 충돌하면 LIPSYNC_TOOL_PYTHON_<이름대문자> 로 도구별 지정: 예) LIPSYNC_TOOL_PYTHON_RIFE)
#  2) 가중치 다운로드: `huggingface-cli` 는 삭제되었다 -> `hf download <repo> [파일...] --local-dir <폴더>`.
#     `--exclude` 뒤에 오는 인자는 파일명으로 해석되어 오류가 나므로 쓰지 않는다 (필요한 파일은 위치 인자로 나열).
#  3) 외부 모델 실행 시 MPLBACKEND=Agg 가 필요하다 (주피터/코랩이 넣어 둔 matplotlib_inline 백엔드가 가상환경에는 없다).
#     어댑터(models/base.py run_tool)가 자동으로 덮어쓰지만, 직접 실행할 때를 위해 환경 파일에도 넣는다.
#  4) LatentSync 는 24fps 입력을 25fps 로 다시 만든다 -> 출력의 fps/프레임 수를 입력과 맞추는 conform_to_source 가
#     파이프라인(models/base.py run())에 들어 있다. 직접 LatentSync 를 돌릴 때만 신경 쓰면 된다.
#  5) 작업 폴더는 반드시 절대경로로 넘긴다 (외부 모델은 저장소 폴더를 cwd 로 실행되므로 상대경로 입력을 못 찾는다).
#     -> 아래 사용 순서의 --work-root "$WORK_ROOT".
#
# TODO(미검증): 이 스크립트는 GPU 가 없는 환경에서 작성되어 실행해 보지 못했다. 설치 절차는 각 저장소 README 를 읽고 옮겼고
#   (musetalk/infinitetalk/wan_s2v/codeformer/realesrgan/rife: 근거는 lipsync_pipeline/models/*.py 상단 주석),
#   latentsync 는 Colab 에서 실제로 돌려 본 절차(uv venv 3.10 + hf download)를 따른다.
set -euo pipefail

ROOT="${ROOT:-/workspace}"                     # 저장소/가중치/가상환경을 둘 위치 (RunPod 볼륨)
REPO_URL="${REPO_URL:-https://github.com/nahanbang71/-snow-motion}"
REPO_BRANCH="${REPO_BRANCH:-}"                 # 비우면 기본 브랜치
REPO_DIR="${REPO_DIR:-$ROOT/-snow-motion}"
ENV_FILE="${ENV_FILE:-$HOME/.lipsync_env}"
TARGETS=("$@")
[ "${#TARGETS[@]}" -gt 0 ] || { echo "사용: bash gpu/runpod_setup.sh <latentsync|musetalk|infinitetalk|wan_s2v|codeformer|realesrgan|rife>..." >&2; exit 1; }

# 작업 폴더(절대경로) — 사용 순서에서 --work-root 로 넘긴다
WORK_ROOT="${WORK_ROOT:-$REPO_DIR/lipsync-pipeline/work}"

say() { printf '\n==> %s\n' "$*"; }
export_line() { grep -qxF "$1" "$ENV_FILE" 2>/dev/null || echo "$1" >> "$ENV_FILE"; }

say "[1/4] 기본 도구 (ffmpeg, git, uv, hf)"
apt-get update -y >/dev/null && apt-get install -y ffmpeg git git-lfs unzip libgl1 >/dev/null
git lfs install >/dev/null 2>&1 || true
pip install -q -U uv "huggingface_hub[cli]" gdown      # `hf` 명령 제공 (huggingface-cli 아님)
command -v hf >/dev/null || { echo "hf 명령을 찾지 못했습니다. pip install -U huggingface_hub 를 확인하세요." >&2; exit 1; }
mkdir -p "$ROOT/envs"
export_line "export MPLBACKEND=Agg"
export_line "export WORK_ROOT=$WORK_ROOT"

say "[2/4] 파이프라인 설치 ($REPO_URL)"
if [ ! -d "$REPO_DIR" ]; then
  git clone -q ${REPO_BRANCH:+--branch "$REPO_BRANCH"} "$REPO_URL" "$REPO_DIR"
fi
(cd "$REPO_DIR/lipsync-pipeline" && pip install -q -e .)
mkdir -p "$WORK_ROOT"

# make_env <이름> <파이썬 버전>  -> $ROOT/envs/<이름> (pip 포함: mim 등이 pip 를 부른다)
make_env() { uv venv --seed --python "$2" "$ROOT/envs/$1" >/dev/null; echo "$ROOT/envs/$1/bin/python"; }
# vpip <python> 인자... -> uv pip install
vpip() { local py="$1"; shift; uv pip install --python "$py" "$@"; }
clone() { [ -d "$2" ] || git clone -q "https://github.com/$1" "$2"; }

say "[3/4] 모델 설치: ${TARGETS[*]}"
for t in "${TARGETS[@]}"; do
  case "$t" in
    latentsync)   # Colab 에서 실제로 동작한 절차
      clone bytedance/LatentSync "$ROOT/LatentSync"
      PY=$(make_env latentsync 3.10)
      (cd "$ROOT/LatentSync" && vpip "$PY" -r requirements.txt \
        && hf download ByteDance/LatentSync-1.5 --local-dir checkpoints && ls -la checkpoints)   # latentsync_unet.pt, whisper/tiny.pt 가 보여야 함
      export_line "export LATENTSYNC_DIR=$ROOT/LatentSync"
      export_line "export LIPSYNC_TOOL_PYTHON=$PY" ;;

    musetalk)     # MuseTalk README.md:148-184 (Python 3.10, torch 2.0.1+cu118, MMLab), download_weights.sh
      clone TMElyralab/MuseTalk "$ROOT/MuseTalk"
      PY=$(make_env musetalk 3.10)
      (cd "$ROOT/MuseTalk"
       vpip "$PY" torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
       vpip "$PY" -r requirements.txt
       vpip "$PY" --no-cache openmim
       for p in mmengine "mmcv==2.0.1" "mmdet==3.1.0" "mmpose==1.1.0"; do "$PY" -m mim install "$p"; done
       mkdir -p models/musetalk models/musetalkV15 models/syncnet models/dwpose models/face-parse-bisent models/sd-vae models/whisper
       hf download TMElyralab/MuseTalk musetalkV15/musetalk.json musetalkV15/unet.pth --local-dir models
       hf download stabilityai/sd-vae-ft-mse config.json diffusion_pytorch_model.bin --local-dir models/sd-vae
       hf download openai/whisper-tiny config.json pytorch_model.bin preprocessor_config.json --local-dir models/whisper
       hf download yzd-v/DWPose dw-ll_ucoco_384.pth --local-dir models/dwpose
       hf download ByteDance/LatentSync latentsync_syncnet.pt --local-dir models/syncnet
       gdown --id 154JgKpzCPW82qINcVieuPH3fZ2e0P812 -O models/face-parse-bisent/79999_iter.pth
       curl -L https://download.pytorch.org/models/resnet18-5c106cde.pth -o models/face-parse-bisent/resnet18-5c106cde.pth)
      export_line "export MUSETALK_DIR=$ROOT/MuseTalk"
      export_line "export LIPSYNC_TOOL_PYTHON_MUSETALK=$PY" ;;

    infinitetalk) # InfiniteTalk README.md:133-180 (Python 3.10, torch 2.4.1+cu121, xformers 0.0.28, flash_attn 2.7.4.post1)
      clone MeiGen-AI/InfiniteTalk "$ROOT/InfiniteTalk"
      PY=$(make_env infinitetalk 3.10)
      (cd "$ROOT/InfiniteTalk"
       vpip "$PY" torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu121
       vpip "$PY" -U xformers==0.0.28 --index-url https://download.pytorch.org/whl/cu121
       vpip "$PY" "misaki[en]" ninja psutil packaging wheel
       vpip "$PY" flash_attn==2.7.4.post1 --no-build-isolation || echo "[경고] flash_attn 빌드 실패: 저장소 README 의 안내를 확인하세요."
       vpip "$PY" -r requirements.txt librosa
       hf download Wan-AI/Wan2.1-I2V-14B-480P --local-dir weights/Wan2.1-I2V-14B-480P
       hf download TencentGameMate/chinese-wav2vec2-base --local-dir weights/chinese-wav2vec2-base
       hf download TencentGameMate/chinese-wav2vec2-base model.safetensors --revision refs/pr/1 --local-dir weights/chinese-wav2vec2-base
       hf download MeiGen-AI/InfiniteTalk --local-dir weights/InfiniteTalk)
      export_line "export INFINITETALK_DIR=$ROOT/InfiniteTalk"
      export_line "export LIPSYNC_TOOL_PYTHON_INFINITETALK=$PY" ;;

    wan_s2v)      # Wan2.2 README.md:97-103 (torch >= 2.4.0, flash_attn 은 마지막), 가중치 Wan-AI/Wan2.2-S2V-14B
      clone Wan-Video/Wan2.2 "$ROOT/Wan2.2"
      PY=$(make_env wan_s2v 3.10)
      (cd "$ROOT/Wan2.2"
       vpip "$PY" torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu121
       grep -v '^flash_attn' requirements.txt > /tmp/wan_req.txt && vpip "$PY" -r /tmp/wan_req.txt
       vpip "$PY" flash_attn --no-build-isolation || echo "[경고] flash_attn 빌드 실패: README 안내를 확인하세요."
       hf download Wan-AI/Wan2.2-S2V-14B --local-dir Wan2.2-S2V-14B)       # 수십 GB
      export_line "export WAN22_DIR=$ROOT/Wan2.2"
      export_line "export LIPSYNC_TOOL_PYTHON_WAN_S2V=$PY" ;;

    codeformer)   # CodeFormer README.md:64-89 (conda python 3.8)
      clone sczhou/CodeFormer "$ROOT/CodeFormer"
      PY=$(make_env codeformer 3.8)
      (cd "$ROOT/CodeFormer" && vpip "$PY" -r requirements.txt && "$PY" basicsr/setup.py develop \
        && "$PY" scripts/download_pretrained_models.py facelib && "$PY" scripts/download_pretrained_models.py CodeFormer)
      export_line "export CODEFORMER_DIR=$ROOT/CodeFormer"
      export_line "export LIPSYNC_TOOL_PYTHON_CODEFORMER=$PY" ;;

    realesrgan)   # Real-ESRGAN README.md:100-111. 가중치(weights/*.pth)는 첫 실행 때 자동 다운로드
      clone xinntao/Real-ESRGAN "$ROOT/Real-ESRGAN"
      PY=$(make_env realesrgan 3.10)
      (cd "$ROOT/Real-ESRGAN" && vpip "$PY" torch torchvision && vpip "$PY" basicsr facexlib gfpgan ffmpeg-python \
        && vpip "$PY" -r requirements.txt && "$PY" setup.py develop)
      export_line "export REALESRGAN_DIR=$ROOT/Real-ESRGAN"
      export_line "export LIPSYNC_TOOL_PYTHON_REALESRGAN=$PY" ;;

    rife)         # Practical-RIFE README.md:39-45 (python <= 3.11, requirements.txt 는 numpy<=1.23.5)
      clone hzwer/Practical-RIFE "$ROOT/Practical-RIFE"
      PY=$(make_env rife 3.10)
      (cd "$ROOT/Practical-RIFE" && vpip "$PY" -r requirements.txt && mkdir -p train_log)
      # 가중치는 README 의 Google Drive/Baidu 링크뿐이라 자동 다운로드가 없다. 아래 시도는 TODO(미검증): zip 안의 구성을 확인하지 못했다.
      if [ ! -f "$ROOT/Practical-RIFE/train_log/flownet.pkl" ]; then
        (cd "$ROOT/Practical-RIFE" && gdown --id 1gViYvvQrtETBgU1w8axZSsr7YUuw31uy -O rife_weights.zip \
          && unzip -o -q rife_weights.zip -d rife_weights_tmp \
          && find rife_weights_tmp -name flownet.pkl -exec dirname {} \; | head -1 | xargs -I{} sh -c 'cp -r {}/* train_log/') \
          || echo "[안내] RIFE 가중치를 자동으로 받지 못했습니다. README 의 모델 목록에서 받아 $ROOT/Practical-RIFE/train_log/ 에 *.py 와 flownet.pkl 을 넣으세요."
      fi
      export_line "export RIFE_DIR=$ROOT/Practical-RIFE"
      export_line "export LIPSYNC_TOOL_PYTHON_RIFE=$PY" ;;

    *) echo "알 수 없는 대상: $t" >&2; exit 1 ;;
  esac
done

say "[4/4] 완료. 새 셸에서는 'source $ENV_FILE' 를 먼저 실행하세요."
cat <<MSG

사용 순서 (GPU 에서) — 작업 폴더는 반드시 절대경로:
  1) PC 에서 만든 gpu_upload.zip 업로드 (RunPod: 웹 터미널 업로드 또는 scp)
  2) source $ENV_FILE ; cd $REPO_DIR/lipsync-pipeline
  3) python -m lipsync unpack 내영상 gpu_upload.zip --work-root "\$WORK_ROOT"
  4) python -m lipsync run 내영상 --work-root "\$WORK_ROOT" --preset quality --stages emotion,lipsync    # VRAM 이 작으면 --offload model|sequential
  5) python -m lipsync pack 내영상 --work-root "\$WORK_ROOT" --kind result    # → \$WORK_ROOT/내영상/gpu_result.zip 을 PC 로 내려받기
(후처리까지 GPU 에서 하려면 PC 에서 pack --kind full → 여기서 unpack → python -m lipsync finalize 내영상 --work-root "\$WORK_ROOT")
MSG
