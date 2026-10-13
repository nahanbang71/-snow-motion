#!/usr/bin/env python3
"""European landmark scenes seen from a hot-air balloon: aerial drift -> zoom on the footprint -> laser elevation + label.
14 s each (same timeline as the Eiffel sample).   usage: python3 tools/gen_europe.py [id ...]  -> 유럽열기구/svg/<id>.svg"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import europe_sites as ES  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '유럽열기구', 'svg')
FONT = "font-family=\"'Helvetica Neue', Arial, sans-serif\""
GOLD, ACC, BLUE = '#ffd166', '#ff4fd8', '#4a66b0'


def svg(name, country, aer, foot, elev, scale, sid):
    rnd = random.Random(sum(map(ord, sid)))
    stars = ''.join(f'<circle class="star" cx="{rnd.randint(20, 1900)}" cy="{rnd.randint(30, 700)}" r="{rnd.choice((1, 1.2, 1.6, 2))}" '
                    f'style="animation-duration:{rnd.uniform(3, 7):.1f}s;animation-delay:-{rnd.uniform(0, 6):.1f}s"/>' for _ in range(80))
    tw = ''.join(f'<path class="tw" d="M{x - 8} {y}H{x + 8}M{x} {y - 8}V{y + 8}" style="animation-delay:{d}s"/>' for x, y, d in
                 ((860, 520, 0), (1065, 470, .9), (905, 380, 1.7), (1020, 600, 2.3), (950, 330, 3.1), (840, 700, 1.3), (1090, 720, 2.8)))
    layers = ''
    t0 = [0.0]

    def many(ds, cls, step=.012, base=.1):
        nonlocal layers
        for i, d in enumerate(ds):
            layers += f'<path class="{cls}" d="{d}" style="animation-delay:{base + i * step:.2f}s"/>'
    many(aer['streets'], 'a', .012, .1)
    many(aer['water'], 'r', .15, .05)
    many(aer['green'], 'g', .25, .8)
    many(aer['sec'], 's', .2, 1.2)
    ev = ''.join(f'<path class="d" pathLength="1" style="animation-delay:{7.5 + i * .2:.2f}s" d="{d}"/>' for i, d in enumerate(elev))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
<title>{name}</title>
<defs>
<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.a{{fill:none;stroke:{BLUE};stroke-width:1.6;stroke-linecap:round;opacity:0;animation:fi 1.2s ease-out both}}
.r{{fill:none;stroke:#35f3ff;stroke-width:2.4;opacity:0;animation:fi 1.4s ease-out both}}
.g{{fill:none;stroke:#39ff9c;stroke-width:2.4;stroke-linejoin:round;opacity:0;animation:fi 1.4s ease-out both}}
.s{{fill:none;stroke:#ffb03a;stroke-width:2.4;stroke-linejoin:round;opacity:0;animation:fi 1.4s ease-out both}}
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
.gl{{fill:none;stroke:{ACC};stroke-width:1.6;stroke-linecap:round;opacity:0;animation:fi 1s ease-out 9.6s both}}
.t{{fill:none;text-anchor:middle;opacity:0;animation:fi .9s ease-out both}}
.star{{fill:#b9c9ff;opacity:.2;animation:tws 5s ease-in-out infinite alternate}}@keyframes tws{{from{{opacity:.1}}to{{opacity:.7}}}}
.tw{{fill:none;stroke:#fff1c8;stroke-width:1.6;stroke-linecap:round;opacity:0;animation:twk 3.4s ease-in-out 9.6s infinite}}@keyframes twk{{0%,60%,100%{{opacity:0}}80%{{opacity:.85}}}}
.all{{animation:out .9s linear 13.1s both}}@keyframes out{{from{{opacity:1}}to{{opacity:0}}}}
</style>
</defs>
<rect width="1920" height="1080" fill="#05060d"/>
<g filter="url(#glow)" class="all">
<g>{stars}</g>
<g class="drift"><g class="zoom">{layers}<path class="foot" d="{foot}"/></g></g>
<g class="rim"><path d="M-80 1100 Q960 940 2000 1100"/><path d="M-60 1060 Q960 906 1980 1060" opacity=".45"/><path d="M150 1030 L110 520"/><path d="M1770 1030 L1810 520"/></g>
<g transform="translate(960 880) scale({scale})">{ev}<path class="gl" d="M-480 0 H480"/></g>
<g transform="translate(960 880) scale({scale})"><g>{tw}</g></g>
<text class="t" stroke="{GOLD}" stroke-width="1.8" x="960" y="962" font-size="64" letter-spacing="14" {FONT} style="animation-delay:10s">{name}</text>
<text class="t" stroke="{ACC}" stroke-width="1.4" x="960" y="1012" font-size="26" letter-spacing="10" {FONT} style="animation-delay:10.4s">{country}</text>
</g>
</svg>
'''


def main():
    want = sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    for s in ES.SITES:
        if want and s['id'] not in want:
            continue
        A, elev = s['build']()
        aer, foot = A.result()
        open(os.path.join(OUT, f"{s['id']}.svg"), 'w', encoding='utf-8').write(svg(s['name'], s['country'], aer, foot, elev, s['scale'], s['id']))
        print('wrote', s['id'])


if __name__ == '__main__':
    main()
