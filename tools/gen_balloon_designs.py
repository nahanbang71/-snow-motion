#!/usr/bin/env python3
"""Three hot-air-balloon redesigns side by side -> 유럽열기구/balloon_designs.svg"""
import math
import os
import random

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '유럽열기구')
FONT = "font-family=\"'Helvetica Neue', Arial, sans-serif\""
f = lambda v: ('%.1f' % v).rstrip('0').rstrip('.')
CH = ['#35f3ff', '#ffb03a', '#b78bff', '#39ff9c', '#ff4fd8']


def bez(p0, p1, p2, p3, n=30):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


# sleeker pear envelope: round crown, widest high up, tapering to a narrow mouth
R = bez((0, -240), (125, -240), (200, -150), (192, -48)) + bez((192, -48), (184, 34), (84, 92), (36, 142))[1:]
YTOP, YBOT = -240, 142


def xr(y):
    y = min(YBOT, max(YTOP, y))
    for (x0, y0), (x1, y1) in zip(R, R[1:]):
        if y0 <= y <= y1:
            return x0 + (x1 - x0) * ((y - y0) / ((y1 - y0) or 1))
    return R[-1][0]


def poly(pts):
    return 'M' + ' L'.join(f'{f(x)} {f(y)}' for x, y in pts)


def outline():
    return poly(R + [(-x, y) for x, y in reversed(R)]) + ' Z'


def meridian(s):
    return poly([(s * x, y) for x, y in R])


def band(y, bulge=30):
    x = xr(y)
    return f'M{f(-x)} {f(y)} Q0 {f(y + bulge)} {f(x)} {f(y)}'


def gear(color):
    """mouth, ropes, burner frame and basket (shared by all designs)"""
    mouth = f'M-36 142 Q0 154 36 142 M-36 142 L-30 176 M36 142 L30 176 M-30 176 Q0 184 30 176'
    ropes = 'M-30 176 L-34 214 M30 176 L34 214 M-14 180 L-14 214 M14 180 L14 214'
    basket = 'M-38 214 H38 L30 268 H-30 Z M-36 232 H36 M-34 250 H34 M-14 214 V268 M14 214 V268'
    flame = 'M0 196 C-8 186 -3 178 0 166 C3 178 8 186 0 196 Z'
    return mouth, ropes, basket, flame


class Doc:
    def __init__(self):
        self.k = 0
        self.defs = ''

    def path(self, d, color, w=2.6, op=1):
        s = f'<path class="d" pathLength="1" stroke="{color}" stroke-width="{w}" opacity="{op}" style="animation-delay:{self.k * .1:.2f}s" d="{d}"/>'
        self.k += 1
        return s


def balloon(design, phase):
    D = Doc()
    mouth, ropes, basket, flame = gear('')
    g = ''
    if design == 'A':
        main, alt = '#ff4fd8', '#ffd166'
        g += D.path(outline(), main, 3.2)
        for s in (-.55, 0, .55):
            g += D.path(meridian(s), alt, 2.2)
        # chevron band
        zz = []
        n = 12
        for i in range(n + 1):
            s = -1 + 2 * i / n
            y = -52 if i % 2 == 0 else -14
            zz.append((s * xr(y), y))
        g += D.path(poly(zz), main, 2.4)
        g += D.path(band(-118, 26), alt, 2) + D.path(band(34, 22), alt, 2)
        g += D.path('M0 -240 V-262 L22 -254 L0 -246', main, 2.4)          # crown pennant
    elif design == 'B':
        main, alt = '#35f3ff', '#ff4fd8'
        g += D.path(outline(), main, 3.2)
        def lat(c, sign):
            pts = []
            for i in range(41):
                t = 0.1 + 0.82 * i / 40
                y = YTOP + t * (YBOT - YTOP)
                s = c + sign * 2.1 * (t - 0.5)
                if abs(s) <= 1:
                    pts.append((s * xr(y), y))
            return pts
        for c in [x * 0.5 for x in range(-6, 7)]:
            for sign in (1, -1):
                pts = lat(c, sign)
                if len(pts) > 3:
                    g += D.path(poly(pts), alt if sign > 0 else main, 1.8, .9)
        g += D.path(band(-30, 0), main, 2.4)
    else:
        main, alt = '#ffd166', '#ffd166'
        g += D.path(outline(), '#ffd166', 3.2)
        for i, y in enumerate((-176, -112, -50, 12, 76)):
            g += D.path(band(y, 34), CH[i], 3.2)
        for s in (-.5, 0, .5):
            g += D.path(meridian(s), '#8a7a52', 1.6, .8)
    g += D.path(mouth, main, 2.8) + D.path(ropes, '#ffd166', 2.2) + D.path(basket, '#ffd166', 3)
    g += f'<path class="flame" d="{flame}"/>'
    return f'<g class="bob" style="animation-delay:-{phase}s">{g}</g>'


def build():
    rnd = random.Random(5)
    stars = ''.join(f'<circle class="star" cx="{rnd.randint(20, 1900)}" cy="{rnd.randint(30, 860)}" r="{rnd.choice((1, 1.2, 1.6, 2))}" '
                    f'style="animation-duration:{rnd.uniform(3, 7):.1f}s;animation-delay:-{rnd.uniform(0, 6):.1f}s"/>' for _ in range(90))
    cols = [(400, 'A', 'A  CLASSIC', 0), (960, 'B', 'B  DIAMOND', 1.3), (1520, 'C', 'C  CHAPTER STRIPES', 2.6)]
    body = ''.join(f'<g transform="translate({x} 460) scale(1.08)">{balloon(d, ph)}</g>'
                   f'<text class="t" x="{x}" y="900" font-size="28" letter-spacing="12" {FONT}>{label}</text>' for x, d, label, ph in cols)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
<title>Hot-air balloon redesigns</title>
<defs>
<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.d{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;opacity:0;animation:draw 1.4s cubic-bezier(.12,.7,.3,1) both}}
@keyframes draw{{0%{{stroke-dashoffset:1;opacity:0}}1%{{opacity:1}}100%{{stroke-dashoffset:0;opacity:1}}}}
.flame{{fill:none;stroke:#ff9a3c;stroke-width:2.6;stroke-linejoin:round;opacity:0;transform-box:fill-box;transform-origin:50% 100%;animation:fi 1s ease-out 2.6s both,flk 2.4s ease-in-out 3.6s infinite alternate}}
@keyframes fi{{from{{opacity:0}}to{{opacity:1}}}}@keyframes flk{{from{{transform:scale(1,1)}}to{{transform:scale(1.07,1.12)}}}}
.bob{{animation:bob 4s ease-in-out infinite alternate}}@keyframes bob{{from{{transform:translateY(-10px) rotate(-1.2deg)}}to{{transform:translateY(10px) rotate(1.2deg)}}}}
.t{{fill:none;stroke:#8fb0ff;stroke-width:1.5;text-anchor:middle;opacity:0;animation:fi .9s ease-out 3s both}}
.star{{fill:#b9c9ff;opacity:.2;animation:tws 5s ease-in-out infinite alternate}}@keyframes tws{{from{{opacity:.1}}to{{opacity:.7}}}}
</style>
</defs>
<rect width="1920" height="1080" fill="#05060d"/>
<g filter="url(#glow)"><g>{stars}</g>{body}</g>
</svg>
'''


if __name__ == '__main__':
    open(os.path.join(OUT, 'balloon_designs.svg'), 'w', encoding='utf-8').write(build())
    print('ok')
