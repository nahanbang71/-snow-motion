#!/usr/bin/env python3
"""Full-screen mosaic intro made of the flower heads from the collection -> flowers/intro.svg"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_flowers as G  # noqa: E402
from flower_shapes import B, SHAPES  # noqa: E402

W, H = 1600, 900
SCALE = {'spike': .3, 'crest': .55, 'anthurium': .62, 'lotus': .5}
DUR = 6.0


def main():
    rnd = random.Random(7)
    pool = [f for f in G.F if f[5] != 'bell']
    rnd.shuffle(pool)
    sx, sy = 112, 100
    cells = []
    for r, y in enumerate(range(-20, H + 60, sy)):
        for x in range(-40 - (r % 2) * (sx // 2), W + 60, sx):
            cells.append((x + rnd.randint(-8, 8), y + rnd.randint(-8, 8)))
    cx, cy = W / 2, H / 2
    maxd = math.hypot(cx, cy)
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="1920" height="1080">
<title>Neon flowers intro</title>
<defs>
<radialGradient id="bg" cx="50%" cy="50%" r="75%"><stop offset="0" stop-color="#14183a"/><stop offset="1" stop-color="#080a1a"/></radialGradient>
<filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.d{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;animation:draw var(--t,.6s) ease-out var(--s,0s) forwards}}
.pet{{stroke:var(--c);stroke-width:2.8}}
.pet2{{stroke:var(--c2);stroke-width:2.2}}
.stem{{stroke:#3df2c0;stroke-width:3}}
.rip{{stroke:#5ad7ff;stroke-width:2.4}}
.fi{{opacity:0;animation:fade .3s ease-out var(--s,0s) forwards}}
.dotc{{fill:var(--c2)}}
.zoom{{transform-origin:800px 450px;animation:zoom {DUR}s ease-in-out forwards}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@keyframes fade{{to{{opacity:1}}}}
@keyframes zoom{{from{{transform:scale(1.0)}}to{{transform:scale(1.07)}}}}
</style>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<g class="zoom"><g filter="url(#glow)">''']
    for i, (x, y) in enumerate(cells):
        slug, en, ko, men, mko, shape, kw, color = pool[i % len(pool)]
        d = math.hypot(x - cx, y - cy) / maxd
        t0 = .15 + d * 3.1 + rnd.random() * .2
        b = B(t0, k=.3)
        meta = SHAPES[shape](b, **kw)
        c, c2 = G.COL[color]
        sc = SCALE.get(shape, .62)
        oy = 0
        if shape == 'lotus':
            oy = 25
        elif shape == 'spike':
            oy = 40
        rot = rnd.randint(-18, 18)
        parts.append(f'<g style="--c:{c};--c2:{c2}" transform="translate({x} {y + oy}) rotate({rot}) scale({sc})">{b.out()}</g>')
    parts.append('</g></g></svg>')
    with open(os.path.join(G.ROOT, 'intro.svg'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(parts))
    print(len(cells), 'flowers in intro')


if __name__ == '__main__':
    main()
