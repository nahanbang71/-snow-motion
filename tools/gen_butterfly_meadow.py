#!/usr/bin/env python3
"""Laser-style sample: swallowtails on a randomised flower meadow, drifting clouds.
usage: python3 tools/gen_butterfly_meadow.py [seed]   -> flowers/butterfly_meadow.svg
3 scenes loop forever (1 -> 2 -> 3 butterflies). Each scene re-draws a fresh random meadow
(flower kind / size / colour / petal count / position all vary). Clouds drift across continuously.
Single-stroke neon line art (no fills); animation is pure CSS (scene restart = display toggle).
"""
import math
import os
import random
import sys

W, H = 960, 540
D = 14.0            # seconds per scene
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 7
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flowers', 'butterfly_meadow.svg')


T = D * 3
KF = {}


def kf(prop, v0, v1, a, t):
    """cycle-aware keyframes: hold v0 until a, ramp to v1 over t, hold v1 (all times in seconds from cycle start)"""
    key = (prop, v0, v1, round(a, 2), round(t, 2))
    if key not in KF:
        KF[key] = f'k{len(KF)}'
    return KF[key]


def kf_css():
    out = []
    for (prop, v0, v1, a, t), n in KF.items():
        out.append(f'@keyframes {n}{{0%,{a/T*100:.3f}%{{{prop}:{v0}}}{(a+t)/T*100:.3f}%,100%{{{prop}:{v1}}}}}')
    return '\n'.join(out)


class Scene:
    def __init__(self, k):
        self.k = k
        self.els = []

    def path(self, d, cls, s, t, col=None):
        c = f';stroke:{col}' if col else ''
        n = kf('stroke-dashoffset', 1, 0, self.k * D + s, t)
        self.els.append(f'<path class="d {cls}" pathLength="1" style="animation-name:{n}{c}" d="{d}"/>')

    def dot(self, x, y, r, cls, s, col=None):
        c = f';fill:{col}' if col else ''
        n = kf('opacity', 0, 1, self.k * D + s, .5)
        self.els.append(f'<circle class="fi {cls}" style="animation-name:{n}{c}" cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>')


def circ(x, y, r):
    return f'M{x-r:.1f} {y:.1f} a{r:.1f} {r:.1f} 0 1 0 {2*r:.1f} 0 a{r:.1f} {r:.1f} 0 1 0 {-2*r:.1f} 0'


def rot(px, py, a):
    c, s = math.cos(a), math.sin(a)
    return px * c - py * s, px * s + py * c


def poly(cmds, a, cx, cy, sc):
    out = []
    for let, v in cmds:
        pts = []
        for i in range(0, len(v), 2):
            x, y = rot(v[i], v[i + 1], a)
            pts += [f'{cx + x*sc:.1f}', f'{cy + y*sc:.1f}']
        out.append(let + ' '.join(pts))
    return ' '.join(out)


PETAL = [('M', [0, -12]), ('C', [-30, -30, -38, -80, -30, -98]), ('L', [-18, -90]), ('L', [-9, -100]), ('L', [0, -91]),
         ('L', [9, -100]), ('L', [18, -90]), ('L', [30, -98]), ('C', [38, -80, 30, -30, 0, -12]), ('Z', [])]
VEIN = [('M', [0, -16]), ('L', [0, -82])]
DAISY = [('M', [0, -9]), ('C', [-10, -22, -10, -46, 0, -54]), ('C', [10, -46, 10, -22, 0, -9]), ('Z', [])]


# ---------- flowers: each returns nothing, draws into scene `S`, height ~ extent above (x,y) ----------
def stem(S, x, y, dx, d):
    S.path(f'M{x:.1f} {y:.1f} C{x:.1f} {y+(H-y)*.4:.1f} {x+dx:.1f} {y+(H-y)*.7:.1f} {x+dx:.1f} {H+4}', 'stem', d, 1.0)


def cosmos(S, R, x, y, sc, col, d):
    n = R.randint(6, 10)
    stem(S, x, y + 90 * sc, R.uniform(-30, 30) * sc, d)
    a0 = R.uniform(0, 6.28)
    for i in range(n):
        a = a0 + i * 2 * math.pi / n
        S.path(poly(PETAL, a, x, y, sc * R.uniform(.88, 1.08)), 'pet', d + .1 + i * .05, .7, col)
        if sc > .55:
            S.path(poly(VEIN, a, x, y, sc), 'pet2', d + .4 + i * .05, .4, col)
    S.path(circ(x, y, 12 * sc), 'ctr', d + .6, .5)
    if sc > .55:
        for k in range(10):
            a = k * .628
            S.dot(x + 22 * sc * math.cos(a), y + 22 * sc * math.sin(a), 2, 'ctrd', d + .8 + k * .03)


def daisy(S, R, x, y, sc, col, d):
    n = R.randint(10, 16)
    stem(S, x, y + 55 * sc, R.uniform(-22, 22) * sc, d)
    a0 = R.uniform(0, 6.28)
    for i in range(n):
        S.path(poly(DAISY, a0 + i * 2 * math.pi / n, x, y, sc * R.uniform(.85, 1.1)), 'pet2', d + .1 + i * .03, .5, col)
    S.path(circ(x, y, 8 * sc), 'ctr', d + .5, .4)


def lupine(S, R, x, y, h, col, d):
    stem(S, x, y + h, R.uniform(-12, 12), d)
    rows = int(h / 16)
    for k in range(rows):
        yy = y + k * 16
        wd = 4 + 9 * (1 - abs(k / rows - .35) * 1.2)
        for sx in (-1, 1):
            S.path(f'M{x} {yy} C{x+sx*wd:.1f} {yy-6} {x+sx*(wd+4):.1f} {yy+8} {x+sx*2} {yy+14}', 'pet2', d + .1 + k * .06, .4, col)


def bud(S, R, x, y, sc, col, d):
    stem(S, x, y + 40 * sc, R.uniform(-14, 14) * sc, d)
    S.path(f'M{x} {y-30*sc:.1f} C{x-22*sc:.1f} {y-10*sc:.1f} {x-18*sc:.1f} {y+30*sc:.1f} {x} {y+38*sc:.1f} '
           f'C{x+18*sc:.1f} {y+30*sc:.1f} {x+22*sc:.1f} {y-10*sc:.1f} {x} {y-30*sc:.1f}', 'pet', d + .1, .8, col)
    S.path(f'M{x-14*sc:.1f} {y+22*sc:.1f} L{x} {y+4*sc:.1f} L{x+14*sc:.1f} {y+22*sc:.1f}', 'pet2', d + .5, .4, col)


def tiny(S, R, x, y, sc, col, d):
    n = R.choice([4, 5, 5, 6])
    stem(S, x, y + 14 * sc, R.uniform(-8, 8), d)
    for i in range(n):
        a = i * 2 * math.pi / n
        S.path(circ(x + 9 * sc * math.cos(a), y + 9 * sc * math.sin(a), 5 * sc), 'pet2', d + .1 + i * .05, .3, col)
    S.path(circ(x, y, 3 * sc), 'ctr', d + .4, .3)


PINKS = ['#ff6fb5', '#ff8ac4', '#ff9fd0', '#ffb3da', '#ff5fa0']
WARM = ['#ff9f43', '#ffd23f', '#ff7a7a', '#fff4a0']
COOL = ['#7ad8ff', '#8f9bff', '#a78bff', '#c9a6ff']
WHITE = ['#ffffff', '#fff4a0', '#e8f0ff']

BFLY = [  # wing, band, eye colours
    ('#ffe45a', '#4d7cff', '#ff8a2e'), ('#7ae8ff', '#ff6fb5', '#ffe45a'), ('#ffb35a', '#a78bff', '#ff6f6f')]

WING = [
    ('M4 -8 C30 -50 70 -78 96 -62 C104 -40 92 -10 60 8 C40 16 20 12 4 6 Z', 'wing', 0),
    ('M4 6 C34 12 66 20 76 40 C82 58 66 68 54 62 L58 90 L44 66 C28 62 10 40 4 28', 'wing', 1),
    ('M10 -6 C34 -34 62 -54 86 -56', 'stripe', 2), ('M12 -2 C40 -24 70 -34 96 -40', 'stripe', 3),
    ('M14 2 C44 -10 72 -14 98 -14', 'stripe', 4), ('M22 8 C46 4 66 4 74 4', 'stripe', 5),
    ('M12 22 C34 28 56 34 70 46', 'band', 6),
    ('M70 50 a7 7 0 1 0 0.1 0', 'eye', 7), ('M70 50 a2.6 2.6 0 1 0 0.1 0', 'eye', 8),
]
TT = {'wing': (0.0, 1.0), 'stripe': (0.8, 0.6), 'band': (1.2, 0.5), 'eye': (1.4, 0.4)}


def butterfly(k, x, y, sc, pal, t0, flap_dur, i):
    """t0 = draw start (s into scene). wings flap forever after drawing."""
    def dr(s, t):
        return f'animation-name:{kf("stroke-dashoffset", 1, 0, k * D + s, t)}'

    def wing():
        return ''.join(
            f'<path class="d {c}" pathLength="1" style="{dr(t0 + TT[c][0] + j*.05, TT[c][1])}" d="{d}"/>'
            for d, c, j in WING)
    ko = kf('opacity', 0, 1, k * D + t0 + 1.7, .5)
    fl = f'class="flap" style="--fd:{flap_dur}s;--fs:{t0 + 2.3:.2f}s"'
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({sc})" style="--w:{pal[0]};--b:{pal[1]};--e:{pal[2]}">'
            f'<g class="bob" style="--bs:{t0 + 2.3:.2f}s;--bd:{2.6 + i*.5:.1f}s">'
            f'<g {fl}>{wing()}</g><g transform="scale(-1 1)"><g {fl}>{wing()}</g></g>'
            f'<path class="d body" pathLength="1" style="{dr(t0+.4, .8)}" d="M0 -24 C-5 -20 -5 -10 0 -6 C5 -10 5 -20 0 -24 Z M0 -6 C-4 10 -4 36 0 54 C4 36 4 10 0 -6"/>'
            f'<path class="d ant" pathLength="1" style="{dr(t0+1.2, .6)}" d="M-2 -24 C-8 -44 -20 -56 -34 -62 M2 -24 C8 -44 20 -56 34 -62"/>'
            f'<circle class="fi antd" style="animation-name:{ko}" cx="-34" cy="-62" r="2.6"/><circle class="fi antd" style="animation-name:{ko}" cx="34" cy="-62" r="2.6"/>'
            '</g></g>')


def build_scene(k, n_bfly):
    R = random.Random(SEED * 100 + k)
    S = Scene(k)
    n = R.randint(15, 19)
    xs = [18 + (W - 36) * (i + .5) / n + R.uniform(-22, 22) for i in range(n)]
    order = list(range(n))
    R.shuffle(order)
    placed = []   # (x, topY, kind) for flowers a butterfly can perch above
    for rank, i in enumerate(order):
        x, d = xs[i], .2 + rank * .2
        i0 = len(S.els)
        kind = R.choice(['cosmos', 'cosmos', 'daisy', 'daisy', 'lupine', 'bud', 'tiny', 'tiny'])
        pal = R.choice([PINKS, PINKS, WARM, COOL, WHITE])
        col = R.choice(pal)
        if kind == 'cosmos':
            sc, y = R.uniform(.38, .9), R.uniform(385, 440)
            cosmos(S, R, x, y, sc, col, d)
            placed.append((x, y - 100 * sc))
        elif kind == 'daisy':
            sc, y = R.uniform(.45, .95), R.uniform(405, 470)
            daisy(S, R, x, y, sc, R.choice(WHITE), d)
            placed.append((x, y - 54 * sc))
        elif kind == 'lupine':
            lupine(S, R, x, R.uniform(320, 390), R.uniform(100, 150), R.choice(COOL), d)
        elif kind == 'bud':
            bud(S, R, x, R.uniform(430, 480), R.uniform(.5, .85), col, d)
        else:
            tiny(S, R, x, R.uniform(440, 505), R.uniform(.8, 1.2), R.choice(WARM + COOL + WHITE), d)
        # every flower sways on its own: own amplitude, speed, phase (pivot = where the stem meets the bottom edge)
        amp = R.uniform(1.2, 3.6) * (-1 if R.random() < .5 else 1)
        dur = R.uniform(2.6, 5.4)
        S.els[i0:] = [f'<g class="sway" style="--sa:{amp:.2f}deg;--sd:{dur:.2f}s;--sl:-{R.uniform(0, dur):.2f}s;'
                      f'transform-origin:{x:.1f}px {H}px">' + ''.join(S.els[i0:]) + '</g>']
    # butterflies perch above distinct flowers
    placed.sort(key=lambda p: R.random())
    chosen = []
    for p in placed:
        if all(abs(p[0] - c[0]) > 170 for c in chosen):
            chosen.append(p)
        if len(chosen) == n_bfly:
            break
    parts = []
    for i, (fx, ftop) in enumerate(chosen):
        bs = R.uniform(.6, .95)
        by = max(125 * bs, ftop - 70 * bs + R.uniform(-30, 5))
        parts.append(butterfly(k, fx, by, bs, BFLY[(i + k) % 3], 4.2 + i * .9, round(R.uniform(1.3, 1.9), 2), i))
    # drifting petals
    for i in range(3):
        sx = R.uniform(300, 700)
        sy = R.uniform(300, 380)
        pd = (f'M{sx:.0f} {sy:.0f} C{sx+80:.0f} {sy-50:.0f} {sx+170:.0f} {sy+20:.0f} {sx+250:.0f} {sy-10:.0f} '
              f'S{sx+360:.0f} {sy+80:.0f} {sx+400:.0f} {sy+170:.0f}')
        parts.append(f'<path class="petal pt" style="offset-path:path(\'{pd}\');--pd:{R.uniform(6,9):.1f}s;--ps:{6 + i*2.4:.1f}s" '
                     f'd="M0 0 C6 -7 15 -5 18 2 C13 9 4 9 0 0 Z"/>')
    return S.els + parts


# ---------- clouds (continuous drift, wrap-around) ----------
def cloud_d(s):
    return (f'M0 0 a{18*s:.1f} {18*s:.1f} 0 0 1 {30*s:.1f} {-6*s:.1f} a{26*s:.1f} {26*s:.1f} 0 0 1 {50*s:.1f} {-12*s:.1f} '
            f'a{22*s:.1f} {22*s:.1f} 0 0 1 {44*s:.1f} {8*s:.1f} a{15*s:.1f} {15*s:.1f} 0 0 1 {8*s:.1f} {10*s:.1f} H0')


RC = random.Random(SEED)
clouds = []
for i in range(5):
    s = RC.uniform(.8, 1.3)
    y = 50 + i * 28 + RC.uniform(-6, 6)
    dur = RC.uniform(55, 90)
    clouds.append(f'<g transform="translate(0 {y:.0f})"><g class="drift" style="--dd:{dur:.0f}s;--dl:-{RC.uniform(0, dur):.0f}s">'
                  f'<path class="d1 cloud" pathLength="1" style="--s:{.3 + i*.3:.1f}s;--t:1.4s" d="{cloud_d(s)}"/></g></g>')

scenes = []
for k in range(3):
    scenes.append(f'<g class="scene sc{k}">' + ''.join(build_scene(k, k + 1)) + '</g>')

def _pc(x):
    return f'{x/T*100:.3f}%'


SCENE_KF = ''
for k in range(3):
    a, b = k * D, (k + 1) * D
    pts = [(0, 0), (a, 0), (a + .4, 1), (b - .8, 1), (b, 0), (T, 0)] if k else [(0, 1), (b - .8, 1), (b, 0), (T, 0)]
    pts = [pt for i, pt in enumerate(pts) if i == 0 or pt[0] > pts[i - 1][0]]
    SCENE_KF += f'@keyframes sc{k}{{' + ''.join(f'{_pc(t)}{{opacity:{v}}}' for t, v in pts) + '}\n'

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>Butterflies &amp; Meadow - laser line art sample</title>
<defs>
<radialGradient id="bg" cx="50%" cy="45%" r="70%"><stop offset="0" stop-color="#14183a"/><stop offset="1" stop-color="#080a1a"/></radialGradient>
<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.d,.d1{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1}}
.d{{animation:{T:.0f}s infinite ease-out}}
.d1{{animation:draw var(--t,1s) ease-out var(--s,0s) forwards}}
.fi{{opacity:0;animation:{T:.0f}s infinite ease-out}}
.sway{{animation:sway var(--sd) ease-in-out var(--sl) infinite}}
.cloud{{stroke:#e8f0ff;stroke-width:1.8}} .stem{{stroke:#3df2c0;stroke-width:2.4}}
.pet{{stroke:#ff6fb5;stroke-width:2.2}} .pet2{{stroke:#ffb3da;stroke-width:1.5}}
.ctr{{stroke:#ffd23f;stroke-width:2.2}} .ctrd{{fill:#ffd23f}}
.wing{{stroke:var(--w);stroke-width:2.6}} .stripe{{stroke:#ffffff;stroke-width:1.9}} .band{{stroke:var(--b);stroke-width:2.8}}
.eye{{stroke:var(--e);stroke-width:2.2}} .body{{stroke:#ffffff;stroke-width:2.4}} .ant{{stroke:#ffffff;stroke-width:1.6}} .antd{{fill:#ffffff}}
.petal{{fill:none;stroke:#ff9fd0;stroke-width:1.8;stroke-linejoin:round}}
.pt{{opacity:0;offset-rotate:auto;animation:fly var(--pd) linear var(--ps) infinite}}
.flap{{animation:flap var(--fd) cubic-bezier(.4,0,.6,1) var(--fs) infinite}}
.bob{{animation:bob var(--bd) ease-in-out var(--bs) infinite}}
.drift{{animation:drift var(--dd) linear var(--dl) infinite}}
.scene{{opacity:0;animation:{T:.0f}s linear infinite}} .sc0{{animation-name:sc0}} .sc1{{animation-name:sc1}} .sc2{{animation-name:sc2}}
@keyframes draw{{to{{stroke-dashoffset:0}}}} @keyframes fade{{to{{opacity:1}}}}
@keyframes flap{{0%,100%{{transform:scaleX(1)}}50%{{transform:scaleX(.22)}}}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-8px)}}}}
@keyframes drift{{from{{transform:translateX(-300px)}}to{{transform:translateX({W+60}px)}}}}
@keyframes fly{{0%{{offset-distance:0%;opacity:0}}10%{{opacity:1}}85%{{opacity:1}}100%{{offset-distance:100%;opacity:0}}}}
@keyframes sway{{0%,100%{{transform:rotate(calc(var(--sa)*-1))}}50%{{transform:rotate(var(--sa))}}}}
{SCENE_KF}
{kf_css()}
</style>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<g filter="url(#glow)">
{''.join(clouds)}
{chr(10).join(scenes)}
</g>
</svg>
'''
if __name__ == '__main__':
    open(OUT, 'w', encoding='utf-8').write(svg)
    print('wrote', os.path.normpath(OUT), len(svg) // 1024, 'KB')
