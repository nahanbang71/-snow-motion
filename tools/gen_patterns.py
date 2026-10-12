#!/usr/bin/env python3
"""Generate every Korean traditional pattern (neon / laser line art):
  한국전통문양/<category>/<slug>.svg   grow animation: dot -> expands past the screen (8 s, 1920x1080)
  한국전통문양/_preview/<slug>.svg      static medallion (for the gallery / thumbnails)
  한국전통문양/intro.svg               full-screen mosaic of all patterns (intro page)
  한국전통문양/index.html + READMEs

usage: python3 tools/gen_patterns.py
"""
import html
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'kp'))
import core  # noqa: E402
from core import frame, grow_svg  # noqa: E402
import plants, animals, nature, geometry, text, special, dancheong  # noqa: E402

ROOT = os.path.join(HERE, '..', '한국전통문양')
MODULES = [plants, animals, nature, geometry, text, special, dancheong]
ALL = {}
for m in MODULES:
    ALL.update(m.PATTERNS)

# patterns that are not procedural (made from a supplied drawing)
EXTERNAL = {'bonghwang': ('02_동물문', '봉황', 'bonghwang_laser.svg')}
CATS = ['01_식물문', '02_동물문', '03_자연문', '04_기하문', '05_문자_길상문', '06_특별묶음', '07_단청문양']
CAT_NAME = {'01_식물문': '식물문', '02_동물문': '동물문', '03_자연문': '자연문', '04_기하문': '기하문',
            '05_문자_길상문': '문자·길상문', '06_특별묶음': '특별 묶음', '07_단청문양': '단청 문양'}

STATIC_DEFS = ('<defs><clipPath id="clipc"><circle r="102"/></clipPath>'
               '<filter id="glow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="3" result="b"/>'
               '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
               '<style>.l{fill:none;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}</style></defs>')


def static_svg(inner, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-140 -140 280 280" width="560" height="560"><title>{title}</title>'
            f'{STATIC_DEFS}<rect x="-140" y="-140" width="280" height="280" fill="#0d1030"/>'
            f'<g filter="url(#glow)">{frame()}{inner}</g></svg>')


def bonghwang_tile():
    src = open(os.path.join(ROOT, '02_동물문', 'bonghwang_laser.svg'), encoding='utf-8').read()
    ds = re.findall(r'<path class="d c" [^>]*d="([^"]+)"', src)
    body = ''.join(f'<path class="l" stroke="url(#gph)" stroke-width="3.2" d="{d}"/>' for d in ds)
    return G_scale(body)


def G_scale(body):
    return f'<g transform="scale(.19) translate(-500 -500)">{body}</g>'


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(data)


def main():
    inners = {}
    for slug, (cat, ko, fn) in ALL.items():
        inner = fn()
        inners[slug] = inner
        write(os.path.join(ROOT, cat, slug + '.svg'), grow_svg(inner, f'{ko} - neon line art'))
        write(os.path.join(ROOT, '_preview', slug + '.svg'), static_svg(inner, ko))
    # static preview of the phoenix (from the existing laser svg)
    write(os.path.join(ROOT, '_preview', 'bonghwang.svg'), static_svg(bonghwang_tile(), '봉황').replace('<defs>', GPH_DEFS + '<defs>', 1))
    intro(inners)
    readmes()
    gallery()
    print(len(ALL), 'procedural patterns +', len(EXTERNAL), 'external')


GPH_DEFS = ''  # gradient defs are injected inside static/intro svg (below)
GPH = ('<linearGradient id="gph" gradientUnits="userSpaceOnUse" x1="0" y1="60" x2="0" y2="950">'
       '<stop offset="0" stop-color="#ff3860"/><stop offset=".2" stop-color="#ff9628"/><stop offset=".36" stop-color="#ffe14a"/>'
       '<stop offset=".52" stop-color="#3df2c0"/><stop offset=".68" stop-color="#5aa9ff"/><stop offset=".82" stop-color="#b48cff"/>'
       '<stop offset="1" stop-color="#ff4fd8"/></linearGradient>')


def intro(inners):
    W, H = 1600, 900
    rnd = random.Random(11)
    tiles = list(inners.items()) + [('bonghwang', None)]
    pool = []
    while len(pool) < 140:
        t = tiles[:]
        rnd.shuffle(t)
        pool += t
    sx, sy = 128, 112
    cells = []
    for r, y in enumerate(range(-10, H + 70, sy)):
        for x in range(-50 - (r % 2) * (sx // 2), W + 70, sx):
            cells.append((x + rnd.randint(-6, 6), y + rnd.randint(-6, 6)))
    cx, cy = W / 2, H / 2
    maxd = math.hypot(cx, cy)
    out = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="1920" height="1080">
<title>Korean traditional patterns - intro</title>
<defs><radialGradient id="bg" cx="50%" cy="50%" r="75%"><stop offset="0" stop-color="#14183a"/><stop offset="1" stop-color="#080a1a"/></radialGradient>
{GPH}<clipPath id="clipc"><circle r="102"/></clipPath>
<filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>.l{{fill:none;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}}
.t{{opacity:0;transform:scale(.2);animation:pop .7s cubic-bezier(.2,.8,.3,1) var(--s) forwards}}
.zoom{{transform-origin:800px 450px;animation:zoom 6s ease-in-out forwards}}
@keyframes pop{{to{{opacity:1;transform:scale(1)}}}}
@keyframes zoom{{from{{transform:scale(1)}}to{{transform:scale(1.06)}}}}</style></defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/><g class="zoom"><g filter="url(#glow)">''']
    for i, (x, y) in enumerate(cells):
        slug, inner = pool[i]
        d = math.hypot(x - cx, y - cy) / maxd
        t0 = .1 + d * 3.3 + rnd.random() * .25
        body = (frame() + inner) if inner is not None else (frame() + bonghwang_tile())
        out.append(f'<g transform="translate({x} {y}) scale(.47)"><g class="t" style="--s:{t0:.2f}s">{body}</g></g>')
    out.append('</g></g></svg>')
    write(os.path.join(ROOT, 'intro.svg'), '\n'.join(out))


def readmes():
    root = ['# 한국 전통문양 (Korean traditional patterns)\n',
            '네온/레이저 라인 아트 SVG 모음. 글자(이름) 없이 문양만, 화면 중앙의 점에서 시작해 커지면서 화면 밖으로 나가는 8초 애니메이션 (1920×1080).\n',
            '- `intro.svg` / `intro.mp4` : 모든 문양이 화면을 가득 채우는 인트로\n- `index.html` : 전체 갤러리\n- `_preview/` : 문양별 정지 이미지(미리보기)\n- `_source/` : 원본(참고용) 이미지\n- 번호 폴더 : 분류별 SVG\n']
    total = 0
    for cat in CATS:
        items = [(s, ko, f'{s}.svg') for s, (c, ko, _) in ALL.items() if c == cat]
        items += [(s, ko, fn) for s, (c, ko, fn) in EXTERNAL.items() if c == cat]
        total += len(items)
        root.append(f'\n## {cat} — {CAT_NAME[cat]} ({len(items)}개)\n\n| 문양 | 파일 |\n|---|---|')
        for s, ko, fn in items:
            root.append(f'| {ko} | `{cat}/{fn}` |')
        write(os.path.join(ROOT, cat, 'README.md'), f'# {CAT_NAME[cat]}\n\n' + '\n'.join(f'- {ko} (`{fn}`)' for s, ko, fn in items) + '\n')
    root.append(f'\n총 {total}개.\n')
    root.append('\n※ 십장생·사군자는 다른 분류와 겹치는 문양(소나무, 거북, 학, 매·난·국·죽 등)을 작게 모은 구성작입니다. 개별 문양은 각 분류 폴더에 있습니다.')
    root.append('\n※ 문양은 제가 직접 도안한 단순화된 해석입니다. 시대·용도별 전통 도상과 세부가 다를 수 있습니다. 수·복·희 등 글자 문양은 폰트 윤곽선을 경로로 변환한 것입니다.')
    write(os.path.join(ROOT, 'README.md'), '\n'.join(root) + '\n')


def gallery():
    cards = []
    for cat in CATS:
        cards.append(f'<h2>{cat[3:] if False else CAT_NAME[cat]}</h2><div class="g">')
        for s, (c, ko, _) in ALL.items():
            if c == cat:
                cards.append(f'<figure><img loading="lazy" src="_preview/{s}.svg" alt="{html.escape(ko)}"><figcaption>{html.escape(ko)}<span>{cat}/{s}.svg</span></figcaption></figure>')
        for s, (c, ko, fn) in EXTERNAL.items():
            if c == cat:
                cards.append(f'<figure><img loading="lazy" src="_preview/{s}.svg" alt="{html.escape(ko)}"><figcaption>{html.escape(ko)}<span>{cat}/{fn}</span></figcaption></figure>')
        cards.append('</div>')
    write(os.path.join(ROOT, 'index.html'), f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>한국 전통문양</title><style>:root{{--bg:#080a1a;--fg:#e6e9ff;--mut:#8f95c4}}
body{{margin:0;padding:24px 16px;background:var(--bg);color:var(--fg);font-family:system-ui,'Noto Sans KR','Malgun Gothic',sans-serif}}
h1,h2{{text-align:center;font-weight:600}}.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;max-width:1300px;margin:0 auto 28px}}
figure{{margin:0;background:#0d1030;border-radius:12px;overflow:hidden}}img{{width:100%;display:block}}
figcaption{{padding:8px 12px;display:flex;flex-direction:column;font-size:14px}}figcaption span{{color:var(--mut);font-size:11px}}</style></head>
<body><h1>한국 전통문양 · {len(ALL) + len(EXTERNAL)}</h1>{''.join(cards)}</body></html>''')


# the static phoenix preview needs the gradient: patch static_svg for it
_old_static = static_svg


def static_svg(inner, title):  # noqa: F811
    s = _old_static(inner, title)
    if 'url(#gph)' in inner:
        s = s.replace('<defs>', '<defs>' + GPH, 1)
    return s


if __name__ == '__main__':
    main()
