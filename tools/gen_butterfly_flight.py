#!/usr/bin/env python3
"""Laser-style sample: swallowtails flying left -> right over a swaying flower strip, clouds drifting.
usage: python3 tools/gen_butterfly_flight.py [seed]   -> flowers/butterfly_flight.svg
Butterflies are seen from above (head toward travel direction); they follow gently wavy paths,
each with its own size / speed / wing-beat rate / colour, and loop forever.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_butterfly_meadow as m  # noqa: E402

W, H = m.W, m.H
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 3
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flowers', 'butterfly_flight.svg')
R = random.Random(SEED)


class Once(m.Scene):
    """draw-on once, then stay"""
    def path(self, d, cls, s, t, col=None):
        c = f';stroke:{col}' if col else ''
        self.els.append(f'<path class="d1 {cls}" pathLength="1" style="--s:{s:.2f}s;--t:{t:.2f}s{c}" d="{d}"/>')

    def dot(self, x, y, r, cls, s, col=None):
        c = f';fill:{col}' if col else ''
        self.els.append(f'<circle class="fi1 {cls}" style="--s:{s:.2f}s{c}" cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>')


# ---------- flower strip along the bottom ----------
S = Once(0)
n = 20
xs = [10 + (W - 20) * (i + .5) / n + R.uniform(-18, 18) for i in range(n)]
order = list(range(n))
R.shuffle(order)
for rank, i in enumerate(order):
    x, d = xs[i], .2 + rank * .15
    i0 = len(S.els)
    kind = R.choice(['cosmos', 'daisy', 'daisy', 'lupine', 'bud', 'tiny', 'tiny'])
    col = R.choice(R.choice([m.PINKS, m.PINKS, m.WARM, m.COOL, m.WHITE]))
    if kind == 'cosmos':
        m.cosmos(S, R, x, R.uniform(440, 480), R.uniform(.35, .6), col, d)
    elif kind == 'daisy':
        m.daisy(S, R, x, R.uniform(450, 490), R.uniform(.4, .65), R.choice(m.WHITE), d)
    elif kind == 'lupine':
        m.lupine(S, R, x, R.uniform(385, 430), R.uniform(85, 115), R.choice(m.COOL), d)
    elif kind == 'bud':
        m.bud(S, R, x, R.uniform(460, 490), R.uniform(.5, .8), col, d)
    else:
        m.tiny(S, R, x, R.uniform(470, 510), R.uniform(.8, 1.2), R.choice(m.WARM + m.COOL + m.WHITE), d)
    amp = R.uniform(1.2, 3.6) * (-1 if R.random() < .5 else 1)
    dur = R.uniform(2.6, 5.4)
    S.els[i0:] = [f'<g class="sway" style="--sa:{amp:.2f}deg;--sd:{dur:.2f}s;--sl:-{R.uniform(0, dur):.2f}s;'
                  f'transform-origin:{x:.1f}px {H}px">' + ''.join(S.els[i0:]) + '</g>']

# ---------- flying butterflies ----------
WING = ''.join(f'<path class="{c}" d="{d}"/>' for d, c, _ in m.WING)
BODY = ('<path class="body" d="M0 -24 C-5 -20 -5 -10 0 -6 C5 -10 5 -20 0 -24 Z M0 -6 C-4 10 -4 36 0 54 C4 36 4 10 0 -6"/>'
        '<path class="ant" d="M-2 -24 C-8 -44 -20 -56 -34 -62 M2 -24 C8 -44 20 -56 34 -62"/>')


def flyer(i, n):
    sc = R.uniform(.3, .85)
    y0 = R.uniform(90, 330)
    amp = R.uniform(25, 70)
    pts = [(-120, y0)]
    for k in range(1, 5):
        pts.append((-120 + k * (W + 240) / 4, y0 + R.uniform(-amp, amp)))
    d = f'M{pts[0][0]} {pts[0][1]:.0f}'
    for k in range(1, 5):
        (x0, y_0), (x1, y1) = pts[k - 1], pts[k]
        d += f' C{x0+(x1-x0)*.5:.0f} {y_0:.0f} {x0+(x1-x0)*.5:.0f} {y1:.0f} {x1:.0f} {y1:.0f}'
    dur = R.uniform(11, 20) / (.6 + sc)
    delay = -dur * i / n - R.uniform(0, 2)
    pal = m.BFLY[i % 3]
    return (f'<g class="fly" style="offset-path:path(\'{d}\');--fdur:{dur:.1f}s;--fdel:{delay:.1f}s">'
            f'<g transform="scale({sc:.2f})" style="--w:{pal[0]};--b:{pal[1]};--e:{pal[2]}">'
            f'<g class="beat" style="--bd:{R.uniform(.45, .8):.2f}s;--bl:-{R.uniform(0, .5):.2f}s">'
            f'<g class="flap">{WING}</g><g transform="scale(-1 1)"><g class="flap">{WING}</g></g>{BODY}</g></g></g>')


NB = 7
flyers = [flyer(i, NB) for i in range(NB)]

clouds = []
for i in range(5):
    s = R.uniform(.8, 1.3)
    y = 45 + i * 24 + R.uniform(-6, 6)
    dur = R.uniform(55, 90)
    clouds.append(f'<g transform="translate(0 {y:.0f})"><g class="drift" style="--dd:{dur:.0f}s;--dl:-{R.uniform(0, dur):.0f}s">'
                  f'<path class="d1 cloud" pathLength="1" style="--s:{.3 + i*.3:.1f}s;--t:1.4s" d="{m.cloud_d(s)}"/></g></g>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>Butterflies in flight - laser line art sample</title>
<defs>
<radialGradient id="bg" cx="50%" cy="45%" r="70%"><stop offset="0" stop-color="#14183a"/><stop offset="1" stop-color="#080a1a"/></radialGradient>
<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.d1{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;animation:draw var(--t,1s) ease-out var(--s,0s) forwards}}
.fi1{{opacity:0;animation:fade .5s ease-out var(--s,0s) forwards}}
.cloud{{stroke:#e8f0ff;stroke-width:1.8}} .stem{{stroke:#3df2c0;stroke-width:2.4}}
.pet{{stroke:#ff6fb5;stroke-width:2.2}} .pet2{{stroke:#ffb3da;stroke-width:1.5}}
.ctr{{stroke:#ffd23f;stroke-width:2.2}} .ctrd{{fill:#ffd23f}}
.wing,.stripe,.band,.eye,.body,.ant{{fill:none;stroke-linecap:round;stroke-linejoin:round}}
.wing{{stroke:var(--w);stroke-width:3}} .stripe{{stroke:#ffffff;stroke-width:2.2}} .band{{stroke:var(--b);stroke-width:3.2}}
.eye{{stroke:var(--e);stroke-width:2.6}} .body{{stroke:#ffffff;stroke-width:2.8}} .ant{{stroke:#ffffff;stroke-width:1.8}}
.fly{{offset-rotate:auto 90deg;animation:fly var(--fdur) linear var(--fdel) infinite}}
.flap{{animation:flap var(--bd) ease-in-out var(--bl) infinite}}
.beat{{display:inline}}
.sway{{animation:sway var(--sd) ease-in-out var(--sl) infinite}}
.drift{{animation:drift var(--dd) linear var(--dl) infinite}}
@keyframes draw{{to{{stroke-dashoffset:0}}}} @keyframes fade{{to{{opacity:1}}}}
@keyframes fly{{from{{offset-distance:0%}}to{{offset-distance:100%}}}}
@keyframes flap{{0%,100%{{transform:scaleX(1)}}50%{{transform:scaleX(.2)}}}}
@keyframes sway{{0%,100%{{transform:rotate(calc(var(--sa)*-1))}}50%{{transform:rotate(var(--sa))}}}}
@keyframes drift{{from{{transform:translateX(-300px)}}to{{transform:translateX({W+60}px)}}}}
</style>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<g filter="url(#glow)">
{''.join(clouds)}
{''.join(S.els)}
{''.join(flyers)}
</g>
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print('wrote', os.path.normpath(OUT), len(svg) // 1024, 'KB')
