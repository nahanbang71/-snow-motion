#!/usr/bin/env python3
"""Hot-air-balloon sample: aerial view of Paris -> descend/zoom to the Eiffel Tower -> laser line-art elevation -> 유럽열기구/eiffel_sample.svg (14 s)"""
import math
import os
import random

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '유럽열기구')
FONT = "font-family=\"'Helvetica Neue', Arial, sans-serif\""
GOLD, ACC, BLUE = '#ffd166', '#ff4fd8', '#4a66b0'
f = lambda v: ('%.1f' % v).rstrip('0').rstrip('.')


def w(y):                      # half-width of the tower at height y
    return 6 + 164 * math.exp(-y / 150)


def elevation():
    P = lambda pts: 'M' + ' L'.join(f'{f(x)} {f(-y)}' for x, y in pts)
    ys = list(range(0, 561, 20))
    outline = P([(-w(y), y) for y in ys] + [(0, 585)] + [(w(y), y) for y in reversed(ys)])
    inner = lambda s: P([(s * (w(y) - 52 * math.exp(-y / 110)), y) for y in range(0, 141, 10)])
    arch = f'M{f(-(w(0) - 52))} 0 C{f(-(w(0) - 52))} -100 {f(w(0) - 52)} -100 {f(w(0) - 52)} 0'
    plat = lambda y, ex: f'M{f(-w(y) - ex)} {-y} H{f(w(y) + ex)} M{f(-w(y) - ex + 4)} {-y - 9} H{f(w(y) + ex - 4)}'
    def braces(y0, y1, n):
        d = ''
        for i in range(n):
            a, b = y0 + (y1 - y0) * i / n, y0 + (y1 - y0) * (i + 1) / n
            d += f'M{f(-w(a))} {f(-a)} L{f(w(b))} {f(-b)} M{f(w(a))} {f(-a)} L{f(-w(b))} {f(-b)} '
        return d
    cabin = f'M{f(-w(400) - 6)} -400 V-420 H{f(w(400) + 6)} V-400 M{f(-w(400))} -420 L-6 -438 H6 L{f(w(400))} -420'
    spire = 'M0 -438 V-585 M-5 -480 H5 M-4 -520 H4'
    return [outline, inner(-1), inner(1), arch, plat(130, 12), plat(285, 8), braces(140, 285, 4), braces(285, 400, 3), cabin, spire, braces(0, 130, 0) or 'M0 0']


def aerial():
    rnd = random.Random(21)
    out = {'streets': [], 'river': [], 'accent': []}
    # Haussmann-ish blocks: short lines at two angles around the tower
    for _ in range(70):
        cx, cy = rnd.uniform(-100, 2020), rnd.uniform(-60, 1140)
        a = math.radians(rnd.choice((38, 128, 38, 128, 83)))
        L = rnd.uniform(70, 230)
        out['streets'].append(f'M{f(cx - L * math.cos(a) / 2)} {f(cy - L * math.sin(a) / 2)} l{f(L * math.cos(a))} {f(L * math.sin(a))}')
    # Etoile: ring + 12 avenues
    ex, ey = 330, 130
    out['accent'].append(f'M{ex - 46} {ey} a46 46 0 1 0 92 0 a46 46 0 1 0 -92 0')
    for k in range(12):
        a = math.radians(k * 30 + 15)
        out['streets'].append(f'M{f(ex + 46 * math.cos(a))} {f(ey + 46 * math.sin(a))} l{f(900 * math.cos(a))} {f(900 * math.sin(a))}')
    # Seine, two banks
    for off in (-14, 14):
        out['river'].append(f'M-300 {360 + off} C200 {500 + off} 560 {330 + off} 900 {380 + off} C1200 {425 + off} 1500 {660 + off} 2300 {600 + off}')
    # Champ de Mars: rectangle along the axis from the tower
    ux, uy = 130 / math.hypot(130, 150), 150 / math.hypot(130, 150)
    vx, vy = -uy, ux
    c = (960 + ux * 190, 540 + uy * 190)
    corners = [(c[0] + sx * ux * 190 + sy * vx * 52, c[1] + sx * uy * 190 + sy * vy * 52) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    out['accent'].append('M' + ' L'.join(f'{f(x)} {f(y)}' for x, y in corners) + ' Z')
    # tower footprint (square on the axis) + X
    s = 34
    fp = [(960 + sx * ux * s + sy * vx * s, 540 + sx * uy * s + sy * vy * s) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    foot = 'M' + ' L'.join(f'{f(x)} {f(y)}' for x, y in fp) + f' Z M{f(fp[0][0])} {f(fp[0][1])} L{f(fp[2][0])} {f(fp[2][1])} M{f(fp[1][0])} {f(fp[1][1])} L{f(fp[3][0])} {f(fp[3][1])}'
    return out, foot


def build():
    el = elevation()
    ae, foot = aerial()
    rnd = random.Random(5)
    stars = ''.join(f'<circle class="star" cx="{rnd.randint(20, 1900)}" cy="{rnd.randint(30, 700)}" r="{rnd.choice((1, 1.2, 1.6, 2))}" '
                    f'style="animation-duration:{rnd.uniform(3, 7):.1f}s;animation-delay:-{rnd.uniform(0, 6):.1f}s"/>' for _ in range(80))
    tw = ''.join(f'<path class="tw" d="M{x - 8} {y}H{x + 8}M{x} {y - 8}V{y + 8}" style="animation-delay:{d}s"/>' for x, y, d in
                 ((860, 520, 0), (1065, 470, .9), (905, 380, 1.7), (1020, 600, 2.3), (950, 330, 3.1), (840, 700, 1.3), (1090, 720, 2.8)))
    street_els = ''.join(f'<path class="a" d="{d}" style="animation-delay:{.1 + i * .012:.2f}s"/>' for i, d in enumerate(ae['streets']))
    river = ''.join(f'<path class="r" d="{d}" style="animation-delay:{.05 + i * .15}s"/>' for i, d in enumerate(ae['river']))
    acc = ''.join(f'<path class="g" d="{d}" style="animation-delay:{.8 + i * .25}s"/>' for i, d in enumerate(ae['accent']))
    elev = ''.join(f'<path class="d" pathLength="1" style="animation-delay:{6.7 + i * .22:.2f}s" d="{d}"/>' for i, d in enumerate(el))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
<title>Eiffel Tower hot-air-balloon sample</title>
<defs>
<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.a{{fill:none;stroke:{BLUE};stroke-width:1.6;stroke-linecap:round;opacity:0;animation:fi 1.2s ease-out both}}
.r{{fill:none;stroke:#35f3ff;stroke-width:2.4;opacity:0;animation:fi 1.4s ease-out both}}
.g{{fill:none;stroke:#39ff9c;stroke-width:2.4;stroke-linejoin:round;opacity:0;animation:fi 1.4s ease-out both}}
.foot{{fill:none;stroke:{GOLD};stroke-width:3;stroke-linejoin:round;opacity:0;animation:fi 1s ease-out 1.8s both}}
@keyframes fi{{from{{opacity:0}}to{{opacity:1}}}}
.drift{{transform-origin:960px 540px;animation:drift 4.6s cubic-bezier(.25,.6,.3,1) both}}
@keyframes drift{{from{{transform:translate(190px,70px) rotate(3.5deg)}}to{{transform:translate(0,0) rotate(0)}}}}
.zoom{{transform-origin:960px 540px;animation:zoom 3.4s cubic-bezier(.55,0,.35,1) 4.4s both,wideout 1.6s ease-in 6.3s both}}
@keyframes zoom{{from{{transform:scale(1)}}to{{transform:scale(9)}}}}
@keyframes wideout{{from{{opacity:1}}to{{opacity:0}}}}
.rim{{fill:none;stroke:{ACC};stroke-width:3;stroke-linecap:round;opacity:.6;animation:fi 1s ease-out both,rimout 1.4s ease-in 4.2s both,sway 3.4s ease-in-out infinite alternate}}
@keyframes rimout{{from{{opacity:.6}}to{{opacity:0}}}}
@keyframes sway{{from{{transform:translateX(-5px) rotate(-.4deg)}}to{{transform:translateX(5px) rotate(.4deg)}}}}
.d{{fill:none;stroke:{GOLD};stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;opacity:0;animation:draw 1.5s cubic-bezier(.12,.7,.3,1) both}}
@keyframes draw{{0%{{stroke-dashoffset:1;opacity:0}}1%{{opacity:1}}100%{{stroke-dashoffset:0;opacity:1}}}}
.gl{{fill:none;stroke:{ACC};stroke-width:1.6;stroke-linecap:round;opacity:0;animation:fi 1s ease-out 9.2s both}}
.t{{fill:none;text-anchor:middle;opacity:0;animation:fi .9s ease-out both}}
.star{{fill:#b9c9ff;opacity:.2;animation:tws 5s ease-in-out infinite alternate}}@keyframes tws{{from{{opacity:.1}}to{{opacity:.7}}}}
.tw{{fill:none;stroke:#fff1c8;stroke-width:1.6;stroke-linecap:round;opacity:0;animation:twk 3.4s ease-in-out 8.6s infinite}}@keyframes twk{{0%,60%,100%{{opacity:0}}80%{{opacity:.85}}}}
.all{{animation:out .9s linear 13.1s both}}@keyframes out{{from{{opacity:1}}to{{opacity:0}}}}
</style>
</defs>
<rect width="1920" height="1080" fill="#05060d"/>
<g filter="url(#glow)" class="all">
<g>{stars}</g>
<g class="drift"><g class="zoom">{street_els}{river}{acc}<path class="foot" d="{foot}"/></g></g>
<g class="rim"><path d="M-80 1100 Q960 940 2000 1100"/><path d="M-60 1060 Q960 906 1980 1060" opacity=".45"/><path d="M150 1030 L110 520"/><path d="M1770 1030 L1810 520"/></g>
<g transform="translate(960 880) scale(1.2)">{elev}<path class="gl" d="M-480 0 H480"/></g>
<g transform="translate(960 880) scale(1.2)"><g>{tw}</g></g>
<text class="t" stroke="{GOLD}" stroke-width="1.8" x="960" y="962" font-size="64" letter-spacing="14" {FONT} style="animation-delay:9s">EIFFEL TOWER</text>
<text class="t" stroke="{ACC}" stroke-width="1.4" x="960" y="1012" font-size="26" letter-spacing="10" {FONT} style="animation-delay:9.4s">PARIS · FRANCE</text>
</g>
</svg>
'''


if __name__ == '__main__':
    open(os.path.join(OUT, 'eiffel_sample.svg'), 'w', encoding='utf-8').write(build())
    print('ok')
