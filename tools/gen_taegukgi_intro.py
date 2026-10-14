#!/usr/bin/env python3
"""Taegukgi - cinematic version, 32 s, high-key white stage.
   0- 2     white-out clears; haze, dust in slanted window light, big out-of-focus fragments sweep past the lens
   2- 8     scattered pieces drift at different depths; rack focus pulls them sharp as they head home
   6.5-9.5  the two halves of the taeguk orbit each other in slow motion and lock
  10-17.4   the 18 trigram bars snap in with an accelerating beat; a pause before the last one
  17.4-19   the last bar slams home: shock ring, flash, camera shake
  19-22     the camera cranes back, light sweeps the flag and a lens flare blooms; the flag lifts onto a pole
  22-30     slow-motion flutter with gusts, drifting camera, bokeh crossing the lens
  30-32     slow push-in, fade to white
Official layout: 3:2 white field, taeguk diameter = half the height (red above, blue below, tilted 33.69 deg),
trigrams at the four corners, bars pointing at the centre: geon top-left, gam top-right, ri bottom-left, gon bottom-right.
usage: python3 tools/gen_taegukgi_intro.py [--out=PATH]   -> flowers/taegukgi_intro.svg
"""
import math
import os
import random
import sys

W, H, T = 960, 540, 32.0
OUT = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--out=')), None) or \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flowers', 'taegukgi_intro.svg')
R = random.Random(33)
FW, FH = 720, 480
CX, CY = 510, 270
FL, FT = CX - FW // 2, CY - FH // 2
TR = FH / 4
TILT = math.degrees(math.atan2(2, 3))
RED, BLUE, INK = '#cd2e3a', '#0047a0', '#111114'
S = FH / 400
BAR_L, BAR_T, GAP = 118 * S, 22 * S, 17 * S
SEG = (BAR_L - 20 * S) / 2
KFS = []


def kfs(points):
    out, last = [], -1
    for t, p in points:
        t = max(min(t, T), last + 0.002)
        out.append((t, p))
        last = t
    if out[-1][0] < T:
        out.append((T, out[-1][1]))
    KFS.append('@keyframes z%d{%s}' % (len(KFS), ''.join(f'{t/T*100:.4f}%{{{p}}}' for t, p in out)))
    return f'z{len(KFS)-1}'


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

r_, r2 = TR, TR / 2
red_d = f'M{-r_} 0 A{r_} {r_} 0 0 1 {r_} 0 A{r2} {r2} 0 0 1 0 0 A{r2} {r2} 0 0 0 {-r_} 0 Z'
blue_d = f'M{r_} 0 A{r_} {r_} 0 0 1 {-r_} 0 A{r2} {r2} 0 0 1 0 0 A{r2} {r2} 0 0 0 {r_} 0 Z'

# ---------- timing: an accelerating beat, a held breath before the last bar ----------
GAPS = [.72, .64, .57, .5, .46, .42, .38, .35, .32, .3, .28, .26, .25, .24, .23, .22, .22]
LAND = [10.4]
for g in GAPS:
    LAND.append(LAND[-1] + g)
LAND[-1] = 17.5            # the last bar waits: a beat of silence, then the slam
T_DONE = LAND[-1] + .1

# ---------- scatter ----------
spots, tries = [], 0
while len(spots) < len(SLOTS) + 2 and tries < 6000:
    tries += 1
    x, y = R.uniform(50, 910), R.uniform(40, 500)
    if all(math.hypot(x - a, y - b) > 100 for a, b in spots):
        spots.append((x, y))
R.shuffle(spots)

pieces, shadows, ghosts, pings, bursts = [], [], [], [], []


def add_piece(kind, start, end, land, fd, color, shape=None, big_arc=False):
    sx, sy = start
    ex, ey, ew, eh, ea = end
    k0 = R.uniform(.62, 1.05) if kind == 'bar' else R.uniform(.55, .8)
    sa = R.uniform(-160, 160)
    spin = 0 if kind == 'bar' else R.choice([-1, 1]) * 360      # whole turns only, so the halves arrive exactly aligned
    ax, ay = (R.uniform(-160, 160), R.uniform(-190, -80)) if big_arc else (R.uniform(-70, 70), R.uniform(-110, -30))
    dx, dy = R.uniform(-9, 9), R.uniform(-9, 9)
    delay = land - fd
    b0 = R.uniform(3, 9)
    if kind == 'bar':
        geom = f'--sx:{sx:.0f}px;--sy:{sy:.0f}px;--sw:{ew * k0:.1f};--sh:{eh * k0:.1f};--sa:{sa:.0f}deg;--ex:{ex:.1f}px;--ey:{ey:.1f}px;--ew:{ew:.1f};--eh:{eh:.1f};--ea:{ea:.2f}deg'
        body = '<rect x="-.5" y="-.5" width="1" height="1"/>'
    else:
        geom = f'--sx:{sx:.0f}px;--sy:{sy:.0f}px;--sw:{k0:.2f};--sh:{k0:.2f};--sa:{sa:.0f}deg;--ex:{ex:.1f}px;--ey:{ey:.1f}px;--ew:1;--eh:1;--ea:{ea + spin:.2f}deg'
        body = f'<path d="{shape}"/>'
    fl = (f'--fd:{fd}s;--fl:{delay:.2f}s;--wt:{delay:.2f}s;--ax:{ax:.0f}px;--ay:{ay:.0f}px;--dx:{dx:.1f}px;--dy:{dy:.1f}px;'
          f'--in:{R.uniform(.6, 2.2):.2f}s;--b0:{b0:.1f}px;--ld:{land:.2f}s')
    shadows.append(f'<g class="idle" style="{fl}"><g class="arc" style="{fl}"><g class="shw" style="{fl}"><g class="focus" style="{fl}"><g filter="url(#blur)"><g class="pc sh" style="{geom};{fl}"><g fill="#000">{body}</g></g></g></g></g></g></g>')
    pieces.append(f'<g class="settle" style="transform-origin:{ex:.1f}px {ey:.1f}px;--ld:{land:.2f}s"><g class="idle" style="{fl}"><g class="arc" style="{fl}"><g class="focus" style="{fl}">'
                  f'<g class="pc" style="{geom};{fl}"><g fill="{color}">{body}</g></g></g></g></g></g>')
    if kind == 'bar':
        ghosts.append(f'<g transform="translate({ex:.1f} {ey:.1f}) rotate({ea:.2f}) scale({ew:.1f} {eh:.1f})"><rect class="ghost" style="--gl:{land - .15:.2f}s" x="-.5" y="-.5" width="1" height="1"/></g>')
        pings.append(f'<g transform="translate({ex:.1f} {ey:.1f}) rotate({ea:.2f})"><rect class="ping" style="--gl:{land:.2f}s" x="{-ew / 2:.1f}" y="{-eh / 2:.1f}" width="{ew:.1f}" height="{eh:.1f}"/></g>')
        for _ in range(7):
            an = R.uniform(0, 6.28)
            mg = R.uniform(24, 78)
            bursts.append(f'<circle class="burst" style="--gl:{land:.2f}s;--bx:{mg * math.cos(an):.0f}px;--by:{mg * math.sin(an):.0f}px" cx="{ex:.1f}" cy="{ey:.1f}" r="{R.uniform(1, 2.3):.1f}"/>')


add_piece('half', spots[0], (CX, CY, 1, 1, -TILT), 8.6, 3.4, RED, red_d, True)
add_piece('half', spots[1], (CX, CY, 1, 1, -TILT), 9.4, 3.4, BLUE, blue_d, True)
ghosts.append(f'<circle class="ghost" style="--gl:8.9s" cx="{CX}" cy="{CY}" r="{TR}"/>')
for n, sl in enumerate(SLOTS):
    add_piece('bar', spots[n + 2], sl, LAND[n], 1.9 if n < 17 else 2.4, INK)

# ---------- the cloth (vertical strips) ----------
flag_art = (f'<rect x="{FL}" y="{FT}" width="{FW}" height="{FH}" fill="#ffffff"/>'
            f'<g transform="translate({CX} {CY}) rotate({-TILT:.2f})"><path d="{red_d}" fill="{RED}"/><path d="{blue_d}" fill="{BLUE}"/></g>'
            + ''.join(f'<rect x="{-ew / 2:.1f}" y="{-eh / 2:.1f}" width="{ew:.1f}" height="{eh:.1f}" fill="{INK}" transform="translate({ex:.1f} {ey:.1f}) rotate({ea:.2f})"/>' for ex, ey, ew, eh, ea in SLOTS))
NS = 190
sw_ = FW / NS
clips, strips = [], []
for i in range(NS):
    x0 = FL + i * sw_
    clips.append(f'<clipPath id="sc{i}"><rect x="{x0 - .6:.2f}" y="{FT - 80}" width="{sw_ + 1.2:.2f}" height="{FH + 160}"/></clipPath>')
    fr = (i + 1) / NS
    amp, amp2 = .8 + 34 * fr ** 1.1, .4 + 7 * fr
    d1, d2 = -(i * .0316), -(i * .0474) - .3
    xc = x0 + sw_ / 2
    slope = math.degrees(math.atan(amp * .0262 * 1.0))
    strips.append(f'<g class="w1" style="--a:{amp:.1f}px;--wd:{d1:.3f}s"><g class="w2" style="--a:{amp2:.1f}px;--wd:{d2:.3f}s">'
                  f'<g class="ws" style="--sk:{slope:.2f}deg;--wd:{d1 - .8:.3f}s;transform-origin:{xc:.2f}px {CY}px"><g class="shd" style="--wd:{d1 - .8:.3f}s">'
                  f'<g clip-path="url(#sc{i})"><use href="#flagart"/></g></g></g></g></g>')
pole = (f'<g class="pole"><rect x="{FL - 12}" y="{FT - 44}" width="8" height="{FH + 150}" rx="3" fill="url(#brass)"/>'
        f'<circle cx="{FL - 8}" cy="{FT - 50}" r="9" fill="url(#brass)"/><rect x="{FL - 14}" y="{FT - 40}" width="12" height="6" rx="2" fill="#b58a35"/></g>')

# ---------- atmosphere ----------
motes = []
for i in range(110):
    r = R.choice([.8, 1.1, 1.5, 2.0, 2.8, 4.0])
    bl = 'url(#blur1)' if r < 1.8 else ('url(#blur2)' if r < 3 else 'url(#blur3)')
    motes.append(f'<circle class="mote" filter="{bl}" cx="{R.uniform(-40, 1000):.0f}" cy="{R.uniform(-40, 580):.0f}" r="{r}" '
                 f'style="--md:{R.uniform(14, 34):.1f}s;--mdl:-{R.uniform(0, 30):.1f}s;--mx:{R.uniform(-70, 80):.0f}px;--my:{R.uniform(-110, 20):.0f}px;--mo:{R.uniform(.25, .6):.2f}"/>')
bands = []
for i in range(6):
    w = R.uniform(120, 260)
    bands.append(f'<g style="transform:translateX({R.uniform(-300, 900):.0f}px) skewX(-24deg)"><rect class="band" style="--bd:{R.uniform(38, 70):.0f}s;--bdl:-{R.uniform(0, 50):.0f}s;--bo:{R.uniform(.05, .11):.2f}" x="0" y="-100" width="{w:.0f}" height="760"/></g>')
cross = []
CROSS = [(.5, 4.6, 'bar'), (2.0, 5.2, 'bar'), (3.6, 6.4, 'half'), (5.4, 4.0, 'bar'), (23.2, 6.5, 'orb'), (25.6, 6, 'orb'), (27.4, 5.5, 'orb')]
for t0, dur, kind in CROSS:
    y1, y2 = R.uniform(40, 500), R.uniform(40, 500)
    d = 1 if R.random() < .5 else -1
    xs, xe = (-260, 1220) if d > 0 else (1220, -260)
    if kind == 'orb':
        rr = R.uniform(70, 150)
        cross.append(f'<g class="cross" style="--xs:{xs}px;--ys:{y1:.0f}px;--xe:{xe}px;--ye:{y2:.0f}px;--cd:{dur}s;--cl:{t0}s;--sa:0deg;--ea:0deg"><circle r="{rr:.0f}" fill="url(#orb)"/></g>')
    else:
        body = (f'<rect x="-150" y="-26" width="300" height="52" fill="{INK}"/>' if kind == 'bar' else f'<path d="{blue_d if R.random() < .5 else red_d}" transform="scale(2.6)" fill="{RED if R.random() < .5 else BLUE}"/>')
        cross.append(f'<g class="cross fg" style="--xs:{xs}px;--ys:{y1:.0f}px;--xe:{xe}px;--ye:{y2:.0f}px;--cd:{dur}s;--cl:{t0}s;--sa:{R.uniform(-40, 40):.0f}deg;--ea:{R.uniform(-40, 40):.0f}deg">{body}</g>')

# camera: crane, push-ins, a shake on the slam, pull-back, drift, final push
def cam(t, sc, tx, ty, rt):
    return (t, f'transform:translate({tx}px,{ty}px) rotate({rt}deg) scale({sc})')


shake = [(T_DONE + dt, f'transform:translate({a}px,{b}px) rotate({c}deg) scale(1.14)') for dt, a, b, c in
         ((.0, 0, 0, .3), (.07, -9, 5, .1), (.15, 7, -6, .5), (.24, -5, 4, .2), (.34, 3, -2, .4), (.5, 0, 0, .3))]
CAMK = kfs([cam(0, 1.2, 36, 22, -1.4), cam(5, 1.1, 14, 8, -.6), cam(8.2, 1.18, 0, 0, 0), cam(T_DONE - .1, 1.14, 0, 0, .3)] + shake +
           [cam(21.6, .92, 0, -6, 0), cam(26, .98, -18, 4, -.8), cam(30, 1.02, 12, -2, .5), cam(T_DONE + 14.5, 1.1, 0, 0, 0)])
FAD = kfs([(0, 'opacity:1'), (31, 'opacity:1'), (32, 'opacity:0')])

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>Taegukgi</title>
<defs>
<radialGradient id="bg" cx="52%" cy="44%" r="80%"><stop offset="0" stop-color="#ffffff"/><stop offset=".65" stop-color="#f7f5f0"/><stop offset="1" stop-color="#e6e3da"/></radialGradient>
<linearGradient id="brass" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8a6a22"/><stop offset=".4" stop-color="#f1d68a"/><stop offset="1" stop-color="#8a6a22"/></linearGradient>
<radialGradient id="flash"><stop offset="0" stop-color="#fff2d8" stop-opacity=".95"/><stop offset=".5" stop-color="#ffd9a0" stop-opacity=".35"/><stop offset="1" stop-color="#ffd9a0" stop-opacity="0"/></radialGradient>
<radialGradient id="orb"><stop offset="0" stop-color="#b9ae96" stop-opacity=".32"/><stop offset=".85" stop-color="#b9ae96" stop-opacity=".2"/><stop offset="1" stop-color="#b9ae96" stop-opacity="0"/></radialGradient>
<radialGradient id="vig" cx="50%" cy="50%" r="72%"><stop offset=".55" stop-color="#3a342a" stop-opacity="0"/><stop offset="1" stop-color="#3a342a" stop-opacity=".34"/></radialGradient>
<linearGradient id="bandg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4a4438" stop-opacity="0"/><stop offset=".5" stop-color="#4a4438" stop-opacity="1"/><stop offset="1" stop-color="#4a4438" stop-opacity="0"/></linearGradient>
<linearGradient id="streak" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffcf90" stop-opacity="0"/><stop offset=".5" stop-color="#ffe2b8" stop-opacity=".95"/><stop offset="1" stop-color="#ffcf90" stop-opacity="0"/></linearGradient>
<filter id="blur" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="8"/></filter>
<filter id="soft" x="-5%" y="-10%" width="110%" height="120%"><feGaussianBlur stdDeviation=".7"/></filter>
<filter id="blur1"><feGaussianBlur stdDeviation=".6"/></filter><filter id="blur2"><feGaussianBlur stdDeviation="1.6"/></filter><filter id="blur3"><feGaussianBlur stdDeviation="3.4"/></filter>
<filter id="bandblur" x="-50%" y="-10%" width="200%" height="120%"><feGaussianBlur stdDeviation="26"/></filter>
<filter id="fshadow" x="-20%" y="-20%" width="140%" height="150%"><feGaussianBlur stdDeviation="16"/></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="4"/><feColorMatrix type="matrix" values="0 0 0 0 .25  0 0 0 0 .22  0 0 0 0 .18  0 0 0 .9 -.28"/></filter>
<g id="flagart">{flag_art}</g>
{''.join(clips)}
<style>
@property --k {{ syntax:'&lt;number&gt;'; inherits:true; initial-value:0 }}
@property --g {{ syntax:'&lt;number&gt;'; inherits:true; initial-value:1 }}
.cam{{transform-origin:{W // 2}px {H // 2}px;animation:cam {T}s cubic-bezier(.45,.02,.3,1) both}}
.stage{{animation:fad {T}s linear both}}
.idle{{animation:idle var(--wt) ease-in-out both}}
.arc{{animation:arc var(--fd) cubic-bezier(.4,0,.3,1) var(--fl) both}}
.focus{{animation:focus var(--fd) ease-out var(--fl) both}}
.settle{{animation:settle .6s ease-out var(--ld) both}}
.pc{{transform:translate(var(--sx),var(--sy)) rotate(var(--sa)) scale(var(--sw),var(--sh));opacity:0;
  animation:fly var(--fd) cubic-bezier(.16,.02,.12,1) var(--fl) both, fadein 1.6s ease-out var(--in) both}}
.pc.sh{{animation:fly var(--fd) cubic-bezier(.16,.02,.12,1) var(--fl) both, fadeinS 1.6s ease-out var(--in) both}}
.shw{{animation:shw var(--fd) cubic-bezier(.16,.02,.12,1) var(--fl) both}}
.ghost{{fill:none;stroke:#c9c4b4;stroke-width:1.2;vector-effect:non-scaling-stroke;stroke-dasharray:4 4;opacity:0;animation:ghostin 2s ease-out 1.6s forwards, ghostout .6s ease-in var(--gl) forwards}}
.ping{{fill:none;stroke:#7d7766;stroke-width:1.6;opacity:0;transform-box:fill-box;transform-origin:center;animation:ping 1s ease-out var(--gl) both}}
.burst{{fill:#6b6557;opacity:0;animation:burst .95s cubic-bezier(.1,.7,.3,1) var(--gl) both}}
.field{{opacity:0;animation:fadein 1.2s ease-out {T_DONE - .9:.2f}s forwards}}
.assembled{{animation:asm {T_DONE + 3.6:.2f}s linear both}}
.fsh{{opacity:0;animation:fadein 1.5s ease-out {T_DONE - .6:.2f}s forwards, sway 3.4s ease-in-out {T_DONE + 4:.2f}s infinite alternate}}
.cloth{{opacity:0;animation:clothin .01s linear {T_DONE + 3.2:.2f}s forwards, ramp 5s ease-in-out {T_DONE + 3.6:.2f}s both, gust 4.2s ease-in-out {T_DONE + 6:.2f}s infinite alternate}}
.pole{{opacity:0;animation:fadein 1.2s ease-out {T_DONE + 3.4:.2f}s forwards}}
.flash{{opacity:0;animation:flash 1.8s ease-out {T_DONE:.2f}s both}}
.flare{{opacity:0;animation:flare 2.6s ease-out {T_DONE + 2.6:.2f}s both}}
.gloss{{opacity:0;animation:gloss 3.2s ease-in-out {T_DONE + 2.4:.2f}s both}}
.w1{{animation:wave 1.7s ease-in-out var(--wd) infinite alternate}}
.w2{{animation:wave2 2.6s ease-in-out var(--wd) infinite alternate}}
.ws{{animation:slope 1.7s ease-in-out var(--wd) infinite alternate}}
.shd{{animation:shade 1.7s ease-in-out var(--wd) infinite alternate}}
.mote{{fill:#8c8574;opacity:0;animation:mote var(--md) ease-in-out var(--mdl) infinite}}
.band{{fill:url(#bandg);opacity:var(--bo);filter:url(#bandblur);animation:bandmove var(--bd) linear var(--bdl) infinite}}
.cross{{opacity:0;animation:cross var(--cd) cubic-bezier(.3,.1,.7,.9) var(--cl) both}}
.cross.fg{{filter:blur(13px)}}
.open{{animation:open 2.4s ease-out both}}
.grain{{animation:grain .5s steps(1) infinite}}
@keyframes cam{{{CAMK}}}
@keyframes fad{{0%,{31 / T * 100:.2f}%{{opacity:1}}100%{{opacity:0}}}}
@keyframes idle{{0%{{transform:translate(0,0)}}30%{{transform:translate(var(--dx),var(--dy))}}65%{{transform:translate(calc(var(--dx)*-.7),calc(var(--dy)*.8))}}100%{{transform:translate(0,0)}}}}
@keyframes fadein{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes fadeinS{{from{{opacity:0}}to{{opacity:.3}}}}
@keyframes fly{{from{{transform:translate(var(--sx),var(--sy)) rotate(var(--sa)) scale(var(--sw),var(--sh))}}to{{transform:translate(var(--ex),var(--ey)) rotate(var(--ea)) scale(var(--ew),var(--eh))}}}}
@keyframes arc{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(var(--ax),var(--ay))}}}}
@keyframes focus{{from{{filter:blur(var(--b0))}}to{{filter:blur(0px)}}}}
@keyframes settle{{0%{{transform:scale(1)}}30%{{transform:scale(1.07)}}100%{{transform:scale(1)}}}}
@keyframes shw{{from{{transform:translate(30px,52px)}}to{{transform:translate(1px,3px)}}}}
@keyframes ghostin{{to{{opacity:1}}}}
@keyframes ghostout{{to{{opacity:0}}}}
@keyframes ping{{0%{{opacity:.85;transform:scale(1)}}100%{{opacity:0;transform:scale(1.6,2.6)}}}}
@keyframes burst{{0%{{opacity:.9;transform:translate(0,0)}}100%{{opacity:0;transform:translate(var(--bx),var(--by))}}}}
@keyframes asm{{0%,99.9%{{opacity:1}}100%{{opacity:0}}}}
@keyframes sway{{from{{transform:translate(0,0) scaleX(.985)}}to{{transform:translate(8px,5px) scaleX(1.015)}}}}
@keyframes clothin{{to{{opacity:1}}}}
@keyframes ramp{{from{{--k:0}}to{{--k:1}}}}
@keyframes gust{{from{{--g:.85}}to{{--g:1.5}}}}
@keyframes flash{{0%{{opacity:0}}18%{{opacity:.9}}100%{{opacity:0}}}}
@keyframes flare{{0%{{opacity:0}}22%{{opacity:.9}}100%{{opacity:0}}}}
@keyframes gloss{{0%{{opacity:0;transform:translateX(-760px)}}25%{{opacity:.85}}75%{{opacity:.85}}100%{{opacity:0;transform:translateX(760px)}}}}
@keyframes wave{{from{{transform:translateY(calc(var(--a) * var(--k) * var(--g) * -1))}}to{{transform:translateY(calc(var(--a) * var(--k) * var(--g)))}}}}
@keyframes wave2{{from{{transform:translateY(calc(var(--a) * var(--k) * var(--g)))}}to{{transform:translateY(calc(var(--a) * var(--k) * var(--g) * -1))}}}}
@keyframes slope{{from{{transform:skewY(calc(var(--sk) * var(--k) * var(--g) * -1))}}to{{transform:skewY(calc(var(--sk) * var(--k) * var(--g)))}}}}
@keyframes shade{{from{{filter:brightness(1)}}to{{filter:brightness(calc(1 - .15 * var(--k) * var(--g)))}}}}
@keyframes mote{{0%{{opacity:0;transform:translate(0,0)}}20%{{opacity:var(--mo)}}80%{{opacity:var(--mo)}}100%{{opacity:0;transform:translate(var(--mx),var(--my))}}}}
@keyframes bandmove{{from{{transform:translateX(-900px)}}to{{transform:translateX(1500px)}}}}
@keyframes cross{{0%{{opacity:0;transform:translate(var(--xs),var(--ys)) rotate(var(--sa))}}12%{{opacity:.75}}88%{{opacity:.75}}100%{{opacity:0;transform:translate(var(--xe),var(--ye)) rotate(var(--ea))}}}}
@keyframes open{{from{{opacity:1}}to{{opacity:0}}}}
@keyframes grain{{0%{{transform:translate(0,0)}}25%{{transform:translate(-37px,21px)}}50%{{transform:translate(23px,-44px)}}75%{{transform:translate(-12px,-29px)}}}}
{chr(10).join(KFS)}
</style>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<g class="stage">
<g class="cam">
<g>{''.join(bands)}</g>
<g>{''.join(motes)}</g>
{''.join(ghosts)}
<g>{''.join(shadows)}</g>
<g class="fsh"><rect x="{FL + 14}" y="{FT + 34}" width="{FW}" height="{FH}" fill="#000" opacity=".16" filter="url(#fshadow)"/></g>
<rect class="field" x="{FL}" y="{FT}" width="{FW}" height="{FH}" fill="#ffffff"/>
<g class="assembled">{''.join(pieces)}</g>
{''.join(pings)}
{''.join(bursts)}
<g class="cloth">{pole}<g filter="url(#soft)">{''.join(strips)}</g></g>
<circle class="flash" cx="{CX}" cy="{CY}" r="420" fill="url(#flash)"/>
<g>{''.join(cross)}</g>
<g class="flare"><rect x="-60" y="{CY - 70}" width="1080" height="9" fill="url(#streak)"/><circle cx="{CX + 150}" cy="{CY - 66}" r="46" fill="url(#flash)"/><circle cx="{CX - 120}" cy="{CY - 50}" r="22" fill="url(#flash)" opacity=".7"/><circle cx="{CX - 260}" cy="{CY - 38}" r="34" fill="url(#flash)" opacity=".5"/></g>
</g>
<rect width="{W}" height="{H}" fill="url(#vig)"/>
<g opacity=".16" style="mix-blend-mode:multiply"><rect class="grain" x="-60" y="-60" width="{W + 120}" height="{H + 120}" filter="url(#grain)"/></g>
</g>
<rect class="open" width="{W}" height="{H}" fill="#ffffff"/>
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print('wrote', os.path.normpath(OUT), len(svg) // 1024, 'KB;', len(SLOTS) + 2, 'pieces; home at', round(T_DONE, 1), 's')
