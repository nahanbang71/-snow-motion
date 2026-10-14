#!/usr/bin/env python3
"""Lantern festival (연등축제) - 120 s looping neon line-art film, laser style (outlines + glow, no text).
  0- 14  night falls: the temple hall and pagoda are drawn in light
 10- 50  the hillside of lanterns lights up row by row (red / orange / pink / blue / green / yellow bands in
         perspective), colour waves roll up the slope, big lanterns sway along the foreground
 48- 56  the view lifts to the sky
 52-112  hundreds of sky lanterns rise over the tower, blue laser beams sweep from the lower left
 88-112  a lotus lantern blooms in the middle, a ring of small lanterns turns around it
112-120  everything fades to night, back to the temple
usage: python3 tools/gen_lantern_festival.py [seed] [--out=PATH]   -> flowers/lantern_festival.svg
"""
import math
import os
import random
import sys

W, H, T = 960, 540, 120.0
SEED = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8
OUT = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--out=')), None) or \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flowers', 'lantern_festival.svg')
R = random.Random(SEED)
KFS = []


def kfs(points):
    pts = [(min(t, T), p) for t, p in points if t <= T + 1e-9]
    if pts[-1][0] < T:
        pts.append((T, pts[-1][1]))
    out, last = [], -1
    for t, p in pts:
        t = max(t, last + 0.002)
        out.append((t, p))
        last = t
    KFS.append('@keyframes q%d{%s}' % (len(KFS), ''.join(f'{t/T*100:.4f}%{{{p}}}' for t, p in out)))
    return f'q{len(KFS)-1}'


def op(*pts):
    return kfs([(t, f'opacity:{v}') for t, v in pts])


def draw(a, t, b=None):
    """stroke draw-on from a to a+t, held until b, undrawn at the end of the cycle"""
    return kfs([(0, 'stroke-dashoffset:1'), (a, 'stroke-dashoffset:1'), (a + t, 'stroke-dashoffset:0'), ((b or 48) + 2, 'stroke-dashoffset:0'), ((b or 48) + 6, 'stroke-dashoffset:1')])


BAND = ['#ff3b4e', '#ff8a2b', '#ff5fa8', '#3f86ff', '#35d07f', '#ffd23f']
BAND8 = ['#ff3b4e', '#ff8a2b', '#ffd23f', '#35d07f', '#3f86ff', '#ff5fa8', '#ff8a2b', '#ffd23f']   # the hillside stripes


def circ(x, y, r):
    return f'M{x-r:.1f} {y:.1f} a{r:.1f} {r:.1f} 0 1 0 {2*r:.1f} 0 a{r:.1f} {r:.1f} 0 1 0 {-2*r:.1f} 0'


# ======================= Scene A: the temple and the lantern hillside =======================
A = []
CAM_A = kfs([(0, 'transform:scale(1) translate(0px,0px)'), (52, 'transform:scale(1.09) translate(0px,18px)'), (T, 'transform:scale(1.09) translate(0px,18px)')])

# distant hills + temple + pagoda (drawn in light)
hills = ['M0 150 C100 122 200 142 300 124 S500 104 600 120 S800 112 960 138']
temple = [
    ('M300 168 C330 150 400 138 480 138 S630 150 660 168', 'roof'), ('M300 168 Q278 171 266 156', 'roof'), ('M660 168 Q682 171 694 156', 'roof'),
    ('M268 190 C330 175 410 168 480 168 S630 175 692 190', 'roof'), ('M268 190 Q246 194 236 180', 'roof'), ('M692 190 Q714 194 724 180', 'roof'),
    ('M470 138 L470 126 M490 138 L490 126 M470 126 Q480 116 490 126', 'roof'),
    ('M258 206 L702 206', 'wall'), ('M290 190 L290 206 M350 183 L350 206 M410 177 L410 206 M480 175 L480 206 M550 177 L550 206 M610 183 L610 206 M670 190 L670 206', 'wall'),
    ('M455 206 L455 190 Q480 178 505 190 L505 206', 'wall'),
    ('M118 192 C150 178 200 174 238 184', 'roof'), ('M118 192 Q100 194 92 184', 'roof'), ('M92 206 L238 206', 'wall'),
    ('M722 184 C760 174 810 178 842 192', 'roof'), ('M842 192 Q860 194 868 184', 'roof'), ('M722 206 L868 206', 'wall'),
]
pag = []
for k in range(5):
    y, hw = 188 - k * 17, 27 - k * 4.5
    pag.append((f'M{58-hw:.0f} {y} Q58 {y-9} {58+hw:.0f} {y} M{58-hw*.7:.0f} {y} L{58-hw*.7:.0f} {y+8} L{58+hw*.7:.0f} {y+8} L{58+hw*.7:.0f} {y}', 'roof'))
pag.append(('M58 103 L58 80 M52 94 L64 94 M54 88 L62 88', 'roof'))
for i, d in enumerate(hills):
    A.append(f'<path class="d0 k hill" pathLength="1" style="animation-name:{draw(.5, 5)}" d="{d}"/>')
for i, (d, c) in enumerate(temple + pag):
    A.append(f'<path class="d0 k {c}" pathLength="1" style="animation-name:{draw(1.5 + i * .25, 2.2)}" d="{d}"/>')
# lit windows under the eaves
for i in range(26):
    x = 275 + i * 17.5
    A.append(f'<circle class="k win" style="opacity:0;animation-name:{op((0,0),(6+i*.12,0),(7+i*.12,1),(50,1),(54,0))}" cx="{x:.0f}" cy="199" r="1.6"/>')

# the hillside: rows of lanterns in perspective, colour bands converge on the temple
D, C = 30, 48
rows = []
ys = [214 + 232 * (d / (D - 1)) ** 1.25 for d in range(D)]
for d in range(D):
    t = d / (D - 1)
    y = ys[d]
    gap = (ys[d + 1] - ys[d]) if d < D - 1 else (ys[d] - ys[d - 1])
    half = 105 + 560 * t
    sp = 2 * half / C
    rx, ry = max(1.1, sp * .52), max(.9, gap * .5)
    els = []
    for c in range(C):
        x = 480 + (-1 + 2 * (c + .5) / C) * half
        els.append(f'<ellipse class="L b{c // 6}" cx="{x:.1f}" cy="{y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}"/>')
    t_on = 9 + (D - 1 - d) * .62
    pts = [(0, 0), (t_on, 0), (t_on + 1.6, .82)]
    for w in range(26, 48, 4):
        tw = w + (D - 1 - d) * .15
        pts += [(tw, .82), (tw + .6, 1), (tw + 1.5, .82)]
    pts += [(50, .82), (55, 0)]
    nm = kfs([(t, f'opacity:{v}') for t, v in pts])
    rows.append(f'<g class="k" style="opacity:0;animation-name:{nm}">{"".join(els)}</g>')
A += rows
# stairs / rails and string lights on the slope edges
for xa, xb in ((440, 150), (520, 810), (480, 480)):
    A.append(f'<path class="d0 k stair" pathLength="1" style="animation-name:{draw(14, 5)}" d="M{xa} 214 L{xb} 446"/>')
for side in (-1, 1):
    for i in range(36):
        t = i / 35
        x = 480 + side * (105 + 560 * t) * 1.02
        y = 214 + 232 * t ** 1.25
        col = BAND8[i % 8]
        A.append(f'<circle class="tw" style="fill:{col};--td:{R.uniform(1.2, 3):.1f}s;--tl:-{R.uniform(0, 3):.1f}s" cx="{x:.0f}" cy="{y:.0f}" r="{1.4 + 2*t:.1f}"/>')

# foreground: big lanterns hanging from a string, each swaying on its own
fg_str = 'M-20 452 C160 478 320 440 480 462 S800 440 980 466'
A.append(f'<path class="d0 k stair" pathLength="1" style="animation-name:{draw(18, 4)}" d="{fg_str}"/>')
FG = [(70, 470, '#ff5fa8'), (190, 466, '#ff3b4e'), (300, 458, '#ffd23f'), (410, 462, '#ff8a2b'), (520, 466, '#ff5fa8'), (630, 458, '#ff3b4e'),
      (745, 458, '#ffd23f'), (860, 462, '#ff8a2b'), (935, 470, '#ff5fa8')]
for i, (x, y, col) in enumerate(FG):
    s = R.uniform(.9, 1.2)
    rr = 19 * s
    body = (f'<line x1="0" y1="0" x2="0" y2="8" class="cord"/><rect class="cap" x="-7" y="8" width="14" height="5" rx="1.5"/>'
            f'<ellipse class="fgL" style="color:{col}" cx="0" cy="{13+rr:.1f}" rx="{rr:.1f}" ry="{rr*1.05:.1f}"/>'
            f'<path class="rib" style="color:{col}" d="M0 {13+rr*.0:.1f} Q{rr*.55:.1f} {13+rr:.1f} 0 {13+rr*2.1:.1f} M0 13 Q{-rr*.55:.1f} {13+rr:.1f} 0 {13+rr*2.1:.1f}"/>'
            f'<path class="cord" d="M-4 {13+rr*2.1:.1f} l0 14 M0 {13+rr*2.1:.1f} l0 18 M4 {13+rr*2.1:.1f} l0 14"/>'
            f'<circle cx="0" cy="{13+rr:.1f}" r="{rr*1.5:.1f}" fill="url(#halo_{BAND.index(col) if col in BAND else 0})" style="stroke:none"/>')
    nm = op((0, 0), (16 + i * .35, 0), (18 + i * .35, 1), (50, 1), (55, 0))
    sd = R.uniform(2.6, 4.2)
    A.append(f'<g class="k" style="opacity:0;animation-name:{nm}"><g class="sw" style="--sa:{R.uniform(2, 4.5)*(-1)**i:.1f}deg;--sd:{sd:.1f}s;--sl:-{R.uniform(0, sd):.1f}s;'
             f'transform-origin:{x}px {y}px"><g transform="translate({x} {y})">{body}</g></g></g>')
for i in range(26):   # embers rising off the slope
    A.append(f'<circle class="ember" cx="{R.uniform(100, 860):.0f}" cy="{R.uniform(250, 470):.0f}" r="{R.uniform(1, 2.2):.1f}" '
             f'style="--md:{R.uniform(7, 14):.1f}s;--mdl:-{R.uniform(0, 14):.1f}s;--dx:{R.uniform(-30, 40):.0f}px;--dy:-{R.uniform(80, 200):.0f}px"/>')

# ======================= Scene B: sky lanterns, tower, laser beams =======================
B = []
# hill line + tower
B.append(f'<path class="d0 k hill2" pathLength="1" style="animation-name:{draw(52, 4, 112)}" d="M0 436 C60 424 100 440 160 430 S280 416 340 432 S470 424 520 436 S650 422 720 434 S860 420 960 432"/>')
TX = 560
B.append(f'<rect x="{TX-8}" y="296" width="16" height="140" fill="url(#towerglow)" class="k" style="stroke:none;opacity:0;animation-name:{op((0,0),(52,0),(58,.8),(112,.8),(118,0))}"/>')
tower = [f'M{TX-5} 436 L{TX-5} 250 M{TX+5} 436 L{TX+5} 250', f'M{TX-24} 436 L{TX-5} 392 M{TX+24} 436 L{TX+5} 392',
         f'M{TX-5} 250 L{TX} 222 L{TX+5} 250', f'M{TX-22} 330 a22 6 0 1 0 44 0 a22 6 0 1 0 -44 0', f'M{TX-16} 296 a16 5 0 1 0 32 0 a16 5 0 1 0 -32 0',
         f'M{TX-22} 330 L{TX-18} 344 L{TX+18} 344 L{TX+22} 330', f'M{TX-16} 296 L{TX-13} 306 L{TX+13} 306 L{TX+16} 296']
for i, d in enumerate(tower):
    B.append(f'<path class="d0 k tower" pathLength="1" style="animation-name:{draw(53 + i * .5, 2.5, 112)}" d="{d}"/>')
# no people: a row of pine trees along the bottom, and lamps lit along the path between them
trees = 'M0 520 ' + ''.join(
    f'l{R.uniform(10, 16):.0f} {-R.uniform(26, 52):.0f} l{R.uniform(10, 16):.0f} {R.uniform(26, 52):.0f} ' for _ in range(40))
B.append(f'<path class="d0 k crowd" pathLength="1" style="animation-name:{draw(54, 6, 112)}" d="{trees}"/>')
for i in range(26):
    xx = 20 + i * 36 + R.uniform(-6, 6)
    B.append(f'<circle class="tw" style="fill:{R.choice(["#ffb35a", "#ff8f5a", "#ffe08a"])};--td:{R.uniform(1.6, 3.4):.1f}s;--tl:-{R.uniform(0, 3):.1f}s" '
             f'cx="{xx:.0f}" cy="{R.uniform(504, 522):.0f}" r="{R.uniform(1.6, 2.8):.1f}"/>')
# laser beams from the lower left
beams = []
for i, ang in enumerate([-78, -68, -58, -50, -42, -34, -27, -20, -14]):
    a = math.radians(ang)
    L = 1100
    x2, y2 = 30 + L * math.cos(a), 530 + L * math.sin(a)
    wd = R.uniform(2.5, 8)
    beams.append(f'<line class="beam" style="--bd:{R.uniform(2.5, 5):.1f}s;--bl:-{R.uniform(0, 5):.1f}s;stroke-width:{wd:.1f}" x1="30" y1="530" x2="{x2:.0f}" y2="{y2:.0f}"/>')
B.append(f'<g class="k" style="opacity:0;animation-name:{op((0,0),(64,0),(70,1),(88,1),(94,1),(112,1),(118,0))}"><g class="sweep" style="transform-origin:30px 530px">{"".join(beams)}</g></g>')


def lantern_path(S):
    return (f'M{-.9*S:.1f} {-1.2*S:.1f} C{-1.25*S:.1f} {-.3*S:.1f} {-1.0*S:.1f} {.7*S:.1f} {-.55*S:.1f} {1.25*S:.1f} L{.55*S:.1f} {1.25*S:.1f} '
            f'C{1.0*S:.1f} {.7*S:.1f} {1.25*S:.1f} {-.3*S:.1f} {.9*S:.1f} {-1.2*S:.1f} Z M{-.9*S:.1f} {-1.2*S:.1f} Q0 {-1.5*S:.1f} {.9*S:.1f} {-1.2*S:.1f} '
            f'M0 {-1.35*S:.1f} L0 {1.2*S:.1f}')


LCOL = [('#ff9a3d', 'o'), ('#ff9a3d', 'o'), ('#ff5a4a', 'r'), ('#ffd45a', 'y'), ('#ffd45a', 'y'), ('#ff7fb0', 'p'), ('#59d6c0', 't'), ('#6aa8ff', 'u')]
N = 150
for i in range(N):
    col, g = R.choice(LCOL)
    z = R.uniform(.35, 1.0) ** 1.4                      # depth: 1 = near (big, fast), 0 = far (tiny, slow)
    S = 3.6 + 9.5 * z
    x0 = R.uniform(10, 950)
    a = 50 + (i / N) ** 1.1 * 46 + R.uniform(0, 2.5)
    dur = 70 - 28 * z + R.uniform(-4, 4)
    y0 = R.uniform(470, 520)
    rise = y0 + 60
    dx = R.uniform(-60, 60)
    fa = min(a + dur, T - 8)
    nm = kfs([(0, f'transform:translate(0px,0px);opacity:0'), (a, 'transform:translate(0px,0px);opacity:0'), (a + 2.5, f'transform:translate({dx*2.5/dur:.1f}px,{-rise*2.5/dur:.1f}px);opacity:1'),
              (fa - 4, f'transform:translate({dx*(fa-4-a)/dur:.1f}px,{-rise*(fa-4-a)/dur:.1f}px);opacity:1'), (fa, f'transform:translate({dx*(fa-a)/dur:.1f}px,{-rise*(fa-a)/dur:.1f}px);opacity:0')])
    sd = R.uniform(3, 6.5)
    B.append(f'<g class="k" style="opacity:0;animation-name:{nm}"><g transform="translate({x0:.0f} {y0:.0f})"><g class="ls" style="--sx:{R.uniform(3, 9)*z+2:.1f}px;--sa:{R.uniform(2, 6):.1f}deg;'
             f'--sd:{sd:.1f}s;--sl:-{R.uniform(0, sd):.1f}s">'
             f'<circle r="{S*2.8:.1f}" fill="url(#lh_{g})" style="stroke:none"/>'
             f'<path class="sl" style="color:{col}" d="{lantern_path(S)}"/><circle class="flame" cy="{S*1.2:.1f}" r="{max(.9, S*.2):.1f}"/></g></g></g>')

# the lotus lantern (88-112)
LC = (480, 318)
LOT = []
for layer, (n, rad, wid, rot, colr) in enumerate([(8, 118, 34, 0, '#ff8fc4'), (8, 96, 30, 22.5, '#ffb3d9'), (6, 66, 24, 10, '#fff0f6')]):
    for k in range(n):
        ang = rot + k * 360 / n
        d = f'M0 0 C{-wid} {-rad*.35:.0f} {-wid*.7:.0f} {-rad*.8:.0f} 0 {-rad} C{wid*.7:.0f} {-rad*.8:.0f} {wid} {-rad*.35:.0f} 0 0 Z M0 {-rad*.15:.0f} L0 {-rad*.82:.0f}'
        t0 = 88 + layer * 1.2 + k * .12
        nm = kfs([(0, 'transform:scale(.05) rotate(-30deg);opacity:0'), (t0, 'transform:scale(.05) rotate(-30deg);opacity:0'), (t0 + 5, 'transform:scale(1) rotate(0deg);opacity:1'),
                  (112, 'transform:scale(1) rotate(0deg);opacity:1'), (117, 'transform:scale(1.15) rotate(8deg);opacity:0')])
        LOT.append(f'<g class="k" style="opacity:0;transform-origin:{LC[0]}px {LC[1]}px;animation-name:{nm}"><g transform="translate({LC[0]} {LC[1]}) rotate({ang})">'
                   f'<path class="lot" style="color:{colr}" d="{d}"/></g></g>')
LOT.append(f'<circle class="k" style="opacity:0;animation-name:{op((0,0),(92,0),(97,1),(112,1),(117,0))}" cx="{LC[0]}" cy="{LC[1]}" r="150" fill="url(#lotglow)"/>')
ring = []
for k in range(12):
    ang = k * 30
    x, y = LC[0] + 175 * math.cos(math.radians(ang)), LC[1] + 175 * .42 * math.sin(math.radians(ang))
    col = BAND[k % 6]
    S = 7.5
    ring.append(f'<g transform="translate({x:.0f} {y:.0f})"><circle r="{S*2.6:.0f}" fill="url(#halo_{k % 6})" style="stroke:none"/>'
                f'<path class="sl" style="color:{col}" d="{lantern_path(S)}"/><circle class="flame" cy="{S*1.2:.1f}" r="1.6"/></g>')
LOT.append(f'<g class="k" style="opacity:0;animation-name:{op((0,0),(94,0),(98,1),(112,1),(117,0))}"><g class="ringspin" style="transform-origin:{LC[0]}px {LC[1]}px">{"".join(ring)}</g></g>')

# ======================= assemble =======================
bgA = op((0, 0), (1.5, 1), (50, 1), (55, 0))
bgB = op((0, 0), (49, 0), (56, 1), (112, 1), (118, 0))
fadeA = op((0, 0), (2, 1), (52, 1), (56, 0))
fadeB = op((0, 0), (50, 0), (54, 1), (112, 1), (118, 0))
halos = ''.join(f'<radialGradient id="halo_{i}"><stop offset="0" stop-color="{c}" stop-opacity=".5"/><stop offset=".5" stop-color="{c}" stop-opacity=".16"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
                for i, c in enumerate(BAND))
lh = ''.join(f'<radialGradient id="lh_{g}"><stop offset="0" stop-color="{c}" stop-opacity=".38"/><stop offset=".45" stop-color="{c}" stop-opacity=".1"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
             for c, g in {(c, g) for c, g in LCOL})

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>Lantern festival - laser line art</title>
<defs>
<radialGradient id="bgA" cx="50%" cy="72%" r="85%"><stop offset="0" stop-color="#3a1630"/><stop offset=".5" stop-color="#150b24"/><stop offset="1" stop-color="#05040c"/></radialGradient>
<linearGradient id="bgB" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#020716"/><stop offset=".65" stop-color="#06173c"/><stop offset="1" stop-color="#0b2a66"/></linearGradient>
<linearGradient id="towerglow" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe27a" stop-opacity=".9"/><stop offset="1" stop-color="#ffb23a" stop-opacity=".25"/></linearGradient>
<radialGradient id="lotglow"><stop offset="0" stop-color="#ffd6ea" stop-opacity=".55"/><stop offset=".6" stop-color="#ff8fc4" stop-opacity=".18"/><stop offset="1" stop-color="#ff8fc4" stop-opacity="0"/></radialGradient>
{halos}{lh}
<filter id="glow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="blur2"><feGaussianBlur stdDeviation="2.2"/></filter>
<style>
.d0{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1}}
.k{{animation-duration:{T:.0f}s;animation-timing-function:linear;animation-iteration-count:infinite}}
.hill{{stroke:#7f78c8;stroke-width:1.4;opacity:.55}} .hill2{{stroke:#4d86d8;stroke-width:1.6;opacity:.6}}
.roof{{stroke:#ffd9a0;stroke-width:2.2}} .wall{{stroke:#e8b878;stroke-width:1.6}} .win{{fill:#ffe9a8}}
.L{{fill:currentColor;fill-opacity:.38;stroke:currentColor;stroke-width:.9}}
.b0{{color:{BAND8[0]}}} .b1{{color:{BAND8[1]}}} .b2{{color:{BAND8[2]}}} .b3{{color:{BAND8[3]}}} .b4{{color:{BAND8[4]}}} .b5{{color:{BAND8[5]}}} .b6{{color:{BAND8[6]}}} .b7{{color:{BAND8[7]}}}
.stair{{stroke:#ffffff;stroke-width:1.2;opacity:.35}} .cord{{stroke:#d8c8a8;stroke-width:1.4;fill:none}} .cap{{fill:none;stroke:#e8d8b8;stroke-width:1.4}}
.fgL{{fill:currentColor;fill-opacity:.22;stroke:currentColor;stroke-width:2}} .rib{{fill:none;stroke:currentColor;stroke-width:1.3;opacity:.8}}
.sw{{animation:sw var(--sd) ease-in-out var(--sl) infinite}}
.tw{{opacity:.2;animation:twinkle var(--td) ease-in-out var(--tl) infinite}}
.ember{{fill:#ffb35a;opacity:0;animation:mote var(--md) ease-in-out var(--mdl) infinite}}
.tower{{stroke:#ffe9a0;stroke-width:2}} .crowd{{stroke:#3f6fc0;stroke-width:1.6;opacity:.65}}
.beam{{stroke:#4aa8ff;opacity:.5;stroke-linecap:round;filter:url(#blur2);animation:beamfl var(--bd) ease-in-out var(--bl) infinite}}
.sweep{{animation:sweep {16:.0f}s ease-in-out infinite alternate}}
.sl{{fill:currentColor;fill-opacity:.3;stroke:currentColor;stroke-width:1.1}} .flame{{fill:#fff4c8;stroke:none}}
.ls{{animation:ls var(--sd) ease-in-out var(--sl) infinite}}
.lot{{fill:currentColor;fill-opacity:.12;stroke:currentColor;stroke-width:2.2;stroke-linejoin:round}}
.ringspin{{animation:spin 48s linear infinite}}
@keyframes sw{{0%,100%{{transform:rotate(calc(var(--sa)*-1))}}50%{{transform:rotate(var(--sa))}}}}
@keyframes ls{{0%,100%{{transform:translateX(calc(var(--sx)*-1)) rotate(calc(var(--sa)*-1))}}50%{{transform:translateX(var(--sx)) rotate(var(--sa))}}}}
@keyframes twinkle{{0%,100%{{opacity:.15}}50%{{opacity:1}}}}
@keyframes mote{{0%{{opacity:0;transform:translate(0,0)}}25%{{opacity:.9}}75%{{opacity:.5}}100%{{opacity:0;transform:translate(var(--dx),var(--dy))}}}}
@keyframes sweep{{from{{transform:rotate(-7deg)}}to{{transform:rotate(9deg)}}}}
@keyframes beamfl{{0%,100%{{opacity:.25}}50%{{opacity:.7}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
{chr(10).join(KFS)}
</style>
</defs>
<rect width="{W}" height="{H}" fill="#02030a"/>
<rect class="k" width="{W}" height="{H}" fill="url(#bgB)" style="opacity:0;animation-name:{bgB}"/>
<rect class="k" width="{W}" height="{H}" fill="url(#bgA)" style="opacity:0;animation-name:{bgA}"/>
<g filter="url(#glow)" id="world">
<g class="k" style="opacity:0;animation-name:{fadeB}">{''.join(B)}</g>
<g class="k" style="opacity:0;animation-name:{fadeA}"><g class="k" style="transform-origin:480px 300px;animation-name:{CAM_A}">{''.join(A)}</g></g>
{''.join(LOT)}
</g>
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print('wrote', os.path.normpath(OUT), len(svg) // 1024, 'KB', len(KFS), 'keyframes')
