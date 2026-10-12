#!/usr/bin/env python3
"""Samtaegeuk intro: starts as a dot at the centre, grows and expands past the screen edges.
No text. -> patterns/svg/samtaegeuk.svg   (1920x1080, 8 s)
"""
import math
import os

R = 108
DUR = 8.0
S0, S1 = 0.004, 13.0           # start (a dot) / end scale (far outside the frame)
COLS = ['#ff3860', '#5aa9ff', '#ffe14a']     # red / blue / yellow (obangsaek)
LIGHT = ['#ffb3c1', '#c2e0ff', '#fff4b0']


def pt(r, deg):
    a = math.radians(deg)
    return r * math.cos(a), r * math.sin(a)


def f(v):
    return f"{v:.1f}"


def poly(pts):
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts)


def main():
    stops = []
    for i in range(0, 21):
        p = i / 20
        stops.append(f"{p * 100:.0f}%{{transform:scale({S0 * (S1 / S0) ** (p ** 0.72):.4f})}}")
    o = []
    A = o.append
    A(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1920" height="1080">
<title>Samtaegeuk - neon line art</title>
<defs>
<radialGradient id="bg" cx="50%" cy="50%" r="75%"><stop offset="0" stop-color="#14183a"/><stop offset="1" stop-color="#080a1a"/></radialGradient>
<filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.l{{fill:none;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}}
.grow{{transform-origin:0 0;animation:grow {DUR}s linear forwards}}
.spin{{transform-origin:0 0;animation:spin {DUR}s linear forwards}}
.seed{{opacity:1;animation:seed 1.6s ease-in forwards}}
@keyframes grow{{{''.join(stops)}}}
@keyframes spin{{to{{transform:rotate(240deg)}}}}
@keyframes seed{{to{{opacity:0}}}}
</style>
</defs>
<rect width="1600" height="900" fill="url(#bg)"/>
<g filter="url(#glow)"><g transform="translate(800 450)">
<path class="l seed" stroke="#fff1c4" stroke-width="12" d="M0 0 l0 0"/>
<g class="grow">''')
    # gold outer rings + bead ring (yeonjumun)
    for r, w in ((R + 34, 2.4), (R + 14, 2)):
        A(f'<path class="l" stroke="#ffd76a" stroke-width="{w + 1}" d="M{-r} 0 a{r} {r} 0 1 0 {2 * r} 0 a{r} {r} 0 1 0 {-2 * r} 0"/>')
    n = 36
    for i in range(n):
        x, y = pt(R + 24, i * 360 / n)
        A(f'<path class="l" stroke="#fff1c4" stroke-width="7" d="M{f(x)} {f(y)} l0 0"/>')
    A('<g class="spin">')
    for k in range(3):
        a0 = k * 120
        c, l = COLS[k], LIGHT[k]
        x0, y0 = pt(R, a0)
        x1, y1 = pt(R, a0 + 120)
        A(f'<path class="l" stroke="{c}" stroke-width="4.4" d="M{f(x0)} {f(y0)} A{R} {R} 0 0 1 {f(x1)} {f(y1)}"/>')
        A(f'<path class="l" stroke="{c}" stroke-width="4.4" d="{poly([pt(R * t, a0 - 100 * (1 - t)) for t in [i / 40 for i in range(41)]])}"/>')
        A(f'<path class="l" stroke="{l}" stroke-width="2.2" d="{poly([pt(R * t * .93, a0 - 100 * (1 - t) + 9) for t in [.15 + i / 40 * .8 for i in range(41)]])}"/>')
        ex, ey = pt(R * .6, a0 + 20)
        A(f'<path class="l" stroke="{c}" stroke-width="4.4" d="M{f(ex - 13)} {f(ey)} a13 13 0 1 0 26 0 a13 13 0 1 0 -26 0"/>')
        A(f'<path class="l" stroke="{l}" stroke-width="9" d="M{f(ex)} {f(ey)} l0 0"/>')
    A('</g></g></g></g></svg>')
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'patterns', 'svg', 'samtaegeuk.svg')
    open(p, 'w', encoding='utf-8').write('\n'.join(o))


main()
