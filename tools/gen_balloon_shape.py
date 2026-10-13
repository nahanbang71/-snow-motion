#!/usr/bin/env python3
"""Hot-air balloon shape sample (neon line art, drifting over a night skyline) -> 유럽열기구/balloon_sample.svg"""
import math
import os
import random

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '유럽열기구')
FONT = "font-family=\"'Helvetica Neue', Arial, sans-serif\""
PINK, GOLD, CYAN, FLAME = '#ff4fd8', '#ffd166', '#35f3ff', '#ff9a3c'
f = lambda v: ('%.1f' % v).rstrip('0').rstrip('.')


def bez(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def balloon():
    R = bez((0, -230), (130, -230), (190, -140), (190, -70)) + bez((190, -70), (190, 10), (90, 80), (40, 130))[1:]
    L = [(-x, y) for x, y in R]
    outline = 'M' + ' L'.join(f'{f(x)} {f(y)}' for x, y in R) + ' L' + ' L'.join(f'{f(x)} {f(y)}' for x, y in reversed(L[:-1])) + ' Z'
    meridians = []
    for s in (-.7, -.38, 0, .38, .7):
        meridians.append('M' + ' L'.join(f'{f(s * x)} {f(y)}' for x, y in R))
    bands = []
    for yb in (-120, -20, 60):                      # curved horizontal bands, bulging downward like seams on a real envelope
        xs = min(R, key=lambda p: abs(p[1] - yb))[0]
        bands.append(f'M{f(-xs)} {yb} Q0 {yb + 34} {f(xs)} {yb}')
    mouth = 'M-40 130 L-30 178 M40 130 L30 178 M-40 130 Q0 142 40 130'
    ropes = 'M-92 62 L-32 190 M92 62 L32 190 M-58 104 L-14 190 M58 104 L14 190'
    basket = 'M-34 190 H34 L28 246 H-28 Z M-32 208 H32 M-30 226 H30'
    flame = 'M0 168 C-9 156 -3 146 0 134 C3 146 9 156 0 168 Z'
    return outline, meridians, bands, mouth, ropes, basket, flame


def skyline():
    rnd = random.Random(8)
    d = 'M0 1010'
    x = 0
    while x < 1920:
        k = rnd.random()
        w = rnd.randint(34, 70)
        if k < .12:      # spire
            d += f' V{1010 - rnd.randint(70, 110)} L{x + w // 2} {1010 - rnd.randint(150, 220)} L{x + w} {1010 - rnd.randint(70, 110)} V1010'
        elif k < .22:    # dome
            h = rnd.randint(60, 90)
            d += f' V{1010 - h} A{w // 2} {w // 2} 0 0 1 {x + w} {1010 - h} V1010'
        else:
            d += f' V{1010 - rnd.randint(30, 100)} H{x + w} V1010'
        x += w
    return d


def build():
    outline, mer, bands, mouth, ropes, basket, flame = balloon()
    rnd = random.Random(5)
    stars = ''.join(f'<circle class="star" cx="{rnd.randint(20, 1900)}" cy="{rnd.randint(30, 760)}" r="{rnd.choice((1, 1.2, 1.6, 2))}" '
                    f'style="animation-duration:{rnd.uniform(3, 7):.1f}s;animation-delay:-{rnd.uniform(0, 6):.1f}s"/>' for _ in range(90))
    k = [0]

    def p(d, cls, w='2.8'):
        s = f'<path class="d {cls}" pathLength="1" stroke-width="{w}" style="animation-delay:{k[0] * .16:.2f}s" d="{d}"/>'
        k[0] += 1
        return s
    body = p(outline, 'pk', '3.2') + ''.join(p(m, 'gd', '2') for m in mer) + ''.join(p(b, 'gd', '2') for b in bands) + p(mouth, 'pk') + p(ropes, 'gd', '2') + p(basket, 'gd', '3')
    bal = body + f'<path class="flame" d="{flame}"/>'     # drawn inline twice: animations inside <use> shadow trees are not seekable
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
<title>Hot-air balloon sample</title>
<defs>
<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.d{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;opacity:0;animation:draw 1.4s cubic-bezier(.12,.7,.3,1) both}}
@keyframes draw{{0%{{stroke-dashoffset:1;opacity:0}}1%{{opacity:1}}100%{{stroke-dashoffset:0;opacity:1}}}}
.pk{{stroke:{PINK}}}.gd{{stroke:{GOLD}}}
.flame{{fill:none;stroke:{FLAME};stroke-width:2.6;stroke-linejoin:round;opacity:0;transform-box:fill-box;transform-origin:50% 100%;animation:fi 1s ease-out 2.4s both,flk 2.4s ease-in-out 3.4s infinite alternate}}
@keyframes fi{{from{{opacity:0}}to{{opacity:1}}}}@keyframes flk{{from{{transform:scale(1,1)}}to{{transform:scale(1.07,1.12)}}}}
.main{{animation:drift 14s linear both}}@keyframes drift{{from{{transform:translate(-200px,0)}}to{{transform:translate(200px,-40px)}}}}
.bob{{animation:bob 4s ease-in-out infinite alternate}}@keyframes bob{{from{{transform:translateY(-12px) rotate(-1.4deg)}}to{{transform:translateY(12px) rotate(1.4deg)}}}}
.far{{animation:drift2 14s linear both;opacity:.55}}@keyframes drift2{{from{{transform:translate(-60px,0)}}to{{transform:translate(60px,-10px)}}}}
.sky{{fill:none;stroke:#3a4f86;stroke-width:2;stroke-linejoin:round;opacity:0;animation:fi 1.6s ease-out both}}
.t{{fill:none;stroke:{CYAN};stroke-width:1.6;text-anchor:middle;opacity:0;animation:fi .9s ease-out 3s both}}
.star{{fill:#b9c9ff;opacity:.2;animation:tws 5s ease-in-out infinite alternate}}@keyframes tws{{from{{opacity:.1}}to{{opacity:.7}}}}
</style>
</defs>
<rect width="1920" height="1080" fill="#05060d"/>
<g filter="url(#glow)">
<g>{stars}</g>
<path class="sky" d="{skyline()}"/>
<g transform="translate(1500 330) scale(.34)"><g class="far">{bal}</g></g>
<g transform="translate(930 470) scale(1.3)"><g class="main"><g class="bob">{bal}</g></g></g>
<text class="t" x="960" y="1060" font-size="26" letter-spacing="14" {FONT}>HOT-AIR BALLOON</text>
</g>
</svg>
'''


if __name__ == '__main__':
    open(os.path.join(OUT, 'balloon_sample.svg'), 'w', encoding='utf-8').write(build())
    print('ok')
