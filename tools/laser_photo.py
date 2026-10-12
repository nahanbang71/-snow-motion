#!/usr/bin/env python3
"""Laser treatment of a flower photo: lasers run along the petal veins (extracted from the photo itself).
usage: python3 tools/laser_photo.py <photo> <out_dir>
"""
import base64
import io
import os
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
from skan import Skeleton
from skimage.morphology import skeletonize, remove_small_objects

src, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
im = Image.open(src).convert('RGB')
W, H = im.size
a = np.asarray(im).astype(np.float32)
white = a.min(axis=2)                       # veins are the whitest thing on the petal
ridge = ndi.gaussian_filter(white, 1.5) - ndi.gaussian_filter(white, 9)
mask = ridge > 9
mask &= ndi.gaussian_filter(a[..., 0], 2) > 150     # stay on the pink petals (not the green background)
mask = remove_small_objects(mask, 120)
sk = skeletonize(mask)
S = Skeleton(sk)
paths = []
for i in range(S.n_paths):
    c = S.path_coordinates(i)
    if len(c) < 45:
        continue
    k = np.ones(9) / 9
    q = np.pad(c, ((4, 4), (0, 0)), mode='edge')
    c = np.stack([np.convolve(q[:, j], k, mode='valid') for j in range(2)], 1)
    idx = list(range(0, len(c), 6)) + [len(c) - 1]
    p = c[idx]
    d = f"M{p[0][1]:.0f} {p[0][0]:.0f}" + ''.join(
        f"Q{p[j][1]:.0f} {p[j][0]:.0f} {(p[j][1] + p[j + 1][1]) / 2:.0f} {(p[j][0] + p[j + 1][0]) / 2:.0f}" for j in range(1, len(p) - 1)
    ) + f"L{p[-1][1]:.0f} {p[-1][0]:.0f}"
    paths.append((len(c), d))
print(len(paths), 'laser lines')

buf = io.BytesIO()
im.save(buf, 'JPEG', quality=84)
b64 = base64.b64encode(buf.getvalue()).decode()

COLS = ['#ff2bd6', '#00e5ff', '#ffffff', '#7dff6a', '#ffd23f']
o = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>Flower photo - laser</title>
<defs>
<filter id="dim"><feColorMatrix type="matrix" values=".4 0 0 0 0  0 .4 0 0 0  0 0 .42 0 0  0 0 0 1 0"/></filter>
<filter id="glow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.beam{{fill:none;stroke-linecap:round;stroke-dasharray:.13 .87;stroke-dashoffset:.13;opacity:0;animation:run var(--t) linear var(--s) infinite}}
.trace{{fill:none;stroke-linecap:round;stroke-dasharray:1;stroke-dashoffset:1;animation:draw 2.4s ease-out var(--s) forwards}}
@keyframes run{{0%{{stroke-dashoffset:.13;opacity:1}}100%{{stroke-dashoffset:-.87;opacity:1}}}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
</style></defs>
<image href="data:image/jpeg;base64,{b64}" width="{W}" height="{H}" filter="url(#dim)"/>
<g filter="url(#glow)" style="mix-blend-mode:screen">''']
for n, (ln, d) in enumerate(sorted(paths, key=lambda t: -t[0])):
    col = COLS[n % len(COLS)]
    s = .1 + (n % 9) * .12
    t = 1.6 + (n % 5) * .35
    attr = f'pathLength="1" d="{d}"'
    o.append(f'<path class="trace" stroke="{col}" stroke-width="2.6" stroke-opacity=".8" style="--s:{s:.2f}s" {attr}/>')
    o.append(f'<path class="beam" stroke="{col}" stroke-width="11" style="--s:{s + 2.4:.2f}s;--t:{t:.2f}s" {attr}/>')
    o.append(f'<path class="beam" stroke="#fff" stroke-width="3.6" style="--s:{s + 2.4:.2f}s;--t:{t:.2f}s" {attr}/>')
o.append('</g></svg>')
open(os.path.join(out_dir, 'flower_laser_veins.svg'), 'w').write('\n'.join(o))
