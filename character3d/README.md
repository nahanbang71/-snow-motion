# Character Builder 3D

슬라이더로 3D 캐릭터의 머리 크기·체형·키를 바꾸고, 조명/배경 색을 바꾸며, 영상으로 뽑는 프로그램입니다.

## 실행
```
python3 -m http.server 8000      # 저장소 루트에서
# 브라우저: http://localhost:8000/character3d/index.html
```
- 모델 없이 열면 기본 3D 캐릭터(Nieve)가 나옵니다.
- `.glb` 파일을 화면에 끌어다 놓거나 "📂 .glb 모델 불러오기"를 누르면 내 캐릭터로 바뀝니다.
- 모델에 애니메이션 클립이 있으면 Animation 드롭다운에서 고를 수 있습니다.
- "▶ 자동 데모"는 영상과 같은 20초 타임라인(머리 커짐 → 키 커짐 → 체형 → 배경색 변경 → 원래대로)을 재생합니다.

## 영상 만들기
```
# 기본 캐릭터 → mp4 (UI 패널 포함, 프레임 단위로 정확하게 렌더링)
node tools/render_character3d.js character3d/demo.mp4 20 1280 720
# 내 모델로
node tools/render_character3d.js out.mp4 20 1280 720 character3d/models/my.glb
```
브라우저에서 바로 녹화하려면 "⏺ 캔버스 녹화"(webm, 캐릭터 영역만)를 쓰세요.

## 영상 속 같은 캐릭터 만드는 순서
1. **이미지 만들기** (Midjourney / Nano Banana / Flux 등)
   `Pixar-style 3D girl, short bob hair, dark brown hoodie, baseball cap, olive cargo pants, chunky sneakers, soft studio lighting, full body, neutral background, front view, T-pose-like relaxed stance`
   정면 전신, 단색 배경으로 만들면 다음 단계가 잘 됩니다.
2. **3D 모델로 변환** (Meshy / Tripo / Rodin / Hunyuan3D) → `.glb` 다운로드. 가능하면 "rig/animate" 옵션을 켜세요.
3. **리깅·동작** (Mixamo, 무료): 모델 업로드 → 자동 리깅 → 동작(Idle, Waving 등) 선택 → `.glb`로 변환(Blender)해 받기.
4. 이 프로그램에 올려서 슬라이더·색 조절 → `render_character3d.js`로 mp4 출력.

### 머리 크기가 안 먹으면
머리 뼈대/노드 이름에 `head`가 들어 있어야 합니다(Mixamo는 `mixamorig:Head`). 없으면 Head size 슬라이더는 비활성화됩니다. Height/Body shape는 모델 전체 크기로 동작합니다.

## 구성
- `index.html`: 앱 본체(Three.js, 모듈은 `lib/`에 포함되어 오프라인 동작)
- `../tools/render_character3d.js`: 데모 타임라인을 mp4로 렌더링 (Playwright + ffmpeg)
