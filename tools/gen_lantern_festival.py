#!/usr/bin/env python3
"""Lantern festival (연등축제) - 216 s looping neon line-art film, laser style (outlines + glow, no text, no people).
   0- 54  A  temple hall + pagoda drawn in light; the lantern hillside lights up row by row (colour bands in perspective)
  50- 98  C  Cheonggyecheon-style stream: stone embankments, bridges hung with lanterns, lantern sculptures on plinths
            standing in the water (lotus, crane, pagoda, elephant, fish, dharma wheel) with rippling reflections
  94-130  D  a stairway under rows of hanging lotus lanterns, the camera climbs slowly
 126-158  E  a ceiling of hanging lanterns of many shapes
 154-214  B  the sky: lanterns rise over the tower, blue laser beams sweep; a lotus lantern blooms in the middle
usage: python3 tools/gen_lantern_festival.py [seed] [--out=PATH]   -> flowers/lantern_festival.svg
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lantern_shapes as LS  # noqa: E402

W, H, T = 960, 540, 216.0
SEED = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8
OUT = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--out=')), None) or \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flowers', 'lantern_festival.svg')
R = random.Random(SEED)
KFS = []


def kfs(points):
    pts = [(min(t, T), p) for t, p in points if t <= T + 1e-9]
    if pts[-1][0] < T:
        pts.append((T, pts[-1][1]))
    out, last = [], -1
    for t, p in pts:
        t = max(t, last + 0.002)
        out.append((t, p))
        last = t
    KFS.append('@keyframes q%d{%s}' % (len(KFS), ''.join(f'{t/T*100:.4f}%{{{p}}}' for t, p in out)))
    return f'q{len(KFS)-1}'


def op(*pts):
    return kfs([(t, f'opacity:{v}') for t, v in pts])


def draw(a, t, b):
    return kfs([(0, 'stroke-dashoffset:1'), (a, 'stroke-dashoffset:1'), (a + t, 'stroke-dashoffset:0'), (b + 2, 'stroke-dashoffset:0'), (b + 6, 'stroke-dashoffset:1')])


def scene_fade(a, b, fi=6, fo=6):
    return op((0, 0), (a, 0), (a + fi, 1), (b, 1), (b + fo, 0))


BAND = ['#ff3b4e', '#ff8a2b', '#ff5fa8', '#3f86ff', '#35d07f', '#ffd23f']
BAND8 = ['#ff3b4e', '#ff8a2b', '#ffd23f', '#35d07f', '#3f86ff', '#ff5fa8', '#ff8a2b', '#ffd23f']
HALOS = {}


def halo_id(col):
    if col not in HALOS:
        HALOS[col] = f'hl{len(HALOS)}'
    return HALOS[col]


def halo(col, r, cx=0, cy=0, o=1.0):
    return f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="url(#{halo_id(col)})" style="stroke:none;opacity:{o}"/>'


def tw(col, r, x, y):
    return f'<circle class="tw" style="fill:{col};--td:{R.uniform(1.2, 3):.1f}s;--tl:-{R.uniform(0, 3):.1f}s" cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}"/>'


def circ(x, y, r):
    return f'M{x-r:.1f} {y:.1f} a{r:.1f} {r:.1f} 0 1 0 {2*r:.1f} 0 a{r:.1f} {r:.1f} 0 1 0 {-2*r:.1f} 0'


def sway_wrap(inner, x, y, amp, dur, tag='sw'):
    return (f'<g class="{tag}" style="--sa:{amp:.1f}deg;--sd:{dur:.1f}s;--sl:-{R.uniform(0, dur):.1f}s;transform-origin:{x:.0f}px {y:.0f}px">{inner}</g>')


# =============================================================================================
# Scene A: the temple and the lantern hillside (0-54)
# =============================================================================================
A = []
CAM_A = kfs([(0, 'transform:scale(1) translate(0px,0px)'), (52, 'transform:scale(1.09) translate(0px,18px)'), (T, 'transform:scale(1.09) translate(0px,18px)')])
hills = ['M0 150 C100 122 200 142 300 124 S500 104 600 120 S800 112 960 138']
temple = [
    ('M300 168 C330 150 400 138 480 138 S630 150 660 168', 'roof'), ('M300 168 Q278 171 266 156', 'roof'), ('M660 168 Q682 171 694 156', 'roof'),
    ('M268 190 C330 175 410 168 480 168 S630 175 692 190', 'roof'), ('M268 190 Q246 194 236 180', 'roof'), ('M692 190 Q714 194 724 180', 'roof'),
    ('M470 138 L470 126 M490 138 L490 126 M470 126 Q480 116 490 126', 'roof'),
    ('M258 206 L702 206', 'wall'), ('M290 190 L290 206 M350 183 L350 206 M410 177 L410 206 M480 175 L480 206 M550 177 L550 206 M610 183 L610 206 M670 190 L670 206', 'wall'),
    ('M455 206 L455 190 Q480 178 505 190 L505 206', 'wall'),
    ('M118 192 C150 178 200 174 238 184', 'roof'), ('M118 192 Q100 194 92 184', 'roof'), ('M92 206 L238 206', 'wall'),
    ('M722 184 C760 174 810 178 842 192', 'roof'), ('M842 192 Q860 194 868 184', 'roof'), ('M722 206 L868 206', 'wall'),
]
pag = []
for k in range(5):
    y, hw = 188 - k * 17, 27 - k * 4.5
    pag.append((f'M{58-hw:.0f} {y} Q58 {y-9} {58+hw:.0f} {y} M{58-hw*.7:.0f} {y} L{58-hw*.7:.0f} {y+8} L{58+hw*.7:.0f} {y+8} L{58+hw*.7:.0f} {y}', 'roof'))
pag.append(('M58 103 L58 80 M52 94 L64 94 M54 88 L62 88', 'roof'))
for d in hills:
    A.append(f'<path class="d0 k hill" pathLength="1" style="animation-name:{draw(.5, 5, 50)}" d="{d}"/>')
for i, (d, c) in enumerate(temple + pag):
    A.append(f'<path class="d0 k {c}" pathLength="1" style="animation-name:{draw(1.5 + i * .25, 2.2, 50)}" d="{d}"/>')
for i in range(26):
    A.append(f'<circle class="k win" style="opacity:0;animation-name:{op((0,0),(6+i*.12,0),(7+i*.12,1),(50,1),(54,0))}" cx="{275 + i*17.5:.0f}" cy="199" r="1.6"/>')
# trees flanking the temple (hand-drawn pines and broad-leaf trees)
for x, h, kind in [(160, 46, 'pine'), (205, 34, 'round'), (255, 52, 'pine'), (715, 52, 'pine'), (760, 36, 'round'), (810, 48, 'pine'), (880, 40, 'round'), (30, 38, 'pine')]:
    A.append(f'<g class="k" style="opacity:0;--tf:#170b22;--ts:#9a7cc0;animation-name:{op((0,0),(8,0),(11,.9),(50,.9),(54,0))}"><g transform="translate({x} 212)">'
             f'{LS.pine(h, R) if kind == "pine" else LS.round_tree(h, R)}</g></g>')
D_, C_ = 30, 48
ys = [214 + 232 * (d / (D_ - 1)) ** 1.25 for d in range(D_)]
for d in range(D_):
    t = d / (D_ - 1)
    y = ys[d]
    gap = (ys[d + 1] - ys[d]) if d < D_ - 1 else (ys[d] - ys[d - 1])
    half = 105 + 560 * t
    sp = 2 * half / C_
    rx, ry = max(1.1, sp * .52), max(.9, gap * .5)
    els = ''.join(f'<ellipse class="L b{c // 6}" cx="{480 + (-1 + 2 * (c + .5) / C_) * half:.1f}" cy="{y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}"/>' for c in range(C_))
    t_on = 9 + (D_ - 1 - d) * .62
    pts = [(0, 0), (t_on, 0), (t_on + 1.6, .82)]
    for w in range(26, 48, 4):
        tw_ = w + (D_ - 1 - d) * .15
        pts += [(tw_, .82), (tw_ + .6, 1), (tw_ + 1.5, .82)]
    pts += [(50, .82), (55, 0)]
    A.append(f'<g class="k" style="opacity:0;animation-name:{kfs([(t_, f"opacity:{v}") for t_, v in pts])}">{els}</g>')
for xa, xb in ((440, 150), (520, 810), (480, 480)):
    A.append(f'<path class="d0 k stair" pathLength="1" style="animation-name:{draw(14, 5, 50)}" d="M{xa} 214 L{xb} 446"/>')
for side in (-1, 1):
    for i in range(36):
        t = i / 35
        A.append(tw(BAND8[i % 8], 1.4 + 2 * t, 480 + side * (105 + 560 * t) * 1.02, 214 + 232 * t ** 1.25))
fg_str = 'M-20 452 C160 478 320 440 480 462 S800 440 980 466'
A.append(f'<path class="d0 k stair" pathLength="1" style="animation-name:{draw(18, 4, 50)}" d="{fg_str}"/>')
FG = [(70, 470, '#ff5fa8'), (190, 466, '#ff3b4e'), (300, 458, '#ffd23f'), (410, 462, '#ff8a2b'), (520, 466, '#ff5fa8'), (630, 458, '#ff3b4e'),
      (745, 458, '#ffd23f'), (860, 462, '#ff8a2b'), (935, 470, '#ff5fa8')]
for i, (x, y, col) in enumerate(FG):
    rr = 19 * R.uniform(.9, 1.2)
    body = (f'<path class="cord" d="M0 0 L0 8"/><rect class="cap" x="-7" y="8" width="14" height="5" rx="1.5"/>'
            f'<ellipse class="fgL" style="color:{col}" cx="0" cy="{13+rr:.1f}" rx="{rr:.1f}" ry="{rr*1.05:.1f}"/>'
            f'<path class="rib" style="color:{col}" d="M0 13 Q{rr*.55:.1f} {13+rr:.1f} 0 {13+rr*2.1:.1f} M0 13 Q{-rr*.55:.1f} {13+rr:.1f} 0 {13+rr*2.1:.1f}"/>'
            f'<path class="cord" d="M-4 {13+rr*2.1:.1f} l0 14 M0 {13+rr*2.1:.1f} l0 18 M4 {13+rr*2.1:.1f} l0 14"/>' + halo(col, rr * 1.7, 0, 13 + rr, .55))
    A.append(f'<g class="k" style="opacity:0;animation-name:{op((0, 0), (16 + i * .35, 0), (18 + i * .35, 1), (50, 1), (55, 0))}">'
             f'{sway_wrap(f"<g transform=\"translate({x} {y})\">{body}</g>", x, y, R.uniform(2, 4.5) * (-1) ** i, R.uniform(2.6, 4.2))}</g>')
for i in range(26):
    A.append(f'<circle class="ember" cx="{R.uniform(100, 860):.0f}" cy="{R.uniform(250, 470):.0f}" r="{R.uniform(1, 2.2):.1f}" '
             f'style="--md:{R.uniform(7, 14):.1f}s;--mdl:-{R.uniform(0, 14):.1f}s;--dx:{R.uniform(-30, 40):.0f}px;--dy:-{R.uniform(80, 200):.0f}px"/>')

# =============================================================================================
# Scene C: the stream (50-98)
# =============================================================================================
C = []
VPX, VPY = 480, 238
CAM_C = kfs([(0, 'transform:scale(1)'), (50, 'transform:scale(1)'), (98, 'transform:scale(1.12)'), (T, 'transform:scale(1.12)')])


def Lz(z): return 462 - 502 * z
def Rz(z): return 498 + 502 * z
def Ty(z): return 232 - 192 * z
def By(z): return 246 + 224 * z


C.append('<path d="M-40 470 L462 246 L498 246 L1000 470 L1000 560 L-40 560 Z" fill="url(#waterG)" style="stroke:none"/>')
C.append('<path d="M-40 40 L462 232 L462 246 L-40 470 Z M1000 40 L498 232 L498 246 L1000 470 Z" fill="#0a1230" style="stroke:none;opacity:.85"/>')
# stone embankments: courses and staggered joints, mirrored on both sides
courses, joints = '', ''
for k in range(1, 7):
    y0, y1 = 232 + 14 * k / 7, 40 + 430 * k / 7
    courses += f'M462 {y0:.1f} L-40 {y1:.1f} '
for k in range(7):
    for j in range(9):
        z = .06 + .115 * j + (k % 2) * .057
        if z > 1:
            continue
        ta, ba = Ty(z), By(z)
        joints += f'M{Lz(z):.1f} {ta + (ba - ta) * k / 7:.1f} L{Lz(z):.1f} {ta + (ba - ta) * (k + 1) / 7:.1f} '
for sx in (1, -1):
    tr = '' if sx == 1 else 'transform="translate(960 0) scale(-1 1)"'
    C.append(f'<g {tr}><path class="wallc" d="M462 232 L-40 40 M462 246 L-40 470 {courses}"/><path class="wallj" d="{joints}"/></g>')
# railings, posts
for sx in (1, -1):
    tr = '' if sx == 1 else 'transform="translate(960 0) scale(-1 1)"'
    posts = ''.join(f'M{Lz(z):.1f} {Ty(z):.1f} L{Lz(z):.1f} {Ty(z) - 6 - 22 * z:.1f} ' for z in [i * .07 + .04 for i in range(14)])
    C.append(f'<g {tr}><path class="rail" d="M462 226 L-40 12 {posts}"/></g>')
# distant buildings above the walls, windows twinkling
for sx in (-1, 1):
    x = 470 if sx == 1 else 470
    cur = 0
    for i in range(7):
        bw, bh = R.uniform(14, 26), R.uniform(30, 118) * (1 - .06 * i)
        x0 = (500 + cur) if sx == 1 else (460 - cur - bw)
        cur += bw + R.uniform(2, 6)
        C.append(f'<path class="bld" d="M{x0:.0f} 232 L{x0:.0f} {232-bh:.0f} L{x0+bw:.0f} {232-bh:.0f} L{x0+bw:.0f} 232"/>')
        for wy in range(int(232 - bh + 6), 228, 9):
            for wx in range(int(x0 + 4), int(x0 + bw - 3), 7):
                if R.random() < .42:
                    C.append(f'<circle class="tw" style="fill:#ffe9a8;--td:{R.uniform(2, 6):.1f}s;--tl:-{R.uniform(0, 6):.1f}s" cx="{wx}" cy="{wy}" r="1"/>')
# trees along the street, lamp posts
for sx in (-1, 1):
    tr = '' if sx == 1 else 'transform="translate(960 0) scale(-1 1)"'
    s = ''
    for z, kind in [(.07, 'pine'), (.17, 'round'), (.3, 'pine'), (.45, 'round'), (.62, 'pine'), (.8, 'round')]:
        h = 26 + 120 * z
        s += f'<g transform="translate({Lz(z) - 6:.1f} {Ty(z) - 5:.1f})">{LS.pine(h, R) if kind == "pine" else LS.round_tree(h, R)}</g>'
    C.append(f'<g {tr} style="--tf:#0a1636;--ts:#5a7fd2">{s}</g>')
    for z in (.12, .38, .7):
        x, y = (Lz(z) + 14 * z, Ty(z) - 6 - 22 * z)
        px = x if sx == 1 else 960 - x
        C.append(f'<path class="rail" d="M{px:.0f} {y:.0f} L{px:.0f} {y - 40 * z - 10:.0f}"/>{halo("#ffd27a", 18 + 40 * z, px, y - 40 * z - 12, .9)}'
                 f'<circle cx="{px:.0f}" cy="{y - 40 * z - 12:.0f}" r="{2 + 3 * z:.1f}" fill="#fff4c8" style="stroke:none"/>')
# water flow lines, far waterfall
for i in range(-9, 10):
    xf, xn = 480 + i * 5, 480 + i * 115
    C.append(f'<path class="flow" style="--fd:{R.uniform(5, 9):.1f}s;--fl:-{R.uniform(0, 8):.1f}s" d="M{xf} 252 C{xf + i * 8} 330 {xn - i * 20} 450 {xn} 560"/>')
for i in range(5):
    C.append(f'<path class="fall" style="--fd:{R.uniform(1.2, 2.2):.1f}s;--fl:-{R.uniform(0, 2):.1f}s" d="M{472 + i * 4} 240 L{472 + i * 4} 252"/>')
# bridges with lantern strings
for z in (.3, .62):
    xl, xr, yt, yw = Lz(z), Rz(z), Ty(z), By(z)
    yb = yt + 24 * z + 5
    ys_, ya = yb + (yw - yb) * .42, yb + (yw - yb) * .02
    xs = [xl + (xr - xl) * k / 3 for k in range(4)]
    arch = ''.join(f'M{xa:.0f} {yw:.0f} L{xa:.0f} {ys_:.0f} C{xa:.0f} {ya:.0f} {xb:.0f} {ya:.0f} {xb:.0f} {ys_:.0f} L{xb:.0f} {yw:.0f} ' for xa, xb in zip(xs, xs[1:]))
    C.append(f'<path class="brg" d="M{xl:.0f} {yt:.0f} L{xr:.0f} {yt:.0f} M{xl:.0f} {yb:.0f} L{xr:.0f} {yb:.0f} {arch}"/>')
    bal = ''.join(f'M{xl + (xr - xl) * i / 30:.0f} {yt:.0f} l0 {-5 - 14 * z:.0f} ' for i in range(31))
    C.append(f'<path class="rail" d="M{xl:.0f} {yt - 5 - 14 * z:.0f} L{xr:.0f} {yt - 5 - 14 * z:.0f} {bal}"/>')
    n = 11
    for i in range(n):
        t = i / (n - 1)
        x = xl + (xr - xl) * (.03 + .94 * t)
        y = yb + 5 + 14 * z * math.sin(math.pi * t)
        col = BAND[i % 6]
        r = 2 + 8 * z
        C.append(f'<g class="gl">{halo(col, r * 3.2, x, y + r, .7)}<ellipse class="L" style="color:{col}" cx="{x:.1f}" cy="{y + r:.1f}" rx="{r:.1f}" ry="{r * 1.1:.1f}"/></g>')
# sculptures on plinths in the water (+ mirrored, rippling reflections)
SC = [(-1, .17, 'lotus', ('#ff8fc4', '#ffc4e0')), (1, .22, 'crane', ('#ffd23f', '#fff4a0')), (-1, .36, 'pagoda', ('#ff8a2b', '#ffd9a0')),
      (1, .44, 'elephant', ('#8fd8ff', '#e0f4ff')), (-1, .62, 'fish', ('#ff6a5a', '#ffb0a0')), (1, .72, 'wheel', ('#ffb43a', '#ffe08a')),
      (-1, .88, 'crane', ('#ff8fc4', '#ffe0f0'))]
for sx, z, kind, (c1, c2) in sorted(SC, key=lambda a: a[1]):
    xl, xr = Lz(z), Rz(z)
    fx = .22 if sx < 0 else .78
    x = xl + fx * (xr - xl)
    y = By(z) + 8 * z + 6
    s = .2 + 1.05 * z
    plinth = ('<path class="S" style="color:#7f93d8" d="M-40 0 L40 0 L40 -30 L-40 -30 Z M-40 -30 L-30 -37 L50 -37 L40 -30"/>'
              '<path class="N" style="color:#7f93d8" d="M-40 -15 L40 -15"/>')
    fig = LS.SCULPT[kind](c1, c2)
    body = f'{plinth}<g transform="translate(0 -37)">{halo(c1, 95, 0, -48, .8)}{fig}</g>'
    ph = R.uniform(0, 3)
    C.append(f'<g transform="translate({x:.0f} {y:.0f})"><ellipse class="rip" style="--rd:3.6s;--rl:-{ph:.1f}s" cx="0" cy="6" rx="{60 * s:.0f}" ry="{12 * s:.0f}"/>'
             f'<ellipse class="rip" style="--rd:3.6s;--rl:-{ph + 1.8:.1f}s" cx="0" cy="6" rx="{60 * s:.0f}" ry="{12 * s:.0f}"/></g>')
    C.append(f'<g class="wob" style="transform-origin:{x:.0f}px {y:.0f}px;--wl:-{ph:.1f}s"><g transform="translate({x:.0f} {y:.0f}) scale({s:.2f} {-s:.2f})" style="opacity:.28" filter="url(#blurR)">{body}</g></g>')
    C.append(f'<g class="gl" style="--gl:-{ph:.1f}s"><g transform="translate({x:.0f} {y:.0f}) scale({s:.2f})">{body}</g></g>')
for i in range(30):
    C.append(tw(R.choice(['#ffb35a', '#ffe08a', '#8fd8ff', '#ff8fc4']), R.uniform(1, 2.4), R.uniform(0, 960), R.uniform(262, 530)))

# =============================================================================================
# Scene D: the stairway under hanging lotus lanterns (94-130)
# =============================================================================================
Dg = []
DX, DY = 480, 240
CAM_D = kfs([(0, 'transform:scale(1)'), (94, 'transform:scale(1)'), (130, 'transform:scale(1.22)'), (T, 'transform:scale(1.22)')])
n_steps = 18
tread, riser = '', ''
for i in range(1, n_steps + 1):
    t = i / n_steps
    y, w = 252 + 300 * t ** 1.4, 34 + 440 * t
    r_ = 3 + 26 * t
    tread += f'M{DX - w:.0f} {y:.0f} L{DX + w:.0f} {y:.0f} '
    riser += f'M{DX - w:.0f} {y + r_:.0f} L{DX + w:.0f} {y + r_:.0f} '
    Dg.append(f'<path d="M{DX - w:.0f} {y:.0f} L{DX + w:.0f} {y:.0f} L{DX + w:.0f} {y + r_:.0f} L{DX - w:.0f} {y + r_:.0f} Z" fill="#ffcf8a" style="stroke:none;opacity:{.05 + .08 * t:.2f}"/>')
Dg.append(f'<path class="stairS" d="{tread}"/><path class="stairR" d="{riser}"/>')
Dg.append(f'<path class="stairS" d="M{DX - 34} 252 L{DX - 474} 552 M{DX + 34} 252 L{DX + 474} 552"/>')
for sx in (-1, 1):
    pts = [(DX + sx * (34 + 440 * t), 252 + 300 * t ** 1.4 - (10 + 90 * t)) for t in [k / 20 for k in range(21)]]
    Dg.append('<path class="rail2" d="M' + ' L'.join(f'{x:.0f} {y:.0f}' for x, y in pts) + '"/>')
    for i in range(1, n_steps + 1):
        t = i / n_steps
        x, y = DX + sx * (34 + 440 * t), 252 + 300 * t ** 1.4
        hr = 10 + 90 * t
        Dg.append(f'<path class="rail2" d="M{x:.0f} {y:.0f} L{x:.0f} {y - hr:.0f}"/>')
        s = .18 + .7 * t
        col = ['#ff4f7a', '#ffc83a'][(i + (sx > 0)) % 2]
        Dg.append(f'<g transform="translate({x:.0f} {y - hr:.0f}) scale({s:.2f})"><g class="sw" style="--sa:{R.uniform(2, 5):.1f}deg;--sd:{R.uniform(3, 5):.1f}s;--sl:-{R.uniform(0, 5):.1f}s;transform-origin:0px 0px">'
                 f'{halo(col, 38, 0, 40, .55)}{LS.lotus_hang(col)}</g></g>')
Dg.append(f'<path class="beams" d="M{DX} {DY} L-40 -40 M{DX} {DY} L1000 -40 M{DX} {DY} L-40 120 M{DX} {DY} L1000 120"/>')
Dg.append(f'<circle cx="{DX}" cy="{DY}" r="150" fill="url(#dglow)" style="stroke:none"/>')
for c_i, off in enumerate((-330, -170, 0, 170, 330)):
    M_ = 9
    for j in range(M_):
        zz = ((j + 1) / M_) ** 1.25
        x, y = DX + off * zz, 250 - 255 * zz
        s = .12 + 1.2 * zz
        col = ['#ff4f7a', '#ffc83a'][(j + c_i) % 2]
        Dg.append(f'<path class="cordD" d="M{x:.0f} {y - 40 * s:.0f} L{x:.0f} {y:.0f}"/>'
                  f'<g transform="translate({x:.0f} {y:.0f}) scale({s:.2f})"><g class="sw" style="--sa:{R.uniform(1.5, 4):.1f}deg;--sd:{R.uniform(3, 5.5):.1f}s;--sl:-{R.uniform(0, 5):.1f}s;transform-origin:0px 0px">'
                  f'{halo(col, 46, 0, 36, .6)}{LS.lotus_hang(col)}</g></g>')
for i in range(40):
    Dg.append(tw(R.choice(['#ffe08a', '#ffb35a', '#ff8fc4']), R.uniform(1, 2.4), DX + R.uniform(-60, 60), DY + R.uniform(-30, 40)))

# --- stairway backdrop: a dim ceiling of hanging lanterns, glints, fairy lights, bokeh (own RNG, so other scenes stay unchanged) ---
RD = random.Random(SEED + 500)
bgD = []
WARM_D = [('#ff9a3d', '#ffd45a'), ('#ffb43a', '#fff0a0'), ('#ff6a4a', '#ffd9a0'), ('#ff7fb0', '#ffe0ee'), ('#ffd45a', '#ff9a3d'), ('#9be05a', '#fff0a0')]
for i in range(16):      # soft bokeh blobs far behind
    bgD.append(f'<g class="pl" style="--pd:{RD.uniform(2.4, 5):.1f}s;--pl:-{RD.uniform(0, 5):.1f}s">'
               f'{halo(RD.choice(["#ffb35a", "#ff8fc4", "#ffd27a", "#ff9a4a"]), RD.uniform(34, 80), RD.uniform(0, 960), RD.uniform(10, 380), .55)}</g>')
for yy, sag in ((34, 64), (62, 80), (92, 56)):      # strings of fairy lights across the ceiling
    bgD.append(f'<path class="cordD" style="opacity:.5" d="M-20 {yy} Q480 {yy + sag} 980 {yy}"/>')
    for k in range(36):
        t_ = k / 35
        bx, by = -20 + 1000 * t_, (1 - t_) ** 2 * yy + 2 * t_ * (1 - t_) * (yy + sag) + t_ ** 2 * yy
        col = RD.choice(['#ffe9a8', '#ff8fc4', '#ffb35a', '#9be05a', '#8fd8ff'])
        bgD.append(f'<g class="pl" style="--pd:{RD.uniform(1.2, 2.6):.1f}s;--pl:-{RD.uniform(0, 3):.1f}s">{halo(col, 10, bx, by + 3, .8)}'
                   f'<circle cx="{bx:.0f}" cy="{by + 3:.0f}" r="2.2" fill="{col}" style="stroke:none"/></g>')
placedD, itemsD, tries = [], [], 0
while len(itemsD) < 70 and tries < 5000:
    tries += 1
    kind = RD.choice(['hex', 'hex', 'round', 'round', 'star', 'drum', 'lotus', 'lotus', 'tag', 'tag'])
    size = RD.uniform(.5, .98)
    rr = {'hex': 34, 'round': 30, 'star': 32, 'drum': 30, 'lotus': 30, 'tag': 14}[kind] * size
    x, drop = RD.uniform(0, 960), RD.uniform(16, 300)
    cy = drop + rr * (1.1 if kind != 'tag' else 2.6)
    if cy + rr > 300:       # stay above the stairs
        continue
    if 320 < x < 640 and cy + rr > 110 and cy - rr < 330:      # keep the glowing tunnel clear
        continue
    if any(math.hypot(x - px, cy - py) < (rr + pr) * .72 for px, py, pr in placedD):
        continue
    placedD.append((x, cy, rr))
    itemsD.append((size, kind, x, drop, rr))
for size, kind, x, drop, rr in sorted(itemsD, key=lambda a: a[0]):
    c1, c2 = RD.choice(WARM_D)
    if kind == 'hex':
        g = LS.hex_lantern(46 * size, 50 * size, c1, c2)
    elif kind == 'round':
        g = LS.round_lantern(25 * size, c1, c2)
    elif kind == 'star':
        g = LS.star_lantern(27 * size, c1, c2)
    elif kind == 'drum':
        g = LS.drum_lantern(24 * size, 40 * size, c1, c2)
    elif kind == 'lotus':
        g = f'<g transform="scale({size:.2f})">{LS.lotus_hang(RD.choice(["#ff4f7a", "#ffc83a", "#ff8fc4"]))}</g>'
    else:
        g = LS.tag_strip(18 * size, 74 * size, c1)
    dd = RD.uniform(3.4, 6)
    inner = (f'<g class="pl" style="--pd:{RD.uniform(2.2, 4.6):.1f}s;--pl:-{RD.uniform(0, 5):.1f}s"><g transform="translate({x:.0f} {drop:.0f})">'
             f'{halo(c1, rr * 1.9, 0, rr * 1.1, .6)}{g}</g></g>')
    bgD.append(f'<g style="opacity:.62"><path class="cordD" style="opacity:.6" d="M{x:.0f} 0 L{x:.0f} {drop:.0f}"/>'
               f'<g class="sw" style="--sa:{RD.uniform(1, 2.6):.1f}deg;--sd:{dd:.1f}s;--sl:-{RD.uniform(0, dd):.1f}s;transform-origin:{x:.0f}px 0px">{inner}</g></g>')
for i in range(110):     # four-point glints
    sx_, sy_, ss = RD.uniform(0, 960), RD.uniform(0, 420), RD.uniform(2.5, 7.5)
    col = RD.choice(['#fff3c8', '#ffd27a', '#ffe9a8', '#ffc0dc'])
    bgD.append(f'<g transform="translate({sx_:.0f} {sy_:.0f})"><path class="spk" style="fill:{col};--td:{RD.uniform(1.6, 4.2):.1f}s;--tl:-{RD.uniform(0, 4):.1f}s" '
               f'd="M0 {-ss:.1f} Q0 0 {ss:.1f} 0 Q0 0 0 {ss:.1f} Q0 0 {-ss:.1f} 0 Q0 0 0 {-ss:.1f} Z"/></g>')
Dg[0:0] = bgD

# =============================================================================================
# Scene E: the ceiling of hanging lanterns (126-158)
# =============================================================================================
Eg = []
CAM_E = kfs([(0, 'transform:translateX(30px)'), (126, 'transform:translateX(30px)'), (158, 'transform:translateX(-50px)'), (T, 'transform:translateX(-50px)')])
placed = []
WARM = [('#ff9a3d', '#ffd45a'), ('#ffb43a', '#fff0a0'), ('#ff6a4a', '#ffd9a0'), ('#ff7fb0', '#ffe0ee'), ('#ffd45a', '#ff9a3d'), ('#9be05a', '#fff0a0'), ('#59d6c0', '#ffd45a')]
items = []
tries = 0
while len(items) < 46 and tries < 3000:
    tries += 1
    kind = R.choice(['hex', 'hex', 'round', 'round', 'star', 'drum', 'lotus', 'lotus', 'tag', 'tag'])
    size = R.uniform(.7, 1.45)
    rr = {'hex': 34, 'round': 30, 'star': 32, 'drum': 30, 'lotus': 30, 'tag': 14}[kind] * size
    x, drop = R.uniform(10, 950), R.uniform(30, 400)
    cy = drop + rr * (1.1 if kind != 'tag' else 2.6)
    if cy + rr > 540:
        continue
    if any(math.hypot(x - px, cy - py) < (rr + pr) * .8 for px, py, pr in placed):
        continue
    placed.append((x, cy, rr))
    items.append((size, kind, x, drop, rr))
for size, kind, x, drop, rr in sorted(items, key=lambda a: a[0]):
    c1, c2 = R.choice(WARM)
    if kind == 'hex':
        g = LS.hex_lantern(46 * size, 50 * size, c1, c2)
    elif kind == 'round':
        g = LS.round_lantern(25 * size, c1, c2)
    elif kind == 'star':
        g = LS.star_lantern(27 * size, c1, c2)
    elif kind == 'drum':
        g = LS.drum_lantern(24 * size, 40 * size, c1, c2)
    elif kind == 'lotus':
        g = f'<g transform="scale({size:.2f})">{LS.lotus_hang(R.choice(["#ff4f7a", "#ffc83a", "#ff8fc4"]))}</g>'
    else:
        g = LS.tag_strip(18 * size, 74 * size, c1)
    cord = f'<path class="cordD" d="M{x:.0f} 0 L{x:.0f} {drop:.0f}"/>'
    Eg.append(cord + sway_wrap(f'<g transform="translate({x:.0f} {drop:.0f})">{halo(c1, rr * 1.8, 0, rr * 1.1, .55)}{g}</g>', x, 0, R.uniform(1.2, 3.4), R.uniform(3.2, 6)))
Eg.append('<path class="rail2" d="M-60 0 L1020 0"/>')
for i in range(34):
    Eg.append(tw(R.choice(['#ffe9a8', '#ffc870']), R.uniform(1, 2.4), R.uniform(0, 960), R.uniform(10, 520)))

# =============================================================================================
# Scene B: the night sky - sky lanterns, tower, laser beams (154-214)
# =============================================================================================
B = []
OB = 96
B.append(f'<path class="d0 k hill2" pathLength="1" style="animation-name:{draw(52 + OB, 4, 112 + OB)}" d="M0 436 C60 424 100 440 160 430 S280 416 340 432 S470 424 520 436 S650 422 720 434 S860 420 960 432"/>')
TXB = 560
B.append(f'<rect x="{TXB-8}" y="296" width="16" height="140" fill="url(#towerglow)" class="k" style="stroke:none;opacity:0;animation-name:{op((0,0),(52+OB,0),(58+OB,.8),(112+OB,.8),(118+OB,0))}"/>')
for i, d in enumerate([f'M{TXB-5} 436 L{TXB-5} 250 M{TXB+5} 436 L{TXB+5} 250', f'M{TXB-24} 436 L{TXB-5} 392 M{TXB+24} 436 L{TXB+5} 392',
                       f'M{TXB-5} 250 L{TXB} 222 L{TXB+5} 250', f'M{TXB-22} 330 a22 6 0 1 0 44 0 a22 6 0 1 0 -44 0', f'M{TXB-16} 296 a16 5 0 1 0 32 0 a16 5 0 1 0 -32 0',
                       f'M{TXB-22} 330 L{TXB-18} 344 L{TXB+18} 344 L{TXB+22} 330', f'M{TXB-16} 296 L{TXB-13} 306 L{TXB+13} 306 L{TXB+16} 296']):
    B.append(f'<path class="d0 k tower" pathLength="1" style="animation-name:{draw(53 + OB + i * .5, 2.5, 112 + OB)}" d="{d}"/>')
# a proper tree line: two layers of pines and broad-leaf trees, with lamps lit along the path
for layer, (base, hmin, hmax, step, tfc, tsc, o) in enumerate([(508, 30, 56, 38, '#04102c', '#2f5aa8', .7), (532, 56, 100, 62, '#050d26', '#4a78d0', .95)]):
    s = ''
    x = R.uniform(-10, 20)
    while x < 980:
        h = R.uniform(hmin, hmax)
        s += f'<g transform="translate({x:.0f} {base})">{LS.pine(h, R) if R.random() < .55 else LS.round_tree(h, R)}</g>'
        x += step * R.uniform(.8, 1.25)
    B.append(f'<g class="k" style="opacity:0;--tf:{tfc};--ts:{tsc};animation-name:{op((0,0),(54+OB,0),(60+OB,o),(112+OB,o),(118+OB,0))}">{s}</g>')
for i in range(26):
    B.append(tw(R.choice(['#ffb35a', '#ff8f5a', '#ffe08a']), R.uniform(1.6, 2.8), 20 + i * 36 + R.uniform(-6, 6), R.uniform(520, 534)))
beams = []
for ang in [-78, -68, -58, -50, -42, -34, -27, -20, -14]:
    a = math.radians(ang)
    beams.append(f'<line class="beam" style="--bd:{R.uniform(2.5, 5):.1f}s;--bl:-{R.uniform(0, 5):.1f}s;stroke-width:{R.uniform(2.5, 8):.1f}" x1="30" y1="530" x2="{30 + 1100 * math.cos(a):.0f}" y2="{530 + 1100 * math.sin(a):.0f}"/>')
B.append(f'<g class="k" style="opacity:0;animation-name:{op((0,0),(64+OB+6,0),(70+OB+6,1),(112+OB,1),(118+OB,0))}"><g class="sweep" style="transform-origin:30px 530px">{"".join(beams)}</g></g>')


def lantern_path(S):
    return (f'M{-.9*S:.1f} {-1.2*S:.1f} C{-1.25*S:.1f} {-.3*S:.1f} {-1.0*S:.1f} {.7*S:.1f} {-.55*S:.1f} {1.25*S:.1f} L{.55*S:.1f} {1.25*S:.1f} '
            f'C{1.0*S:.1f} {.7*S:.1f} {1.25*S:.1f} {-.3*S:.1f} {.9*S:.1f} {-1.2*S:.1f} Z M{-.9*S:.1f} {-1.2*S:.1f} Q0 {-1.5*S:.1f} {.9*S:.1f} {-1.2*S:.1f} '
            f'M0 {-1.35*S:.1f} L0 {1.2*S:.1f}')


LCOL = [('#ff9a3d', 'o'), ('#ff9a3d', 'o'), ('#ff5a4a', 'r'), ('#ffd45a', 'y'), ('#ffd45a', 'y'), ('#ff7fb0', 'p'), ('#59d6c0', 't'), ('#6aa8ff', 'u')]
N = 150
for i in range(N):
    col, g = R.choice(LCOL)
    z = R.uniform(.35, 1.0) ** 1.4
    S = 3.6 + 9.5 * z
    x0 = R.uniform(10, 950)
    a = 156 + (i / N) ** 1.1 * 46 + R.uniform(0, 2.5)
    dur = 70 - 28 * z + R.uniform(-4, 4)
    y0 = R.uniform(470, 520)
    rise, dx = y0 + 60, R.uniform(-60, 60)
    fa = min(a + dur, 210)
    k_ = lambda tt: (dx * (tt - a) / dur, -rise * (tt - a) / dur)
    nm = kfs([(0, 'transform:translate(0px,0px);opacity:0'), (a, 'transform:translate(0px,0px);opacity:0'),
              (a + 2.5, 'transform:translate(%.1fpx,%.1fpx);opacity:1' % k_(a + 2.5)), (fa - 4, 'transform:translate(%.1fpx,%.1fpx);opacity:1' % k_(fa - 4)),
              (fa, 'transform:translate(%.1fpx,%.1fpx);opacity:0' % k_(fa))])
    sd = R.uniform(3, 6.5)
    B.append(f'<g class="k" style="opacity:0;animation-name:{nm}"><g transform="translate({x0:.0f} {y0:.0f})"><g class="ls" style="--sx:{R.uniform(3, 9)*z+2:.1f}px;--sa:{R.uniform(2, 6):.1f}deg;'
             f'--sd:{sd:.1f}s;--sl:-{R.uniform(0, sd):.1f}s"><circle r="{S*2.8:.1f}" fill="url(#lh_{g})" style="stroke:none"/>'
             f'<path class="sl" style="color:{col}" d="{lantern_path(S)}"/><circle class="flame" cy="{S*1.2:.1f}" r="{max(.9, S*.2):.1f}"/></g></g></g>')
LC = (480, 318)
LOT = []
for layer, (n_, rad, wid, rot, colr) in enumerate([(8, 118, 34, 0, '#ff8fc4'), (8, 96, 30, 22.5, '#ffb3d9'), (6, 66, 24, 10, '#fff0f6')]):
    for k in range(n_):
        d = f'M0 0 C{-wid} {-rad*.35:.0f} {-wid*.7:.0f} {-rad*.8:.0f} 0 {-rad} C{wid*.7:.0f} {-rad*.8:.0f} {wid} {-rad*.35:.0f} 0 0 Z M0 {-rad*.15:.0f} L0 {-rad*.82:.0f}'
        t0 = 88 + OB + layer * 1.2 + k * .12
        nm = kfs([(0, 'transform:scale(.05) rotate(-30deg);opacity:0'), (t0, 'transform:scale(.05) rotate(-30deg);opacity:0'), (t0 + 5, 'transform:scale(1) rotate(0deg);opacity:1'),
                  (112 + OB, 'transform:scale(1) rotate(0deg);opacity:1'), (117 + OB, 'transform:scale(1.15) rotate(8deg);opacity:0')])
        LOT.append(f'<g class="k" style="opacity:0;transform-origin:{LC[0]}px {LC[1]}px;animation-name:{nm}"><g transform="translate({LC[0]} {LC[1]}) rotate({rot + k * 360 / n_})">'
                   f'<path class="lot" style="color:{colr}" d="{d}"/></g></g>')
LOT.append(f'<circle class="k" style="opacity:0;animation-name:{op((0,0),(92+OB,0),(97+OB,1),(112+OB,1),(117+OB,0))}" cx="{LC[0]}" cy="{LC[1]}" r="150" fill="url(#lotglow)"/>')
ring = ''.join(f'<g transform="translate({LC[0] + 175 * math.cos(math.radians(k * 30)):.0f} {LC[1] + 175 * .42 * math.sin(math.radians(k * 30)):.0f})">{halo(BAND[k % 6], 20)}'
               f'<path class="sl" style="color:{BAND[k % 6]}" d="{lantern_path(7.5)}"/><circle class="flame" cy="9" r="1.6"/></g>' for k in range(12))
LOT.append(f'<g class="k" style="opacity:0;animation-name:{op((0,0),(94+OB,0),(98+OB,1),(112+OB,1),(117+OB,0))}"><g class="ringspin" style="transform-origin:{LC[0]}px {LC[1]}px">{ring}</g></g>')

# =============================================================================================
# assemble
# =============================================================================================
fadeA, fadeC, fadeD, fadeE, fadeB = scene_fade(0, 52, 2, 4), scene_fade(50, 94), scene_fade(94, 124), scene_fade(126, 152), scene_fade(154, 208)
bgs = [('bgA', op((0, 0), (1.5, 1), (50, 1), (56, 0))), ('bgC', op((0, 0), (50, 0), (56, 1), (92, 1), (98, 0))), ('bgD', op((0, 0), (94, 0), (100, 1), (124, 1), (130, 0))),
       ('bgE', op((0, 0), (126, 0), (132, 1), (152, 1), (158, 0))), ('bgB', op((0, 0), (152, 0), (160, 1), (208, 1), (214, 0)))]
halos_defs = ''.join(f'<radialGradient id="halo_{i}"><stop offset="0" stop-color="{c}" stop-opacity=".5"/><stop offset=".5" stop-color="{c}" stop-opacity=".16"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
                     for i, c in enumerate(BAND))
halos_defs += ''.join(f'<radialGradient id="{i}"><stop offset="0" stop-color="{c}" stop-opacity=".55"/><stop offset=".45" stop-color="{c}" stop-opacity=".16"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
                      for c, i in HALOS.items())
lh = ''.join(f'<radialGradient id="lh_{g}"><stop offset="0" stop-color="{c}" stop-opacity=".38"/><stop offset=".45" stop-color="{c}" stop-opacity=".1"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
             for c, g in {(c, g) for c, g in LCOL})
rects = ''.join(f'<rect class="k" width="{W}" height="{H}" fill="url(#{i})" style="opacity:0;animation-name:{nm}"/>' for i, nm in bgs)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>Lantern festival - laser line art</title>
<defs>
<radialGradient id="bgA" cx="50%" cy="72%" r="85%"><stop offset="0" stop-color="#3a1630"/><stop offset=".5" stop-color="#150b24"/><stop offset="1" stop-color="#05040c"/></radialGradient>
<linearGradient id="bgC" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#050a22"/><stop offset=".45" stop-color="#0c1740"/><stop offset="1" stop-color="#06122e"/></linearGradient>
<radialGradient id="bgD" cx="50%" cy="44%" r="80%"><stop offset="0" stop-color="#5a2a10"/><stop offset=".5" stop-color="#220f0a"/><stop offset="1" stop-color="#07040a"/></radialGradient>
<radialGradient id="bgE" cx="50%" cy="0%" r="110%"><stop offset="0" stop-color="#8a4a10"/><stop offset=".55" stop-color="#3a1806"/><stop offset="1" stop-color="#0d0503"/></radialGradient>
<linearGradient id="bgB" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#020716"/><stop offset=".65" stop-color="#06173c"/><stop offset="1" stop-color="#0b2a66"/></linearGradient>
<linearGradient id="waterG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d2e66" stop-opacity=".95"/><stop offset="1" stop-color="#040c22" stop-opacity=".95"/></linearGradient>
<radialGradient id="dglow"><stop offset="0" stop-color="#ffd08a" stop-opacity=".75"/><stop offset=".5" stop-color="#ff9a4a" stop-opacity=".22"/><stop offset="1" stop-color="#ff9a4a" stop-opacity="0"/></radialGradient>
<linearGradient id="towerglow" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe27a" stop-opacity=".9"/><stop offset="1" stop-color="#ffb23a" stop-opacity=".25"/></linearGradient>
<radialGradient id="lotglow"><stop offset="0" stop-color="#ffd6ea" stop-opacity=".55"/><stop offset=".6" stop-color="#ff8fc4" stop-opacity=".18"/><stop offset="1" stop-color="#ff8fc4" stop-opacity="0"/></radialGradient>
{halos_defs}{lh}
<filter id="glow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="blur2"><feGaussianBlur stdDeviation="2.2"/></filter><filter id="blurR"><feGaussianBlur stdDeviation="1.6"/></filter>
<style>
.d0{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1}}
.k{{animation-duration:{T:.0f}s;animation-timing-function:linear;animation-iteration-count:infinite}}
.S{{fill:currentColor;fill-opacity:.25;stroke:currentColor;stroke-width:1.7;stroke-linejoin:round;stroke-linecap:round}}
.N{{fill:none;stroke:currentColor;stroke-width:1.4;stroke-linecap:round;stroke-linejoin:round;color:#fff4d0}}
.T{{fill:var(--tf,#06143a);stroke:var(--ts,#6f95e8);stroke-width:1.6;stroke-linejoin:round}} .tb{{stroke:var(--ts,#6f95e8);color:var(--ts,#6f95e8)}}
.hill{{stroke:#7f78c8;stroke-width:1.4;opacity:.55}} .hill2{{stroke:#4d86d8;stroke-width:1.6;opacity:.6}}
.roof{{stroke:#ffd9a0;stroke-width:2.2}} .wall{{stroke:#e8b878;stroke-width:1.6}} .win{{fill:#ffe9a8}}
.L{{fill:currentColor;fill-opacity:.38;stroke:currentColor;stroke-width:.9}}
.b0{{color:{BAND8[0]}}} .b1{{color:{BAND8[1]}}} .b2{{color:{BAND8[2]}}} .b3{{color:{BAND8[3]}}} .b4{{color:{BAND8[4]}}} .b5{{color:{BAND8[5]}}} .b6{{color:{BAND8[6]}}} .b7{{color:{BAND8[7]}}}
.stair{{stroke:#ffffff;stroke-width:1.2;opacity:.35;fill:none}} .cord{{stroke:#d8c8a8;stroke-width:1.4;fill:none}} .cap{{fill:none;stroke:#e8d8b8;stroke-width:1.4}}
.fgL{{fill:currentColor;fill-opacity:.22;stroke:currentColor;stroke-width:2}} .rib{{fill:none;stroke:currentColor;stroke-width:1.3;opacity:.8}}
.sw{{animation:sw var(--sd) ease-in-out var(--sl) infinite}}
.tw{{opacity:.2;animation:twinkle var(--td) ease-in-out var(--tl) infinite}}
.ember{{fill:#ffb35a;opacity:0;animation:mote var(--md) ease-in-out var(--mdl) infinite}}
.wallc{{fill:none;stroke:#5a6fb0;stroke-width:1.5;opacity:.8}} .wallj{{fill:none;stroke:#46599a;stroke-width:1.2;opacity:.7}} .rail{{fill:none;stroke:#8fa6e8;stroke-width:1.4;opacity:.8}}
.bld{{fill:none;stroke:#4a5fa8;stroke-width:1.3;opacity:.75}} .brg{{fill:#0a1230;fill-opacity:.55;stroke:#8fa6e8;stroke-width:1.8}}
.flow{{fill:none;stroke:#6aa8ff;stroke-width:1.5;opacity:.45;stroke-dasharray:16 14;animation:flow var(--fd) linear var(--fl) infinite}}
.fall{{stroke:#bfe2ff;stroke-width:1.6;stroke-dasharray:4 5;animation:flow var(--fd) linear var(--fl) infinite}}
.rip{{fill:none;stroke:#9cc8ff;stroke-width:1.3;opacity:0;transform-box:fill-box;transform-origin:center;animation:rip var(--rd) ease-out var(--rl) infinite}}
.wob{{animation:wob 4.2s ease-in-out var(--wl) infinite}} .gl{{animation:gl 3.6s ease-in-out var(--gl,0s) infinite}}
.stairS{{fill:none;stroke:#ffd9a0;stroke-width:1.6;opacity:.8}} .stairR{{fill:none;stroke:#b57a46;stroke-width:1.2;opacity:.7}} .rail2{{fill:none;stroke:#d8c8a8;stroke-width:1.5;opacity:.8}}
.cordD{{fill:none;stroke:#d8c8a8;stroke-width:1.3;opacity:.8}} .pl{{animation:pl var(--pd) ease-in-out var(--pl) infinite}}
.spk{{stroke:none;transform-box:fill-box;transform-origin:center;animation:spk var(--td) ease-in-out var(--tl) infinite}} .beams{{fill:none;stroke:#ffb870;stroke-width:1;opacity:.25}}
.tower{{stroke:#ffe9a0;stroke-width:2}}
.beam{{stroke:#4aa8ff;opacity:.5;stroke-linecap:round;filter:url(#blur2);animation:beamfl var(--bd) ease-in-out var(--bl) infinite}}
.sweep{{animation:sweep 16s ease-in-out infinite alternate}}
.sl{{fill:currentColor;fill-opacity:.3;stroke:currentColor;stroke-width:1.1}} .flame{{fill:#fff4c8;stroke:none}}
.ls{{animation:ls var(--sd) ease-in-out var(--sl) infinite}}
.lot{{fill:currentColor;fill-opacity:.12;stroke:currentColor;stroke-width:2.2;stroke-linejoin:round}}
.ringspin{{animation:spin 48s linear infinite}}
@keyframes sw{{0%,100%{{transform:rotate(calc(var(--sa)*-1))}}50%{{transform:rotate(var(--sa))}}}}
@keyframes ls{{0%,100%{{transform:translateX(calc(var(--sx)*-1)) rotate(calc(var(--sa)*-1))}}50%{{transform:translateX(var(--sx)) rotate(var(--sa))}}}}
@keyframes twinkle{{0%,100%{{opacity:.15}}50%{{opacity:1}}}}
@keyframes mote{{0%{{opacity:0;transform:translate(0,0)}}25%{{opacity:.9}}75%{{opacity:.5}}100%{{opacity:0;transform:translate(var(--dx),var(--dy))}}}}
@keyframes flow{{to{{stroke-dashoffset:-60}}}}
@keyframes rip{{0%{{opacity:.7;transform:scale(.4)}}100%{{opacity:0;transform:scale(1.5)}}}}
@keyframes wob{{0%,100%{{transform:skewX(-2.5deg)}}50%{{transform:skewX(2.5deg)}}}}
@keyframes pl{{0%,100%{{opacity:.45}}50%{{opacity:1}}}}
@keyframes spk{{0%,100%{{opacity:0;transform:scale(.2) rotate(0deg)}}50%{{opacity:1;transform:scale(1) rotate(45deg)}}}}
@keyframes gl{{0%,100%{{opacity:.86}}50%{{opacity:1}}}}
@keyframes sweep{{from{{transform:rotate(-7deg)}}to{{transform:rotate(9deg)}}}}
@keyframes beamfl{{0%,100%{{opacity:.25}}50%{{opacity:.7}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
{chr(10).join(KFS)}
</style>
</defs>
<rect width="{W}" height="{H}" fill="#02030a"/>
{rects}
<g filter="url(#glow)" id="world">
<g class="k" style="opacity:0;animation-name:{fadeB}">{''.join(B)}</g>
<g class="k" style="opacity:0;animation-name:{fadeE}"><g class="k" style="animation-name:{CAM_E}">{''.join(Eg)}</g></g>
<g class="k" style="opacity:0;animation-name:{fadeD}"><g class="k" style="transform-origin:{DX}px {DY}px;animation-name:{CAM_D}">{''.join(Dg)}</g></g>
<g class="k" style="opacity:0;animation-name:{fadeC}"><g class="k" style="transform-origin:{VPX}px {VPY}px;animation-name:{CAM_C}">{''.join(C)}</g></g>
<g class="k" style="opacity:0;animation-name:{fadeA}"><g class="k" style="transform-origin:480px 300px;animation-name:{CAM_A}">{''.join(A)}</g></g>
{''.join(LOT)}
</g>
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print('wrote', os.path.normpath(OUT), len(svg) // 1024, 'KB', len(KFS), 'keyframes')
