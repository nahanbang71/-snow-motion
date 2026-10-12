#!/usr/bin/env python3
"""Samtaegeuk (three-part taegeuk) neon line-art sample -> patterns/svg/samtaegeuk.svg"""
import math
import os

R = 108
COLS = ['#ff3860', '#5aa9ff', '#ffe14a']     # red / blue / yellow (obangsaek)
LIGHT = ['#ffb3c1', '#c2e0ff', '#fff4b0']


def pt(r, deg):
    a = math.radians(deg)
    return r * math.cos(a), r * math.sin(a)


def f(v):
    return f"{v:.1f}"


def main():
    o = []
    A = o.append
    A('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
<title>Samtaegeuk - neon line art</title>
<defs>
<radialGradient id="bg" cx="50%" cy="45%" r="70%"><stop offset="0" stop-color="#14183a"/><stop offset="1" stop-color="#080a1a"/></radialGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.d{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;animation:draw var(--t,1s) ease-out var(--s,0s) forwards}
.fi{opacity:0;animation:fade .4s ease-out var(--s,0s) forwards}
.title{font-family:'Poppins','Helvetica Neue',Arial,sans-serif;font-weight:600;fill:none;stroke:#ffd76a;stroke-width:1.6;clip-path:inset(0 100% 0 0);animation:wipe 1.1s ease-out var(--s) forwards}
.sub{font-family:'Poppins','Helvetica Neue',Arial,sans-serif;font-weight:500;fill:#fff1c4;clip-path:inset(0 100% 0 0);animation:wipe 1s ease-out calc(var(--s) + .7s) forwards}
.spin{transform-origin:0 0;animation:spin 24s linear 4s infinite}
.sp{fill:#fff1c4;opacity:0;animation:tw 3s ease-in-out infinite}
@keyframes draw{to{stroke-dashoffset:0}}
@keyframes fade{to{opacity:1}}
@keyframes wipe{to{clip-path:inset(0 0 0 0)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes tw{0%,100%{opacity:0;transform:translateY(0)}50%{opacity:.9;transform:translateY(-14px)}}
</style>
</defs>
<rect width="800" height="600" fill="url(#bg)"/>
<g filter="url(#glow)"><g transform="translate(200 300)">''')
    # outer rings (gold): thin double circle + bead ring (yeonjumun)
    for r, t, dl in ((R + 34, 2.2, .1), (R + 14, 1.8, .3)):
        A(f'<path class="d" pathLength="1" style="--s:{dl}s;--t:{t}s;stroke:#ffd76a;stroke-width:2" '
          f'd="M{-r} 0 a{r} {r} 0 1 0 {2 * r} 0 a{r} {r} 0 1 0 {-2 * r} 0"/>')
    n = 36
    for i in range(n):
        x, y = pt(R + 24, i * 360 / n)
        A(f'<circle class="fi" cx="{f(x)}" cy="{f(y)}" r="3" fill="#fff1c4" style="--s:{.4 + i * .05:.2f}s"/>')
    # rotating core
    A('<g class="spin">')
    for k in range(3):
        a0 = k * 120
        c, l = COLS[k], LIGHT[k]
        x0, y0 = pt(R, a0)
        x1, y1 = pt(R, a0 + 120)
        # outer arc in region colour
        A(f'<path class="d" pathLength="1" style="--s:{1.2 + k * .35:.2f}s;--t:1.2s;stroke:{c};stroke-width:3" '
          f'd="M{f(x0)} {f(y0)} A{R} {R} 0 0 1 {f(x1)} {f(y1)}"/>')
        # swirling boundary: smooth spiral arm from the centre to the rim
        pts = [pt(R * t, a0 - 100 * (1 - t)) for t in [i / 40 for i in range(41)]]
        d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts)
        A(f'<path class="d" pathLength="1" style="--s:{1.6 + k * .35:.2f}s;--t:1.4s;stroke:{c};stroke-width:3" d="{d}"/>')
        # light inner echo of the arm
        pts = [pt(R * t * .93, a0 - 100 * (1 - t) + 9) for t in [.15 + i / 40 * .8 for i in range(41)]]
        d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts)
        A(f'<path class="d" pathLength="1" style="--s:{2.4 + k * .3:.2f}s;--t:1.2s;stroke:{l};stroke-width:1.4" d="{d}"/>')
        # eye (small circle) in the middle of the blade
        ex, ey = pt(R * .6, a0 + 20)
        A(f'<path class="d" pathLength="1" style="--s:{3 + k * .25:.2f}s;--t:.8s;stroke:{c};stroke-width:3" '
          f'd="M{f(ex - 13)} {f(ey)} a13 13 0 1 0 26 0 a13 13 0 1 0 -26 0"/>')
        A(f'<circle class="fi" cx="{f(ex)}" cy="{f(ey)}" r="5" fill="{l}" style="--s:{3.6 + k * .25:.2f}s"/>')
    A('</g></g></g>')
    A('<text class="title" x="364" y="285" font-size="46" style="--s:3.6s">Samtaegeuk</text>')
    A('<text class="sub" x="368" y="328" font-size="19" style="--s:3.6s">Harmony of heaven, earth &amp; humanity</text>')
    for i, (x, y) in enumerate([(90, 90), (380, 150), (60, 470), (400, 500), (330, 60), (120, 560), (430, 330)]):
        A(f'<circle class="sp" cx="{x}" cy="{y}" r="2" style="animation-delay:{i * .5:.1f}s"/>')
    A('</svg>')
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'patterns', 'svg', 'samtaegeuk.svg')
    open(p, 'w', encoding='utf-8').write('\n'.join(o))


main()
