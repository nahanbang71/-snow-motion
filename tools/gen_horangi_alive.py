#!/usr/bin/env python3
"""Tiger (horangi) with 'alive' motion: grows from a dot, holds while breathing / blinking / twitching, then flies out.
-> 한국전통문양/02_동물문/horangi_alive.svg   (12 s, 1920x1080)
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'kp'))
from core import *  # noqa: E402,F403

DUR = 12.0


def scale_at(t):
    if t <= 3:
        return S0 * (3.9 / S0) ** ((t / 3) ** .72)
    if t <= 9:
        return 3.9 + (t - 3) / 6 * .3
    return 4.2 * (S1 * 1.2 / 4.2) ** (((t - 9) / 3) ** 1.5)


def tiger():
    O, R, G_, Y, W, P_ = ORANGE, RED, GOLD, YELLOW, WHITE, PINK
    def half(side):
        s = ''
        s += P("M0 -52 C-34 -54 -60 -34 -60 -2 C-60 30 -36 52 0 52", O[0], 4.4)
        s += '<g class="ear">' + P("M-36 -40 C-48 -58 -64 -52 -62 -34", O[0], 4) + P("M-40 -40 C-48 -50 -56 -48 -57 -38", O[1], 1.6) + '</g>'
        s += '<g class="stripe">' + P("M-60 -6 L-42 -2 L-58 2Z", R[0], 2.6) + P("M-58 12 L-42 14 L-54 20Z", R[0], 2.6) + P("M-52 28 L-38 28 L-46 34Z", R[0], 2.6) \
            + P("M-24 -48 L-18 -34 L-28 -36Z", R[0], 2.6) + P("M-40 -34 L-34 -22 L-44 -24Z", R[0], 2.6) + '</g>'
        s += '<g class="eye">' + P("M-30 -16 C-26 -26 -12 -26 -8 -16 C-12 -8 -26 -8 -30 -16Z", G_[0], 3.4) + DOT(-19, -16, R[0], 9) \
            + '<g class="pupil">' + DOT(-19, -16, W[1], 3.4) + '</g></g>'
        s += P("M-34 -28 C-24 -34 -12 -34 -6 -28", O[1], 2.4)
        s += '<g class="jaw">' + P("M0 14 C-8 10 -18 12 -22 20 C-26 30 -12 36 0 32", W[0], 3.2) + P("M0 26 C-4 34 -10 38 -16 36", O[1], 2.4) + '</g>'
        s += '<g class="whisk">' + P("M-12 22 L-32 19 M-12 26 L-32 28 M-12 18 L-30 11", W[1], 1.8) + '</g>'
        return s
    face = half(0) + G("scale(-1 1)", half(1))
    face += P("M-9 6 L9 6 L0 16Z", P_[0], 3.4) + P("M0 16 L0 26", W[1], 2.4)
    face += '<g class="mark">' + ''.join(P(d, Y[0], 3.4) for d in ("M-14 -42 L14 -42", "M-9 -34 L9 -34", "M-13 -26 L13 -26", "M0 -42 L0 -26")) + '</g>'
    return G("scale(1.2)", '<g class="face">' + face + '</g>')


def build():
    stops = ''.join(f"{t / DUR * 100:.2f}%{{transform:scale({scale_at(t):.4f})}}" for t in [i * .25 for i in range(int(DUR / .25) + 1)])
    rnd = random.Random(5)
    flies = ''
    for i in range(16):
        a = rnd.uniform(0, 360)
        r = rnd.uniform(66, 98)
        x, y = pt(r, a)
        flies += f'<circle class="fly" cx="{f(x)}" cy="{f(y)}" r="1.6" style="animation-delay:{rnd.uniform(0, 3):.2f}s;animation-duration:{rnd.uniform(2.2, 4):.2f}s"/>'
    inner = (frame() + P(circle(92), GOLD[0], 1.4).replace('class="l"', 'class="l aura"') + tiger() + flies)
    import re
    inner = re.sub(r'stroke-width="([\d.]+)"', lambda m: f'stroke-width="{float(m.group(1)) * 1.9:.1f}"', inner)
    style = f'''.l{{fill:none;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}}
.grow{{transform-origin:0 0;animation:grow {DUR}s linear forwards}}
.seed{{opacity:1;animation:seed 1.6s ease-in forwards}}
.face,.eye,.ear,.whisk,.jaw,.mark,.pupil,.stripe{{transform-box:fill-box;transform-origin:center}}
.face{{animation:breathe 3.4s ease-in-out infinite;transform-origin:50% 100%}}
.eye{{animation:blink 4.6s infinite}}
.pupil{{animation:slit 3s ease-in-out infinite}}
.ear{{transform-origin:100% 100%;animation:ear 5.3s infinite}}
.whisk{{transform-origin:100% 50%;animation:whisk 3.4s ease-in-out infinite alternate}}
.jaw{{animation:jaw 3.4s ease-in-out infinite}}
.mark,.stripe{{animation:glow 2.2s ease-in-out infinite alternate}}
.aura{{animation:aura 3.4s ease-in-out infinite}}
.fly{{fill:#fff1c4;opacity:0;animation:twinkle 3s ease-in-out infinite}}
@keyframes grow{{{stops}}}
@keyframes seed{{to{{opacity:0}}}}
@keyframes breathe{{0%,100%{{transform:scale(1,1)}}50%{{transform:scale(1.018,1.03)}}}}
@keyframes blink{{0%,90%,100%{{transform:scaleY(1)}}93%{{transform:scaleY(.08)}}96%{{transform:scaleY(1)}}}}
@keyframes slit{{0%,100%{{transform:scaleX(1)}}50%{{transform:scaleX(.45)}}}}
@keyframes ear{{0%,58%,70%,100%{{transform:rotate(0)}}62%{{transform:rotate(-8deg)}}66%{{transform:rotate(2deg)}}}}
@keyframes whisk{{from{{transform:rotate(-3deg)}}to{{transform:rotate(3deg)}}}}
@keyframes jaw{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(1.2px)}}}}
@keyframes glow{{from{{opacity:.55}}to{{opacity:1}}}}
@keyframes aura{{0%,100%{{opacity:.15}}50%{{opacity:.7}}}}
@keyframes twinkle{{0%,100%{{opacity:0;transform:translateY(0)}}50%{{opacity:.95;transform:translateY(-5px)}}}}'''
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1920" height="1080"><title>Tiger - alive</title>'
           f'<defs>{DEFS_COMMON}<filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="5" result="b"/>'
           '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
           f'<style>{style}</style></defs><rect width="1600" height="900" fill="url(#bg)"/>'
           '<g filter="url(#glow)"><g transform="translate(800 450)"><path class="l seed" stroke="#ffd1e6" stroke-width="12" d="M0 0 l0 0"/>'
           f'<g class="grow">{inner}</g></g></g></svg>')
    out = os.path.join(HERE, '..', '한국전통문양', '02_동물문', 'horangi_alive.svg')
    open(out, 'w', encoding='utf-8').write(svg)


build()
