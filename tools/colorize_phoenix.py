#!/usr/bin/env python3
"""Colourise the twin-phoenix line drawing (patterns/source/phoenix_line.png).

Closed regions between the outlines are found by flood-fill labelling, vectorised with potrace and
filled with an obangsaek-inspired gradient (red head -> gold -> teal -> blue -> violet -> magenta tail).
Outputs patterns/svg/phoenix_neon.svg (dark, glowing) and patterns/svg/phoenix_light.svg (white paper).
"""
import os

import numpy as np
import potrace
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'patterns', 'source', 'phoenix_line.png')
OUT = os.path.join(HERE, '..', 'patterns', 'svg')
N = 1000          # working / viewBox size

STOPS = [(0.06, (255, 56, 96)), (0.22, (255, 150, 40)), (0.36, (255, 225, 74)), (0.52, (61, 242, 192)),
         (0.68, (90, 169, 255)), (0.82, (180, 140, 255)), (0.95, (255, 79, 216))]


def grad(y):
    if y <= STOPS[0][0]:
        return STOPS[0][1]
    for (y0, c0), (y1, c1) in zip(STOPS, STOPS[1:]):
        if y <= y1:
            t = (y - y0) / (y1 - y0)
            return tuple(c0[i] + (c1[i] - c0[i]) * t for i in range(3))
    return STOPS[-1][1]


def hexc(c, mix=0.0):
    return '#%02x%02x%02x' % tuple(int(min(255, v + (255 - v) * mix)) for v in c)


def trace(mask, ox=0, oy=0):
    """potrace a boolean mask -> SVG path data"""
    plist = potrace.Bitmap(~mask).trace(turdsize=2, alphamax=1.0, opticurve=True, opttolerance=0.3)
    d = []
    for curve in plist:
        s = curve.start_point
        d.append(f"M{s.x + ox:.1f} {s.y + oy:.1f}")
        for seg in curve.segments:
            if seg.is_corner:
                d.append(f"L{seg.c.x + ox:.1f} {seg.c.y + oy:.1f}L{seg.end_point.x + ox:.1f} {seg.end_point.y + oy:.1f}")
            else:
                d.append(f"C{seg.c1.x + ox:.1f} {seg.c1.y + oy:.1f} {seg.c2.x + ox:.1f} {seg.c2.y + oy:.1f} "
                         f"{seg.end_point.x + ox:.1f} {seg.end_point.y + oy:.1f}")
        d.append('Z')
    return ''.join(d)


def main():
    g = Image.open(SRC).convert('L').resize((N, N), Image.BICUBIC)
    a = np.array(g)
    line = a < 214
    free = ~ndi.binary_dilation(line, iterations=1)
    lab, n = ndi.label(free)
    bg = lab[0, 0]
    areas = np.bincount(lab.ravel(), minlength=n + 1)
    regions = []
    for i in range(1, n + 1):
        if i == bg or areas[i] < 40:
            continue
        ys, xs = np.nonzero(lab == i)
        regions.append((i, ys.min(), ys.max(), xs.min(), xs.max(), ys.mean() / N, xs.mean() / N, areas[i]))
    print(len(regions), 'regions')
    fills = []
    for (i, y0, y1, x0, x1, cy, cx, area) in regions:
        pad = 3
        y0, x0 = max(0, y0 - pad), max(0, x0 - pad)
        y1, x1 = min(N, y1 + pad + 1), min(N, x1 + pad + 1)
        m = ndi.binary_dilation(lab[y0:y1, x0:x1] == i, iterations=2)   # tuck the fill under the outlines
        if m.sum() < 30:
            continue
        col = grad(cy)
        small = area < 700
        fills.append(dict(d=trace(m, x0, y0), c=hexc(col, .35 if small else 0), cy=cy, cx=cx, small=small))
    ld = trace(line)

    for name, dark in (('phoenix_neon', True), ('phoenix_light', False)):
        o = []
        A = o.append
        bgcol = '<radialGradient id="bg" cx="50%" cy="50%" r="75%"><stop offset="0" stop-color="#14183a"/><stop offset="1" stop-color="#080a1a"/></radialGradient>' \
            if dark else '<linearGradient id="bg"><stop offset="0" stop-color="#fffdf7"/><stop offset="1" stop-color="#fffdf7"/></linearGradient>'
        A(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {N} {N}" width="1000" height="1000">
<title>Twin phoenix - colourised</title>
<defs>{bgcol}
<filter id="glow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.f{{opacity:0;animation:fade .9s ease-out var(--s) forwards}}
.ln{{opacity:0;animation:fade 1.2s ease-out .1s forwards}}
@keyframes fade{{to{{opacity:1}}}}
</style></defs>
<rect width="{N}" height="{N}" fill="url(#bg)"/>
<g{' filter="url(#glow)"' if dark else ''}>''')
        for f in fills:
            dl = .3 + f['cy'] * 3.4 + (0 if not f['small'] else .15)
            op = (.78 if not f['small'] else .95) if dark else (.9 if not f['small'] else .95)
            A(f'<path class="f" style="--s:{dl:.2f}s" fill="{f["c"]}" fill-opacity="{op}" d="{f["d"]}"/>')
        A('</g>')
        line_col = '#fff1c4' if dark else '#3a2a1c'
        A(f'<path class="ln" fill="{line_col}" d="{ld}"/>')
        A('</svg>')
        open(os.path.join(OUT, name + '.svg'), 'w', encoding='utf-8').write('\n'.join(o))


main()
