# 전 세계 공항 레이저 영상 (5분)

`공항_5분.mp4` — 1920×1080, 30fps, 정확히 300초. 소리 없음(음악은 편집 단계에서 얹기).
공항 30곳(7초) + 이착륙 10개(7초) + 타이틀 8초 + 크레딧 12초 = 300초. 컷 사이는 페이드 없이 그대로 이어 붙임
(각 클립이 스스로 마지막 0.8초에 페이드아웃).

| 구간 | 내용 | 길이 |
|---|---|---|
| 타이틀 | 로고·제목 | 8초 |
| 챕터1 아시아 | F01 이륙 → ICN PKX HKG BKK KIX SIN HND → F02 이륙 | 63초 |
| 챕터2 중동·아프리카 | F03 착륙 → DXB DOH IST CAI CPT → F04 이륙 | 49초 |
| 챕터3 유럽 | F05 착륙 → LHR CDG AMS MAD FCO ZRH → F06 이륙 | 56초 |
| 챕터4 북미 | F07 착륙 → JFK LAX SFO DEN YVR MIA → F08 이륙 | 56초 |
| 챕터5 남미·오세아니아 | F09 착륙 → GIG SCL EZE SYD AKL HNL → F10 착륙(엔딩) | 56초 |
| 크레딧 | 영문 크레딧 (Suno 상업 라이선스 표기 포함) | 12초 |

챕터 색(메인 / 포인트): 1 `#35f3ff`/`#ff4fd8` · 2 `#ffb03a`/`#ff5a8a` · 3 `#b78bff`/`#ffd166` · 4 `#39ff9c`/`#4d7cff` · 5 `#ff4fd8`/`#ffe14d`

## 폴더

- `svg/` — 원본 SVG 42개. 공항 `ch{챕터}_{번호}_{코드}.svg`, 이착륙 `flight_{번호}_{takeoff|landing}.svg`, `title.svg`, `credits.svg`
- `clips/` — SVG를 7초(타이틀 8초, 크레딧 12초) mp4로 렌더한 클립. 파일 앞 번호가 재생 순서
- `정지시트/` — 검수용 정지 프레임 시트. `airports_A~F.jpg`는 PDF의 배치 A~F(5개씩), `flights_multiexposure.jpg`는 이착륙 10개를 여러 시점 겹쳐 비행기·장식이 겹치지 않는지 본 것

## 공항별 배경

공항마다 지역 특색에 맞는 배경을 랜드마크 양옆에 아주 옅게(불투명도 40%, 가는 선) 깔았음. 중앙과 하단은 비워 두어 어디에 가사·타이포를 얹어도 읽히게 함.
예) HKG 고층 스카이라인+항구 물결, DXB 사막 능선+고층 실루엣, IST 돔·미나렛+초승달, AMS 운하 박공집, SYD 하버브리지 아치+요트, AKL 요트+화산.
정의는 `tools/airport_bg.py`의 `build(코드)`.

## 다시 만들기

```
python3 tools/gen_airports.py          # SVG 42개 생성 (랜드마크 데이터는 tools/airport_data.py)
python3 tools/make_airport_video.py    # 클립 렌더(4병렬) + 순서대로 이어 붙이기. 이미 있는 클립은 건너뜀
node tools/render_airport.js still <svg> <out.png> 4        # 정지 프레임(시각 t초)
node tools/render_airport.js video <svg> <out.mp4> 7        # 한 개만 렌더
```

SVG는 CSS 애니메이션(그리기·페이드)과 이착륙의 SMIL(animateMotion)을 쓰므로 렌더러가 시간을 직접 옮겨가며 캡처합니다.

## 사양 대비 메모

- 공항 SVG는 마스터 프롬프트 1의 캔버스·선 규칙·타이밍(그리기 1.4초/0.22초 간격, 글자 2.6·3.0초, 페이드아웃 6.2초)을 그대로 따름.
- 이착륙 SVG는 마스터 프롬프트 3의 무대·비행기 path·궤적·keySplines를 그대로 따름.
- **F02(이륙)의 관제탑은 표에는 "우"지만 좌로 배치.** 이륙 궤적이 x≈1780에서 y≈545를 지나가서 우측 탑과 비행기가 겹침. 이륙은 모두 좌, 착륙은 모두 우로 통일.
- 한글 폰트가 없어 영상 속 글자는 전부 영문. 외곽선 글꼴은 Helvetica Neue → Arial 폴백(렌더 환경에서는 Liberation Sans).
- 크레딧의 Suno 문구와 "created with Claude" 문구는 임시 문구라, 실제 사용한 곡·플랜에 맞게 `tools/gen_airports.py`의 `credits_svg()`에서 고칠 것.
