#!/usr/bin/env bash
# 외부 GPU(RunPod 등)에서 5~6단계(lipsync/emotion)를 돌리기 위한 환경 세팅.
# 사용: bash gpu/runpod_setup.sh [latentsync|musetalk|infinitetalk|wan_s2v|postprocess ...]
#
# TODO(미검증): 이 스크립트는 GPU 가 없는 환경에서 작성되어 실행해 보지 못했다.
#   각 저장소의 설치 방법/체크포인트 이름은 기억에 의존한 것이므로, 막히면 해당 저장소 README 를 따를 것.
set -euo pipefail

ROOT="${ROOT:-/workspace}"                     # 모델/저장소를 둘 위치 (RunPod 볼륨)
REPO_DIR="${REPO_DIR:-$ROOT/-snow-motion}"
REPO_URL="${REPO_URL:-https://github.com/nahanbang71/-snow-motion}"
TARGETS=("${@:-latentsync}")

echo "[1/4] 기본 도구"
apt-get update -y && apt-get install -y ffmpeg git git-lfs unzip >/dev/null
git lfs install

echo "[2/4] 파이프라인 설치"
mkdir -p "$ROOT" && cd "$ROOT"
[ -d "$REPO_DIR" ] || git clone "$REPO_URL" "$REPO_DIR"
cd "$REPO_DIR/lipsync-pipeline"
pip install -e .

echo "[3/4] 모델 저장소 설치: ${TARGETS[*]}"
for t in "${TARGETS[@]}"; do
  case "$t" in
    latentsync)
      [ -d "$ROOT/LatentSync" ] || git clone https://github.com/bytedance/LatentSync "$ROOT/LatentSync"
      (cd "$ROOT/LatentSync" && pip install -r requirements.txt
       # TODO: 체크포인트 이름/저장소 확인 (HF: ByteDance/LatentSync-1.5 또는 1.6)
       pip install -q "huggingface_hub[cli]"
       huggingface-cli download ByteDance/LatentSync-1.5 latentsync_unet.pt whisper/tiny.pt --local-dir checkpoints)
      echo "export LATENTSYNC_DIR=$ROOT/LatentSync" >> ~/.lipsync_env ;;
    musetalk)
      [ -d "$ROOT/MuseTalk" ] || git clone https://github.com/TMElyralab/MuseTalk "$ROOT/MuseTalk"
      (cd "$ROOT/MuseTalk" && pip install -r requirements.txt
       # TODO: 가중치 다운로드는 저장소의 download_weights 스크립트를 사용 (이름은 버전마다 다름)
       ls download_weights* 2>/dev/null || echo "[안내] download_weights 스크립트를 README 에서 확인하세요")
      echo "export MUSETALK_DIR=$ROOT/MuseTalk" >> ~/.lipsync_env ;;
    infinitetalk)
      [ -d "$ROOT/InfiniteTalk" ] || git clone https://github.com/MeiGen-AI/InfiniteTalk "$ROOT/InfiniteTalk"
      echo "[TODO] InfiniteTalk 의존성/가중치(Wan 기반 대용량)는 저장소 README 를 따라 설치하세요."
      echo "export INFINITETALK_DIR=$ROOT/InfiniteTalk" >> ~/.lipsync_env ;;
    wan_s2v)
      [ -d "$ROOT/Wan2.2" ] || git clone https://github.com/Wan-Video/Wan2.2 "$ROOT/Wan2.2"
      echo "[TODO] Wan2.2-S2V-14B 가중치(수십 GB)는 저장소 README 를 따라 내려받으세요."
      echo "export WAN22_DIR=$ROOT/Wan2.2" >> ~/.lipsync_env ;;
    postprocess)   # 후처리(finalize)를 GPU 쪽에서 돌릴 때만
      [ -d "$ROOT/CodeFormer" ] || git clone https://github.com/sczhou/CodeFormer "$ROOT/CodeFormer"
      (cd "$ROOT/CodeFormer" && pip install -r requirements.txt && python basicsr/setup.py develop \
       && python scripts/download_pretrained_models.py facelib && python scripts/download_pretrained_models.py CodeFormer)
      [ -d "$ROOT/Real-ESRGAN" ] || git clone https://github.com/xinntao/Real-ESRGAN "$ROOT/Real-ESRGAN"
      (cd "$ROOT/Real-ESRGAN" && pip install basicsr facexlib gfpgan -r requirements.txt && python setup.py develop)
      [ -d "$ROOT/Practical-RIFE" ] || git clone https://github.com/hzwer/Practical-RIFE "$ROOT/Practical-RIFE"
      (cd "$ROOT/Practical-RIFE" && pip install -r requirements.txt)    # TODO: train_log 가중치 배치
      { echo "export CODEFORMER_DIR=$ROOT/CodeFormer"; echo "export REALESRGAN_DIR=$ROOT/Real-ESRGAN"; echo "export RIFE_DIR=$ROOT/Practical-RIFE"; } >> ~/.lipsync_env ;;
    *) echo "알 수 없는 대상: $t" >&2; exit 1 ;;
  esac
done

echo "[4/4] 완료. 새 셸에서는 'source ~/.lipsync_env' 를 먼저 실행하세요."
cat <<MSG

사용 순서 (GPU 에서):
  1) PC 에서 만든 gpu_upload.zip 을 업로드 (RunPod: 웹 터미널 업로드 또는 scp)
  2) cd $REPO_DIR/lipsync-pipeline && source ~/.lipsync_env
  3) python -m lipsync unpack 내영상 gpu_upload.zip --work-root work
  4) python -m lipsync run 내영상 --preset quality --stages emotion,lipsync        # VRAM 이 작으면 --offload sequential
  5) python -m lipsync pack 내영상 --kind result      # -> work/내영상/gpu_result.zip 을 PC 로 내려받기
MSG
