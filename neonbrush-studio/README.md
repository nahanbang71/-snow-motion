# NeonBrush Studio

1024×1024 투명 PNG 글자 팩(.zip)을 **① 컴퓨터에 설치하는 폰트(.ttf/.otf/컬러 .otf)** 로 바꾸고,
**② 브라우저에서 키보드로 바로 조판해 투명 PNG로 저장**하고, **③ BRSh 워터마크를 여러 이미지에 일괄 합성**하는 프로젝트입니다.

```
neonbrush-studio/
├─ packs/                 pack_overrides.json(파일명/내용 불일치 보정표). 원본 .zip은 용량 때문에 삭제함(아래 '원본 zip 복구' 참고)
├─ pipeline/              Part 1: PNG → 폰트 변환 파이프라인 (Python)
│   ├─ build_fonts.py       ← 한 번에 전부 변환하는 배치 스크립트
│   └─ nbfont/              naming · packs · clean · layout · vector · build · verify · specimen · webpack
├─ output_fonts/          변환 결과 (폰트 이름별 폴더: .ttf .otf [-Color.otf] specimen.png report.json)
├─ webapp/                Part 2: NeonBrush Studio 웹앱 (React + TypeScript + Vite + Canvas)
│   └─ public/packs, public/watermarks   앱에 내장되는 글꼴/워터마크 (파이프라인이 생성)
├─ samples/               테스트용 샘플 PNG/zip 생성기
└─ tests/                 test_pipeline.py (단위/빌드 검증) · e2e.mjs (브라우저 전체 시나리오)
```

## 원본 zip 복구
원본 글자 팩 zip(46개)은 작업이 끝난 뒤 작업 폴더에서 삭제했습니다. 변환 결과(`output_fonts/`, `webapp/public/packs/`)는 그대로 있고,
원본이 다시 필요하면 git 기록에서 꺼낼 수 있습니다(마지막으로 모두 들어 있던 커밋 `be1f373`):
```bash
git checkout be1f373 -- neonbrush-studio/packs      # packs/*.zip 복원
```
새 팩은 평소처럼 `packs/`에 넣고 변환하면 됩니다. 폰트를 다시 만들 때는 원본 zip이 필요하고, `ALPHABET_V2.zip`은 `pack_overrides.json`과 함께 있어야 합니다.

## 빠른 시작 (새 zip 5개를 받을 때마다 이 순서)

```bash
pip install -r pipeline/requirements.txt          # 1회
cp 새팩들.zip packs/                               # zip을 packs/ 에 넣는다
python3 pipeline/build_fonts.py                    # packs/ 의 모든 zip을 일괄 변환 → output_fonts/, webapp/public/*
cd webapp && npm install && npm run build          # (선택) 웹앱 다시 빌드 → webapp/dist
```

`build_fonts.py` 한 번이 하는 일
1. `packs/*.zip` (폴더도 가능)를 전부 읽는다. zip 안에 하위 폴더가 여러 개면 폴더마다 별개 폰트(예: ALPHABET_V2 → 4개 스타일).
2. 파일명을 글자에 매핑한다 → `A.png`=A, `0.png`=0, `COMMA`=`,` `APOS`=`'` `EXCL`=`!` `QUEST`=`?` `AMP`=`&` `AT`=`@` `PERIOD` `HYPHEN` `COLON` … `u0041.png`(유니코드)도 가능. 글자가 아닌 파일(`10.png` 등)은 건너뛴다.
3. BRSh 워터마크 팩처럼 글자 파일이 아닌 zip은 자동으로 **워터마크 팩**으로 분류해 `webapp/public/watermarks/`로 복사한다.
4. 정리(clean) → 베이스라인/크기 계산(layout) → 알파 윤곽 벡터화(potrace) → `.ttf` `.otf` 생성.
5. 색이 있는 팩(네온/멀티컬러)이면 원본 PNG를 품은 **OpenType-SVG 컬러 `.otf`** 도 추가 생성(`--color all|none`으로 강제 가능).
6. 모든 폰트를 검증(cmap · HarfBuzz 타이핑 시뮬레이션 · 컬러 SVG 문서 검사)하고 `specimen.png`/`report.json` 저장.
7. `--webpacks DIR`이면 웹앱용 정규화 팩(`pack.json` + 정리된 PNG)도 만든다.

옵션: `-j N`(동시에 변환할 팩 수, 기본 4) · `--web-px 768`(웹앱 팩 글자 이미지 최대 크기) · `-o 출력폴더` · `--only 이름일부` · `--color auto|all|none` · `--no-lower`(소문자를 대문자 글리프에 연결하지 않음) · `--svg-px 384` · `--overrides 파일` · `--webpacks 폴더` · `--watermarks 폴더`

## ⚠️ 받은 팩에서 발견된 문제와 처리 방법

| 팩 | 문제 | 처리 |
|---|---|---|
| ALPHABET_V2 (4개 스타일) | **파일명과 실제 글자가 다름** (예: `A.png`에 K/P/Z가 들어 있음), 타일 안에 **옆 글자 조각**이 섞임, 숫자(0-9)·`&`·`@` 없음 | `packs/pack_overrides.json`에 파일→실제 글자 보정표 기록(눈으로 확인), `clean: neighbors`로 조각 제거, `layout: align`으로 기준선 정렬 |
| autumn_maple / bold_calligraphy / plum_blossom / brush / calligraphy(검정·흰색) / candy_neon / cyan_neon | 정상(파일명=내용). autumn·plum·candy의 `10.png`는 글자 하나가 아니라 "10" 이라 폰트에서 제외. `calligraphy_alphabet`(검정 잉크)은 어두운 글자라 웹앱 미리보기 배경을 '밝게'로 | — |
| 모든 글자 팩 | **`&`, `@`는 어느 팩에도 없음**. 숫자 0-9는 autumn·plum·candy 팩만 있음(나머지는 A-Z와 `, ' ! ?` 만 수록) | `AMP.png`/`AT.png`를 추가하면 자동 반영 |
| BRSh 워터마크 2팩 | 글자 팩이 아님(2000×1000 워터마크 8종×2) | 워터마크 탭에 내장 |

새 팩의 파일명이 어긋나 있으면 `output_fonts/<이름>/specimen.png`에서 바로 보이므로(순서가 뒤섞여 보임),
`packs/pack_overrides.json`에 항목을 추가하면 됩니다:
```json
{ "팩파일명일부::하위폴더": {
    "labels":  { "A": "K", "APOS": "'" },          // 파일명(확장자 제외) → 실제 글자
    "options": { "clean": "neighbors", "layout": "align", "threshold": 40 } } }
```
`options`: `clean`(`neighbors` = 타일 안 옆 글자 조각 제거) · `layout`(`auto`/`canvas`/`fit`/`align`) · `threshold`(알파 임계값, 가는 선 팩은 낮게) · `mono_source`(`white` = 컬러 장식 제외하고 흰 획만 벡터화).

## 현재 변환된 폰트 (`output_fonts/`)
Alphabet V2 (Dry Scratch · Rough Grunge · Smooth Ink · Wispy Feathered) · Autumn Maple Momiji (+Color) · Bold Calligraphy Alphabet White ·
Brush Alphabet · Calligraphy Alphabet · Calligraphy Alphabet White · Candy Neon Pastel (+Color) · Cyan Neon Alphabet (+Color) · White Plum Blossom — 총 12개, 컬러(OpenType-SVG) 3개.

## 설치해서 쓰기
- **.ttf** : 윈도우/맥 어디서나 (더블클릭 → 설치). 한 가지 색(프로그램의 글자색)으로 나옵니다.
- **.otf** : 디자인 프로그램용 같은 윤곽(CFF).
- **`-Color.otf`** : OpenType-SVG 컬러 폰트. **포토샵 · 일러스트레이터 · 인디자인**은 컬러로 표시합니다. 브라우저는 Firefox는 지원하지만 Chrome/Edge/Safari는 일부만 지원하거나 흑백 윤곽으로 보입니다. 지원하지 않는 프로그램(구형 프리미어 등)에서는 같은 이름의 흑백 윤곽이 보이는 것이 정상이며, 이때는 웹앱에서 투명 PNG로 뽑아 쓰는 것이 가장 확실합니다.
- 소문자 입력은 같은 대문자 모양으로 나옵니다. 팩에 없는 글자는 표시되지 않습니다(한글 불가).

## 웹앱 (NeonBrush Studio)
```bash
cd webapp && npm install
npm run dev        # 개발 서버
npm run build      # webapp/dist (상대경로라 어느 폴더/깃허브 페이지에서도 동작)
npm run preview    # 빌드 결과 확인 http://127.0.0.1:4173
```
- **글자 조판 탭**: 왼쪽 목록에서 글꼴 선택(파이프라인이 만든 내장 글꼴 + 직접 `.zip` 드래그 앤 드롭). 아무 키나 누르면 입력창에 들어가고 캔버스에 실시간 조판됩니다.
  자간 · 띄어쓰기 폭 · 줄 간격 · 아치 곡선(−100 ~ +100) · 글자 크기 · 줄 정렬(좌/중/우) · 여러 줄(Enter) · 단색 팩 글자색.
  **투명 PNG 다운로드**: 여백이 딱 맞게 크롭되고 1×~6× 해상도 선택(최대 12000px).
- **배치 워터마커 탭**: 이미지 여러 장을 올리고 BRSh 워터마크(내장 8종 또는 내 PNG)를 선택, 투명도(기본 45%) · 크기 · 위치 9칸 · 여백 · 타일 반복 · 저장 형식(PNG/JPEG/WebP) 조절 → **일괄 합성** → ZIP 저장.
- 원본 zip을 그대로 드롭해도 열리지만(파일명 기준, 크기·기준선은 추정), 파일명 불일치 보정·조각 제거는 파이프라인(`build_fonts.py`)이 만든 **내장 글꼴**에만 적용됩니다.

## 검증
```bash
pip install -r pipeline/requirements.txt
python3 -m unittest discover -s tests -v            # 이름 매핑·정리·보정·폰트 생성(.ttf/.otf/OpenType-SVG)·HarfBuzz 타이핑 검증
cd webapp && npm install && npm run build && npm i --no-save playwright && cd ..
node tests/e2e.mjs                                   # 브라우저: 내장글꼴 로드, zip 로드, 타이핑, 자간/아치, 투명PNG 크롭 검증, 워터마크 일괄 합성+ZIP
```
샘플 PNG 세트는 `samples/make_samples.py`가 생성합니다(`TestMono.zip` 단색, `TestNeon.zip` 네온 글로우 → 컬러 폰트 경로 검증, `images/` 워터마크 시험용 사진).

## 원리 / 한계
- 벡터화는 알파 채널을 potrace(potracer)로 따라 그립니다. 손맛이 있는 브러시(거친 가장자리, 가는 깃털 선)는 윤곽이 많아져 폰트 용량이 큽니다.
- 글자 크기·기준선은 팩 전체에서 하나로 계산합니다(`layout.py`): `canvas`(PNG 안 위치 유지) · `fit`(모든 글자를 같은 높이로) · `align`(한 크기 + 바닥 정렬). 기본 `auto`.
- 커닝 쌍(kern/GPOS)은 만들지 않습니다(글자 사이는 균일한 좌우 여백 + 앱의 자간 슬라이더).
- 컬러 폰트는 글리프마다 원본 PNG(기본 최대 384px)를 SVG 안에 data URI로 포함합니다. 큰 글자로 쓰면 해상도가 부족할 수 있어 `--svg-px 1024`로 올릴 수 있습니다(파일 용량 증가).
