#!/usr/bin/env python3
"""Taegukgi (Korean flag) intro, 16 s one-shot, neon line-art style to lead into the lantern festival film.
  0- 3  red and blue points swirl in from every side and gather into the taeguk (halftone-dot look), spinning into place
  3- 6  the solid glow fills in under the dots; the flag outline is drawn
  5- 9  the four trigrams light up one by one: geon (heaven), gon (earth), gam (water), ri (fire)
  8-12  small sky lanterns rise around the flag, the taeguk pulses
 11-16  the camera pushes into the taeguk, the frame dissolves, everything fades to the night the lantern film starts from
Proportions follow the flag: 3:2 field, taeguk diameter = half the height, trigrams at the four corners, bars pointing at the centre.
usage: python3 tools/gen_taegukgi_intro.py [--out=PATH]   -> flowers/taegukgi_intro.svg
"""
import math
import os
import random
import sys

W, H = 960, 540
OUT = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--out=')), None) or \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flowers', 'taegukgi_intro.svg')
R = random.Random(14)
CX, CY = 480, 270
FW, FH = 600, 400                 # flag field, 3:2
TR = FH / 4                       # taeguk radius = 100 (diameter = half the height)
TILT = math.degrees(math.atan2(2, 3))   # 33.69 degrees
RED, BLUE = '#ff3d55', '#2d6bff'
CREAM = '#fff1d0'


def in_red(x, y):
    """is a point of the (untilted) taeguk red? top half minus the small left half-disc, plus the small right half-disc below"""
    r2 = TR / 2
    if y < 0:
        return math.hypot(x + r2, y) > r2
    return math.hypot(x - r2, y) <= r2


# ---- the taeguk: filled halves (exact arcs) + halftone dots ----
r, r2 = TR, TR / 2
red_d = f'M{-r} 0 A{r} {r} 0 0 1 {r} 0 A{r2} {r2} 0 0 1 0 0 A{r2} {r2} 0 0 0 {-r} 0 Z'
blue_d = f'M{r} 0 A{r} {r} 0 0 1 {-r} 0 A{r2} {r2} 0 0 1 0 0 A{r2} {r2} 0 0 0 {r} 0 Z'
dots = []
sp = 5.2
n = 0
y = -r + sp / 2
while y < r:
    x = -r + sp / 2 + (sp / 2 if int((y + r) / sp) % 2 else 0)
    while x < r:
        d = math.hypot(x, y)
        if d < r - 1.5:
            red = in_red(x, y)
            rad = 2.15 * (1 - .45 * (d / r) ** 2)
            ang = math.atan2(y, x)
            delay = .25 + 2.2 * ((ang + math.pi) / (2 * math.pi)) * .8 + R.uniform(0, .5)
            sa = R.uniform(0, 2 * math.pi)
            sd = R.uniform(260, 620)
            dots.append(f'<circle class="dot" style="--sx:{sd*math.cos(sa):.0f}px;--sy:{sd*math.sin(sa):.0f}px;--dd:{delay:.2f}s;--dl:{R.uniform(1.6, 2.4):.2f}s;fill:{RED if red else BLUE}" '
                        f'cx="{x:.1f}" cy="{y:.1f}" r="{rad:.2f}"/>')
            n += 1
        x += sp
    y += sp * .866

# halftone fringe: dots thinning out beyond the rim (more on the lower-left / upper-right like the reference artwork)
fr = []
y = -r - 30
while y < r + 30:
    x = -r - 30 + (sp / 2 if int((y + r + 30) / sp) % 2 else 0)
    while x < r + 30:
        d = math.hypot(x, y)
        if r - 1.5 <= d < r + 26:
            t = (d - r) / 26
            lean = 0.5 + 0.5 * math.sin(math.atan2(y, x) * 2 - 1.1)      # stronger on two opposite sides
            keep = (1 - t) ** 1.3 * (0.35 + 0.65 * lean)
            if R.random() < keep:
                fr.append(f'<circle class="fringe" style="--fd:{4.0 + R.uniform(0, 1.2):.2f}s;--fo:{0.9 - .5 * t:.2f};fill:{RED if in_red(x, y) else BLUE}" '
                          f'cx="{x:.1f}" cy="{y:.1f}" r="{max(.45, 2.0 * (1 - t)):.2f}"/>')
        x += sp
    y += sp * .866

# ---- trigrams (geon, gon, gam, ri): bars point at the centre ----
BAR_L, BAR_T, GAP = 118, 15, 12
SOLID, BROKEN = 'S', 'B'
TRI = [('geon', (-1, -1), TILT, [SOLID, SOLID, SOLID], 5.4),      # top-left
       ('gon', (1, 1), TILT, [BROKEN, BROKEN, BROKEN], 6.4),       # bottom-right
       ('gam', (1, -1), -TILT, [BROKEN, SOLID, BROKEN], 7.4),      # top-right
       ('ri', (-1, 1), -TILT, [SOLID, BROKEN, SOLID], 8.4)]        # bottom-left
tri_svg = []
for name, (sx, sy), ang, bars, t0 in TRI:
    cx, cy = CX + sx * 212, CY + sy * 140
    parts = []
    for i, kind in enumerate(bars):
        yy = (i - 1) * (BAR_T + GAP)
        if kind == SOLID:
            segs = [(-BAR_L / 2, BAR_L)]
        else:
            seg = (BAR_L - 22) / 2
            segs = [(-BAR_L / 2, seg), (BAR_L / 2 - seg, seg)]
        for xx, ww in segs:
            parts.append(f'<rect class="bar" style="--bd:{t0 + i * .22:.2f}s" x="{xx:.1f}" y="{yy - BAR_T / 2:.1f}" width="{ww:.1f}" height="{BAR_T}" rx="1.5"/>')
    tri_svg.append(f'<g transform="translate({cx:.0f} {cy:.0f}) rotate({ang:.2f})"><g class="trig" style="--td:{t0:.2f}s">{"".join(parts)}</g></g>')

# ---- sky lanterns rising around the flag ----
def lantern_path(S):
    return (f'M{-.9*S:.1f} {-1.2*S:.1f} C{-1.25*S:.1f} {-.3*S:.1f} {-1.0*S:.1f} {.7*S:.1f} {-.55*S:.1f} {1.25*S:.1f} L{.55*S:.1f} {1.25*S:.1f} '
            f'C{1.0*S:.1f} {.7*S:.1f} {1.25*S:.1f} {-.3*S:.1f} {.9*S:.1f} {-1.2*S:.1f} Z M{-.9*S:.1f} {-1.2*S:.1f} Q0 {-1.5*S:.1f} {.9*S:.1f} {-1.2*S:.1f} M0 {-1.35*S:.1f} L0 {1.2*S:.1f}')


lan = []
LCOL = ['#ff9a3d', '#ffd45a', '#ff5a4a', '#ff7fb0', '#59d6c0', '#6aa8ff']
for i in range(34):
    S = R.uniform(4, 10)
    x = R.choice([R.uniform(20, 170), R.uniform(790, 940), R.uniform(20, 940)])
    col = R.choice(LCOL)
    t0 = 7 + R.uniform(0, 4)
    dur = R.uniform(6, 9)
    lan.append(f'<g class="rise" style="--rt:{t0:.1f}s;--rd:{dur:.1f}s;--rx:{R.uniform(-40, 40):.0f}px"><g transform="translate({x:.0f} 560)">'
               f'<circle r="{S*2.8:.1f}" fill="url(#lh)" style="stroke:none;color:{col}"/><path class="lan" style="color:{col}" d="{lantern_path(S)}"/>'
               f'<circle cy="{S*1.2:.1f}" r="{max(.9, S*.2):.1f}" fill="#fff4c8"/></g></g>')
spark = []
for i in range(70):
    s = R.uniform(2.5, 7)
    spark.append(f'<g transform="translate({R.uniform(0, 960):.0f} {R.uniform(0, 540):.0f})"><path class="spk" style="--td:{R.uniform(1.6, 3.6):.1f}s;--tl:-{R.uniform(0, 4):.1f}s;'
                 f'fill:{R.choice(["#fff3c8", "#ffd27a", "#ffc0dc", "#cfe0ff"])}" d="M0 {-s:.1f} Q0 0 {s:.1f} 0 Q0 0 0 {s:.1f} Q0 0 {-s:.1f} 0 Q0 0 0 {-s:.1f} Z"/></g>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>Taegukgi intro</title>
<defs>
<radialGradient id="bg" cx="50%" cy="50%" r="75%"><stop offset="0" stop-color="#1a1230"/><stop offset=".6" stop-color="#0a0818"/><stop offset="1" stop-color="#03030a"/></radialGradient>
<radialGradient id="lh"><stop offset="0" stop-color="currentColor" stop-opacity=".5"/><stop offset="1" stop-color="currentColor" stop-opacity="0"/></radialGradient>
<radialGradient id="bloom"><stop offset="0" stop-color="#fff1d0" stop-opacity=".9"/><stop offset=".35" stop-color="#ff9a6a" stop-opacity=".4"/><stop offset="1" stop-color="#6a3a8a" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="2.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.world{{transform-origin:{CX}px {CY}px;animation:push 16s cubic-bezier(.45,0,.75,.55) both}}
.fade{{animation:endfade 16s linear both}}
.dot{{opacity:0;transform-box:fill-box;transform-origin:center;animation:dotin var(--dl) cubic-bezier(.2,.7,.2,1) var(--dd) both}}
.spinin{{animation:spinin 4.6s cubic-bezier(.15,.8,.2,1) .25s both}}
.fillr,.fillb{{opacity:0;animation:fillin 2.6s ease-out 2.8s forwards}}
.fringe{{opacity:0;animation:fringe 2s ease-out var(--fd) both}}
.pulse{{animation:pulse 3s ease-in-out 6s infinite}}
.flag{{fill:#ffffff;fill-opacity:.04;stroke:#e6ecff;stroke-width:2;stroke-dasharray:1;stroke-dashoffset:1;animation:drawf 2.4s ease-in-out 3.6s forwards, fadef 2.6s ease-in 10.6s forwards}}
.trig{{animation:fadef 2.6s ease-in 10.6s both}}
.bar{{fill:{CREAM};fill-opacity:.28;stroke:{CREAM};stroke-width:2;transform-box:fill-box;transform-origin:center;opacity:0;animation:barin .7s cubic-bezier(.2,.8,.2,1) var(--bd) both}}
.rise{{opacity:0;animation:rise var(--rd) ease-in var(--rt) both}}
.lan{{fill:currentColor;fill-opacity:.3;stroke:currentColor;stroke-width:1.2}}
.spk{{stroke:none;opacity:0;transform-box:fill-box;transform-origin:center;animation:spk var(--td) ease-in-out var(--tl) infinite}}
.bloomc{{opacity:0;animation:bloomin 4s ease-in 11s both}}
@keyframes dotin{{from{{opacity:0;transform:translate(var(--sx),var(--sy)) scale(.3)}}to{{opacity:1;transform:translate(0,0) scale(1)}}}}
@keyframes spinin{{from{{transform:rotate(560deg)}}to{{transform:rotate(0deg)}}}}
@keyframes fillin{{to{{opacity:.62}}}}
@keyframes fringe{{from{{opacity:0;transform:scale(.6)}}to{{opacity:var(--fo);transform:scale(1)}}}}
@keyframes pulse{{0%,100%{{filter:brightness(1)}}50%{{filter:brightness(1.35)}}}}
@keyframes drawf{{to{{stroke-dashoffset:0}}}}
@keyframes fadef{{to{{opacity:0}}}}
@keyframes barin{{0%{{opacity:0;transform:scaleX(0)}}60%{{opacity:1;transform:scaleX(1.06)}}100%{{opacity:1;transform:scaleX(1)}}}}
@keyframes rise{{0%{{opacity:0;transform:translate(0,0)}}12%{{opacity:1}}85%{{opacity:1}}100%{{opacity:0;transform:translate(var(--rx),-640px)}}}}
@keyframes spk{{0%,100%{{opacity:0;transform:scale(.2) rotate(0deg)}}50%{{opacity:1;transform:scale(1) rotate(45deg)}}}}
@keyframes push{{0%,60%{{transform:scale(1)}}100%{{transform:scale(4.6)}}}}
@keyframes bloomin{{to{{opacity:.85}}}}
@keyframes endfade{{0%,88%{{opacity:1}}100%{{opacity:0}}}}
</style>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<g class="fade">
{''.join(spark)}
<g class="world">
<g filter="url(#glow)">
<rect class="flag" pathLength="1" x="{CX - FW // 2}" y="{CY - FH // 2}" width="{FW}" height="{FH}"/>
<g transform="translate({CX} {CY}) rotate({-TILT:.2f})"><g class="spinin"><g class="pulse">
<path class="fillr" d="{red_d}" fill="{RED}"/><path class="fillb" d="{blue_d}" fill="{BLUE}"/>
{''.join(dots)}{''.join(fr)}
</g></g></g>
{''.join(tri_svg)}
{''.join(lan)}
</g>
</g>
<circle class="bloomc" cx="{CX}" cy="{CY}" r="520" fill="url(#bloom)"/>
</g>
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print('wrote', os.path.normpath(OUT), len(svg) // 1024, 'KB,', n, 'dots')
