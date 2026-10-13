#!/usr/bin/env python3
"""World-airport laser line-art set -> 공항영상/svg/*.svg
30 airport SVGs (7 s) + 10 takeoff/landing SVGs (7 s) + title (8 s) + credits (12 s) = 300 s.
Spec: airport_laser_prompts (master prompts 1 and 3)."""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from airport_data import A, CH_COLOR, f, circle, wave, palm  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '공항영상', 'svg')
FONT = "font-family=\"'Helvetica Neue', Arial, sans-serif\""
PLANE_GLYPH = ('M0 -40 C4 -40 5 -30 5 -20 L40 8 V16 L5 6 L5 26 L16 34 V39 L0 35 L-16 39 V34 L-5 26 L-5 6 '
               'L-40 16 V8 L-5 -20 C-5 -30 -4 -40 0 -40 Z')

GLOW = ('<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080">'
        '<feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge></filter>')


def svg_wrap(title, body, style, extra_defs=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">\n'
            f'<title>{title}</title>\n<defs>{GLOW}{extra_defs}<style>{style}</style></defs>\n'
            f'<rect width="1920" height="1080" fill="#05060d"/>\n{body}\n</svg>\n')


# ---------------------------------------------------------------- airports
def airport_svg(a, n):
    main, acc = CH_COLOR[a['ch']]
    css = (
        f'.m{{stroke:{main}}}.p{{stroke:{acc}}}'
        '.d{fill:none;stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;'
        'opacity:0;animation:draw 1.4s cubic-bezier(.12,.7,.3,1) both}'
        '@keyframes draw{0%{stroke-dashoffset:1;opacity:0}1%{opacity:1}100%{stroke-dashoffset:0;opacity:1}}'
        '.all{animation:out .8s linear 6.2s both}@keyframes out{from{opacity:1}to{opacity:0}}'
        '.t{fill:none;stroke-width:1.6;text-anchor:middle;opacity:0;animation:fade .7s ease-out both}'
        '@keyframes fade{from{opacity:0}to{opacity:1}}')
    els = []
    k = 0

    def path(d, cls, extra=''):
        nonlocal k
        els.append(f'<path class="d {cls}" pathLength="1" style="animation-delay:{k * .22:.2f}s" d="{d}"{extra}/>')
        k += 1

    path('M0 360 H600', 'p')
    for d in a['main']:
        path(d, 'm')
    for d in a['aux']:
        path(d, 'p')
    px, py, pa = a['plane']
    path(PLANE_GLYPH, 'p', f' transform="translate({px} {py}) rotate({pa}) scale(0.9)"')
    body = (f'<g filter="url(#glow)" class="all">\n<g transform="translate(480 150) scale(1.6)">\n' + '\n'.join(els) + '\n</g>\n'
            f'<text class="t p" x="960" y="800" font-size="30" letter-spacing="14" {FONT} style="animation-delay:2.6s">{a["name"]}</text>\n'
            f'<text class="t m" x="960" y="900" font-size="64" letter-spacing="14" {FONT} style="animation-delay:3s">{a["code"]}</text>\n</g>')
    return svg_wrap(f'{a["code"]} {a["name"]}', body, css)


# ----------------------------------------------------------------- flights
def cross(x, y, s):
    return f'M{f(x - s)} {f(y)} H{f(x + s)} M{f(x)} {f(y - s)} V{f(y + s)}'


def cloud(x, y, spec):
    d = f'M{x} {y}'
    for r in spec:
        d += f' a{r} {r} 0 0 1 {2 * r} 0'
    return d


def semi(cx, cy, r):
    return f'M{f(cx - r)} {f(cy)} A{r} {r} 0 0 1 {f(cx + r)} {f(cy)}'


def conifer(x, base, h):
    t = h / 100
    return (f'M{f(x)} {base} V{f(base - 10 * t)} M{f(x - 30 * t)} {f(base - 10 * t)} L{f(x)} {f(base - 55 * t)} L{f(x + 30 * t)} {f(base - 10 * t)} '
            f'M{f(x - 24 * t)} {f(base - 40 * t)} L{f(x)} {f(base - 82 * t)} L{f(x + 24 * t)} {f(base - 40 * t)} '
            f'M{f(x - 18 * t)} {f(base - 68 * t)} L{f(x)} {f(base - 110 * t)} L{f(x + 18 * t)} {f(base - 68 * t)}')


def lamp(x, base):
    return f'M{x} {base} V{base - 78} H{x + 26} V{base - 66}'


def stars_f01():
    rnd = random.Random(11)
    pts = []
    while len(pts) < 40:
        x, y = rnd.randint(60, 1860), rnd.randint(190, 520)
        if (80 < x < 210 and y > 420) or (x > 1500 and y > 380) or (1380 < x < 1560 and 170 < y < 330):
            continue
        if all(math.hypot(x - a, y - b) > 70 for a, b in pts):
            pts.append((x, y))
    return pts


def skyline(x0, x1, base, rnd):
    d = f'M{x0} {base}'
    x = x0
    while x < x1:
        w = rnd.choice((30, 40, 50))
        h = rnd.choice((40, 70, 95, 120, 55))
        d += f' V{base - h} H{x + w} V{base}'
        x += w
    return d


def mesa():
    return ('M450 700 V660 H500 V630 H560 V610 H640 V645 H690 V590 H760 V640 H820 V670 H880 V620 H960 V660 H1020 V700')


def ridge(x0, x1, base, rnd, amp):
    pts = [(x0, base)]
    x = x0 + 50
    while x < x1:
        pts.append((x, base - rnd.randint(amp // 3, amp)))
        x += rnd.randint(55, 95)
    pts.append((x1, base))
    return 'M' + ' L'.join(f'{a} {b}' for a, b in pts)


# number -> (kind, chapter, tower side, sky items, ground items, top, bottom)
def decor(n):
    rnd = random.Random(100 + n)
    sky, ground = [], []
    if n == 1:
        sky = [cross(x, y, 7) for x, y in stars_f01()] + ['M1450 235 A60 60 0 1 0 1450 355 A44 60 0 1 1 1450 235']
    elif n == 2:
        sky = [semi(640, 700, 130), semi(640, 700, 95), semi(640, 700, 60), 'M490 700 H790',
               cloud(210, 520, (26, 34, 26, 20)), cloud(930, 450, (22, 30, 38, 24))]
    elif n == 3:
        sky = [semi(1300, 700, 190), semi(1300, 700, 125)]
        ground = ['M880 700 C960 640 1060 640 1160 700', 'M1100 700 C1200 625 1330 625 1450 700', 'M1380 700 C1460 655 1570 655 1740 700']
    elif n == 4:
        sky = [circle(1000, 300, 75), circle(1000, 300, 55), wave(780, 1230, 335, 7, 70)]
        for x, h, l in ((760, 150, 25), (860, 115, -20)):
            t, fr = palm(x, 700, h, l)
            ground += [t, fr]
    elif n == 5:
        sky = [wave(300, 1200, 250, 6, 150), wave(600, 1550, 310, 6, 170), wave(200, 1000, 370, 6, 130),
               wave(800, 1700, 430, 6, 160), wave(350, 1100, 485, 6, 140)]
        ground = [lamp(1050, 700), lamp(1250, 700), lamp(1450, 700)]
    elif n == 6:
        sky = [wave(250, 1450, 250, 40, 300), wave(300, 1400, 315, 34, 260), wave(350, 1350, 380, 28, 220)]
        ground = [conifer(x, 700, h) for x, h in ((560, 100), (640, 125), (720, 95), (800, 115))]
    elif n == 7:
        sky = [semi(1100, 700, 110), 'M930 600 H1290 M900 635 H1330 M890 668 H1340']
        ground = [skyline(1300, 1720, 700, rnd)]
    elif n == 8:
        sky = ['M940 285 L820 330' + ' M826 330 a6 6 0 1 0 -0.1 0', 'M1300 215 L1180 260 M1186 260 a6 6 0 1 0 -0.1 0']
        ground = [mesa()]
    elif n == 9:
        sky = [cross(1000, 250, 18), cross(1000, 430, 18), cross(930, 340, 15), cross(1068, 322, 13), cross(1042, 388, 8)]
        ground = [ridge(930, 1740, 700, rnd, 120), ridge(1000, 1700, 700, rnd, 60)]
    elif n == 10:
        sky = [semi(1000, 700, 130)]
        for i in range(9):
            a = math.radians(195 + i * 18.75)
            sky.append(f'M{f(1000 + 155 * math.cos(a))} {f(700 + 155 * math.sin(a))} L{f(1000 + 195 * math.cos(a))} {f(700 + 195 * math.sin(a))}')
        sky += [cloud(500, 520, (28, 36, 24)), cloud(1290, 460, (24, 32, 40, 22))]
    return sky, ground


FLIGHTS = {
    1: ('takeoff', 1, 'L', 'TAKEOFF', 'DEPARTURE'),
    2: ('takeoff', 1, 'L', 'TAKEOFF', 'ASIA'),
    3: ('landing', 2, 'R', 'LANDING', 'MIDDLE EAST'),
    4: ('takeoff', 2, 'L', 'TAKEOFF', 'AFRICA'),
    5: ('landing', 3, 'R', 'LANDING', 'EUROPE'),
    6: ('takeoff', 3, 'L', 'TAKEOFF', 'EUROPE'),
    7: ('landing', 4, 'R', 'LANDING', 'NORTH AMERICA'),
    8: ('takeoff', 4, 'L', 'TAKEOFF', 'NORTH AMERICA'),
    9: ('landing', 5, 'R', 'LANDING', 'SOUTH AMERICA'),
    10: ('landing', 5, 'R', 'WELCOME HOME', 'FLIGHT COMPLETE'),
}

LAND = dict(path='M-200 500 C300 610 800 740 1180 781 L1500 781', spl='0.25 0.5 0.45 1',
            rot='5;5;-4;-4;0;0', kt='0;0.35;0.62;0.72;0.82;1')
TAKE = dict(path='M340 781 L1150 781 C1500 781 1600 650 2250 260', spl='0.55 0 0.85 0.55',
            rot='0;0;-15;-15', kt='0;0.5;0.66;1')
PLANE_PATHS = ['M100 2 C94 -9 72 -15 48 -15 H-62 L-90 -52 H-104 L-98 -6 L-102 6 H48 C74 6 94 6 100 2 Z',
               'M20 4 L-34 30 H-48 L-14 4',
               'M-2 22 H22 Q30 27 22 32 H-2 Q-8 27 -2 22 Z',
               'M-82 -2 L-110 10 H-118 L-100 -2',
               'M62 -12 L80 -5 H60 Z']
WHEELS = 'M30 6 V26 M-30 6 V26 M72 6 V27 ' + ' '.join(circle(cx, cy, r) for cx, cy, r in ((30, 32, 6), (-30, 32, 6), (72, 32, 5)))


def flight_svg(n):
    kind, ch, side, top, bot = FLIGHTS[n]
    main, acc = CH_COLOR[ch]
    cx = 140 if side == 'L' else 1780
    mv = LAND if kind == 'landing' else TAKE
    sky, ground = decor(n)
    css = (f'.m{{stroke:{main}}}.p{{stroke:{acc}}}'
           '.d{fill:none;stroke-width:3;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;'
           'opacity:0;animation:draw 1.4s cubic-bezier(.12,.7,.3,1) both}'
           '@keyframes draw{0%{stroke-dashoffset:1;opacity:0}1%{opacity:1}100%{stroke-dashoffset:0;opacity:1}}'
           '.all{animation:out .8s linear 6.2s both}@keyframes out{from{opacity:1}to{opacity:0}}'
           '.t{fill:none;stroke-width:1.6;text-anchor:middle;opacity:0;animation:fade .7s ease-out 2.4s both}'
           '@keyframes fade{from{opacity:0}to{opacity:1}}'
           '.fi{fill:none;stroke-width:7;stroke-linecap:round;opacity:0;animation:fade .3s ease-out both}')
    k = 0
    defs, els = [], []

    def delay():
        nonlocal k
        v = f'{k * .2:.2f}s'
        k += 1
        return v

    def solid(d, cls, w=None):
        ws = f' stroke-width="{w}"' if w else ''
        els.append(f'<path class="d {cls}" pathLength="1"{ws} style="animation-delay:{delay()}" d="{d}"/>')

    def dashed(d, cls, attrs, mid):
        dl = delay()
        defs.append(f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="-300" y="0" width="2800" height="1080">'
                    f'<path class="d" pathLength="1" style="animation-delay:{dl};stroke:#fff;stroke-width:40" d="{d}"/></mask>')
        els.append(f'<path class="{cls}" fill="none" stroke-linecap="round" mask="url(#{mid})" {attrs} d="{d}"/>')

    solid('M0 830 H1920', 'p')
    if n == 10:
        # runway lights stay dark until the plane has stopped, then light up in the 5 chapter colours in order
        for i in range(5):
            c = CH_COLOR[i + 1][0]
            x0, x1 = i * 384, (i + 1) * 384
            els.append(f'<path class="fi" stroke="{c}" stroke-dasharray="0.1 42" d="M{x0 + 10} 848 H{x1}" style="animation-delay:{4.8 + i * .3:.1f}s"/>')
    else:
        dashed('M0 848 H1920', 'm', 'stroke-width="7" stroke-dasharray="0.1 42"', 'mk1')
    dashed('M0 888 H1920', 'p', 'stroke-width="3" stroke-dasharray="46 34"', 'mk2')
    solid(f'M{cx - 10} 830 V560 M{cx + 10} 830 V560', 'm')
    solid(f'M{cx - 36} 560 H{cx + 36} L{cx + 24} 512 H{cx - 24} Z', 'm')
    solid(f'M{cx - 30} 536 H{cx + 30}', 'm')
    solid(f'M{cx} 512 V450', 'm')
    dashed(mv['path'], 'p', 'stroke-width="2" stroke-dasharray="3 16"', 'mk3')
    for d in sky:
        solid(d, 'p', 2.6)
    for d in ground:
        solid(d, 'm', 2.6)
    plane = ''.join(f'<path d="{d}" stroke="{main}"/>' for d in PLANE_PATHS)
    wheel_anim = ('<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.72;0.8;1" dur="5.2s" begin="0.8s" fill="freeze"/>'
                  if kind == 'takeoff' else '')
    plane_g = (
        '<g opacity="0"><set attributeName="opacity" to="1" begin="0.8s" fill="freeze"/>'
        f'<animateMotion dur="5.2s" begin="0.8s" fill="freeze" calcMode="spline" keyPoints="0;1" keyTimes="0;1" keySplines="{mv["spl"]}" path="{mv["path"]}"/>'
        f'<g><animateTransform attributeName="transform" type="rotate" values="{mv["rot"]}" keyTimes="{mv["kt"]}" dur="5.2s" begin="0.8s" fill="freeze"/>'
        f'<g transform="scale(1.3)" fill="none" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">{plane}'
        f'<g stroke="{acc}">{wheel_anim}<path d="{WHEELS}"/></g></g></g></g>')
    body = ('<g filter="url(#glow)" class="all">\n' + '\n'.join(els) + '\n' + plane_g +
            f'\n<text class="t m" x="960" y="120" font-size="64" letter-spacing="10" {FONT}>{top}</text>\n'
            f'<text class="t p" x="960" y="990" font-size="26" letter-spacing="8" {FONT}>{bot}</text>\n</g>')
    return svg_wrap(f'F{n:02d} {kind}', body, css, ''.join(defs))


# ------------------------------------------------------------- title / credits
def title_svg():
    cols = [CH_COLOR[i][0] for i in range(1, 6)]
    css = ('.d{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;opacity:0;'
           'animation:draw 1.8s cubic-bezier(.12,.7,.3,1) both}'
           '@keyframes draw{0%{stroke-dashoffset:1;opacity:0}1%{opacity:1}100%{stroke-dashoffset:0;opacity:1}}'
           '.all{animation:out 1s linear 7s both}@keyframes out{from{opacity:1}to{opacity:0}}'
           '.t{fill:none;stroke-width:2;text-anchor:middle;opacity:0;animation:fade 1s ease-out both}'
           '@keyframes fade{from{opacity:0}to{opacity:1}}')
    bars = ''.join(f'<path class="d" pathLength="1" stroke="{c}" stroke-width="6" style="animation-delay:{3.2 + i * .25:.2f}s;animation-duration:.8s" '
                   f'd="M{660 + i * 120} 790 H{740 + i * 120}"/>' for i, c in enumerate(cols))
    body = ('<g filter="url(#glow)" class="all">'
            f'<g transform="translate(960 300) scale(3.2)"><path class="d" pathLength="1" stroke="{cols[0]}" stroke-width="2.4" d="{PLANE_GLYPH}"/></g>'
            f'<path class="d" pathLength="1" stroke="{cols[4]}" stroke-width="3" style="animation-delay:.5s" d="{circle(960, 300, 150)}"/>'
            f'<text class="t" stroke="{cols[0]}" x="960" y="620" font-size="124" letter-spacing="22" {FONT} style="animation-delay:1.6s">WORLD AIRPORTS</text>'
            f'<text class="t" stroke="{cols[4]}" x="960" y="710" font-size="36" letter-spacing="20" {FONT} style="animation-delay:2.4s">LASER LINE ART</text>'
            f'{bars}</g>')
    return svg_wrap('World Airports title', body, css)


def credits_svg():
    cols = [CH_COLOR[i][0] for i in range(1, 6)]
    css = ('.all{animation:out 1s linear 11s both}@keyframes out{from{opacity:1}to{opacity:0}}'
           '.t{text-anchor:middle;opacity:0;animation:fade 1s ease-out both}@keyframes fade{from{opacity:0}to{opacity:1}}')
    lines = [('CREDITS', 90, 300, cols[0], 'none', 22, 0.2),
             ('WORLD AIRPORTS — LASER LINE ART', 40, 430, cols[4], 'none', 8, 1.0),
             ('Line art and animation: SVG, created with Claude (Anthropic)', 30, 560, cols[1], cols[1], 2, 2.2),
             ('Music: created with Suno, used under a commercial-use license', 30, 630, cols[3], cols[3], 2, 3.4),
             ('Thank you for flying with us', 36, 780, cols[2], 'none', 6, 5.0)]
    t = ''
    for txt, size, y, c, fill, ls, d in lines:
        if fill == 'none':
            t += f'<text class="t" fill="none" stroke="{c}" stroke-width="1.8" x="960" y="{y}" font-size="{size}" letter-spacing="{ls}" {FONT} style="animation-delay:{d}s">{txt}</text>'
        else:
            t += f'<text class="t" fill="{fill}" x="960" y="{y}" font-size="{size}" letter-spacing="{ls}" {FONT} style="animation-delay:{d}s">{txt}</text>'
    return svg_wrap('World Airports credits', f'<g filter="url(#glow)" class="all">{t}</g>', css)


def write(name, s):
    path = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(s)


def order():
    """final play order: list of (svg filename, seconds)"""
    seq = [('title.svg', 8)]
    n = 0
    chap_flights = {1: (1, 2), 2: (3, 4), 3: (5, 6), 4: (7, 8), 5: (9, 10)}
    for ch in range(1, 6):
        a, b = chap_flights[ch]
        seq.append((f'flight_{a:02d}_{FLIGHTS[a][0]}.svg', 7))
        for ap in [x for x in A if x['ch'] == ch]:
            n += 1
            seq.append((f'ch{ch}_{n:02d}_{ap["code"]}.svg', 7))
        seq.append((f'flight_{b:02d}_{FLIGHTS[b][0]}.svg', 7))
    seq.append(('credits.svg', 12))
    return seq


def main():
    n = 0
    for a in A:
        n += 1
        write(f'ch{a["ch"]}_{n:02d}_{a["code"]}.svg', airport_svg(a, n))
    for i in FLIGHTS:
        write(f'flight_{i:02d}_{FLIGHTS[i][0]}.svg', flight_svg(i))
    write('title.svg', title_svg())
    write('credits.svg', credits_svg())
    seq = order()
    print(len(seq), 'clips,', sum(s for _, s in seq), 'seconds')


if __name__ == '__main__':
    main()
