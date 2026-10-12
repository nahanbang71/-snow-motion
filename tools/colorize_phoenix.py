#!/usr/bin/env python3
"""Laser (neon-tube) version of the twin-phoenix line drawing (한국전통문양/_source/bonghwang_line.png).

The centre-lines of the drawing are extracted (skeleton), smoothed and re-drawn as glowing neon strokes
with a vertical obangsaek-style colour gradient (red head -> gold -> teal -> blue -> violet -> magenta tail).
Strokes are drawn on one after another from the top. -> 한국전통문양/02_동물문/bonghwang_laser.svg
"""
import os

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skan import Skeleton
from skimage.morphology import skeletonize

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', '한국전통문양', '_source', 'bonghwang_line.png')
OUT = os.path.join(HERE, '..', '한국전통문양', '02_동물문', 'bonghwang_laser.svg')
N = 1000


def smooth(p, w=7):
    if len(p) < w + 2:
        return p
    k = np.ones(w) / w
    pad = w // 2
    q = np.pad(p, ((pad, pad), (0, 0)), mode='edge')
    s = np.stack([np.convolve(q[:, i], k, mode='valid') for i in range(2)], 1)
    s[0], s[-1] = p[0], p[-1]
    return s


def path_d(p):
    p = smooth(p)
    idx = list(range(0, len(p), 4))
    if idx[-1] != len(p) - 1:
        idx.append(len(p) - 1)
    q = p[idx]
    if len(q) < 3:
        return "M" + " L".join(f"{x:.1f} {y:.1f}" for y, x in q)
    d = f"M{q[0][1]:.1f} {q[0][0]:.1f}"
    for i in range(1, len(q) - 1):
        mx, my = (q[i][1] + q[i + 1][1]) / 2, (q[i][0] + q[i + 1][0]) / 2
        d += f"Q{q[i][1]:.1f} {q[i][0]:.1f} {mx:.1f} {my:.1f}"
    return d + f"L{q[-1][1]:.1f} {q[-1][0]:.1f}"


def main():
    a = np.array(Image.open(SRC).convert('L').resize((N, N), Image.BICUBIC))
    line = ndi.binary_closing(a < 214, iterations=1)
    sk = skeletonize(line)
    S = Skeleton(sk)
    paths = []
    for i in range(S.n_paths):
        c = S.path_coordinates(i)
        if len(c) < 8:
            continue
        paths.append((c[:, 0].min(), len(c), path_d(c)))
    paths.sort(key=lambda t: t[0])
    print(len(paths), 'strokes')
    o = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {N} {N}" width="1000" height="1000">
<title>Twin phoenix - laser</title>
<defs>
<radialGradient id="bg" cx="50%" cy="50%" r="75%"><stop offset="0" stop-color="#14183a"/><stop offset="1" stop-color="#080a1a"/></radialGradient>
<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="0" y1="60" x2="0" y2="950">
<stop offset="0" stop-color="#ff3860"/><stop offset=".2" stop-color="#ff9628"/><stop offset=".36" stop-color="#ffe14a"/>
<stop offset=".52" stop-color="#3df2c0"/><stop offset=".68" stop-color="#5aa9ff"/><stop offset=".82" stop-color="#b48cff"/><stop offset="1" stop-color="#ff4fd8"/></linearGradient>
<linearGradient id="g2" gradientUnits="userSpaceOnUse" x1="0" y1="60" x2="0" y2="950">
<stop offset="0" stop-color="#ffd0da"/><stop offset=".2" stop-color="#ffe0b8"/><stop offset=".36" stop-color="#fff8cc"/>
<stop offset=".52" stop-color="#d4fff0"/><stop offset=".68" stop-color="#d8eaff"/><stop offset=".82" stop-color="#ece0ff"/><stop offset="1" stop-color="#ffd0f4"/></linearGradient>
<filter id="glow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.d{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;animation:draw var(--t) ease-out var(--s) forwards}}
.o{{stroke:url(#g);stroke-width:4.5}}
.c{{stroke:url(#g2);stroke-width:1.5}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
</style></defs>
<rect width="{N}" height="{N}" fill="url(#bg)"/>''']
    glow, core = [], []
    for ymin, ln, d in paths:
        s = .2 + ymin / N * 4.0
        t = min(1.8, max(.5, ln / 260))
        attr = f'pathLength="1" style="--s:{s:.2f}s;--t:{t:.2f}s" d="{d}"'
        glow.append(f'<path class="d o" {attr}/>')
        core.append(f'<path class="d c" {attr}/>')
    o.append('<g filter="url(#glow)">' + ''.join(glow) + '</g>')
    o.append(''.join(core))
    o.append('</svg>')
    open(OUT, 'w', encoding='utf-8').write('\n'.join(o))


main()
