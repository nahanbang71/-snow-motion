#!/usr/bin/env python3
"""Laser-style sample: swallowtail on a cosmos, drifting petals, cloud backdrop.
usage: python3 tools/gen_butterfly_meadow.py   -> flowers/butterfly_meadow.svg
Single-stroke neon line art (no fills), same draw-on animation as gen_flowers.py.
"""
import math
import os

W, H = 960, 540
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flowers', 'butterfly_meadow.svg')
els = []


def path(d, cls, s, t, extra='', col=None):
    c = f';stroke:{col}' if col else ''
    els.append(f'<path class="d {cls}" pathLength="1" style="--s:{s:.2f}s;--t:{t:.2f}s{c}" d="{d}" {extra}/>')


# ---------- backdrop: clouds ----------
def cloud(x, y, s, d):
    path(f'M{x} {y} a{18*s} {18*s} 0 0 1 {30*s} {-6*s} a{26*s} {26*s} 0 0 1 {50*s} {-12*s} '
         f'a{22*s} {22*s} 0 0 1 {44*s} {8*s} a{15*s} {15*s} 0 0 1 {8*s} {10*s} H{x}', 'cloud', d, 1.4)


cloud(60, 90, 1.0, 0.6)
cloud(380, 60, 1.2, 0.9)
cloud(700, 85, 0.9, 1.2)


# ---------- cosmos (centre 480,400) ----------
CX, CY, R = 480, 400, 0.85
path(f'M{CX} {CY+88} C{CX-8} {CY+120} {CX-40} {CY+135} {CX-44} {H}', 'stem', 3.4, 1.2)
path(f'M{CX-20} {CY+128} C{CX-70} {CY+100} {CX-100} {CY+120} {CX-120} {CY+150} C{CX-70} {CY+160} {CX-40} {CY+150} {CX-20} {CY+128}', 'stem', 4.2, 1.0)


def rot(px, py, a):
    c, s = math.cos(a), math.sin(a)
    return px * c - py * s, px * s + py * c


def poly(cmds, a, cx, cy, sc):
    """cmds: list of (letter, [x,y,...]) with absolute coords, rotated by a around origin then placed."""
    out = []
    for let, v in cmds:
        pts = []
        for i in range(0, len(v), 2):
            x, y = rot(v[i], v[i + 1], a)
            pts += [f'{cx + x*sc:.1f}', f'{cy + y*sc:.1f}']
        out.append(let + ' '.join(pts))
    return ' '.join(out)


petal = [('M', [0, -12]), ('C', [-30, -30, -38, -80, -30, -98]), ('L', [-18, -90]), ('L', [-9, -100]), ('L', [0, -91]),
         ('L', [9, -100]), ('L', [18, -90]), ('L', [30, -98]), ('C', [38, -80, 30, -30, 0, -12]), ('Z', [])]
vein = [('M', [0, -16]), ('L', [0, -82])]
for i in range(8):
    a = i * math.pi / 4 + 0.2
    path(poly(petal, a, CX, CY, R), 'pet', 3.2 + i * 0.08, 0.9)
    path(poly(vein, a, CX, CY, R), 'pet2', 3.6 + i * 0.08, 0.5)
for rr, n, c in [(13, 1, 'ctr'), (9, 10, 'ctr')]:
    if n == 1:
        els.append(f'<circle class="d ctr" pathLength="1" style="--s:4.2s;--t:.8s" cx="{CX}" cy="{CY}" r="{rr}"/>')
    else:
        for k in range(n):
            a = k * 2 * math.pi / n
            els.append(f'<circle class="fi ctrd" style="--s:{4.4+k*.04:.2f}s" cx="{CX+rr*1.9*math.cos(a):.1f}" cy="{CY+rr*1.9*math.sin(a):.1f}" r="2.2"/>')


# ---------- meadow flowers: small & large, several kinds ----------
daisy_petal = [('M', [0, -9]), ('C', [-10, -22, -10, -46, 0, -54]), ('C', [10, -46, 10, -22, 0, -9]), ('Z', [])]


def circ(x, y, r):
    return f'M{x-r:.1f} {y:.1f} a{r} {r} 0 1 0 {2*r} 0 a{r} {r} 0 1 0 {-2*r} 0'


def stem(x, y, dx, d, w=2):
    path(f'M{x} {y} C{x} {y+(H-y)*.4} {x+dx} {y+(H-y)*.7} {x+dx} {H+4}', 'stem', d, 1.0, col=None)


def cosmos_f(x, y, sc, col, d, n=8):
    stem(x, y + 90 * sc, -25 * sc, d)
    for i in range(n):
        a = i * 2 * math.pi / n + 0.3
        path(poly(petal, a, x, y, sc), 'pet', d + .1 + i * .05, .7, col=col)
    path(circ(x, y, 12 * sc), 'ctr', d + .6, .5)


def daisy_f(x, y, sc, col, d, n=12):
    stem(x, y + 55 * sc, 18 * sc, d)
    for i in range(n):
        path(poly(daisy_petal, i * 2 * math.pi / n, x, y, sc), 'pet2', d + .1 + i * .03, .5, col=col)
    path(circ(x, y, 8 * sc), 'ctr', d + .5, .4)


def lupine_f(x, y, h, col, d):
    stem(x, y + h, 6, d)
    rows = int(h / 16)
    for k in range(rows):
        yy = y + k * 16
        wd = 4 + 9 * (1 - abs(k / rows - .35) * 1.2)
        for sx in (-1, 1):
            path(f'M{x} {yy} C{x+sx*wd} {yy-6} {x+sx*(wd+4)} {yy+8} {x+sx*2} {yy+14}', 'pet2', d + .1 + k * .06, .4, col=col)


def bud_f(x, y, sc, col, d):
    stem(x, y + 40 * sc, -10 * sc, d)
    path(f'M{x} {y-30*sc} C{x-22*sc} {y-10*sc} {x-18*sc} {y+30*sc} {x} {y+38*sc} C{x+18*sc} {y+30*sc} {x+22*sc} {y-10*sc} {x} {y-30*sc}', 'pet', d + .1, .8, col=col)
    path(f'M{x-14*sc} {y+22*sc} L{x} {y+4*sc} L{x+14*sc} {y+22*sc}', 'pet2', d + .5, .4, col=col)


def tiny_f(x, y, sc, col, d):
    stem(x, y + 14 * sc, 4, d)
    for i in range(5):
        a = i * 2 * math.pi / 5
        path(circ(x + 9 * sc * math.cos(a), y + 9 * sc * math.sin(a), 5 * sc), 'pet2', d + .1 + i * .05, .3, col=col)
    path(circ(x, y, 3 * sc), 'ctr', d + .4, .3)


MEADOW = [
    (lupine_f, (110, 330, 130, '#a78bff', 2.4)), (lupine_f, (300, 360, 110, '#8f9bff', 2.6)),
    (lupine_f, (690, 350, 120, '#a78bff', 2.5)), (lupine_f, (880, 340, 140, '#8f9bff', 2.7)),
    (cosmos_f, (205, 390, 0.62, '#ff9fd0', None, 2.8)), (cosmos_f, (40, 420, 0.5, '#ff6fb5', None, 3.0)),
    (cosmos_f, (770, 400, 0.7, '#ff8ac4', None, 2.9)), (cosmos_f, (610, 460, 0.38, '#ffb3da', None, 3.1)),
    (daisy_f, (350, 450, 0.7, '#ffffff', 3.0)), (daisy_f, (150, 470, 0.55, '#ffffff', 3.2)),
    (daisy_f, (850, 450, 0.75, '#ffffff', 3.1)), (daisy_f, (690, 490, 0.45, '#fff4a0', 3.3)),
    (bud_f, (560, 470, 0.7, '#ff6fb5', 3.4)), (bud_f, (920, 400, 0.6, '#ffb3da', 3.5)),
    (tiny_f, (260, 500, 1.0, '#7ad8ff', 3.4)), (tiny_f, (90, 380, 0.9, '#ffe45a', 3.5)),
    (tiny_f, (740, 480, 1.1, '#7ad8ff', 3.6)), (tiny_f, (420, 500, 0.8, '#ffe45a', 3.6)),
    (tiny_f, (940, 480, 1.0, '#ffffff', 3.7)),
]
for fn, args in MEADOW:
    fn(*[a for a in args if a is not None])

# ---------- swallowtail (local coords, body axis x=0, wings flap by scaleX) ----------
WING = [
    ('fore', 'M4 -8 C30 -50 70 -78 96 -62 C104 -40 92 -10 60 8 C40 16 20 12 4 6 Z', 'wing'),
    ('hind', 'M4 6 C34 12 66 20 76 40 C82 58 66 68 54 62 L58 90 L44 66 C28 62 10 40 4 28', 'wing'),
    ('s1', 'M10 -6 C34 -34 62 -54 86 -56', 'stripe'),
    ('s2', 'M12 -2 C40 -24 70 -34 96 -40', 'stripe'),
    ('s3', 'M14 2 C44 -10 72 -14 98 -14', 'stripe'),
    ('s4', 'M22 8 C46 4 66 4 74 4', 'stripe'),
    ('band', 'M12 22 C34 28 56 34 70 46', 'band'),
    ('eye', 'M70 50 a7 7 0 1 0 0.1 0', 'eye'),
    ('eye2', 'M70 50 a2.6 2.6 0 1 0 0.1 0', 'eye'),
]
TIMES = {'wing': (5.0, 1.0), 'stripe': (5.8, 0.6), 'band': (6.2, 0.5), 'eye': (6.4, 0.4)}


def wing_markup():
    return ''.join(
        f'<path class="d {c}" pathLength="1" style="--s:{TIMES[c][0] + i*0.05:.2f}s;--t:{TIMES[c][1]}s" d="{d}"/>'
        for i, (_, d, c) in enumerate(WING))


flap = ('<animateTransform attributeName="transform" type="scale" values="1 1;0.22 1;1 1" keyTimes="0;.5;1" '
        'dur="1.6s" begin="7.2s" repeatCount="indefinite" calcMode="spline" keySplines=".4 0 .6 1;.4 0 .6 1"/>')
bf = (f'<g transform="translate(480 258)"><animateTransform attributeName="transform" type="translate" '
      f'values="480 258;480 250;480 258" dur="3.2s" begin="7.2s" repeatCount="indefinite"/>'
      f'<g>{flap}{wing_markup()}</g><g transform="scale(-1 1)"><g>{flap}{wing_markup()}</g></g>'
      '<path class="d body" pathLength="1" style="--s:4.8s;--t:.8s" d="M0 -24 C-5 -20 -5 -10 0 -6 C5 -10 5 -20 0 -24 Z M0 -6 C-4 10 -4 36 0 54 C4 36 4 10 0 -6"/>'
      '<path class="d ant" pathLength="1" style="--s:5.6s;--t:.6s" d="M-2 -24 C-8 -44 -20 -56 -34 -62 M2 -24 C8 -44 20 -56 34 -62"/>'
      '<circle class="fi antd" style="--s:6.1s" cx="-34" cy="-62" r="2.6"/><circle class="fi antd" style="--s:6.1s" cx="34" cy="-62" r="2.6"/>'
      '</g>')
els.append(bf)

# ---------- drifting petals ----------
for i, (d, begin) in enumerate([('M560 330 C620 290 700 350 760 320 S860 400 900 480', 8.0),
                                ('M520 300 C560 250 640 270 700 240 S800 260 880 330', 10.2),
                                ('M600 360 C660 360 700 420 780 410 S880 450 920 520', 12.0)]):
    els.append(
        f'<g class="pt" opacity="0"><path class="petal" d="M0 0 C6 -7 15 -5 18 2 C13 9 4 9 0 0 Z"/>'
        f'<animateMotion dur="7s" begin="{begin}s" repeatCount="indefinite" rotate="auto" path="{d}"/>'
        f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.85;1" dur="7s" begin="{begin}s" repeatCount="indefinite"/></g>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>Butterfly &amp; Cosmos - laser line art sample</title>
<defs>
<radialGradient id="bg" cx="50%" cy="45%" r="70%"><stop offset="0" stop-color="#14183a"/><stop offset="1" stop-color="#080a1a"/></radialGradient>
<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.d{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;animation:draw var(--t,1s) ease-out var(--s,0s) forwards}}
.fi{{opacity:0;animation:fade .5s ease-out var(--s,0s) forwards}}
.mtn{{stroke:#7aa8ff;stroke-width:2.2}} .cloud{{stroke:#e8f0ff;stroke-width:1.8}} .tree{{stroke:#3df2c0;stroke-width:1.8}}
.lake{{stroke:#5ad7ff;stroke-width:1.6}} .stem{{stroke:#3df2c0;stroke-width:3}}
.pet{{stroke:#ff6fb5;stroke-width:2.4}} .pet2{{stroke:#ffb3da;stroke-width:1.4}}
.ctr{{stroke:#ffd23f;stroke-width:2.4}} .ctrd{{fill:#ffd23f}}
.wing{{stroke:#ffe45a;stroke-width:2.4}} .stripe{{stroke:#ffffff;stroke-width:1.8}} .band{{stroke:#4d7cff;stroke-width:2.6}}
.eye{{stroke:#ff8a2e;stroke-width:2}} .body{{stroke:#ffffff;stroke-width:2.2}} .ant{{stroke:#ffffff;stroke-width:1.5}} .antd{{fill:#ffffff}}
.petal{{fill:none;stroke:#ff9fd0;stroke-width:1.8;stroke-linejoin:round}}
@keyframes draw{{to{{stroke-dashoffset:0}}}} @keyframes fade{{to{{opacity:1}}}}
</style>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<g filter="url(#glow)">
{chr(10).join(els)}
</g>
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print('wrote', os.path.normpath(OUT), len(svg) // 1024, 'KB')
