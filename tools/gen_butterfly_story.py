#!/usr/bin/env python3
"""Laser-style sample, one continuous 42 s story over the same meadow (loops):
  Act 1  0-14 s   butterflies fly in from the left and cross the sky
  Act 2 14-28 s   a new flock glides down and lands on the big cosmos (slow wing beats)
  Act 3 28-42 s   wind rises: streaks, flowers bend, petals blow right, butterflies lift off and leave
usage: python3 tools/gen_butterfly_story.py [seed]   -> flowers/butterfly_story.svg
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_butterfly_meadow as m  # noqa: E402

W, H = m.W, m.H
T = 42.0
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 11
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flowers', 'butterfly_story.svg')
R = random.Random(SEED)

KFS = []


def kfs(points):
    """points: [(t_seconds, 'css props'), ...] ascending. returns animation-name (42 s cycle)."""
    body = ''.join(f'{t/T*100:.3f}%{{{p}}}' for t, p in points)
    KFS.append(f'@keyframes q{len(KFS)}{{{body}}}')
    return f'q{len(KFS)-1}'


def motion(start, dur, fade=.4):
    f = fade / dur * 100
    return kfs([(0, 'offset-distance:0%;opacity:0'), (start, 'offset-distance:0%;opacity:0'),
                (start + fade, f'offset-distance:{f:.2f}%;opacity:1'), (start + dur - fade, f'offset-distance:{100-f:.2f}%;opacity:1'),
                (start + dur, 'offset-distance:100%;opacity:0'), (T, 'offset-distance:100%;opacity:0')])


def window(a, b, fade=.4):
    return kfs([(0, 'opacity:0'), (a, 'opacity:0'), (a + fade, 'opacity:1'), (b, 'opacity:1'), (b + fade, 'opacity:0'), (T, 'opacity:0')])


class Once(m.Scene):
    def path(self, d, cls, s, t, col=None):
        c = f';stroke:{col}' if col else ''
        self.els.append(f'<path class="d1 {cls}" pathLength="1" style="--s:{s:.2f}s;--t:{t:.2f}s{c}" d="{d}"/>')

    def dot(self, x, y, r, cls, s, col=None):
        c = f';fill:{col}' if col else ''
        self.els.append(f'<circle class="fi1 {cls}" style="--s:{s:.2f}s{c}" cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>')


# ---------- meadow: 4 big cosmos to land on + random fill ----------
S = Once(0)
BIG = [(150, 1.0), (390, .85), (640, .95), (850, .8)]
perch = []


def sway_wrap(i0, x):
    amp = R.uniform(1.2, 3.6) * (-1 if R.random() < .5 else 1)
    dur = R.uniform(2.6, 5.4)
    S.els[i0:] = [f'<g class="sway" style="--sa:{amp:.2f}deg;--sd:{dur:.2f}s;--sl:-{R.uniform(0, dur):.2f}s;'
                  f'transform-origin:{x:.1f}px {H}px">' + ''.join(S.els[i0:]) + '</g>']


for k, (bx, sc) in enumerate(BIG):
    i0 = len(S.els)
    y = 462
    m.cosmos(S, R, bx, y, .8 * sc, R.choice(m.PINKS), .2 + k * .4)
    perch.append((bx, y - 100 * .8 * sc))
    sway_wrap(i0, bx)
n = 18
for i in range(n):
    x = 15 + (W - 30) * (i + .5) / n + R.uniform(-15, 15)
    if any(abs(x - bx) < 75 for bx, _ in BIG):
        continue
    i0, d = len(S.els), 1.0 + i * .12
    kind = R.choice(['daisy', 'daisy', 'lupine', 'bud', 'tiny', 'tiny', 'cosmos'])
    col = R.choice(R.choice([m.PINKS, m.WARM, m.COOL, m.WHITE]))
    if kind == 'cosmos':
        m.cosmos(S, R, x, R.uniform(470, 500), R.uniform(.3, .45), col, d)
    elif kind == 'daisy':
        m.daisy(S, R, x, R.uniform(470, 500), R.uniform(.4, .6), R.choice(m.WHITE), d)
    elif kind == 'lupine':
        m.lupine(S, R, x, R.uniform(400, 430), R.uniform(85, 110), R.choice(m.COOL), d)
    elif kind == 'bud':
        m.bud(S, R, x, R.uniform(470, 495), R.uniform(.5, .8), col, d)
    else:
        m.tiny(S, R, x, R.uniform(480, 515), R.uniform(.8, 1.2), R.choice(m.WARM + m.COOL + m.WHITE), d)
    sway_wrap(i0, x)

# ---------- butterfly pieces ----------
WING = ''.join(f'<path class="{c}" d="{d}"/>' for d, c, _ in m.WING)
BODY = ('<path class="body" d="M0 -24 C-5 -20 -5 -10 0 -6 C5 -10 5 -20 0 -24 Z M0 -6 C-4 10 -4 36 0 54 C4 36 4 10 0 -6"/>'
        '<path class="ant" d="M-2 -24 C-8 -44 -20 -56 -34 -62 M2 -24 C8 -44 20 -56 34 -62"/>')


def bf_body(cls, bd, bl):
    return (f'<g class="{cls}" style="--bd:{bd}s;--bl:-{bl:.2f}s"><g class="flap">{WING}</g>'
            f'<g transform="scale(-1 1)"><g class="flap">{WING}</g></g>{BODY}</g>')


def flyer(path_d, sc, pal, start, dur):
    """top view, head along the path"""
    return (f'<g class="mv" style="offset-path:path(\'{path_d}\');animation-name:{motion(start, dur)}">'
            f'<g transform="scale({sc:.2f})" style="--w:{pal[0]};--b:{pal[1]};--e:{pal[2]}">'
            f'{bf_body("beat", round(R.uniform(.45, .75), 2), R.uniform(0, .5))}</g></g>')


def wavy(y0, y1, amp, x0=-120, x1=1080, seg=4):
    pts = [(x0 + k * (x1 - x0) / seg, y0 + (y1 - y0) * k / seg + (R.uniform(-amp, amp) if 0 < k < seg else 0)) for k in range(seg + 1)]
    d = f'M{pts[0][0]:.0f} {pts[0][1]:.0f}'
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        xm = (xa + xb) / 2
        d += f' C{xm:.0f} {ya:.0f} {xm:.0f} {yb:.0f} {xb:.0f} {yb:.0f}'
    return d


out = []
# Act 1: crossing flight
for i in range(5):
    sc = R.uniform(.35, .8)
    dur = R.uniform(9, 12.5) / (.6 + sc)
    out.append(flyer(wavy(R.uniform(80, 300), R.uniform(80, 300), 50), sc, m.BFLY[i % 3], .3 + i * 1.3, dur))

# Act 2 + 3: land, rest, lift off
for i, (px, ptop) in enumerate(perch):
    sc = R.uniform(.55, .75)
    pal = m.BFLY[(i + 1) % 3]
    cy = ptop - 48 * sc          # body centre of the upright, resting butterfly
    land0 = 14.4 + i * 1.5
    adur = 5.0
    land = land0 + adur
    lift = 29.6 + i * .8
    xdur = 7.5
    y0 = R.uniform(90, 200)
    arrive = f'M-120 {y0:.0f} C{px*.45:.0f} {y0-50:.0f} {px-140:.0f} {cy-130:.0f} {px:.0f} {cy+15*sc:.0f}'
    leave = f'M{px:.0f} {cy+15*sc:.0f} C{px+60:.0f} {cy-120:.0f} {px+260:.0f} {cy-60:.0f} 1080 {R.uniform(60, 200):.0f}'
    out.append(flyer(arrive, sc, pal, land0, adur))
    out.append(f'<g class="k" style="animation-name:{window(land, lift)}"><g transform="translate({px:.0f} {cy:.0f}) scale({sc:.2f})" '
               f'style="--w:{pal[0]};--b:{pal[1]};--e:{pal[2]}"><g class="bobS" style="--bl:-{i*.7:.1f}s">'
               f'<g class="flapS" style="--bl:-{i*.5:.1f}s">{WING}</g><g transform="scale(-1 1)"><g class="flapS" style="--bl:-{i*.5:.1f}s">{WING}</g></g>{BODY}</g></g></g>')
    out.append(flyer(leave, sc, pal, lift, xdur))

# wind streaks (act 3) and petals
streaks = []
for j, (y, t0) in enumerate([(120, 28.6), (210, 30.6), (300, 32.4), (170, 34.2)]):
    d = wavy(y, y + R.uniform(-30, 30), 25, -50, 1010, 5)
    nm = kfs([(0, 'stroke-dashoffset:.2'), (t0, 'stroke-dashoffset:.2'), (t0 + 3.6, 'stroke-dashoffset:-1'), (T, 'stroke-dashoffset:-1')])
    streaks.append(f'<path class="wind k" pathLength="1" style="animation-name:{nm}" d="{d}"/>')
for j in range(16):
    sx, sy = R.uniform(40, 800), R.uniform(380, 470)
    d = wavy(sy, sy - R.uniform(80, 280), 60, sx, sx + R.uniform(300, 600), 3)
    dur = R.uniform(5, 8)
    out.append(f'<path class="petal mv" style="offset-path:path(\'{d}\');animation-name:{motion(28.8 + j * .75, dur, .6)}" '
               f'd="M0 0 C6 -7 15 -5 18 2 C13 9 4 9 0 0 Z"/>')

# wind bend for the whole meadow
wind = kfs([(0, 'transform:skewX(0deg)'), (28, 'transform:skewX(0deg)'), (30, 'transform:skewX(-4deg)'), (32, 'transform:skewX(-1deg)'),
            (34, 'transform:skewX(-5deg)'), (36.5, 'transform:skewX(-2deg)'), (39, 'transform:skewX(-4deg)'), (41.5, 'transform:skewX(0deg)'),
            (T, 'transform:skewX(0deg)')])

clouds = []
for i in range(5):
    s = R.uniform(.8, 1.3)
    y = 45 + i * 24 + R.uniform(-6, 6)
    dur = R.uniform(55, 90)
    clouds.append(f'<g transform="translate(0 {y:.0f})"><g class="drift" style="--dd:{dur:.0f}s;--dl:-{R.uniform(0, dur):.0f}s">'
                  f'<path class="d1 cloud" pathLength="1" style="--s:{.3 + i*.3:.1f}s;--t:1.4s" d="{m.cloud_d(s)}"/></g></g>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>Butterfly story - laser line art sample</title>
<defs>
<radialGradient id="bg" cx="50%" cy="45%" r="70%"><stop offset="0" stop-color="#14183a"/><stop offset="1" stop-color="#080a1a"/></radialGradient>
<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.d1{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;animation:draw var(--t,1s) ease-out var(--s,0s) forwards}}
.fi1{{opacity:0;animation:fade .5s ease-out var(--s,0s) forwards}}
.cloud{{stroke:#e8f0ff;stroke-width:1.8}} .stem{{stroke:#3df2c0;stroke-width:2.4}}
.pet{{stroke:#ff6fb5;stroke-width:2.2}} .pet2{{stroke:#ffb3da;stroke-width:1.5}}
.ctr{{stroke:#ffd23f;stroke-width:2.2}} .ctrd{{fill:#ffd23f}}
.wing,.stripe,.band,.eye,.body,.ant{{fill:none;stroke-linecap:round;stroke-linejoin:round}}
.wing{{stroke:var(--w);stroke-width:3}} .stripe{{stroke:#ffffff;stroke-width:2.2}} .band{{stroke:var(--b);stroke-width:3.2}}
.eye{{stroke:var(--e);stroke-width:2.6}} .body{{stroke:#ffffff;stroke-width:2.8}} .ant{{stroke:#ffffff;stroke-width:1.8}}
.petal{{fill:none;stroke:#ff9fd0;stroke-width:1.8;stroke-linejoin:round;opacity:0}}
.wind{{fill:none;stroke:#bfe9ff;stroke-width:2;stroke-linecap:round;stroke-dasharray:.2 2;stroke-dashoffset:.2}}
.k,.mv,.meadow{{animation-duration:{T:.0f}s;animation-timing-function:linear;animation-iteration-count:infinite}}
.mv{{opacity:0;offset-rotate:auto 90deg}}
.meadow{{transform-origin:0 {H}px;animation-name:{wind}}}
.flap{{animation:flap var(--bd) ease-in-out var(--bl) infinite}}
.flapS{{animation:flapS 2.4s ease-in-out var(--bl) infinite}}
.bobS{{animation:bob 3.2s ease-in-out var(--bl) infinite}}
.sway{{animation:sway var(--sd) ease-in-out var(--sl) infinite}}
.drift{{animation:drift var(--dd) linear var(--dl) infinite}}
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
<g class="meadow">{''.join(S.els)}</g>
{''.join(streaks)}
{''.join(out)}
</g>
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print('wrote', os.path.normpath(OUT), len(svg) // 1024, 'KB')
