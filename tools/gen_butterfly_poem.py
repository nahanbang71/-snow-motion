#!/usr/bin/env python3
"""'A single butterfly' - a quiet, emotional 96 s laser-line film (loops).
   0-16   dawn      the light slowly comes up, one flower opens
  16-32   meeting   a lonely butterfly wanders in, hesitates, lands; ripples spread from the flower
  32-48   rest      it rests (slow wing beats), the meadow starts to bloom outward from the flower
  48-60   dance     the others are drawn in; butterflies circle the flower, leaving light-dust trails
  60-78   golden    the sky warms; two butterflies draw a heart in the air, the rest settle on flowers
  78-96   goodbye   they fly up into the sky and scatter into light, flowers close, one butterfly stays
usage: python3 tools/gen_butterfly_poem.py [seed] [--slow=1.0] [--laser]   -> flowers/butterfly_poem.svg
--sun: draw the sun (off by default)
--text: add Korean subtitles (for the rendered video; needs a Hangul-capable system font)
--out=PATH: write somewhere else
--laser: lines and points only on pure black (no glow, gradients, sun halo, pollen motes, tinted sky) -> butterfly_poem_laser.svg
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_butterfly_meadow as m  # noqa: E402

W, H, T = m.W, m.H, 96.0
K = next((float(a.split('=')[1]) for a in sys.argv if a.startswith('--slow=')), 1.0)
CYC = T * K
LASER = '--laser' in sys.argv
TEXT = '--text' in sys.argv
SUN = '--sun' in sys.argv      # off by default: the dark sky reads better without it
SEED = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 5
OUT = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--out=')), None) or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flowers', 'butterfly_poem_laser.svg' if LASER else 'butterfly_poem.svg')
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


def window(a, b, fade=1.2):
    return kfs([(0, 'opacity:0'), (a, 'opacity:0'), (a + fade, 'opacity:1'), (b, 'opacity:1'), (b + fade, 'opacity:0'), (T, 'opacity:0')])


def motion(start, dur, fade=.6):
    f = fade / dur * 100
    return kfs([(0, 'offset-distance:0%;opacity:0'), (start, 'offset-distance:0%;opacity:0'), (start + fade, f'offset-distance:{f:.2f}%;opacity:1'),
                (start + dur - fade, f'offset-distance:{100-f:.2f}%;opacity:1'), (start + dur, 'offset-distance:100%;opacity:0'), (T, 'offset-distance:100%;opacity:0')])


class Static(m.Scene):
    def path(self, d, cls, s, t, col=None):
        c = f' style="stroke:{col}"' if col else ''
        self.els.append(f'<path class="sd {cls}" d="{d}"{c}/>')

    def dot(self, x, y, r, cls, s, col=None):
        c = f' style="fill:{col}"' if col else ''
        self.els.append(f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="{r}"{c}/>')


def fmt(pts):
    d = f'M{pts[0][0]:.0f} {pts[0][1]:.0f}'
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        xm = (xa + xb) / 2
        d += f' C{xm:.0f} {ya:.0f} {xm:.0f} {yb:.0f} {xb:.0f} {yb:.0f}'
    return d


def lpath(pts, close=False):
    return 'M' + ' L'.join(f'{x:.0f} {y:.0f}' for x, y in pts) + (' Z' if close else '')


# ---------- butterfly parts ----------
WING = ''.join(f'<path class="{c}" d="{d}"/>' for d, c, _ in m.WING)
BODY = ('<path class="body" d="M0 -24 C-5 -20 -5 -10 0 -6 C5 -10 5 -20 0 -24 Z M0 -6 C-4 10 -4 36 0 54 C4 36 4 10 0 -6"/>'
        '<path class="ant" d="M-2 -24 C-8 -44 -20 -56 -34 -62 M2 -24 C8 -44 20 -56 34 -62"/>')
PAL = [('#ffd27a', '#ff8fb4', '#ffb36b'), ('#d9c2ff', '#7fb0ff', '#ffd27a'), ('#ffb0cc', '#ffd27a', '#ff8f6b')]


def body(beat):
    return (f'<g class="flap" style="--bd:{beat*K:.2f}s;--bl:-{R.uniform(0, .6):.2f}s"><g class="flap2">{WING}</g>'
            f'<g transform="scale(-1 1)"><g class="flap2">{WING}</g></g>{BODY}</g>')


def pv(p):
    return f'--w:{p[0]};--b:{p[1]};--e:{p[2]}'


def flyer(path_d, sc, pal, start, dur, beat=.7, ease=None, shrink=False, fade=.6):
    e = f';animation-timing-function:{ease}' if ease else ''
    inner = body(beat)
    if shrink:
        sk = kfs([(0, 'transform:scale(1)'), (start, 'transform:scale(1)'), (start + dur, 'transform:scale(.2)'), (T, 'transform:scale(.2)')])
        inner = f'<g class="k" style="animation-name:{sk}">{inner}</g>'
    return (f'<g class="mv" style="offset-path:path(\'{path_d}\');animation-name:{motion(start, dur, fade)}{e}">'
            f'<g transform="scale({sc:.2f})" style="{pv(pal)}">{inner}</g></g>')


def perched(px, cy, sc, pal, a, b, i=0):
    return (f'<g class="k" style="opacity:0;animation-name:{window(a, b)}"><g transform="translate({px:.0f} {cy:.0f}) scale({sc:.2f})" style="{pv(pal)}">'
            f'<g class="bobS" style="--bl:-{i*.9:.1f}s"><g class="flapS" style="--bl:-{i*.6:.1f}s">{WING}</g>'
            f'<g transform="scale(-1 1)"><g class="flapS" style="--bl:-{i*.6:.1f}s">{WING}</g></g>{BODY}</g></g></g>')


def orbiter(path_d, sc, pal, od, ol, dots=6, lag=.33):
    """butterfly on a closed loop + a trail of fading light-dust behind it"""
    out = (f'<g class="orb" style="offset-path:path(\'{path_d}\');--od:{od*K:.1f}s;--ol:{ol*K:.2f}s">'
           f'<g transform="scale({sc:.2f})" style="{pv(pal)}">{body(R.uniform(.7, .95))}</g></g>')
    for j in range(1, dots + 1):
        out += (f'<circle class="orb mote2" r="{max(.8, 3.0 - j*.4):.1f}" style="offset-path:path(\'{path_d}\');--od:{od*K:.1f}s;'
                f'--ol:{(ol + lag*j)*K:.2f}s;fill:{pal[0]};opacity:{.8 - j*.11:.2f}"/>')
    return out


def heart(t, cx=300, cy=190, s=6.0):
    return (cx + s * 16 * math.sin(t) ** 3,
            cy - s * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)))


layers = []          # back to front, inside the slowly breathing camera
CX, CY = 480, 380    # the hero flower

# ---------- backdrop ----------
ridge = Static(0)
ridge.els.append('<path class="d1 ridge" pathLength="1" style="--s:.5s;--t:3s" d="M0 262 C120 240 220 270 340 255 S560 236 700 260 S880 250 960 258"/>')
ridge.els.append('<path class="d1 hill" pathLength="1" style="--s:1s;--t:3.5s" d="M0 480 C160 462 320 478 480 470 S800 458 960 474"/>')
layers += ridge.els

sunx, suny = 700, 150
sun_kf = kfs([(0, 'transform:translateY(130px);opacity:0;color:#ffd7a0'), (2, 'transform:translateY(128px);opacity:0;color:#ffd7a0'),
              (6, 'transform:translateY(110px);opacity:1;color:#ffd7a0'), (16, 'transform:translateY(0px);opacity:1;color:#ffe49a'),
              (60, 'transform:translateY(0px);opacity:1;color:#ffd27a'), (80, 'transform:translateY(112px);opacity:1;color:#ff9a5a'),
              (92, 'transform:translateY(124px);opacity:1;color:#ff8a5a'), (95, 'transform:translateY(130px);opacity:0;color:#ff8a5a'),
              (T, 'transform:translateY(130px);opacity:0;color:#ffd7a0')])
rays = ''.join(f'M{sunx+58*math.cos(a):.1f} {suny+58*math.sin(a):.1f} L{sunx+86*math.cos(a):.1f} {suny+86*math.sin(a):.1f} '
               for a in [k * math.pi / 8 for k in range(16)])
if SUN:
    layers.append(f'<g class="k" style="opacity:0;animation-name:{sun_kf}"><g class="spin" style="transform-origin:{sunx}px {suny}px">'
        f'<path class="sunr" d="{rays}"/></g><path class="sunr" d="{m.circ(sunx, suny, 40)}"/>'
        f'<path class="sunr soft" d="{m.circ(sunx, suny, 50)}"/>{"" if LASER else f'<circle cx="{sunx}" cy="{suny}" r="200" fill="url(#sunglow)" style="stroke:none"/>'}</g>')

for i, (cxx, cyy, s) in enumerate([(150, 70, 1.0), (790, 105, .8)]):
    dur = (110 + i * 20) * K
    layers.append(f'<g transform="translate(0 {cyy})" style="opacity:.6"><g class="drift" style="--dd:{dur:.0f}s;--dl:-{R.uniform(0, dur):.0f}s">'
                  f'<path class="d1 cloud" pathLength="1" style="--s:{2+i}s;--t:2s" d="{m.cloud_d(s)}"/></g></g>')

# ---------- hero flower: stem grows, petals open one by one, closes at the end ----------
stem_kf = kfs([(0, 'stroke-dashoffset:1'), (2, 'stroke-dashoffset:1'), (7, 'stroke-dashoffset:0'), (92.5, 'stroke-dashoffset:0'), (95.6, 'stroke-dashoffset:1')])
layers.append(f'<path class="d0 k stem" pathLength="1" style="animation-name:{stem_kf}" d="M{CX} 482 C{CX+4} 450 {CX-6} 420 {CX} {CY+10}"/>')
leaf_kf = kfs([(0, 'stroke-dashoffset:1'), (5, 'stroke-dashoffset:1'), (9, 'stroke-dashoffset:0'), (92.5, 'stroke-dashoffset:0'), (95.5, 'stroke-dashoffset:1')])
layers.append(f'<path class="d0 k stem" pathLength="1" style="animation-name:{leaf_kf}" d="M{CX} 452 C{CX-40} 430 {CX-80} 440 {CX-96} 462 C{CX-60} 468 {CX-26} 462 {CX} 452"/>')
for i in range(8):
    a = i * math.pi / 4 + .2
    t0, tc = 7 + i * .5, 91 + i * .12
    nm = kfs([(0, 'transform:scale(.05) rotate(-40deg);opacity:0'), (t0, 'transform:scale(.05) rotate(-40deg);opacity:0'),
              (t0 + 4.5, 'transform:scale(1) rotate(0deg);opacity:1'), (tc, 'transform:scale(1) rotate(0deg);opacity:1'),
              (tc + 4.2, 'transform:scale(.6) rotate(15deg);opacity:0')])
    layers.append(f'<g class="k" style="opacity:0;transform-origin:{CX}px {CY}px;animation-name:{nm}">'
                  f'<path class="sd pet" d="{m.poly(m.PETAL, a, CX, CY, 1.0)}"/><path class="sd pet2" d="{m.poly(m.VEIN, a, CX, CY, 1.0)}"/></g>')
ctr = [f'<path class="sd ctr" d="{m.circ(CX, CY, 12)}"/>'] + [
    f'<circle class="ctrd" cx="{CX+23*math.cos(k*.628):.1f}" cy="{CY+23*math.sin(k*.628):.1f}" r="2"/>' for k in range(10)]
layers.append(f'<g class="k" style="opacity:0;animation-name:{kfs([(0, "opacity:0"), (12, "opacity:0"), (15, "opacity:1"), (92, "opacity:1"), (95.3, "opacity:0")])}">{"".join(ctr)}</g>')

# ripples from the flower when the butterfly lands
for t0 in (32.0, 33.8, 35.6):
    nm = kfs([(0, 'transform:scale(.15);opacity:0'), (t0, 'transform:scale(.15);opacity:.8'), (t0 + 4.5, 'transform:scale(1);opacity:0'), (T, 'transform:scale(1);opacity:0')])
    layers.append(f'<circle class="k ripple" style="opacity:0;transform-origin:{CX}px {CY}px;animation-name:{nm}" cx="{CX}" cy="{CY}" r="190"/>')

# ---------- the meadow blooms outward from the hero flower ----------
S = Static(0)
spots = [(310, 462, .6, 'cosmos'), (650, 458, .62, 'cosmos'), (200, 470, .45, 'daisy'), (770, 468, .5, 'daisy'), (95, 474, .4, 'cosmos'),
         (870, 474, .42, 'cosmos'), (385, 478, .35, 'daisy'), (575, 476, .35, 'daisy')]
perch_pts = []
for x, y, sc, kind in spots:
    S.els = []
    col = R.choice(m.PINKS)
    if kind == 'cosmos':
        m.cosmos(S, R, x, y, sc, col, 0)
        perch_pts.append((x, y - 100 * sc))
    else:
        m.daisy(S, R, x, y, sc, R.choice(m.WHITE), 0)
        perch_pts.append((x, y - 54 * sc))
    dist = abs(x - CX)
    to, tc = 36 + dist / 380 * 12, 84 + (1 - dist / 420) * 5
    nm = kfs([(0, 'transform:scale(.01);opacity:0'), (to, 'transform:scale(.01);opacity:0'), (to + 5, 'transform:scale(1);opacity:1'),
              (tc, 'transform:scale(1);opacity:1'), (tc + 4, 'transform:scale(.01);opacity:0')])
    amp = R.uniform(1.4, 3.2) * (-1 if R.random() < .5 else 1)
    dd = R.uniform(3.4, 5.6) * K
    layers.append(f'<g class="k" style="opacity:0;transform-origin:{x}px {y}px;animation-name:{nm}"><g class="sway" style="--sa:{amp:.2f}deg;--sd:{dd:.2f}s;'
                  f'--sl:-{R.uniform(0, dd):.2f}s;transform-origin:{x}px {H}px">{"".join(S.els)}</g></g>')

# ---------- butterflies ----------
GOLD, LILAC, ROSE = PAL
hero_top = CY - 100
sc1 = .62
cy1 = hero_top - 48 * sc1 + 6
# 16-32 the lonely one wanders in and lands
arrive = fmt([(-80, 150), (120, 240), (250, 135), (350, 240), (CX, cy1 + 15 * sc1)])
layers.append(flyer(arrive, sc1, GOLD, 16, 16, beat=1.05, ease='cubic-bezier(.3,.5,.4,1)', fade=1.0))
layers.append(perched(CX, cy1, sc1, GOLD, 32, 43.5))
layers.append(flyer(f'M{CX} {cy1+15*sc1:.0f} C{CX+30} 150 {CX+180} 200 {CX+190} 300', sc1, GOLD, 43.5, 4.5, beat=.8, ease='cubic-bezier(.6,0,.8,.6)', fade=.4))
# trail of light-dust behind the wandering butterfly
for j in range(1, 7):
    layers.append(f'<g style="opacity:{.7 - j*.09:.2f}"><g class="mv" style="offset-path:path(\'{arrive}\');animation-name:{motion(16 + j*.45, 16, 1.0)};'
                  f'animation-timing-function:cubic-bezier(.3,.5,.4,1)"><circle r="{max(.9, 3.2 - j*.4):.1f}" fill="{GOLD[0]}"/></g></g>')

# 48-60 the dance: two loops (one each way), five butterflies, trails
ellA = f'M{CX+190} 300 A190 75 0 1 1 {CX-190} 300 A190 75 0 1 1 {CX+190} 300'
ellB = f'M{CX+150} 290 A150 105 0 1 0 {CX-150} 290 A150 105 0 1 0 {CX+150} 290'
dance = ''.join([orbiter(ellA, .6, GOLD, 16, 0), orbiter(ellA, .5, ROSE, 16, 5.4), orbiter(ellA, .55, LILAC, 16, 10.6),
                 orbiter(ellB, .5, LILAC, 16, 2.0), orbiter(ellB, .55, ROSE, 16, 9.0)])
layers.append(f'<g class="k" style="opacity:0;animation-name:{window(48, 59.5)}">{dance}</g>')

# 60-78 golden hour: a heart in the air, the others rest on flowers
hp = [heart(k * 2 * math.pi / 120) for k in range(121)]
hd = lpath(hp, True)
heart_draw = kfs([(0, 'stroke-dashoffset:1;opacity:0'), (62, 'stroke-dashoffset:1;opacity:0'), (62.5, 'stroke-dashoffset:1;opacity:.55'),
                  (72, 'stroke-dashoffset:0;opacity:.55'), (78, 'stroke-dashoffset:0;opacity:.55'), (80, 'stroke-dashoffset:0;opacity:0')])
layers.append(f'<path class="d0 k heartline" pathLength="1" style="animation-name:{heart_draw}" d="{hd}"/>')
layers.append(f'<g class="k" style="opacity:0;animation-name:{window(62, 77.2)}">{orbiter(hd, .55, GOLD, 16, 0, 7, .3)}{orbiter(hd, .5, ROSE, 16, 8, 7, .3)}</g>')
for i, (px, ptop) in enumerate([perch_pts[0], perch_pts[1], perch_pts[3]]):
    sc = .45
    cy = ptop - 48 * sc + 4
    layers.append(perched(px, cy, sc, [LILAC, ROSE, GOLD][i], 60.5, 84.5, i + 1))
    layers.append(flyer(f'M{px:.0f} {cy+15*sc:.0f} C{px+30:.0f} {cy-140:.0f} {px+60:.0f} {cy-230:.0f} {px+110:.0f} {cy-300:.0f}', sc, [LILAC, ROSE, GOLD][i],
                        84.5 + i * 1.2, 8, beat=.9, ease='cubic-bezier(.6,0,.8,.6)', fade=1.2))

TX, TY = (sunx, 272) if SUN else (690, 215)
# 78-96 goodbye: the heart pair flies into the sun, shrinks, and scatters as light
for ph, pal in ((14 / 16, GOLD), (22 / 16 % 1, ROSE)):
    x0, y0 = heart(ph * 2 * math.pi)
    layers.append(flyer(f'M{x0:.0f} {y0:.0f} C{x0+160:.0f} {y0-90:.0f} 560 200 {TX} {TY}', .55, pal, 78, 12, beat=.8,
                        ease='cubic-bezier(.4,0,.6,1)', shrink=True, fade=.8))
for k in range(18):
    ang = k * 2 * math.pi / 18 + R.uniform(-.1, .1)
    r = R.uniform(70, 150)
    nm = kfs([(0, 'transform:translate(0px,0px);opacity:0'), (90, 'transform:translate(0px,0px);opacity:0'), (90.6, 'transform:translate(0px,0px);opacity:1'),
              (95, f'transform:translate({r*math.cos(ang):.0f}px,{r*math.sin(ang)*.8-30:.0f}px);opacity:0')])
    layers.append(f'<circle class="k spark" style="opacity:0;animation-name:{nm}" cx="{TX}" cy="{TY+2}" r="{R.choice([1.6, 2.2, 2.8])}"/>')
# the first butterfly comes back and stays
layers.append(f'<g class="k" style="opacity:0;animation-name:{kfs([(0, "opacity:0"), (84, "opacity:0"), (86, "opacity:1"), (92.5, "opacity:1"), (95.4, "opacity:0")])}"><g transform="translate({CX} {cy1:.0f}) scale({sc1})" style="{pv(GOLD)}"><g class="bobS"><g class="flapS">{WING}</g><g transform="scale(-1 1)"><g class="flapS">{WING}</g></g>{BODY}</g></g></g>')

# ---------- floating light motes (always, very gentle) ----------
motes = '' if LASER else ''.join(
    f'<circle class="mote" cx="{R.uniform(20, 940):.0f}" cy="{R.uniform(200, 520):.0f}" r="{R.uniform(1, 2.4):.1f}" '
    f'style="--md:{R.uniform(8, 15)*K:.1f}s;--mdl:-{R.uniform(0, 15):.1f}s;--dx:{R.uniform(-70, 90):.0f}px;--dy:-{R.uniform(110, 230):.0f}px;'
    f'fill:{R.choice(["#ffe9b0", "#ffd1e0", "#ffe9b0"])}"/>' for _ in range(16))

subs = ''
if TEXT:
    LINES = [(2.0, 13.0, '한 마리의 나비', 40, 195, 380), (18.0, 29.0, '처음엔, 혼자였어요', 24, 520, 480), (49.0, 58.5, '함께라서 따뜻했어요', 24, 520, 480),
             (65.0, 76.0, '사랑이 피어나고', 24, 520, 480), (86.5, 95.0, '다시, 아침이 올 거예요', 24, 520, 480)]
    for a, b, txt, fs, y, x in LINES:
        nm = kfs([(0, 'opacity:0'), (a, 'opacity:0'), (a + 2.2, 'opacity:.9'), (b - 2.2, 'opacity:.9'), (b, 'opacity:0')])
        if y > 400:   # soft dark band under the bottom subtitles so they stay readable over the flowers
            subs += (f'<rect class="k" x="0" y="{y-52}" width="{W}" height="{H-y+52}" fill="url(#subshade)" '
                     f'style="opacity:0;animation-name:{nm}"/>')
        subs += (f'<text class="k sub" x="{x}" y="{y}" text-anchor="middle" style="opacity:0;font-size:{fs}px;animation-name:{nm}">{txt}</text>')

cam = kfs([(0, 'transform:scale(1) translate(0px,0px)'), (48, 'transform:scale(1.045) translate(-6px,-4px)'), (T, 'transform:scale(1) translate(0px,0px)')])
warm = kfs([(0, 'opacity:0'), (50, 'opacity:0'), (66, 'opacity:.6'), (84, 'opacity:.6'), (95, 'opacity:0')])
dawn = kfs([(0, 'opacity:0'), (3, 'opacity:0'), (10, 'opacity:.45'), (20, 'opacity:0')])

BGLAYERS = (f'<rect width="{W}" height="{H}" fill="#000"/>' if LASER else
            f'<rect width="{W}" height="{H}" fill="url(#bg)"/>\n<rect class="k" width="{W}" height="{H}" fill="url(#dawn)" style="opacity:0;animation-name:{dawn}"/>\n'
            f'<rect class="k" width="{W}" height="{H}" fill="url(#warm)" style="opacity:0;animation-name:{warm}"/>')
GLOW = '' if LASER else ' filter="url(#glow)"'

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>A single butterfly - laser line art</title>
<defs>
<radialGradient id="bg" cx="50%" cy="40%" r="75%"><stop offset="0" stop-color="#171a40"/><stop offset="1" stop-color="#070914"/></radialGradient>
<linearGradient id="subshade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#070914" stop-opacity="0"/><stop offset=".55" stop-color="#070914" stop-opacity=".62"/><stop offset="1" stop-color="#070914" stop-opacity=".8"/></linearGradient>
<radialGradient id="sunglow"><stop offset="0" stop-color="#ffc98a" stop-opacity=".26"/><stop offset=".25" stop-color="#ffc98a" stop-opacity=".17"/><stop offset=".5" stop-color="#ffb070" stop-opacity=".075"/><stop offset=".75" stop-color="#ff9a6a" stop-opacity=".02"/><stop offset="1" stop-color="#ff9a6a" stop-opacity="0"/></radialGradient>
<radialGradient id="warm" cx="72%" cy="66%" r="85%"><stop offset="0" stop-color="#ff8a5a" stop-opacity=".75"/><stop offset=".45" stop-color="#b84a6a" stop-opacity=".35"/><stop offset="1" stop-color="#2a1030" stop-opacity="0"/></radialGradient>
<radialGradient id="dawn" cx="72%" cy="68%" r="70%"><stop offset="0" stop-color="#ffc9a0" stop-opacity=".5"/><stop offset=".5" stop-color="#8f7bd9" stop-opacity=".25"/><stop offset="1" stop-color="#2a2a60" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.d0,.d1,.sd{{fill:none;stroke-linecap:round;stroke-linejoin:round}}
.d0,.d1{{stroke-dasharray:1;stroke-dashoffset:1}}
.d1{{animation:draw var(--t,1s) ease-out var(--s,0s) forwards}}
.cloud{{stroke:#e8dcff;stroke-width:1.6}} .ridge{{stroke:#9aa6ff;stroke-width:1.6;opacity:.45}} .hill{{stroke:#ffb3c8;stroke-width:2;opacity:.7}}
.stem{{stroke:#5fe3c0;stroke-width:2.4}} .pet{{stroke:#ff7fb8;stroke-width:2.4}} .pet2{{stroke:#ffc2dd;stroke-width:1.5}}
.ctr{{stroke:#ffd27a;stroke-width:2.2}} .ctrd{{fill:#ffd27a}}
.sunr{{stroke:currentColor;stroke-width:2.4;fill:none;stroke-linecap:round}} .soft{{opacity:.35;stroke-width:1.4}} .spin{{animation:spin {60*K:.0f}s linear infinite}}
.ripple{{fill:none;stroke:#ffd9a0;stroke-width:1.6}} .heartline{{fill:none;stroke:#ff9fc4;stroke-width:1.6;stroke-dasharray:1;stroke-linecap:round}}
.wing,.stripe,.band,.eye,.body,.ant{{fill:none;stroke-linecap:round;stroke-linejoin:round}}
.wing{{stroke:var(--w);stroke-width:3}} .stripe{{stroke:#fff6ea;stroke-width:2.2}} .band{{stroke:var(--b);stroke-width:3.2}}
.eye{{stroke:var(--e);stroke-width:2.6}} .body{{stroke:#fff6ea;stroke-width:2.8}} .ant{{stroke:#fff6ea;stroke-width:1.8}}
.sub{{font-family:'Noto Sans KR','Apple SD Gothic Neo','Malgun Gothic','WenQuanYi Zen Hei',sans-serif;fill:#fff1e0;letter-spacing:.12em;stroke:#0a0c1e;stroke-width:4;stroke-linejoin:round;paint-order:stroke}}
.spark{{fill:#ffe9b0}} .mote2{{}} .mote{{opacity:0;animation:mote var(--md) ease-in-out var(--mdl) infinite}}
.k,.mv,.cam{{animation-duration:{CYC:.0f}s;animation-timing-function:linear;animation-iteration-count:infinite}}
.cam{{transform-origin:480px 330px;animation-name:{cam};animation-timing-function:ease-in-out}}
.mv{{opacity:0;offset-rotate:auto 90deg}}
.orb{{offset-rotate:auto 90deg;animation:orbit var(--od) linear var(--ol) infinite}}
.flap{{animation:beat var(--bd) ease-in-out var(--bl) infinite}}
.flap2{{}} .flapS{{animation:flapS {3.2*K:.2f}s ease-in-out var(--bl) infinite}}
.bobS{{animation:bob {4*K:.2f}s ease-in-out var(--bl) infinite}}
.sway{{animation:sway var(--sd) ease-in-out var(--sl) infinite}}
.drift{{animation:drift var(--dd) linear var(--dl) infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}} @keyframes orbit{{from{{offset-distance:0%}}to{{offset-distance:100%}}}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@keyframes beat{{0%,100%{{transform:scaleX(1)}}50%{{transform:scaleX(.25)}}}}
@keyframes flapS{{0%,100%{{transform:scaleX(1)}}50%{{transform:scaleX(.55)}}}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-3px)}}}}
@keyframes sway{{0%,100%{{transform:rotate(calc(var(--sa)*-1))}}50%{{transform:rotate(var(--sa))}}}}
@keyframes drift{{from{{transform:translateX(-300px)}}to{{transform:translateX({W+60}px)}}}}
@keyframes mote{{0%{{opacity:0;transform:translate(0,0)}}25%{{opacity:.75}}75%{{opacity:.55}}100%{{opacity:0;transform:translate(var(--dx),var(--dy))}}}}
{chr(10).join(KFS)}
</style>
</defs>
{BGLAYERS}
<g{GLOW}><g class="cam">
{''.join(layers)}
{motes}
</g></g>
{subs}
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print('wrote', os.path.normpath(OUT), len(svg) // 1024, 'KB', len(KFS), 'keyframes;', f'{CYC:.0f} s loop')
