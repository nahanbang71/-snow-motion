#!/usr/bin/env python3
"""Yeonhwamun (lotus-flower pattern): starts as a dot, grows and expands past the screen edges. No text.
-> 한국전통문양/01_식물문/yeonhwa.svg   (1920x1080, 8 s)
"""
import math
import os

DUR = 8.0
S0, S1 = 0.004, 13.0


def pt(r, deg):
    a = math.radians(deg - 90)
    return r * math.cos(a), r * math.sin(a)


def circle(r):
    return f"M{-r} 0 a{r} {r} 0 1 0 {2 * r} 0 a{r} {r} 0 1 0 {-2 * r} 0"


def main():
    stops = ''.join(f"{i * 5}%{{transform:scale({S0 * (S1 / S0) ** ((i / 20) ** .72):.4f})}}" for i in range(21))
    o = []
    A = o.append
    A(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1920" height="1080">
<title>Yeonhwamun - neon line art</title>
<defs>
<radialGradient id="bg" cx="50%" cy="50%" r="75%"><stop offset="0" stop-color="#14183a"/><stop offset="1" stop-color="#080a1a"/></radialGradient>
<filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.l{{fill:none;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}}
.grow{{transform-origin:0 0;animation:grow {DUR}s linear forwards}}
.cw{{transform-origin:0 0;animation:cw {DUR}s linear forwards}}
.ccw{{transform-origin:0 0;animation:ccw {DUR}s linear forwards}}
.seed{{opacity:1;animation:seed 1.6s ease-in forwards}}
@keyframes grow{{{stops}}}
@keyframes cw{{to{{transform:rotate(45deg)}}}}
@keyframes ccw{{to{{transform:rotate(-45deg)}}}}
@keyframes seed{{to{{opacity:0}}}}
</style>
</defs>
<rect width="1600" height="900" fill="url(#bg)"/>
<g filter="url(#glow)"><g transform="translate(800 450)">
<path class="l seed" stroke="#ffd1e6" stroke-width="12" d="M0 0 l0 0"/>
<g class="grow">''')
    # outer gold rings + bead ring (yeonjumun)
    for r in (126, 106):
        A(f'<path class="l" stroke="#ffd76a" stroke-width="3.4" d="{circle(r)}"/>')
    for i in range(32):
        x, y = pt(116, i * 360 / 32)
        A(f'<path class="l" stroke="#fff1c4" stroke-width="7" d="M{x:.1f} {y:.1f} l0 0"/>')
    # small petals between the large ones (violet), turning against the large ones
    A('<g class="cw">')
    for k in range(8):
        A(f'<g transform="rotate({22.5 + k * 45})">'
          '<path class="l" stroke="#b48cff" stroke-width="4.4" d="M0 -40 C-12 -56 -11 -80 0 -98 C11 -80 12 -56 0 -40Z"/>'
          '<path class="l" stroke="#e6d6ff" stroke-width="2.2" d="M0 -52 C-5 -62 -4 -76 0 -86 C4 -76 5 -62 0 -52Z"/></g>')
    # large lotus petals (pink) with a notched tip
    for k in range(8):
        A(f'<g transform="rotate({k * 45})">'
          '<path class="l" stroke="#ff7eb6" stroke-width="4.4" d="M0 -30 C-24 -46 -24 -80 -7 -100 L0 -92 L7 -100 C24 -80 24 -46 0 -30Z"/>'
          '<path class="l" stroke="#ffd1e6" stroke-width="2.2" d="M0 -42 C-12 -54 -12 -74 0 -88 C12 -74 12 -54 0 -42Z"/></g>')
    A('</g>')
    # seed pod (yellow) with seeds
    A(f'<path class="l" stroke="#ffe14a" stroke-width="4.4" d="{circle(27)}"/>')
    A(f'<path class="l" stroke="#fff4b0" stroke-width="2.2" d="{circle(18)}"/>')
    A('<path class="l" stroke="#fff4b0" stroke-width="8" d="M0 0 l0 0"/>')
    for i in range(6):
        x, y = pt(10, i * 60)
        A(f'<path class="l" stroke="#fff4b0" stroke-width="6" d="M{x:.1f} {y:.1f} l0 0"/>')
    A('</g></g></g></svg>')
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '한국전통문양', '01_식물문', 'yeonhwa.svg')
    open(p, 'w', encoding='utf-8').write('\n'.join(o))


main()
