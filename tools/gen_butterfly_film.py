#!/usr/bin/env python3
"""Looping laser line-art film: butterflies, flowers, clouds. Scene times below are in "story seconds" (180 s);
every motion is slowed by SLOW (default 1.25) so the real length is 180*SLOW = 225 s (3:45).
   0- 14  A  lake landscape (mountains / pines / river), butterfly rests on a cosmos, lifts off
  14- 28  B  five butterflies cross the sky, left -> right
  28- 42  C  four butterflies glide down and land on the cosmos
  42- 56  D  wind: streaks, bending meadow, blowing petals, butterflies lift off
  56- 70  E  close-up: big flowers, sun, butterflies circling
  70- 90  F  river: butterflies fly right -> left over the water, mirrored reflections
  90-110  G  rainbow: a V-formation of seven butterflies flies beneath it
 110-130  H  close-up again: butterflies land on the big flowers (slow wing beats)
 130-150  I  whirlwind: petals spiral, butterflies rise in spirals
 150-165  J  six butterflies come back down to the meadow
 165-180  K  farewell: they rise to a small sun, shrinking away -> loops to A
usage: python3 tools/gen_butterfly_film.py [seed] [--slow=1.25] [--sun] [--out=PATH]   -> flowers/butterfly_film.svg
(no sun by default: the butterflies of the last act fly up and scatter into light instead)
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_butterfly_meadow as m  # noqa: E402

W, H, T = m.W, m.H, 180.0
K = next((float(a.split('=')[1]) for a in sys.argv if a.startswith('--slow=')), 1.25)
CYC = T * K          # real length of one loop in seconds
SEED = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 21
SUN = '--sun' in sys.argv
OUT = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--out=')), None) or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flowers', 'butterfly_film.svg')
R = random.Random(SEED)
KFS = []


def kfs(points):
    pts = [(min(t, T), p) for t, p in points if t <= T + 1e-9]
    if pts[-1][0] < T:
        pts.append((T, pts[-1][1]))
    out, last = [], -1
    for t, p in pts:
        if t <= last:
            t = last + 0.002
        out.append((t, p))
        last = t
    KFS.append('@keyframes q%d{%s}' % (len(KFS), ''.join(f'{t/T*100:.4f}%{{{p}}}' for t, p in out)))
    return f'q{len(KFS)-1}'


def multi_window(wins, fade=1.0, end_fade=None):
    pts = [(0, 'opacity:0')]
    for a, b in wins:
        pts += [(a, 'opacity:0'), (a + fade, 'opacity:1'), (b - (end_fade or fade) + fade, 'opacity:1'), (b + fade, 'opacity:0')]
    return kfs(pts)


def window(a, b, fade=.4):
    return kfs([(0, 'opacity:0'), (a, 'opacity:0'), (a + fade, 'opacity:1'), (b, 'opacity:1'), (b + fade, 'opacity:0'), (T, 'opacity:0')])


def motion(start, dur, fade=.4, shrink=None):
    f = fade / dur * 100
    return kfs([(0, 'offset-distance:0%;opacity:0'), (start, 'offset-distance:0%;opacity:0'),
                (start + fade, f'offset-distance:{f:.2f}%;opacity:1'), (start + dur - fade, f'offset-distance:{100-f:.2f}%;opacity:1'),
                (start + dur, 'offset-distance:100%;opacity:0'), (T, 'offset-distance:100%;opacity:0')])


class Cyc(m.Scene):
    """draw-on that restarts at the start of each window (a, b)"""
    def __init__(self, wins):
        super().__init__(0)
        self.wins = wins

    def _pts(self, prop, v0, v1, s, t):
        pts = [(0, f'{prop}:{v0}')]
        for a, b in self.wins:
            pts += [(a + s, f'{prop}:{v0}'), (a + s + t, f'{prop}:{v1}'), (b + 1.8, f'{prop}:{v1}'), (b + 1.9, f'{prop}:{v0}')]
        return kfs(pts)

    def path(self, d, cls, s, t, col=None):
        c = f';stroke:{col}' if col else ''
        self.els.append(f'<path class="d0 k {cls}" pathLength="1" style="animation-name:{self._pts("stroke-dashoffset", 1, 0, s, t)}{c}" d="{d}"/>')

    def dot(self, x, y, r, cls, s, col=None):
        c = f';fill:{col}' if col else ''
        self.els.append(f'<circle class="k {cls}" style="opacity:0;animation-name:{self._pts("opacity", 0, 1, s, .5)}{c}" cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>')


class Once(m.Scene):
    def path(self, d, cls, s, t, col=None):
        c = f';stroke:{col}' if col else ''
        self.els.append(f'<path class="d1 {cls}" pathLength="1" style="--s:{s:.2f}s;--t:{t:.2f}s{c}" d="{d}"/>')

    def dot(self, x, y, r, cls, s, col=None):
        c = f';fill:{col}' if col else ''
        self.els.append(f'<circle class="fi1 {cls}" style="--s:{s:.2f}s{c}" cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>')


def sway_wrap(S, i0, x):
    amp = R.uniform(1.2, 3.6) * (-1 if R.random() < .5 else 1)
    dur = R.uniform(2.6, 5.4)
    S.els[i0:] = [f'<g class="sway" style="--sa:{amp:.2f}deg;--sd:{dur*K:.2f}s;--sl:-{R.uniform(0, dur):.2f}s;'
                  f'transform-origin:{x:.1f}px {H}px">' + ''.join(S.els[i0:]) + '</g>']


# ---------- butterfly parts ----------
WING = ''.join(f'<path class="{c}" d="{d}"/>' for d, c, _ in m.WING)
BODY = ('<path class="body" d="M0 -24 C-5 -20 -5 -10 0 -6 C5 -10 5 -20 0 -24 Z M0 -6 C-4 10 -4 36 0 54 C4 36 4 10 0 -6"/>'
        '<path class="ant" d="M-2 -24 C-8 -44 -20 -56 -34 -62 M2 -24 C8 -44 20 -56 34 -62"/>')


def bf_body(cls, bd, bl):
    return (f'<g class="{cls}" style="--bd:{bd*K:.2f}s;--bl:-{bl:.2f}s"><g class="flap">{WING}</g>'
            f'<g transform="scale(-1 1)"><g class="flap">{WING}</g></g>{BODY}</g>')


def pal_of(i):
    return m.BFLY[i % 3]


def fmt(pts):
    d = f'M{pts[0][0]:.0f} {pts[0][1]:.0f}'
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        xm = (xa + xb) / 2
        d += f' C{xm:.0f} {ya:.0f} {xm:.0f} {yb:.0f} {xb:.0f} {yb:.0f}'
    return d


def wpts(y0, y1, amp, x0=-120, x1=1080, seg=4):
    return [(x0 + k * (x1 - x0) / seg, y0 + (y1 - y0) * k / seg + (R.uniform(-amp, amp) if 0 < k < seg else 0)) for k in range(seg + 1)]


def lpath(pts):
    return 'M' + ' L'.join(f'{x:.0f} {y:.0f}' for x, y in pts)


def flyer(path_d, sc, pal, start, dur, fade=.4, shrink=False, refl=False, ease=None):
    inner = f'{bf_body("beat", round(R.uniform(.45, .75), 2), R.uniform(0, .5))}'
    if shrink:
        sk = kfs([(0, 'transform:scale(1)'), (start, 'transform:scale(1)'), (start + dur, 'transform:scale(.22)'), (T, 'transform:scale(.22)')])
        inner = f'<g class="k" style="animation-name:{sk}">{inner}</g>'
    e = f';animation-timing-function:{ease}' if ease else ''
    g = (f'<g class="mv" style="offset-path:path(\'{path_d}\');animation-name:{motion(start, dur, fade)}{e}">'
         f'<g transform="scale({sc:.2f})" style="--w:{pal[0]};--b:{pal[1]};--e:{pal[2]}">{inner}</g></g>')
    return f'<g style="opacity:.3">{g}</g>' if refl else g


def perched(px, cy, sc, pal, a, b, i):
    return (f'<g class="k" style="opacity:0;animation-name:{window(a, b)}"><g transform="translate({px:.0f} {cy:.0f}) scale({sc:.2f})" '
            f'style="--w:{pal[0]};--b:{pal[1]};--e:{pal[2]}"><g class="bobS" style="--bl:-{i*.7:.1f}s">'
            f'<g class="flapS" style="--bl:-{i*.5:.1f}s">{WING}</g><g transform="scale(-1 1)"><g class="flapS" style="--bl:-{i*.5:.1f}s">{WING}</g></g>{BODY}</g></g></g>')


def land_and_leave(px, ptop, sc, pal, land0, lift, i, dest=None, shrink=False, adur=5.0, xdur=7.5, y0=None):
    cy = ptop - 48 * sc
    y0 = y0 if y0 is not None else R.uniform(90, 200)
    arrive = f'M-120 {y0:.0f} C{px*.45:.0f} {y0-50:.0f} {px-140:.0f} {cy-130:.0f} {px:.0f} {cy+15*sc:.0f}'
    if dest:
        leave = f'M{px:.0f} {cy+15*sc:.0f} C{px:.0f} {cy-120:.0f} {dest[0]:.0f} {dest[1]+120:.0f} {dest[0]:.0f} {dest[1]:.0f}'
    else:
        leave = f'M{px:.0f} {cy+15*sc:.0f} C{px+60:.0f} {cy-120:.0f} {px+260:.0f} {cy-60:.0f} 1080 {R.uniform(60, 200):.0f}'
    return [flyer(arrive, sc, pal, land0, adur, ease='cubic-bezier(.2,.6,.3,1)'), perched(px, cy, sc, pal, land0 + adur, lift, i),
            flyer(leave, sc, pal, lift, xdur, shrink=shrink, ease='cubic-bezier(.6,0,.8,.6)')]


layers = {}   # name -> (opacity keyframes name, elements)
bfl = []      # butterflies / petals on top

# ---------- meadow strip (drawn once) ----------
MS = Once(0)
BIG = [(150, 1.0), (390, .85), (640, .95), (850, .8)]
perch = []
extra_perch = []
for k, (bx, sc) in enumerate(BIG):
    i0 = len(MS.els)
    m.cosmos(MS, R, bx, 462, .8 * sc, R.choice(m.PINKS), .2 + k * .4)
    perch.append((bx, 462 - 100 * .8 * sc))
    sway_wrap(MS, i0, bx)
CALM_YELLOW, CALM_LAV = ['#ffd23f', '#fff4a0'], ['#a78bff', '#c9a6ff']
# small flowers fill the gaps between the big cosmos: tall / short alternate so the strip reads as one rhythm
FILL = [(55, 'tiny'), (225, 'lupine'), (305, 'daisy'), (470, 'bud'), (555, 'daisy'), (730, 'lupine'), (790, 'tiny'), (920, 'daisy')]
for i, (x, kind) in enumerate(FILL):
    x += R.uniform(-8, 8)
    i0, d = len(MS.els), 1.0 + i * .3
    if kind == 'lupine':
        m.lupine(MS, R, x, R.uniform(395, 420), R.uniform(95, 115), R.choice(CALM_LAV), d)
    elif kind == 'daisy':
        y, sc = R.uniform(470, 495), R.uniform(.45, .6)
        m.daisy(MS, R, x, y, sc, R.choice(m.WHITE), d)
        extra_perch.append((x, y - 54 * sc))
    elif kind == 'bud':
        m.bud(MS, R, x, R.uniform(470, 490), R.uniform(.6, .8), R.choice(m.PINKS), d)
    else:
        m.tiny(MS, R, x, R.uniform(485, 510), R.uniform(.9, 1.2), R.choice(CALM_YELLOW + CALM_LAV + m.WHITE), d)
    sway_wrap(MS, i0, x)


def interp(pts, t):
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t0 <= t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0) if t1 > t0 else v1
    return pts[-1][1]


skew = [(0, 0), (42, 0), (44, -4), (46, 1), (48, -5), (50, -2), (52, -4), (54.5, 0), (130, 0), (132, -5), (135, 1), (138, -6), (141, -2),
        (144, -5), (147, 0), (T, 0)]
vis = [(0, 1), (55, 1), (56.5, 0), (88.5, 0), (90, 1), (108.5, 1), (110, 0), (128.5, 0), (130, 1), (T, 1)]
times = sorted({t for t, _ in skew} | {t for t, _ in vis})
meadow_kf = kfs([(t, f'transform:skewX({interp(skew, t):.2f}deg);opacity:{interp(vis, t):.2f}') for t in times])

# ---------- A: lake landscape (0-14) and F: river (70-90) ----------


def landscape(C, lake_rows):
    def mk(d, cls, a, t):
        C.path(d, cls, a, t)
    mk('M0 215 L90 150 L140 180 L230 100 L330 190 L400 150 L470 205 L560 130 L660 200 L740 160 L830 210 L960 150', 'mtn', .2, 2.6)
    mk('M230 100 L255 130 L240 128 L228 142 L214 126 L205 130 Z', 'mtn', 1.8, .8)
    mk('M560 130 L582 158 L570 156 L558 168 L546 154 L538 158 Z', 'mtn', 2.0, .8)

    def tree(x, y, h, d):
        w = .3 * h
        pts = [(0, -h)]
        for k in range(3):
            top = -h + k * h * .28
            pts += [(w * (.45 + k * .2) * .55, top + h * .3), (w * (.25 + k * .2) * .55, top + h * .3)]
        pts += [(w, 0)]
        seq = pts + [(-px, py) for px, py in reversed(pts[1:])]
        mk('M' + ' L'.join(f'{x+px:.1f} {y+py:.1f}' for px, py in seq) + ' Z', 'tree', d, 1.0)
    for i, (tx, ty, th) in enumerate([(40, 262, 110), (95, 270, 85), (150, 258, 120), (205, 268, 70),
                                      (770, 262, 75), (825, 258, 120), (885, 268, 90), (935, 260, 105)]):
        tree(tx, ty, th, 1.2 + .15 * i)
    for k, (y, x0, x1) in enumerate(lake_rows):
        mk(f'M{x0} {y}' + ' q10 -6 20 0 t20 0' * int((x1 - x0) / 40), 'lake', 2.6 + .12 * k, 1.5)


C1 = Cyc([(0, 14.4)])
landscape(C1, [(228, 250, 720), (242, 290, 680), (256, 330, 640)])
layers['A'] = (kfs([(0, 'opacity:1'), (12.2, 'opacity:1'), (14.4, 'opacity:0'), (T, 'opacity:0')]), C1.els)

C2 = Cyc([(70, 88.5)])
landscape(C2, [(236 + 22 * k, 0 + 6 * k, 960 - 6 * k) for k in range(7)])
for j in range(4):          # reeds along the bottom corners
    for side in (0, 1):
        rx = (28 + j * 24) if side == 0 else (W - 28 - j * 24)
        h = R.uniform(60, 130)
        C2.path(f'M{rx} {H} C{rx+R.uniform(-10,10):.0f} {H-h*.5:.0f} {rx+R.uniform(-14,14):.0f} {H-h*.8:.0f} {rx+R.uniform(-16,16):.0f} {H-h:.0f}', 'stem', 4 + j * .12, .8)
        if j % 2 == 0:
            C2.path(m.circ(rx, H - h - 8, 4), 'ctr', 5 + j * .12, .4)
layers['F'] = (multi_window([(70, 88.5)], 1.0, 1.5), C2.els)

# ---------- E/H: close-up flowers + sun ----------
C3 = Cyc([(56, 70), (110, 130)])
for fn, args in [(m.lupine, (900, 340, 170, '#8f9bff', 1.4)),
                 (m.cosmos, (300, 300, 1.45, '#ff6fb5', .5)), (m.daisy, (690, 350, 1.8, '#ffffff', 1.0)),
                 (m.cosmos, (520, 450, .7, '#ffb3da', 1.8)), (m.tiny, (150, 490, 1.4, '#ffe45a', 2.2)), (m.tiny, (800, 500, 1.3, '#c9a6ff', 2.3))]:
    i0 = len(C3.els)
    fn(C3, R, *args)
    sway_wrap(C3, i0, args[0])
if SUN:
    sunx, suny = 800, 100
    rays = ''.join(f'M{sunx+58*math.cos(a):.1f} {suny+58*math.sin(a):.1f} L{sunx+88*math.cos(a):.1f} {suny+88*math.sin(a):.1f} '
                   for a in [k * math.pi / 6 for k in range(12)])
    C3.els.append(f'<g class="spin" style="transform-origin:{sunx}px {suny}px">'
                  f'<path class="d0 k sunr" pathLength="1" style="animation-name:{C3._pts("stroke-dashoffset", 1, 0, .6, 2.0)}" d="{rays}"/></g>')
    C3.path(m.circ(sunx, suny, 40), 'sunr', .4, 1.4)
layers['E'] = (multi_window([(56, 70), (110, 130)], 1.0, 1.0), C3.els)

# ---------- G: rainbow (90-110) ----------
C4 = Cyc([(90, 110)])
for k, col in enumerate(['#ff5a5a', '#ffa14a', '#ffe45a', '#5aff9a', '#5ad7ff', '#a78bff']):
    r = 360 - k * 18
    C4.path(f'M{480-r} 470 A{r} {r*.75:.0f} 0 0 1 {480+r} 470', 'rb', .3 + k * .45, 1.6, col)
layers['G'] = (multi_window([(90, 110)], 1.0, 1.0), C4.els)

# ---------- K: (optional) small sun (165-180) ----------
C5 = Cyc([(165, T - 2)])
if SUN:
    C5.path(m.circ(480, 170, 34), 'sunr', .3, 1.4)
    C5.els.append('<path class="d0 k sunr" pathLength="1" style="animation-name:%s" d="%s"/>' % (
        C5._pts("stroke-dashoffset", 1, 0, .8, 1.8),
        ''.join(f'M{480+48*math.cos(a):.1f} {170+48*math.sin(a):.1f} L{480+70*math.cos(a):.1f} {170+70*math.sin(a):.1f} ' for a in [k * math.pi / 6 for k in range(12)])))
else:       # the butterflies dissolve into a burst of light where they meet in the sky
    for k in range(16):
        ang = k * 2 * math.pi / 16 + R.uniform(-.1, .1)
        r = R.uniform(60, 130)
        nm = kfs([(0, 'transform:translate(0px,0px);opacity:0'), (174.2, 'transform:translate(0px,0px);opacity:0'), (174.8, 'transform:translate(0px,0px);opacity:1'),
                  (179, f'transform:translate({r*math.cos(ang):.0f}px,{r*math.sin(ang)*.8-25:.0f}px);opacity:0')])
        C5.els.append(f'<circle class="k" style="opacity:0;fill:#ffe9b0;animation-name:{nm}" cx="480" cy="178" r="{R.choice([1.6, 2.2, 2.8])}"/>')
layers['K'] = (kfs([(0, 'opacity:0'), (165, 'opacity:0'), (166, 'opacity:1'), (T - 1.5, 'opacity:1'), (T, 'opacity:0')]), C5.els)

# ================= butterflies / petals =================
# A: rests on cosmos, lifts off
px, ptop = perch[1]
cy = ptop - 48 * .72
bfl.append(perched(px, cy, .72, pal_of(0), 3.5, 11.4, 0))
bfl.append(flyer(f'M{px:.0f} {cy+10:.0f} C{px+70:.0f} {cy-140:.0f} {px+330:.0f} {cy-70:.0f} 1080 140', .72, pal_of(0), 11.4, 9.5))
# B: crossing
for i, yb in enumerate([100, 190, 280]):
    sc = R.uniform(.45, .8)
    bfl.append(flyer(fmt(wpts(yb, yb + R.uniform(-20, 20), 22)), sc, pal_of(i), 14.3 + i * 2.2, R.uniform(10, 13) / (.6 + sc)))
# C/D: landing, rest, lift
for i, (px, ptop) in enumerate([perch[0], perch[2], perch[3]]):
    bfl += land_and_leave(px, ptop, R.uniform(.55, .75), pal_of(i + 1), 28.4 + i * 1.8, 43.6 + i * .9, i)
# D: wind streaks + petals
for t0, y in [(42.6, 130), (45.4, 250), (48.0, 180)]:
    p = fmt(wpts(y, y + R.uniform(-30, 30), 25, -50, 1010, 5))
    nm = kfs([(0, 'stroke-dashoffset:.2'), (t0, 'stroke-dashoffset:.2'), (t0 + 3.6, 'stroke-dashoffset:-1'), (T, 'stroke-dashoffset:-1')])
    bfl.append(f'<path class="wind k" pathLength="1" style="animation-name:{nm}" d="{p}"/>')
PET = 'M0 0 C6 -7 15 -5 18 2 C13 9 4 9 0 0 Z'
for j in range(8):
    sx, sy = R.uniform(40, 800), R.uniform(380, 470)
    bfl.append(f'<path class="petal mv" style="offset-path:path(\'{fmt(wpts(sy, sy - R.uniform(80, 280), 60, sx, sx + R.uniform(300, 600), 3))}\');'
               f'animation-name:{motion(43.2 + j * 1.3, R.uniform(5, 8), .6)}" d="{PET}"/>')
# E: circling butterflies + falling petals (inside own window group)
orb = []
for i in range(2):
    cx0, cy0 = 480 + R.uniform(-40, 40), 270 + R.uniform(-20, 20)
    ax, ay, ph = R.uniform(260, 340), R.uniform(90, 140), R.uniform(0, 6.28)
    pts = [(cx0 + ax * math.cos(t + ph), cy0 + ay * math.sin(2 * t + ph * .5) * (.6 if i else 1) + 20 * math.sin(t))
           for t in [k * 2 * math.pi / 90 for k in range(91)]]
    dur, sc, pal = R.uniform(10, 15), R.uniform(.5, .8), pal_of(i)
    orb.append(f'<g class="orb" style="offset-path:path(\'{lpath(pts)} Z\');--od:{dur*K:.1f}s;--ol:-{R.uniform(0, dur):.1f}s">'
               f'<g transform="scale({sc:.2f})" style="--w:{pal[0]};--b:{pal[1]};--e:{pal[2]}">{bf_body("beat", round(R.uniform(.45, .75), 2), R.uniform(0, .5))}</g></g>')
for j in range(4):
    sx = R.uniform(60, 900)
    d = f'M{sx:.0f} -20 C{sx+R.uniform(-120,120):.0f} 120 {sx+R.uniform(-120,120):.0f} 260 {sx+R.uniform(-60,60):.0f} 560'
    dur = R.uniform(7, 11)
    orb.append(f'<path class="petal orb" style="opacity:1;offset-path:path(\'{d}\');--od:{dur*K:.1f}s;--ol:-{R.uniform(0, dur):.1f}s" d="{PET}"/>')
bfl.append(f'<g class="k" style="opacity:0;animation-name:{window(56.4, 68.6, 1.0)}">{"".join(orb)}</g>')
# F: right -> left over the river, with reflections (water line y=228 mirrored)
YW = 228
for i, yb in enumerate([105, 165, 205]):
    sc = R.uniform(.45, .7)
    pts = wpts(yb, yb + R.uniform(-15, 15), 20, 1080, -120)
    st, du = 71 + i * 2.6, R.uniform(10, 14) / (.6 + sc)
    bfl.append(flyer(fmt(pts), sc, pal_of(i + 2), st, du))
    bfl.append(flyer(fmt([(x, 2 * YW - y) for x, y in pts]), sc * .9, pal_of(i + 2), st, du, refl=True))
# G: V formation + three small crossers
lead = wpts(330, 300, 30, -120, 1080, 4)
for k in range(5):
    row, side = (k + 1) // 2, (-1 if k % 2 else 1)
    dx, dy = -75 * row, 48 * row * side if k else 0
    bfl.append(flyer(fmt([(x + dx, y + dy) for x, y in lead]), .6 if k else .72, pal_of(k), 92, 12.5))
# H: land on the close-up flowers
for i, (px, ptop, sc) in enumerate([(300, 150, .95), (400, 225, .6), (690, 252, .75)]):
    bfl += land_and_leave(px, ptop, sc, pal_of(i), 111.5 + i * 1.7, 124.2 + i * .9, i, adur=4.6, xdur=6, y0=R.uniform(60, 120))
# I: whirlwind
for j in range(12):
    th0 = R.uniform(0, 6.28)
    rr0, rr1 = R.uniform(20, 60), R.uniform(200, 330)
    pts = [(480 + (rr0 + (rr1 - rr0) * u) * math.cos(th0 + u * 7), 300 + (rr0 + (rr1 - rr0) * u) * .45 * math.sin(th0 + u * 7) - u * 60)
           for u in [k / 40 for k in range(41)]]
    bfl.append(f'<path class="petal mv" style="offset-path:path(\'{lpath(pts)}\');animation-name:{motion(131 + j * 1.2, R.uniform(6, 9), .6)}" d="{PET}"/>')
for i in range(3):
    th0 = i * 2.09
    pts = [(480 + (110 + 90 * u) * math.cos(th0 + u * 9.5), 430 - u * 380 + 40 * math.sin(th0 + u * 9.5)) for u in [k / 80 for k in range(81)]]
    bfl.append(flyer(lpath(pts), R.uniform(.45, .65), pal_of(i), 132 + i * 2.2, 11, shrink=False))
for j, (cx_, cy_, rx_, ry_) in enumerate([(480, 300, 300, 90), (480, 320, 360, 110)]):
    nm = kfs([(0, 'stroke-dashoffset:.2'), (131 + j * 1.6, 'stroke-dashoffset:.2'), (131 + j * 1.6 + 6, 'stroke-dashoffset:-1'), (T, 'stroke-dashoffset:-1')])
    bfl.append(f'<path class="wind k" pathLength="1" style="animation-name:{nm}" d="M{cx_-rx_} {cy_} A{rx_} {ry_} 0 1 1 {cx_+rx_} {cy_} A{rx_} {ry_} 0 1 1 {cx_-rx_} {cy_}"/>')
# J + K: come back, rest, then rise to the sun and shrink away
spots = perch
for i, (px, ptop) in enumerate(spots):
    bfl += land_and_leave(px, ptop, R.uniform(.5, .7), pal_of(i + 2), 150.4 + i * 1.4, 165.4 + i * .9, i, dest=(480 + R.uniform(-30, 30), 175),
                          shrink=True, adur=4.5, xdur=9)

clouds = []
for i in range(3):
    s = R.uniform(.9, 1.3)
    y = 45 + i * 40 + R.uniform(-6, 6)
    dur = R.uniform(55, 90)
    clouds.append(f'<g transform="translate(0 {y:.0f})"><g class="drift" style="--dd:{dur*K:.0f}s;--dl:-{R.uniform(0, dur):.0f}s">'
                  f'<path class="d1 cloud" pathLength="1" style="--s:{.3 + i*.5:.1f}s;--t:1.4s" d="{m.cloud_d(s)}"/></g></g>')

lay = ''.join(f'<g class="k" style="opacity:0;animation-name:{nm}">{"".join(els)}</g>' for nm, els in layers.values())
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>Butterfly film (3 min) - laser line art</title>
<defs>
<radialGradient id="bg" cx="50%" cy="45%" r="70%"><stop offset="0" stop-color="#14183a"/><stop offset="1" stop-color="#080a1a"/></radialGradient>
<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.d0,.d1{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1}}
.d1{{animation:draw var(--t,1s) ease-out var(--s,0s) forwards}}
.fi1{{opacity:0;animation:fade .5s ease-out var(--s,0s) forwards}}
.cloud{{stroke:#e8f0ff;stroke-width:1.8}} .stem{{stroke:#3df2c0;stroke-width:2.4}}
.pet{{stroke:#ff6fb5;stroke-width:2.2}} .pet2{{stroke:#ffb3da;stroke-width:1.5}}
.ctr{{stroke:#ffd23f;stroke-width:2.2}} .ctrd{{fill:#ffd23f}}
.mtn{{stroke:#7aa8ff;stroke-width:2.2}} .tree{{stroke:#3df2c0;stroke-width:1.8}} .lake{{stroke:#5ad7ff;stroke-width:1.6}} .rb{{stroke-width:3.4}}
.wing,.stripe,.band,.eye,.body,.ant{{fill:none;stroke-linecap:round;stroke-linejoin:round}}
.wing{{stroke:var(--w);stroke-width:3}} .stripe{{stroke:#ffffff;stroke-width:2.2}} .band{{stroke:var(--b);stroke-width:3.2}}
.eye{{stroke:var(--e);stroke-width:2.6}} .body{{stroke:#ffffff;stroke-width:2.8}} .ant{{stroke:#ffffff;stroke-width:1.8}}
.petal{{fill:none;stroke:#ff9fd0;stroke-width:1.8;stroke-linejoin:round;opacity:0}}
.wind{{fill:none;stroke:#bfe9ff;stroke-width:2;stroke-linecap:round;stroke-dasharray:.2 2;stroke-dashoffset:.2}}
.sunr{{stroke:#ffd23f;stroke-width:2.4;fill:none;stroke-linecap:round}} .spin{{animation:spin {40*K:.0f}s linear infinite}}
.orb{{offset-rotate:auto 90deg;animation:orbit var(--od) linear var(--ol) infinite}}
.k,.mv,.meadow{{animation-duration:{CYC:.0f}s;animation-timing-function:linear;animation-iteration-count:infinite}}
.mv{{opacity:0;offset-rotate:auto 90deg}}
.meadow{{transform-origin:0 {H}px;animation-name:{meadow_kf}}}
.flap{{animation:flap var(--bd) ease-in-out var(--bl) infinite}}
.flapS{{animation:flapS {2.4*K:.2f}s ease-in-out var(--bl) infinite}}
.bobS{{animation:bob {3.2*K:.2f}s ease-in-out var(--bl) infinite}}
.sway{{animation:sway var(--sd) ease-in-out var(--sl) infinite}}
.drift{{animation:drift var(--dd) linear var(--dl) infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}} @keyframes orbit{{from{{offset-distance:0%}}to{{offset-distance:100%}}}}
@keyframes draw{{to{{stroke-dashoffset:0}}}} @keyframes fade{{to{{opacity:1}}}}
@keyframes flap{{0%,100%{{transform:scaleX(1)}}50%{{transform:scaleX(.2)}}}}
@keyframes flapS{{0%,100%{{transform:scaleX(1)}}50%{{transform:scaleX(.5)}}}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-4px)}}}}
@keyframes sway{{0%,100%{{transform:rotate(calc(var(--sa)*-1))}}50%{{transform:rotate(var(--sa))}}}}
@keyframes drift{{from{{transform:translateX(-300px)}}to{{transform:translateX({W+60}px)}}}}
{chr(10).join(KFS)}
</style>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<g filter="url(#glow)">
{''.join(clouds)}
{lay}
<g class="meadow">{''.join(MS.els)}</g>
{''.join(bfl)}
</g>
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print('wrote', os.path.normpath(OUT), len(svg) // 1024, 'KB', len(KFS), 'keyframes;', f'{CYC:.0f} s loop')
