#!/usr/bin/env python3
"""Taegukgi (Korean flag) film, 24 s, white stage: scattered pieces float, then settle one by one into place; the finished flag flutters.
   0- 2     pieces fade in, scattered and drifting; faint guides show where they belong
   2.2-11.5 the two halves of the taeguk, then the 18 trigram bars, glide home one at a time (soft shadows tighten as they land)
  11.5-13   completed: a soft flash, the flag is lifted onto a pole
  13-22     the flag flutters (cloth made of vertical strips with travelling waves and fold shading)
  22-24     fade to white
Official layout: 3:2 white field, taeguk diameter = half the height (red above, blue below, tilted 33.69 deg),
trigrams at the four corners with the bars pointing at the centre: geon top-left, gam top-right, ri bottom-left, gon bottom-right.
usage: python3 tools/gen_taegukgi_intro.py [--out=PATH]   -> flowers/taegukgi_intro.svg
"""
import math
import os
import random
import sys

W, H, T = 960, 540, 24.0
OUT = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--out=')), None) or \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flowers', 'taegukgi_intro.svg')
R = random.Random(21)
FW, FH = 720, 480
CX, CY = 510, 270
FL, FT = CX - FW // 2, CY - FH // 2
TR = FH / 4
TILT = math.degrees(math.atan2(2, 3))
RED, BLUE, INK = '#cd2e3a', '#0047a0', '#111114'
S = FH / 400            # scale vs the 400-high master drawing
BAR_L, BAR_T, GAP = 118 * S, 22 * S, 17 * S
SEG = (BAR_L - 20 * S) / 2


def rot(x, y, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return x * c - y * s, x * s + y * c


def slot(sx, sy, ang, i, part):
    cx, cy = CX + sx * 212 * S, CY + sy * 140 * S
    yy = (i - 1) * (BAR_T + GAP)
    if part is None:
        lx, w = 0, BAR_L
    else:
        lx, w = (-1 if part == 0 else 1) * (SEG / 2 + 10 * S), SEG
    dx, dy = rot(lx, yy, ang)
    return cx + dx, cy + dy, w, BAR_T, ang


GEON, GAM, RI, GON = (-1, -1, TILT), (1, -1, -TILT), (-1, 1, -TILT), (1, 1, TILT)
SLOTS = []
for tri, bars in ((GEON, [None] * 3), (GAM, [(0, 1), None, (0, 1)]), (RI, [None, (0, 1), None]), (GON, [(0, 1)] * 3)):
    for i, b in enumerate(bars):
        for part in ((None,) if b is None else (0, 1)):
            SLOTS.append(slot(*tri, i, part))

# ---------- shapes ----------
r_, r2 = TR, TR / 2
red_d = f'M{-r_} 0 A{r_} {r_} 0 0 1 {r_} 0 A{r2} {r2} 0 0 1 0 0 A{r2} {r2} 0 0 0 {-r_} 0 Z'
blue_d = f'M{r_} 0 A{r_} {r_} 0 0 1 {-r_} 0 A{r2} {r2} 0 0 1 0 0 A{r2} {r2} 0 0 0 {r_} 0 Z'

# ---------- scatter layout ----------
spots = []
tries = 0
while len(spots) < len(SLOTS) + 2 and tries < 4000:
    tries += 1
    x, y = R.uniform(60, 900), R.uniform(50, 490)
    if all(math.hypot(x - a, y - b) > 104 for a, b in spots):
        spots.append((x, y))
R.shuffle(spots)

T0, DT, FD = 2.3, .36, 1.35
pieces, shadows, ghosts, pings = [], [], [], []


def flight_vars(i, sx, sy, k0, sa, ea, dly):
    ax, ay = R.uniform(-80, 80), R.uniform(-110, -30)
    return ax, ay


def add_piece(idx, kind, start, end, delay, color, shape=None):
    sx, sy = start
    ex, ey, ew, eh, ea = end
    k0 = R.uniform(.72, 1.1) if kind == 'bar' else R.uniform(.62, .9)      # farther away = smaller, grows as it comes home
    sa = R.uniform(-140, 140)
    ax, ay = R.uniform(-70, 70), R.uniform(-100, -30)
    dx, dy = R.uniform(-9, 9), R.uniform(-9, 9)
    wait = delay
    if kind == 'bar':
        geom = (f'--sx:{sx:.0f}px;--sy:{sy:.0f}px;--sw:{ew * k0:.1f};--sh:{eh * k0:.1f};--sa:{sa:.0f}deg;--ex:{ex:.1f}px;--ey:{ey:.1f}px;--ew:{ew:.1f};--eh:{eh:.1f};--ea:{ea:.2f}deg')
        body = '<rect x="-.5" y="-.5" width="1" height="1"/>'
        shape_attr = ''
    else:
        geom = (f'--sx:{sx:.0f}px;--sy:{sy:.0f}px;--sw:{k0:.2f};--sh:{k0:.2f};--sa:{sa:.0f}deg;--ex:{ex:.1f}px;--ey:{ey:.1f}px;--ew:1;--eh:1;--ea:{ea:.2f}deg')
        body = f'<path d="{shape}"/>'
    fl = f'--fd:{FD}s;--fl:{delay:.2f}s;--wt:{wait:.2f}s;--ax:{ax:.0f}px;--ay:{ay:.0f}px;--dx:{dx:.1f}px;--dy:{dy:.1f}px;--in:{R.uniform(0, 1.2):.2f}s'
    if kind == 'bar':
        shadows.append(f'<g class="idle" style="{fl}"><g class="arc" style="{fl}"><g class="shw" style="{fl}"><g filter="url(#blur)"><g class="pc" style="{geom};{fl}"><g fill="#000">{body}</g></g></g></g></g></g>')
    else:
        shadows.append(f'<g class="idle" style="{fl}"><g class="arc" style="{fl}"><g class="shw" style="{fl}"><g filter="url(#blur)"><g class="pc" style="{geom};{fl}"><g fill="#000">{body}</g></g></g></g></g></g>')
    pieces.append(f'<g class="idle" style="{fl}"><g class="arc" style="{fl}"><g class="pc" style="{geom};{fl}"><g fill="{color}">{body}</g></g></g></g>')
    land = delay + FD
    if kind == 'bar':
        ghosts.append(f'<g transform="translate({ex:.1f} {ey:.1f}) rotate({ea:.2f}) scale({ew:.1f} {eh:.1f})"><rect class="ghost" style="--gl:{land - .1:.2f}s" x="-.5" y="-.5" width="1" height="1"/></g>')
        pings.append(f'<g transform="translate({ex:.1f} {ey:.1f}) rotate({ea:.2f})"><rect class="ping" style="--gl:{land - .05:.2f}s" x="{-ew / 2:.1f}" y="{-eh / 2:.1f}" width="{ew:.1f}" height="{eh:.1f}"/></g>')


# taeguk halves first
add_piece(0, 'half', spots[0], (CX, CY, 1, 1, -TILT), T0, RED, red_d)
add_piece(1, 'half', spots[1], (CX, CY, 1, 1, -TILT), T0 + .5, BLUE, blue_d)
ghosts.append(f'<circle class="ghost" style="--gl:{T0 + .5 + FD - .1:.2f}s" cx="{CX}" cy="{CY}" r="{TR}"/>')
t = T0 + 2.0
for n, sl in enumerate(SLOTS):
    add_piece(n + 2, 'bar', spots[n + 2], sl, t + n * DT, INK)
T_DONE = t + (len(SLOTS) - 1) * DT + FD          # all home
for k in range(1):
    pass

# ---------- the cloth: the finished flag cut into vertical strips ----------
flag_art = (f'<rect x="{FL}" y="{FT}" width="{FW}" height="{FH}" fill="#ffffff"/>'
            f'<g transform="translate({CX} {CY}) rotate({-TILT:.2f})"><path d="{red_d}" fill="{RED}"/><path d="{blue_d}" fill="{BLUE}"/></g>'
            + ''.join(f'<rect x="{-ew / 2:.1f}" y="{-eh / 2:.1f}" width="{ew:.1f}" height="{eh:.1f}" fill="{INK}" transform="translate({ex:.1f} {ey:.1f}) rotate({ea:.2f})"/>'
                      for ex, ey, ew, eh, ea in SLOTS))
NS = 120
sw_ = FW / NS
clips, strips = [], []
for i in range(NS):
    x0 = FL + i * sw_
    clips.append(f'<clipPath id="sc{i}"><rect x="{x0 - .6:.2f}" y="{FT - 60}" width="{sw_ + 1.2:.2f}" height="{FH + 120}"/></clipPath>')
    amp = .8 + 15 * ((i + 1) / NS) ** 1.15
    amp2 = .4 + 4 * ((i + 1) / NS)
    d1, d2 = -(i * .052), -(i * .085) - .3
    shade_d = d1 - .45
    xc = x0 + sw_ / 2
    slope = math.degrees(math.atan(amp * .0262))
    strips.append(
        f'<g class="w1" style="--a:{amp:.1f}px;--wd:{d1:.3f}s"><g class="w2" style="--a:{amp2:.1f}px;--wd:{d2:.3f}s">'
        f'<g class="ws" style="--sk:{slope:.2f}deg;--wd:{d1 - .525:.3f}s;transform-origin:{xc:.2f}px {CY}px"><g class="shd" style="--wd:{d1 - .525:.3f}s">'
        f'<g clip-path="url(#sc{i})"><use href="#flagart"/></g></g></g></g></g>')

pole = (f'<g class="pole"><rect x="{FL - 12}" y="{FT - 44}" width="8" height="{FH + 150}" rx="3" fill="url(#brass)"/>'
        f'<circle cx="{FL - 8}" cy="{FT - 50}" r="9" fill="url(#brass)"/><rect x="{FL - 14}" y="{FT - 40}" width="12" height="6" rx="2" fill="#b58a35"/></g>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>Taegukgi</title>
<defs>
<radialGradient id="bg" cx="50%" cy="46%" r="75%"><stop offset="0" stop-color="#ffffff"/><stop offset=".7" stop-color="#f6f5f1"/><stop offset="1" stop-color="#e9e7e0"/></radialGradient>
<linearGradient id="brass" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8a6a22"/><stop offset=".4" stop-color="#f1d68a"/><stop offset="1" stop-color="#8a6a22"/></linearGradient>
<radialGradient id="flash"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<filter id="blur" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="9"/></filter>
<filter id="fshadow" x="-20%" y="-20%" width="140%" height="150%"><feGaussianBlur stdDeviation="14"/></filter>
<g id="flagart">{flag_art}</g>
{''.join(clips)}
<style>
@property --k {{ syntax:'&lt;number&gt;'; inherits:true; initial-value:0 }}
.stage{{animation:endfade 24s linear both}}
.idle{{animation:idle var(--wt) ease-in-out both}}
.arc{{animation:arc var(--fd) ease-in-out var(--fl) both}}
.pc{{transform:translate(var(--sx),var(--sy)) rotate(var(--sa)) scale(var(--sw),var(--sh));opacity:0;
  animation:fly var(--fd) cubic-bezier(.3,.05,.15,1) var(--fl) both, fadein 1.2s ease-out var(--in) both}}
.shw{{animation:shw var(--fd) cubic-bezier(.3,.05,.15,1) var(--fl) both}}
.shw .pc{{animation:fly var(--fd) cubic-bezier(.3,.05,.15,1) var(--fl) both, fadeinS 1.2s ease-out var(--in) both}}
.ghost{{fill:none;stroke:#cfcbbd;stroke-width:1.2;vector-effect:non-scaling-stroke;stroke-dasharray:4 4;opacity:0;animation:ghostin 1.2s ease-out .4s forwards, ghostout .6s ease-in var(--gl) forwards}}
.ping{{fill:none;stroke:#8a8576;stroke-width:1.4;opacity:0;transform-box:fill-box;transform-origin:center;animation:ping .9s ease-out var(--gl) both}}
.fld{{fill:none;stroke:#d6d2c6;stroke-width:1.2;stroke-dasharray:6 6;opacity:0;animation:ghostin 1.6s ease-out .2s forwards, ghostout .8s ease-in {T_DONE:.2f}s forwards}}
.assembled{{animation:asm {T_DONE + 1.2:.2f}s linear both}}
.flash{{opacity:0;animation:flash 1.4s ease-out {T_DONE:.2f}s both}}
.field{{opacity:0;animation:fadein 1.4s ease-out {T_DONE - 1.6:.2f}s forwards}}
.cloth{{opacity:0;animation:clothin .01s linear {T_DONE + .8:.2f}s forwards, ramp 3.2s ease-in-out {T_DONE + 1.4:.2f}s both}}
.pole{{opacity:0;animation:fadein .9s ease-out {T_DONE + 1.0:.2f}s forwards}}
.fsh{{opacity:0;animation:fadein 1.2s ease-out {T_DONE - .6:.2f}s forwards}}
.w1{{animation:wave 1.05s ease-in-out var(--wd) infinite alternate}}
.w2{{animation:wave2 1.7s ease-in-out var(--wd) infinite alternate}}
.ws{{animation:slope 1.05s ease-in-out var(--wd) infinite alternate}}
.shd{{animation:shade 1.05s ease-in-out var(--wd) infinite alternate}}
.whiteout{{opacity:0;animation:wo 2s ease-in 22s forwards}}
@keyframes endfade{{0%,100%{{opacity:1}}}}
@keyframes idle{{0%{{transform:translate(0,0)}}30%{{transform:translate(var(--dx),var(--dy))}}65%{{transform:translate(calc(var(--dx)*-.7),calc(var(--dy)*.8))}}100%{{transform:translate(0,0)}}}}
@keyframes fadein{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes fadeinS{{from{{opacity:0}}to{{opacity:.26}}}}
@keyframes fly{{from{{transform:translate(var(--sx),var(--sy)) rotate(var(--sa)) scale(var(--sw),var(--sh))}}to{{transform:translate(var(--ex),var(--ey)) rotate(var(--ea)) scale(var(--ew),var(--eh))}}}}
@keyframes arc{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(var(--ax),var(--ay))}}}}
@keyframes shw{{from{{transform:translate(18px,34px)}}to{{transform:translate(1px,2px)}}}}
@keyframes ghostin{{to{{opacity:1}}}}
@keyframes ghostout{{to{{opacity:0}}}}
@keyframes ping{{0%{{opacity:.8;transform:scale(1)}}100%{{opacity:0;transform:scale(1.5,2.2)}}}}
@keyframes asm{{0%,99.9%{{opacity:1}}100%{{opacity:0}}}}
@keyframes flash{{0%{{opacity:0}}25%{{opacity:.32}}100%{{opacity:0}}}}
@keyframes clothin{{to{{opacity:1}}}}
@keyframes ramp{{from{{--k:0}}to{{--k:1}}}}
@keyframes wave{{from{{transform:translateY(calc(var(--a) * var(--k) * -1))}}to{{transform:translateY(calc(var(--a) * var(--k)))}}}}
@keyframes wave2{{from{{transform:translateY(calc(var(--a) * var(--k) * 1))}}to{{transform:translateY(calc(var(--a) * var(--k) * -1))}}}}
@keyframes slope{{from{{transform:skewY(calc(var(--sk) * var(--k) * -1))}}to{{transform:skewY(calc(var(--sk) * var(--k)))}}}}
@keyframes shade{{from{{filter:brightness(1)}}to{{filter:brightness(calc(1 - .1 * var(--k)))}}}}
@keyframes shade2{{from{{opacity:calc(.12 * var(--k))}}to{{opacity:0}}}}
@keyframes wo{{to{{opacity:1}}}}
</style>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<g class="stage">
<rect class="fld" x="{FL}" y="{FT}" width="{FW}" height="{FH}"/>
{''.join(ghosts)}
<g>{''.join(shadows)}</g>
<g class="fsh"><rect x="{FL + 10}" y="{FT + 26}" width="{FW}" height="{FH}" fill="#000" opacity=".14" filter="url(#fshadow)"/></g>
<rect class="field" x="{FL}" y="{FT}" width="{FW}" height="{FH}" fill="#ffffff"/>
<g class="assembled">{''.join(pieces)}</g>
{''.join(pings)}
<g class="cloth">{pole}<g>{''.join(strips)}</g></g>
<circle class="flash" cx="{CX}" cy="{CY}" r="360" fill="url(#flash)"/>
</g>
<rect class="whiteout" width="{W}" height="{H}" fill="#ffffff"/>
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print('wrote', os.path.normpath(OUT), len(svg) // 1024, 'KB;', len(SLOTS) + 2, 'pieces; home at', round(T_DONE, 1), 's')
