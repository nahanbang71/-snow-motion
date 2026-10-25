# lipsync-pipeline

외부 서비스(Google Flow, Meta AI 등)에서 **이미 완성된** 실사 인물 영상 + **이미 완성된** 노래 음원에
**립싱크만** 적용하는 파이프라인입니다. 영상/음원 생성 기능은 없고, 워터마크 제거 기능도 없습니다(경고만 합니다).

- 품질 최우선: 기본값은 항상 최대 품질(최대 샘플링 스텝, fp16 이상). 속도 최적화 옵션은 만들지 않았습니다.
- 한국어 경로/공백 파일명 지원, 로그·오류 메시지는 한국어.
- 중간 결과는 **덮어쓰지 않고 전부 보존**합니다(다시 만들면 `_archive/`, 후보는 번호 이어서, 최종본은 `finalize/<tag>/`).

> ⚠️ **검증 범위** (이 저장소는 GPU 없는 환경에서 작성되었습니다)
> - **CPU 테스트로 검증됨**: 전처리/분석/구간 분할/후보 관리/UI 서버/합성/배치, 그리고 모든 외부 모델 어댑터의 **명령 조립·설정 파일 형식·출력 경로 규칙**
>   (가짜 도구 스크립트로 입출력 흐름까지 확인 — `tests/test_adapters.py`).
> - **공식 저장소 코드를 읽어 대조함(실행은 안 함)**: MuseTalk / InfiniteTalk / Wan2.2-S2V / CodeFormer / Real-ESRGAN / RIFE(Practical-RIFE) 어댑터.
>   각 어댑터 파일 상단 주석에 확인한 저장소 커밋과 파일·줄 번호가 있습니다. 저장소가 바뀌면 줄 번호는 어긋날 수 있으니 커밋 해시로 찾으세요.
> - **Colab 에서 실제로 실행해 본 것**: LatentSync 어댑터(및 그 설치 절차)뿐입니다.
> - **한 번도 실행해 보지 못함**: 위 6개 모델의 GPU 실행 자체, SyncNet 점수(스켈레톤), 실제 손 영상에서의 손 검출, RunPod 설치 스크립트. (mediapipe 얼굴 검출은 `mediapipe==0.10.21`/Python 3.12 에서 초기화까지 확인, 손 겹침 판정 로직은 테스트로 확인)
>   코드의 `TODO(미검증)` 표시를 확인하세요.

## 파이프라인

```
prepare → separate → analyze → scan → emotion → segments → lipsync ──→ (review) → finalize
 PC        PC         PC       PC       PC        PC        GPU        PC          PC(또는 GPU)
```

| 단계 | 서브커맨드 | 하는 일 | 주요 산출물 (`work/<이름>/`) |
|---|---|---|---|
| 1 | `prepare` | ffprobe 점검, 오디오 제거 영상(CFR·짝수 해상도), 44.1kHz 스테레오 WAV, 16kHz 모노 WAV | `info.json`, `video_noaudio.mp4`, `audio_44k.wav`, `audio_16k.wav` |
| 2 | `separate` | Demucs 보컬 분리(CPU 가능, 긴 곡은 겹치는 구간으로 나눠 처리) | `vocals.wav`, `vocals_16k.wav` |
| 3 | `analyze` | F0, RMS, 발성/무음 구간, 비트(템포) | `analysis.json` |
| 4 | `scan` | 장면 전환(컷) 감지 → 컷마다 얼굴/크기/각도(yaw·pitch·roll)/눈 감김/입 가림 판정, 워터마크 경고 | `cuts_report.csv`, `cuts.json`, `face_track.json`, `face_crop.mp4`, `scan.json` |
| 5a | `segments` | 립싱크 적용 가능 구간을 무음 기준 프레이즈로 분할(경계 0.5초 겹침) + 모델 입력 자르기 | `segments.json`, `segments/NNN/{input.mp4,audio.wav}` |
| 5b | `lipsync` | 구간마다 `--takes N`(기본 3)개 후보를 다른 seed로 생성, 자동 점수 계산 | `segments/NNN/take_K.mp4`, `take_K.json` |
| 6 | `emotion` | 에너지/F0/비트 → 고개 끄덕임·미세 움직임 파라미터 | `emotion.json` |
| – | `review` | 후보를 나란히 보고 구간별 베스트 선택, 마음에 안 드는 구간만 재생성 | `selection.json` |
| – | `compare` | 같은 구간의 여러 모델/설정 결과를 나란히 붙인 비교 영상 | `compare/cmp_seg001_*.mp4` |
| 7 | `finalize` | 후보 조립(크로스페이드) → CodeFormer → 원본에 합성(색 보정·페더링) → Real-ESRGAN → RIFE → 오디오 결합 | `finalize/<tag>/final.mp4`, `render.json` |
| – | `run` / `batch` | 여러 단계 이어서 실행 / CSV 일괄 처리 (`state.json`, `report.csv`) | `state.json`, `report.csv` |
| – | `pack` / `unpack` | PC ↔ 외부 GPU 전달용 zip | `gpu_upload.zip`, `gpu_result.zip` |

모든 단계는 독립 실행됩니다. `python -m lipsync <서브커맨드> -h` 로 옵션을 확인하세요(`python -m lipsync_pipeline` 도 같습니다).

---

## 🖥️ 내 PC에서 할 일 (Windows, GPU 없음, Python 3.12, ffmpeg, RAM 16GB)

### 0. 설치
```powershell
git clone -b claude/adapter-audit https://github.com/nahanbang71/-snow-motion ; cd -snow-motion\lipsync-pipeline   # 기본 브랜치에는 lipsync-pipeline 이 없으니 브랜치를 지정
.\scripts\setup_windows.ps1            # 가상환경 + numpy/scipy/opencv/pyyaml + mediapipe + CPU torch/demucs
.\.venv\Scripts\Activate.ps1
python -m pytest -q                    # (선택) CPU 테스트
```
ffmpeg 가 없으면 `winget install Gyan.FFmpeg`. 스크립트는 Windows 에서 실행해 본 적이 없으니 실패하면 해당 줄만 수동 실행하세요.

### 1. 전처리 (영상 1개 기준)
```powershell
python -m lipsync prepare "D:\영상\컷 1.mp4" "D:\음원\노래.wav" --name 노래1      # 한글/공백 경로 OK
python -m lipsync separate 노래1 --device cpu       # 긴 곡은 60초 구간(2초 겹침)으로 나눠 처리
python -m lipsync analyze 노래1
python -m lipsync scan 노래1                         # ← cuts_report.csv 를 꼭 열어 보세요
python -m lipsync emotion 노래1
python -m lipsync segments 노래1                     # 프레이즈 단위 분할 + 모델 입력 자르기
python -m lipsync pack 노래1 --kind upload           # work\노래1\gpu_upload.zip → 외부 GPU 로 업로드
```
- 720x1280 세로, 24fps, 5~10초 컷을 기준으로 잡았지만 해상도/FPS 는 자동으로 읽습니다.
- `scan` 은 컷마다 아래를 판정해 `cuts_report.csv`(엑셀에서 한글 정상 표시)에 남기고 경고를 출력합니다.
  - 얼굴 없음 / 너무 작음(기본 96px 미만) / 측면·상하 각도 큼(|yaw|>45°, |pitch|>40° 는 건너뜀, 25° 초과는 경고) / 입 가려짐 / 눈 감김 많음
  - **기본 정책: 얼굴 없음·작음·측면·입 가려짐 구간은 립싱크를 건너뛰고 원본 프레임을 그대로 씁니다.** 경계는 0.25초 알파 램프로 부드럽게 이어집니다. 강제로 적용하려면 `scan --apply-bad-cuts`(얼굴 없음/작음은 항상 건너뜀).
  - 워터마크(Meta AI, sync.so, Flow 마크 등) 의심 고정 오버레이가 있으면 위치와 함께 경고하고, 얼굴 근처면 품질 영향을 추가로 경고합니다. **제거는 하지 않습니다.**
- **판정의 한계(꼭 읽어 주세요)**: mediapipe 가 있으면 yaw/pitch/눈 감김을 랜드마크로 근사하고, 없으면 OpenCV Haar(정면 얼굴만 잡힘, 각도/눈 감김 판정 없음)로 대체됩니다.
  입 가림은 입 바로 바깥 피부 영역에서 "피부색이 아닌 비율"로 판정하므로 **마이크·머리카락·마스크 같은 색이 다른 가림 위주**로 잡고, 손(피부색)은 mediapipe Hands 가 있을 때만(미검증) 보완합니다.
  AI 생성 영상은 얼굴이 프레임마다 미세하게 변해 오탐/미탐이 있을 수 있으니 `cuts_report.csv` 를 사람이 확인하세요.

### 2. GPU 결과를 받은 뒤
```powershell
python -m lipsync unpack 노래1 gpu_result.zip         # 후보를 병합 (번호가 겹치면 새 번호로 보존, 덮어쓰기 없음)
python -m lipsync review 노래1                         # 브라우저가 열립니다 (127.0.0.1)
python -m lipsync compare 노래1 --segment 3 --takes 1,2,4    # 후보/모델 비교 영상
python -m lipsync finalize 노래1                        # 기본: 복원 + 업스케일 + 보간 모두 켬
python -m lipsync finalize 노래1 --tag 조합2 --no-interpolate   # 다른 선택 조합/옵션으로 다시 합치기 (이전 결과 보존)
```
- **review**: 구간마다 원본 입력 + 후보를 나란히 재생(오디오 동기 재생 버튼)하고 "이 후보를 사용"을 고르면 즉시 `selection.json` 에 저장됩니다
  (이전 선택은 `selection_history/` 에 남음). 후보 옆에 **자동 점수**(참고용)가 표시됩니다.
  - 싱크(간이): 입 영역 움직임과 오디오 에너지의 상관(±6프레임 지연 탐색) — **SyncNet 이 아니라 CPU 용 간이 지표**입니다.
    SyncNet(LSE-D/LSE-C) 점수는 `SYNCNET_DIR` 이 설정되면 표시되도록 스켈레톤만 있습니다(미구현 TODO).
  - 안정도/떨림: 원본 대비 얼굴 윗부분의 프레임 간 흔들림, 입 영역 가속도.
  - "이 구간 재생성"은 해당 구간에만 새 후보를 추가합니다. 모델 실행이 필요하므로 GPU 환경에서 `review` 를 띄우거나, GPU 에서 `lipsync --segments 3` 후 `unpack` 하세요.
- 최종 선택은 항상 사용자가 합니다. 선택하지 않은 구간이 있으면 `finalize` 가 멈춥니다(`--fill-missing first|score` 로 명시적으로 허용).
- **finalize 기본값은 후처리 전부 켬**: CodeFormer(얼굴 복원) → 합성 → Real-ESRGAN(전체 프레임 업스케일, 기본 ×2) → RIFE(프레임 보간, 기본 ×2).
  - **해상도/FPS/길이**: 길이는 항상 원본과 같고, 켜 둔 옵션이 만드는 변화만 허용·검증합니다 — 업스케일 ×2 → 해상도 ×2, 보간 ×2 → **FPS ×2(24→48)**.
    원본 FPS 를 그대로 유지하려면 `--no-interpolate`, 원본 해상도 유지는 `--no-upscale` 입니다. 기대와 다르면 `final.mp4` 생성 후 오류로 알려줍니다.
  - CodeFormer/Real-ESRGAN/RIFE 가 설치되어 있지 않으면 한국어 오류로 멈춥니다(`CODEFORMER_DIR`, `REALESRGAN_DIR`, `RIFE_DIR` 환경변수 또는 `--restore-dir` 등). GPU 없이 CPU로도 돌 수 있지만 매우 느립니다. GPU 에서 돌리려면 `pack --kind full` 후 아래 GPU 절차 참고.
  - `--emotion` 을 주면 `emotion.json` 의 고개 끄덕임/미세 움직임을 얼굴 패치에 적용합니다(quality 프리셋은 기본 사용).

---

## ☁️ 외부 GPU(Colab / RunPod)에서 할 일

PC 에서 만든 `gpu_upload.zip` 만 있으면 됩니다(영상 전체가 아니라 구간별 입력만 담깁니다).

- **Colab**: `gpu/colab_notebook.ipynb` 를 열고 위에서부터 실행 — 설정 → 설치 → 모델 다운로드 → 업로드 → 실행 → `gpu_result.zip` 다운로드.
- **RunPod**: `bash gpu/runpod_setup.sh latentsync musetalk` (대상: `latentsync | musetalk | infinitetalk | wan_s2v | codeformer | realesrgan | rife`) 후
  ```bash
  source ~/.lipsync_env ; cd /workspace/-snow-motion/lipsync-pipeline
  python -m lipsync unpack 노래1 gpu_upload.zip --work-root "$WORK_ROOT"
  python -m lipsync run 노래1 --work-root "$WORK_ROOT" --preset quality --stages emotion,lipsync   # 후보 3개/구간, 최대 스텝, fp16
  python -m lipsync pack 노래1 --work-root "$WORK_ROOT" --kind result                              # → $WORK_ROOT/노래1/gpu_result.zip 내려받기
  ```
  후처리(CodeFormer/Real-ESRGAN/RIFE)도 GPU 에서 하려면 PC 에서 `pack --kind full` → 여기서 `unpack` → `python -m lipsync finalize 노래1 --work-root "$WORK_ROOT"`.

### Colab 에서 실제로 겪은 문제와 처리 (실측 교훈)
| 문제 | 처리 |
|---|---|
| 코랩 파이썬이 3.13 이라 LatentSync 의 `torch==2.5.1` 이 설치되지 않음 | `uv venv --python 3.10` 로 가상환경을 따로 만들고 환경변수 `LIPSYNC_TOOL_PYTHON=<그 환경의 python>` 으로 지정. 모델마다 요구 환경이 충돌하면(예: RIFE 는 `numpy<=1.23.5`, CodeFormer 는 Python 3.8 권장) `LIPSYNC_TOOL_PYTHON_<이름 대문자>`(예: `LIPSYNC_TOOL_PYTHON_RIFE`)로 그 도구만 따로 지정 — 우선순위: 도구별 > 공통 > 현재 인터프리터 |
| `huggingface-cli` 가 삭제됨 | `hf download <repo> [파일...] --local-dir <폴더>` 를 쓴다. **`--exclude` 뒤의 인자는 파일명으로 해석되므로 쓰지 않는다**(필요한 파일을 위치 인자로 나열) |
| 외부 모델 실행 시 matplotlib 오류 | 주피터/코랩이 넣어 둔 `MPLBACKEND` 가 별도 가상환경에 없음 → 외부 모델 실행 시 `MPLBACKEND=Agg` (어댑터가 자동으로 덮어씀, 환경 파일에도 기록) |
| LatentSync 가 24fps 입력을 25fps 로 만들어 프레임 수 검사 실패 | 파이프라인이 모델 출력의 fps/프레임 수를 입력과 같게 맞춘다(`models/base.py` `conform_to_source`). 해상도가 다른 얼굴 전체 생성 계열은 `resize_to_source` 도 적용 |
| 외부 모델이 입력 파일을 못 찾음 | 외부 모델은 저장소 폴더를 cwd 로 실행되므로 **작업 폴더는 절대경로**여야 한다(`--work-root "$WORK_ROOT"`) |

### 공식 코드와 대조하며 확인된 모델별 주의점
- **MuseTalk**: 영상·오디오 경로를 따옴표 없이 셸 명령에 넣어서 공백/한글 공백 경로가 깨집니다 → 어댑터가 공백 없는 임시 폴더로 복사해서 실행. 처리 중 예외를 삼켜 **종료 코드 0** 으로 끝나므로 출력 파일 존재로 성공을 판단합니다. `--use_float16` 을 빼면 품질이 좋아집니다(README 안내) → 품질 우선이면 `--precision fp32`. 샘플링 스텝/offload 옵션 없음.
- **InfiniteTalk**: 진입점은 `python generate_infinitetalk.py` (`-m` 아님). fps 25 고정, 출력 해상도는 640/960 정사각 버킷 → 입력 해상도로 되돌립니다. `--sample_steps` 기본 40 이 문서상 값(더 큰 값 안내 없음). offload 는 `--offload_model` / `--num_persistent_param_in_dit 0`.
- **Wan2.2-S2V**: `--prompt/--image/--audio` 를 안 주면 예제(흰 고양이 등)로 **조용히** 채워지므로 항상 명시합니다. 출력 fps 16 고정 → 24fps 입력이면 프레임 복제로 움직임이 끊겨 보일 수 있음. 최소 80GB VRAM 안내, 작은 GPU 는 `--offload model|sequential`.
- **CodeFormer**: `--has_aligned` 는 `restored_faces/` 에만 쓰고 항상 512x512 로 복원. 프레임 폴더 이름이 `.png` 등으로 끝나면 파일로 오인합니다.
- **Real-ESRGAN**: 영상 스크립트는 **CUDA 가 없으면 실행되지 않습니다**(`Pool(0)`) → GPU 가 없는 PC 에서는 어댑터가 프레임 단위 스크립트(CPU, 매우 느림)로 자동 폴백합니다. `-n` 기본값이 애니메이션용이라 `RealESRGAN_x4plus` 를 명시합니다.
- **RIFE(Practical-RIFE)**: 기본 출력은 `mp4v` 코덱(손실)이라 `--png` 로 무손실 프레임을 받아 H.264 로 인코딩합니다. 가중치는 Google Drive/Baidu 링크뿐이라 **수동 설치**(`train_log/flownet.pkl`). 파이썬 3.11 이하.

- **작은 VRAM**: `--offload model`(모델 단위 CPU offload) 또는 `--offload sequential`(레이어 단위, 가장 느리고 VRAM 최소). 정밀도는 `--precision fp16|bf16|fp32`.
  offload 를 실제로 적용하는 코드는 어댑터별 TODO 입니다(공식 코드에 옵션이 없으면 패치 필요).
- 같은 구간을 다른 모델/설정으로 더 만들고 비교: `python -m lipsync lipsync 노래1 --model musetalk --takes 2 --segments 3 --label musetalk-a` →
  PC 에서 `unpack` 후 `compare 노래1 --segment 3`.

---

## 📦 대량 처리 (batch)

`작업목록.csv` (UTF-8 또는 엑셀 cp949 저장 모두 읽음, 상대경로는 CSV 위치 기준):
```csv
영상경로,음원경로,이름,프리셋
D:\영상\컷1.mp4,D:\음원\노래A.wav,노래A_컷1,quality
D:\영상\컷2.mp4,D:\음원\노래A.wav,,fast
```
```powershell
python -m lipsync batch 작업목록.csv --until segments          # PC 에서: 앞 단계(scan, segments)까지
# … 각 작업을 pack/GPU/unpack …                                  # GPU 에서: run <이름> --stages emotion,lipsync
python -m lipsync batch 작업목록.csv --from finalize            # PC 에서: 마무리 (선택은 프리셋 fill_missing=score 로 임시 자동 선택)
```
- **이어하기**: 단계 완료 상태가 `work/<이름>/state.json` 에 기록되고, 끝난 단계는 건너뜁니다(`--force` 로 다시 실행해도 기존 결과는 `_archive`/새 take/새 finalize 폴더로 보존). 앞 단계를 다시 하면 뒤 단계는 `stale` 로 표시됩니다.
- **실패 격리**: 한 작업이 실패해도 다음 작업을 계속하고, 마지막에 실패 목록을 출력하며 `work/batch_summary_<시각>.csv` 로 저장합니다(종료 코드 1).
- **벤치마크**: 단계별 소요 시간이 `work/<이름>/report.csv` 에 누적됩니다(시각, 단계, 상태, 초, 영상 길이, 프레임 수, 모델, 장치, GPU 이름).
  GPU 구매 판단에는 `lipsync` 행의 `seconds / video_seconds` 를 보세요.
- 배치의 `finalize` 는 사람이 고르지 않으므로 점수 기준 임시 선택입니다. 마음에 드는 작업은 `review` 로 직접 고른 뒤 `finalize --tag 최종` 으로 다시 합치세요.

### 프리셋 (`presets/*.yaml`)
| 프리셋 | 내용 |
|---|---|
| `quality` | 얼굴 전체 합성(`paste_mode: face`) + 감정 레이어(`emotion: true`) + 후보 3개 + LatentSync + 후처리 전부 켬 |
| `fast` | 입 영역만 합성(`paste_mode: mouth`) + 후보 1개 + MuseTalk + 감정 레이어 끔. **이름과 달리 스텝/정밀도는 낮추지 않습니다**(속도 최적화 금지) |

키 목록은 `lipsync_pipeline/presets.py` 의 `Preset` 입니다(오타가 있으면 오류). 얼굴 전체 생성 계열(`infinitetalk`, `wan_s2v`)은 프리셋의 `model:` 로 선택합니다.

---

## 🧩 새 모델 추가

`lipsync_pipeline/models/` 에 파일 하나를 추가하고 `@register("이름")` 만 붙이면 CLI(`--model 이름`), 프리셋, review UI 에 나타납니다.

```python
from .base import BaseLipSyncModel, LipSyncRequest, register

@register("my_model")
class MyModel(BaseLipSyncModel):
    MODE = "inpaint_mouth"        # 또는 "face_generation"
    MAX_STEPS = 50                # 기본으로 쓰일 최대 품질 스텝
    def generate(self, req: LipSyncRequest):
        ...                       # req.video(정사각 얼굴 크롭 mp4) + req.audio(16kHz 모노 wav) → req.output
        return req.output
```
입출력 규격은 `models/base.py` 상단 주석: 출력은 **입력과 같은 해상도·fps·프레임 수**(±2프레임 허용, 아니면 오류).
복원/업스케일/보간도 `BasePostProcessor` 로 같은 방식입니다. 현재 어댑터: `latentsync`(Colab 에서 실행 확인), `musetalk`, `infinitetalk`, `wan_s2v`, `codeformer`, `realesrgan`, `rife`(공식 코드 대조 완료·GPU 실행 미검증), `identity`(CPU 테스트용 복사).

## 📁 작업 폴더 구조 (`work/<이름>/`)
```
info.json  state.json  report.csv  video_noaudio.mp4  audio_44k.wav  audio_16k.wav  vocals*.wav
analysis.json  cuts.json  cuts_report.csv  scan.json  face_track.json  face_crop.mp4  emotion.json
segments.json  segments/001/{input.mp4,audio.wav,take_1.mp4,take_1.json,...}  segments/generation_log.jsonl
selection.json  selection_history/  compare/  finalize/<tag>/{01_assembled_crop,02_restored_crop,03_composited,04_upscaled,05_interpolated,final.mp4,render.json}
_archive/<시각>/   # 다시 실행하며 밀려난 이전 결과
```
`.gitignore` 로 영상·음원·가중치·`work/` 는 커밋되지 않습니다.

## 테스트
```bash
pip install -e ".[dev]" && python -m pytest -q
```
ffmpeg 로 합성한 샘플(testsrc+smptebars 영상, sine 톤 음원, 한글·공백 파일명)로 prepare~finalize 전체 흐름, 구간 분할/크로스페이드, 후보 번호 보존, review 서버, batch/이어하기 등을 CPU 에서 검증합니다. 얼굴 검출기는 가짜 검출기를 주입합니다(합성 영상에는 얼굴이 없으므로).
