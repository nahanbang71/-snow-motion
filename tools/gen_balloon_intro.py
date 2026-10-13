#!/usr/bin/env python3
"""Balloon C (chapter stripes) floats over the night skyline -> camera pushes into the basket -> balloon POV over Paris
-> descend to the Eiffel Tower -> laser elevation + label.  -> 유럽열기구/eiffel_balloon.svg (17.6 s)"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_balloon_designs as D  # noqa: E402
import gen_balloon_sample as E  # noqa: E402
import gen_balloon_shape as SH  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '유럽열기구')
FONT = E.FONT
GOLD, ACC, BLUE = E.GOLD, E.ACC, E.BLUE
S = 3.6          # seconds into the film when the balloon POV starts
f = E.f


def balloon_c():
    k = [0]

    def p(d, color, w=2.6, op=1):
        s = f'<path class="d" pathLength="1" stroke="{color}" stroke-width="{w}" opacity="{op}" style="animation-delay:{k[0] * .1:.2f}s" d="{d}"/>'
        k[0] += 1
        return s
    mouth, ropes, basket, flame = D.gear('')
    g = p(D.outline(), GOLD, 3.2)
    for i, y in enumerate((-176, -112, -50, 12, 76)):
        g += p(D.band(y, 34), D.CH[i], 3.4)
    for s in (-.5, 0, .5):
        g += p(D.meridian(s), '#8a7a52', 1.6, .8)
    g += p(mouth, GOLD, 2.8) + p(ropes, GOLD, 2.2) + p(basket, GOLD, 3)
    return g + f'<path class="flame" d="{flame}"/>'


def build():
    el = E.elevation()
    ae, foot = E.aerial()
    rnd = random.Random(5)
    stars = ''.join(f'<circle class="star" cx="{rnd.randint(20, 1900)}" cy="{rnd.randint(30, 800)}" r="{rnd.choice((1, 1.2, 1.6, 2))}" '
                    f'style="animation-duration:{rnd.uniform(3, 7):.1f}s;animation-delay:-{rnd.uniform(0, 6):.1f}s"/>' for _ in range(90))
    tw = ''.join(f'<path class="tw" d="M{x - 8} {y}H{x + 8}M{x} {y - 8}V{y + 8}" style="animation-delay:{d + S}s"/>' for x, y, d in
                 ((860, 520, 0), (1065, 470, .9), (905, 380, 1.7), (1020, 600, 2.3), (950, 330, 3.1), (840, 700, 1.3), (1090, 720, 2.8)))
    streets = ''.join(f'<path class="a" d="{d}" style="animation-delay:{S + .1 + i * .012:.2f}s"/>' for i, d in enumerate(ae['streets']))
    river = ''.join(f'<path class="r" d="{d}" style="animation-delay:{S + .05 + i * .15}s"/>' for i, d in enumerate(ae['river']))
    acc = ''.join(f'<path class="g" d="{d}" style="animation-delay:{S + .8 + i * .25}s"/>' for i, d in enumerate(ae['accent']))
    elev = ''.join(f'<path class="e" pathLength="1" style="animation-delay:{S + 7.5 + i * .2:.2f}s" d="{d}"/>' for i, d in enumerate(el))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
<title>Eiffel Tower, balloon intro</title>
<defs>
<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
@keyframes fi{{from{{opacity:0}}to{{opacity:1}}}}@keyframes fo{{from{{opacity:1}}to{{opacity:0}}}}
.d{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;opacity:0;animation:draw 1.4s cubic-bezier(.12,.7,.3,1) both}}
.e{{fill:none;stroke:{GOLD};stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;opacity:0;animation:draw 1.5s cubic-bezier(.12,.7,.3,1) both}}
@keyframes draw{{0%{{stroke-dashoffset:1;opacity:0}}1%{{opacity:1}}100%{{stroke-dashoffset:0;opacity:1}}}}
.flame{{fill:none;stroke:#ff9a3c;stroke-width:2.6;stroke-linejoin:round;opacity:0;transform-box:fill-box;transform-origin:50% 100%;animation:fi 1s ease-out 1.6s both,flk 2.4s ease-in-out 2.6s infinite alternate}}
@keyframes flk{{from{{transform:scale(1,1)}}to{{transform:scale(1.07,1.12)}}}}
.p1{{animation:fo 1s ease-in {S}s both}}
.cam1{{transform-origin:960px 790px;animation:cam1 2.4s cubic-bezier(.5,0,.8,.45) 1.9s both}}@keyframes cam1{{from{{transform:scale(1)}}to{{transform:scale(4.2)}}}}
.bob{{animation:bob 4s ease-in-out infinite alternate}}@keyframes bob{{from{{transform:translateY(-10px) rotate(-1.2deg)}}to{{transform:translateY(10px) rotate(1.2deg)}}}}
.sky{{fill:none;stroke:#3a4f86;stroke-width:2;stroke-linejoin:round;opacity:0;animation:fi 1.4s ease-out both}}
.p2{{opacity:0;animation:fi 1s ease-out {S}s both}}
.a{{fill:none;stroke:{BLUE};stroke-width:1.6;stroke-linecap:round;opacity:0;animation:fi 1.2s ease-out both}}
.r{{fill:none;stroke:#35f3ff;stroke-width:2.4;opacity:0;animation:fi 1.4s ease-out both}}
.g{{fill:none;stroke:#39ff9c;stroke-width:2.4;stroke-linejoin:round;opacity:0;animation:fi 1.4s ease-out both}}
.foot{{fill:none;stroke:{GOLD};stroke-width:3;stroke-linejoin:round;opacity:0;animation:fi 1s ease-out {S + 1.8}s both}}
.drift{{transform-origin:960px 540px;animation:drift 4.6s cubic-bezier(.25,.6,.3,1) {S}s both}}@keyframes drift{{from{{transform:translate(190px,70px) rotate(3.5deg)}}to{{transform:translate(0,0) rotate(0)}}}}
.zoom{{transform-origin:960px 540px;animation:zoom 3.4s cubic-bezier(.55,0,.35,1) {S + 4.4}s both,fo 1.6s ease-in {S + 6.3}s both}}@keyframes zoom{{from{{transform:scale(1)}}to{{transform:scale(9)}}}}
.rim{{fill:none;stroke:{ACC};stroke-width:3;stroke-linecap:round;opacity:0;animation:fi 1s ease-out {S}s both,rimout 1.4s ease-in {S + 4.2}s both,sway 3.4s ease-in-out infinite alternate}}
@keyframes rimout{{from{{opacity:.6}}to{{opacity:0}}}}@keyframes sway{{from{{transform:translateX(-5px) rotate(-.4deg)}}to{{transform:translateX(5px) rotate(.4deg)}}}}
.gl{{fill:none;stroke:{ACC};stroke-width:1.6;stroke-linecap:round;opacity:0;animation:fi 1s ease-out {S + 9.6}s both}}
.t{{fill:none;text-anchor:middle;opacity:0;animation:fi .9s ease-out both}}
.star{{fill:#b9c9ff;opacity:.2;animation:tws 5s ease-in-out infinite alternate}}@keyframes tws{{from{{opacity:.1}}to{{opacity:.7}}}}
.tw{{fill:none;stroke:#fff1c8;stroke-width:1.6;stroke-linecap:round;opacity:0;animation:twk 3.4s ease-in-out {S + 9.6}s infinite}}@keyframes twk{{0%,60%,100%{{opacity:0}}80%{{opacity:.85}}}}
.all{{animation:fo .9s linear {S + 13.1}s both}}
</style>
</defs>
<rect width="1920" height="1080" fill="#05060d"/>
<g filter="url(#glow)" class="all">
<g>{stars}</g>
<g class="p1"><g class="cam1"><path class="sky" d="{SH.skyline()}"/><g transform="translate(960 430) scale(1.5)"><g class="bob">{balloon_c()}</g></g></g></g>
<g class="p2"><g class="drift"><g class="zoom">{streets}{river}{acc}<path class="foot" d="{foot}"/></g></g>
<g class="rim"><path d="M-80 1100 Q960 940 2000 1100"/><path d="M-60 1060 Q960 906 1980 1060" opacity=".45"/><path d="M150 1030 L110 520"/><path d="M1770 1030 L1810 520"/></g>
<g transform="translate(960 880) scale(1.2)">{elev}<path class="gl" d="M-480 0 H480"/></g>
<g transform="translate(960 880) scale(1.2)"><g>{tw}</g></g>
<text class="t" stroke="{GOLD}" stroke-width="1.8" x="960" y="962" font-size="64" letter-spacing="14" {FONT} style="animation-delay:{S + 10}s">EIFFEL TOWER</text>
<text class="t" stroke="{ACC}" stroke-width="1.4" x="960" y="1012" font-size="26" letter-spacing="10" {FONT} style="animation-delay:{S + 10.4}s">PARIS · FRANCE</text></g>
</g>
</svg>
'''


if __name__ == '__main__':
    open(os.path.join(OUT, 'eiffel_balloon.svg'), 'w', encoding='utf-8').write(build())
    print('ok')
