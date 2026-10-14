#!/usr/bin/env python3
"""Taegukgi intro (24 s, one-shot): the supplied artwork files break into pieces that fly in one by one and assemble the official flag.
   0- 3.6  three cards float in: the halftone taeguk, the colour trigram file, the black trigram file (the finished look)
 3.6- 5    the cards crack and fall away; the pieces stay
 4.8- 7.2  the flag field appears; the two halves of the halftone taeguk fly in and lock together, then fill in as the official red/blue
 8 -16.5   the trigram pieces (cut from the colour file; the middle bar of the 4th group splits in two) fly in one by one,
           tilt toward the centre and turn black as they land: geon, gam, ri, gon
16.5-20    the finished flag: light sweep, rising lanterns
20 -24     the camera pushes into the taeguk and everything fades to night (the lantern film starts from there)
Official layout: 3:2 white field, taeguk diameter = half the height (red above, blue below, tilted 33.69 deg),
trigrams at the four corners with their bars pointing at the centre: geon top-left, gam top-right, ri bottom-left, gon bottom-right.
Piece rectangles are measured from the supplied images (2000x667 artwork, 17 pieces).
usage: python3 tools/gen_taegukgi_intro.py [--out=PATH]   -> flowers/taegukgi_intro.svg
"""
import math
import os
import random
import sys

W, H, T = 960, 540, 24.0
OUT = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--out=')), None) or \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flowers', 'taegukgi_intro.svg')
R = random.Random(14)
CX, CY = 480, 270
FW, FH = 600, 400
TR = FH / 4
TILT = math.degrees(math.atan2(2, 3))
FRED, FBLUE = '#cd2e3a', '#0047a0'          # official-looking flag colours (as in the supplied colour file)
BLACK = '#0c0c0e'

# the 17 pieces of the supplied colour file (x, y, w, h in the 2000x667 artwork), by group
G1 = [(48, 145, 90, 392), (195, 145, 90, 392), (342, 145, 89, 392)]                                            # 3 solid bars (red)
G2 = [(530, 161, 185, 80), (772, 161, 185, 80), (530, 303, 427, 80), (530, 445, 185, 80), (772, 445, 185, 80)]  # broken / solid / broken (blue)
G3 = [(1057, 144, 91, 170), (1057, 366, 91, 171), (1205, 144, 90, 393), (1352, 144, 90, 170), (1352, 366, 90, 171)]  # (red)
G4 = [(1534, 154, 425, 87), (1534, 296, 183, 87), (1774, 296, 185, 87), (1534, 439, 425, 86)]                  # solid / broken / solid (blue)
RED_F, BLUE_F = '#cb323e', '#05499e'
S_ART = .29
CARD_C = (350, 72)       # colour card origin on stage
CARD_K = (350, 288)      # black card origin on stage


def stage(rect, origin):
    x, y, w, h = rect
    return origin[0] + (x + w / 2) * S_ART, origin[1] + (y + h / 2) * S_ART, w * S_ART, h * S_ART


# ---------- target slots in the finished flag ----------
BAR_L, BAR_T, GAP = 118, 22, 17
SEG = (BAR_L - 20) / 2


def rot(x, y, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return x * c - y * s, x * s + y * c


def slot(sx, sy, ang, i, part):
    """bar i (0..2) of a trigram; part: None = solid, 0/1 = left/right half"""
    cx, cy = CX + sx * 212, CY + sy * 140
    yy = (i - 1) * (BAR_T + GAP)
    if part is None:
        lx, w = 0, BAR_L
    else:
        lx, w = (-1 if part == 0 else 1) * (SEG / 2 + 10), SEG
    dx, dy = rot(lx, yy, ang)
    return cx + dx, cy + dy, w, BAR_T, ang


GEON, GAM = (-1, -1, TILT), (1, -1, -TILT)
RI, GON = (-1, 1, -TILT), (1, 1, TILT)
# ordered assignment: (start rect on stage, target slot, tint colour)
JOBS = []
for k, r_ in enumerate(G1):                                    # 건 <- 3 solid red bars
    JOBS.append((stage(r_, CARD_C), slot(*GEON, k, None), RED_F))
for j, r_ in enumerate(G2):                                    # 감 <- 5 blue pieces (broken, solid, broken)
    row, part = [(0, 0), (0, 1), (1, None), (2, 0), (2, 1)][j]
    JOBS.append((stage(r_, CARD_C), slot(*GAM, row, part), BLUE_F))
for j, r_ in enumerate(G4):                                    # 리 <- 4 blue pieces (solid, broken, solid)
    row, part = [(0, None), (1, 0), (1, 1), (2, None)][j]
    JOBS.append((stage(r_, CARD_C), slot(*RI, row, part), BLUE_F))
# 곤 <- 5 red pieces; the solid middle bar splits into two halves, so six pieces
g3 = [stage(r_, CARD_C) for r_ in G3]
mid = g3[2]
halfA = (mid[0], mid[1] - mid[3] / 4, mid[2], mid[3] / 2)
halfB = (mid[0], mid[1] + mid[3] / 4, mid[2], mid[3] / 2)
JOBS.append((g3[0], slot(*GON, 0, 0), RED_F))
JOBS.append((g3[1], slot(*GON, 0, 1), RED_F))
JOBS.append((halfA, slot(*GON, 1, 0), RED_F))
JOBS.append((halfB, slot(*GON, 1, 1), RED_F))
JOBS.append((g3[3], slot(*GON, 2, 0), RED_F))
JOBS.append((g3[4], slot(*GON, 2, 1), RED_F))

pieces = []
T0, DT, FD = 8.0, .46, 1.15
for n, ((sx, sy, sw, sh), (ex, ey, ew, eh, ea), col) in enumerate(JOBS):
    delay = T0 + n * DT
    spin = R.choice([-360, 0, 360, 360])
    ax, ay = R.uniform(-90, 90), R.uniform(-120, -40)
    pieces.append(
        f'<g class="arc" style="--ax:{ax:.0f}px;--ay:{ay:.0f}px;--fd:{FD}s;--fl:{delay:.2f}s">'
        f'<g class="pc" style="--sx:{sx:.1f}px;--sy:{sy:.1f}px;--sw:{sw:.1f};--sh:{sh:.1f};--ex:{ex:.1f}px;--ey:{ey:.1f}px;--ew:{ew:.1f};--eh:{eh:.1f};--sa:0deg;--ea:{ea + spin:.2f}deg;'
        f'--fd:{FD}s;--fl:{delay:.2f}s">'
        f'<rect class="pr" style="--c0:{col};--tl:{delay + FD - .1:.2f}s" x="-.5" y="-.5" width="1" height="1"/></g></g>')

# static black card pieces (the finished look), fading once the flag is done
black = []
for grp in (G1, G2, G3, G4):
    for r_ in grp:
        x, y, w, h = r_
        black.append(f'<rect class="blk" style="--bl:{3.9 + len(black) * .05:.2f}s;--bx:{R.uniform(-30, 30):.0f}px" x="{CARD_K[0] + x * S_ART:.1f}" y="{CARD_K[1] + y * S_ART:.1f}" width="{w * S_ART:.1f}" height="{h * S_ART:.1f}"/>')

# ---------- the taeguk: two halves of halftone dots (red / blue) ----------
r_, r2 = TR, TR / 2
red_d = f'M{-r_} 0 A{r_} {r_} 0 0 1 {r_} 0 A{r2} {r2} 0 0 1 0 0 A{r2} {r2} 0 0 0 {-r_} 0 Z'
blue_d = f'M{r_} 0 A{r_} {r_} 0 0 1 {-r_} 0 A{r2} {r2} 0 0 1 0 0 A{r2} {r2} 0 0 0 {r_} 0 Z'


def in_red(x, y):
    if y < 0:
        return math.hypot(x + r2, y) > r2
    return math.hypot(x - r2, y) <= r2


def halftone(red):
    out = []
    sp = 5.4
    y = -r_ + sp / 2
    while y < r_:
        x = -r_ + sp / 2 + (sp / 2 if int((y + r_) / sp) % 2 else 0)
        while x < r_:
            d = math.hypot(x, y)
            if d < r_ - 1.5 and in_red(x, y) == red:
                rad = 2.3 * (1 - .5 * (d / r_) ** 2)
                out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.2f}"/>')
            x += sp
        y += sp * .866
    return ''.join(out)


CARD_T = (172, 270)        # taeguk card centre on stage
CS = .78                   # taeguk scale on its card
halfR, halfB = halftone(True), halftone(False)
taeguk_flights = []
for name, dots, col, arc, spin in (('r', halfR, '#ff4a5c', (-120, -110), 360), ('b', halfB, '#3b78ff', (120, 110), -360)):
    taeguk_flights.append(
        f'<g class="tarc" style="--ax:{arc[0]}px;--ay:{arc[1]}px"><g class="th" style="--sx:{CARD_T[0]:.0f}px;--sy:{CARD_T[1]:.0f}px;--sa:{-TILT:.2f}deg;--ea:{-TILT + spin:.2f}deg;--s0:{CS}">'
        f'<g class="tdots" style="fill:{col}">{dots}</g></g></g>')

# ---------- cards, cracks, flag, lanterns, sparks ----------
cards = (f'<rect class="card" style="--cd:.2s" x="{CARD_C[0] - 20}" y="{CARD_C[1] - 14}" width="{2000 * S_ART + 40:.0f}" height="{667 * S_ART + 28:.0f}" rx="14"/>'
         f'<rect class="card" style="--cd:.6s" x="{CARD_K[0] - 20}" y="{CARD_K[1] - 14}" width="{2000 * S_ART + 40:.0f}" height="{667 * S_ART + 28:.0f}" rx="14"/>'
         f'<rect class="card" style="--cd:1s" x="{CARD_T[0] - 110}" y="{CARD_T[1] - 110}" width="220" height="220" rx="14"/>')
cracks = ''
for (ox, oy, cw, ch) in ((CARD_C[0] - 20, CARD_C[1] - 14, 2000 * S_ART + 40, 667 * S_ART + 28), (CARD_K[0] - 20, CARD_K[1] - 14, 2000 * S_ART + 40, 667 * S_ART + 28), (CARD_T[0] - 110, CARD_T[1] - 110, 220, 220)):
    p = [(ox + R.uniform(.2, .8) * cw, oy)]
    for k in range(1, 7):
        p.append((p[-1][0] + R.uniform(-30, 30), oy + ch * k / 6))
    cracks += f'<path class="crack" pathLength="1" d="M' + ' L'.join(f'{x:.0f} {y:.0f}' for x, y in p) + '"/>'


def lantern_path(S):
    return (f'M{-.9*S:.1f} {-1.2*S:.1f} C{-1.25*S:.1f} {-.3*S:.1f} {-1.0*S:.1f} {.7*S:.1f} {-.55*S:.1f} {1.25*S:.1f} L{.55*S:.1f} {1.25*S:.1f} '
            f'C{1.0*S:.1f} {.7*S:.1f} {1.25*S:.1f} {-.3*S:.1f} {.9*S:.1f} {-1.2*S:.1f} Z M{-.9*S:.1f} {-1.2*S:.1f} Q0 {-1.5*S:.1f} {.9*S:.1f} {-1.2*S:.1f} M0 {-1.35*S:.1f} L0 {1.2*S:.1f}')


LCOL = ['#ff9a3d', '#ffd45a', '#ff5a4a', '#ff7fb0', '#59d6c0', '#6aa8ff']
lan = []
for i in range(34):
    S = R.uniform(4, 10)
    x = R.choice([R.uniform(20, 170), R.uniform(790, 940), R.uniform(20, 940)])
    col = R.choice(LCOL)
    lan.append(f'<g class="rise" style="--rt:{15 + R.uniform(0, 4):.1f}s;--rd:{R.uniform(6, 9):.1f}s;--rx:{R.uniform(-40, 40):.0f}px"><g transform="translate({x:.0f} 560)">'
               f'<circle r="{S*2.8:.1f}" fill="url(#lh)" style="stroke:none;color:{col}"/><path class="lan" style="color:{col}" d="{lantern_path(S)}"/>'
               f'<circle cy="{S*1.2:.1f}" r="{max(.9, S*.2):.1f}" fill="#fff4c8"/></g></g>')
spark = ''.join(
    f'<g transform="translate({R.uniform(0, 960):.0f} {R.uniform(0, 540):.0f})"><path class="spk" style="--td:{R.uniform(1.6, 3.6):.1f}s;--tl:-{R.uniform(0, 4):.1f}s;'
    f'fill:{R.choice(["#fff3c8", "#ffd27a", "#ffc0dc", "#cfe0ff"])}" d="M0 {-s:.1f} Q0 0 {s:.1f} 0 Q0 0 0 {s:.1f} Q0 0 {-s:.1f} 0 Q0 0 0 {-s:.1f} Z"/></g>'
    for s in [R.uniform(2.5, 7) for _ in range(70)])

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>Taegukgi intro</title>
<defs>
<radialGradient id="bg" cx="50%" cy="50%" r="75%"><stop offset="0" stop-color="#1a1230"/><stop offset=".6" stop-color="#0a0818"/><stop offset="1" stop-color="#03030a"/></radialGradient>
<radialGradient id="lh"><stop offset="0" stop-color="currentColor" stop-opacity=".5"/><stop offset="1" stop-color="currentColor" stop-opacity="0"/></radialGradient>
<linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".7"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="flagclip"><rect x="{CX - FW // 2}" y="{CY - FH // 2}" width="{FW}" height="{FH}"/></clipPath>
<filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="14"/></filter>
<filter id="shadow" x="-10%" y="-10%" width="120%" height="130%"><feGaussianBlur stdDeviation="5"/></filter>
<style>
.world{{transform-origin:{CX}px {CY}px;animation:push 24s cubic-bezier(.45,0,.75,.55) both}}
.fade{{animation:endfade 24s linear both}}
.card{{fill:#fbfaf6;filter:url(#shadow);opacity:0;animation:cardin .9s ease-out var(--cd) forwards, cardout .9s ease-in 3.9s forwards}}
.card{{filter:none}}
.crack{{fill:none;stroke:#5a5a66;stroke-width:2.2;stroke-linecap:round;stroke-dasharray:1;stroke-dashoffset:1;animation:crackd .5s ease-in 3.3s forwards, cardout .8s ease-in 3.9s forwards}}
.blk{{fill:{BLACK};opacity:0;transform-box:fill-box;transform-origin:center;animation:cardin .9s ease-out 1.2s forwards, ink 1.3s ease-in var(--bl) forwards}}
.arc{{animation:arc var(--fd) ease-in-out var(--fl) both}}
.pc{{transform:translate(var(--sx),var(--sy)) rotate(var(--sa)) scale(var(--sw),var(--sh));opacity:0;animation:fly var(--fd) cubic-bezier(.35,.05,.2,1) var(--fl) both, popin .9s ease-out 1.1s both}}
.pr{{fill:var(--c0);animation:tint .35s ease var(--tl) both}}
.th{{transform:translate(var(--sx),var(--sy)) rotate(var(--sa)) scale(var(--s0));animation:tfly 2.6s cubic-bezier(.3,.1,.2,1) 4.9s both, popin .9s ease-out 1.1s both;opacity:0}}
.tarc{{animation:arc 2.6s ease-in-out 4.9s both}}
.tdots{{animation:dotsout 1.1s ease-in 7.6s both}}
.sol{{opacity:0;animation:solin 1.3s ease-out 7.0s forwards}}
.field{{opacity:0;animation:fieldin 1.2s cubic-bezier(.2,.8,.2,1) 4.6s forwards}}
.gloss{{opacity:0;animation:gloss 2.6s ease-in-out 16.8s forwards}}
.halo{{opacity:0;animation:haloin 2s ease-out 15.8s forwards}}
.rise{{opacity:0;animation:rise var(--rd) ease-in var(--rt) both}}
.lan{{fill:currentColor;fill-opacity:.3;stroke:currentColor;stroke-width:1.2}}
.spk{{stroke:none;opacity:0;transform-box:fill-box;transform-origin:center;animation:spk var(--td) ease-in-out var(--tl) infinite}}
@keyframes cardin{{to{{opacity:1}}}}
@keyframes cardout{{to{{opacity:0}}}}
@keyframes ink{{to{{opacity:0;transform:translate(var(--bx),-70px) scale(.5) rotate(25deg)}}}}
@keyframes crackd{{to{{stroke-dashoffset:0}}}}
@keyframes popin{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes fly{{from{{transform:translate(var(--sx),var(--sy)) rotate(var(--sa)) scale(var(--sw),var(--sh))}}to{{transform:translate(var(--ex),var(--ey)) rotate(var(--ea)) scale(var(--ew),var(--eh))}}}}
@keyframes arc{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(var(--ax),var(--ay))}}}}
@keyframes tint{{from{{fill:var(--c0)}}to{{fill:{BLACK}}}}}
@keyframes tfly{{from{{transform:translate(var(--sx),var(--sy)) rotate(var(--sa)) scale(var(--s0))}}to{{transform:translate({CX}px,{CY}px) rotate(var(--ea)) scale(1)}}}}
@keyframes dotsout{{to{{opacity:0}}}}
@keyframes solin{{to{{opacity:1}}}}
@keyframes fieldin{{from{{opacity:0;transform:scale(.88)}}to{{opacity:1;transform:scale(1)}}}}
@keyframes gloss{{0%{{opacity:0;transform:translateX(-700px)}}20%{{opacity:.55}}80%{{opacity:.55}}100%{{opacity:0;transform:translateX(700px)}}}}
@keyframes haloin{{to{{opacity:1}}}}
@keyframes rise{{0%{{opacity:0;transform:translate(0,0)}}12%{{opacity:1}}85%{{opacity:1}}100%{{opacity:0;transform:translate(var(--rx),-640px)}}}}
@keyframes spk{{0%,100%{{opacity:0;transform:scale(.2) rotate(0deg)}}50%{{opacity:1;transform:scale(1) rotate(45deg)}}}}
@keyframes push{{0%,83%{{transform:scale(1)}}100%{{transform:scale(4.2)}}}}
@keyframes endfade{{0%,92%{{opacity:1}}100%{{opacity:0}}}}
</style>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<g class="fade">
{spark}
<g class="world">
{''.join(lan)}
<g class="field" style="transform-origin:{CX}px {CY}px">
<rect x="{CX - FW // 2 - 12}" y="{CY - FH // 2 - 12}" width="{FW + 24}" height="{FH + 24}" fill="#fff3d6" opacity=".35" filter="url(#soft)"/>
<rect x="{CX - FW // 2}" y="{CY - FH // 2}" width="{FW}" height="{FH}" fill="#fdfcf8"/>
</g>
{cards}
{''.join(black)}
{cracks}
<g transform="translate(0 0)">
<g class="sol" transform="translate({CX} {CY}) rotate({-TILT:.2f})"><path d="{red_d}" fill="{FRED}"/><path d="{blue_d}" fill="{FBLUE}"/></g>
{''.join(taeguk_flights)}
{''.join(pieces)}
</g>
<g clip-path="url(#flagclip)"><rect class="gloss" x="{CX - 90}" y="{CY - FH // 2 - 20}" width="180" height="{FH + 40}" fill="url(#sweep)" transform="skewX(-14)"/></g>
</g>
</g>
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print('wrote', os.path.normpath(OUT), len(svg) // 1024, 'KB,', len(JOBS), 'pieces')
