#!/usr/bin/env python3
"""Sample SVGs for the sea scenes: dolphin jump, whale spout, seagulls -> 세계지도비행/{dolphin,whale,gull}_sample.svg"""
import math
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '세계지도비행')
FONT = "font-family=\"'Helvetica Neue', Arial, sans-serif\""
WAVE = ' '.join(f't60 0' for _ in range(24))
SEA = ''.join(f'<path d="M{300 + i * 60} {640 + i * 50} q30 -14 60 0 {WAVE}"/>' for i in range(3))
import random


def starfield(seed=5):
    """~90 slowly breathing stars, a few bright ones with a cross glint, and one rare shooting star"""
    r = random.Random(seed)
    pts = []
    while len(pts) < 90:
        x, y = r.randint(20, 1900), r.randint(40, 600)
        if all(math.hypot(x - a, y - b) > 38 for a, b in pts):
            pts.append((x, y))
    out = ''
    for i, (x, y) in enumerate(pts):
        rad = r.choice((1.0, 1.2, 1.5, 1.8, 2.2))
        out += (f'<circle class="star" cx="{x}" cy="{y}" r="{rad}" '
                f'style="animation-duration:{r.uniform(3, 7):.1f}s;animation-delay:-{r.uniform(0, 6):.1f}s"/>')
        if i % 15 == 0:
            out += (f'<path class="glint" d="M{x - 9} {y}H{x + 9}M{x} {y - 9}V{y + 9}" '
                    f'style="animation-duration:{r.uniform(5, 8):.1f}s;animation-delay:-{r.uniform(0, 5):.1f}s"/>')
    out += '<path class="shoot" d="M1180 120 l-90 -38" style="animation-delay:6s"/>'
    return out


STARS = starfield()

BASE_CSS = ('.d{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;opacity:0;animation:draw 1.2s cubic-bezier(.12,.7,.3,1) both}'
            '@keyframes draw{0%{stroke-dashoffset:1;opacity:0}1%{opacity:1}100%{stroke-dashoffset:0;opacity:1}}'
            '.sea{opacity:.7;animation:fade 1.5s ease-out both}@keyframes fade{from{opacity:0}to{opacity:1}}'
            '.t{fill:none;stroke:#ff4fd8;stroke-width:1.6;text-anchor:middle;opacity:0;animation:fade .9s ease-out 2.4s both}')
STAR_CSS = ('.star{fill:#b9c9ff;opacity:.2;animation:tw 5s ease-in-out infinite alternate}@keyframes tw{from{opacity:.12}to{opacity:.8}}'
            '.glint{fill:none;stroke:#dfe8ff;stroke-width:1.4;stroke-linecap:round;opacity:0;animation:gl 6s ease-in-out infinite}@keyframes gl{0%,70%,100%{opacity:0}85%{opacity:.75}}'
            '.shoot{fill:none;stroke:#eaf0ff;stroke-width:2.4;stroke-linecap:round;opacity:0;animation:shoot 9s linear infinite}'
            '@keyframes shoot{0%{opacity:0;transform:translate(0,0)}3%{opacity:.9}14%{opacity:0;transform:translate(320px,135px)}100%{opacity:0}}')
BASE_CSS += STAR_CSS


def page(title, css, body, label, clip=True):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
<title>{title}</title>
<defs>
<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="above"><rect x="0" y="0" width="1920" height="640"/></clipPath>
<style>{BASE_CSS}{css}</style>
</defs>
<rect width="1920" height="1080" fill="#05060d"/>
<g filter="url(#glow)">
<g class="sea" fill="none" stroke="#4a66b0" stroke-width="2" stroke-linecap="round">{SEA}</g>
<g>{STARS}</g>
{body}
<text class="t" x="960" y="860" font-size="30" letter-spacing="16" {FONT}>{label}</text>
</g>
</svg>
'''


# ---------------------------------------------------------------- dolphin
DOLPHIN = ('M-62 6 C-46 -14 -10 -26 26 -20 C44 -17 54 -10 66 -8 L76 -4 L66 1 C54 5 44 7 30 11 C0 21 -30 19 -62 6 Z '   # body + beak
           'M-8 -23 Q-2 -42 16 -40 Q9 -32 11 -21 '                                                                    # dorsal fin
           'M-62 6 Q-76 -2 -86 -16 M-62 6 Q-76 14 -86 28 '                                                              # tail flukes
           'M22 9 Q12 26 -2 28 '                                                                                        # flipper
           'M44 -11 a2 2 0 1 0 .1 0')


def jump_keyframes(name, x0=330, y0=90, apex=240, n=10, flip=1):
    s = f'@keyframes {name}{{'
    for k in range(n + 1):
        v = -1 + 2 * k / n
        x = v * x0 * flip
        y = y0 - apex * (1 - v * v)
        slope = (apex * 2 * v / x0) * flip      # dy/dx
        ang = math.degrees(math.atan2(slope, 1)) * (1 if flip > 0 else -1)
        ang = math.degrees(math.atan2(apex * 2 * v / x0, 1))
        if flip < 0:
            ang = -ang
        s += f'{k * 100 / n:g}%{{transform:translate({x:.0f}px,{y:.0f}px) rotate({ang:.1f}deg)}}'
    return s + '}'


def dolphin_svg():
    css = ('.jump{animation:jumpA 2.4s linear both}.jump2{animation:jumpA 2.4s linear both}'
           + jump_keyframes('jumpA', x0=430, y0=120, apex=320) +
           '.rip{fill:none;stroke:#7ff0e0;stroke-width:2.2;opacity:0;transform-box:fill-box;transform-origin:center;animation:rip 1.3s ease-out both}'
           '@keyframes rip{0%{opacity:0;transform:scale(.15)}15%{opacity:.8}100%{opacity:0;transform:scale(1)}}')
    def dol(delay, scale, cls):
        return (f'<g transform="translate(960 640)"><g class="{cls}" style="animation-delay:{delay}s"><g transform="scale({scale})">'
                f'<path class="d" pathLength="1" stroke="#7ff0e0" stroke-width="2.6" style="animation:none;stroke-dashoffset:0;opacity:1" d="{DOLPHIN}"/></g></g></g>')
    rips = ''
    for t0, s in ((1.4, 1), (2.0, .8), (5.2, 1)):
        for fx in (-346, 346):
            tt = t0 + (0.25 if fx < 0 else 2.15) * (1 if s == 1 else 1)
            rips += f'<ellipse class="rip" cx="{960 + fx * (1 if s == 1 else 1)}" cy="642" rx="80" ry="14" style="animation-delay:{tt:.2f}s"/>'
    body = ('<g clip-path="url(#above)">' + dol(1.4, 1.9, 'jump') + dol(2.0, 1.45, 'jump2') + dol(5.2, 1.9, 'jump') + '</g>' + rips)
    return page('Dolphin jump sample', css, body, 'DOLPHIN')


# ------------------------------------------------------------------ whale
def whale_svg():
    css = ('.rise{animation:rise 5s ease-in-out infinite}@keyframes rise{0%{transform:translateY(100px)}16%{transform:translateY(0)}58%{transform:translateY(0)}78%{transform:translateY(100px)}100%{transform:translateY(100px)}}'
           '.sp{fill:none;stroke:#cfe3ff;stroke-width:3;stroke-linecap:round;stroke-dasharray:1;stroke-dashoffset:1;opacity:0;animation:spout 5s ease-out infinite}'
           '@keyframes spout{0%,15%{stroke-dashoffset:1;opacity:1}30%{stroke-dashoffset:0;opacity:1}52%{stroke-dashoffset:0;opacity:1}68%{stroke-dashoffset:0;opacity:0}100%{stroke-dashoffset:1;opacity:0}}'
           '.dr{fill:none;stroke:#cfe3ff;stroke-width:2.4;opacity:0;animation:drop 5s ease-in infinite}'
           '@keyframes drop{0%,28%{opacity:0;transform:translateY(0)}34%{opacity:.9}62%{opacity:0;transform:translateY(90px)}100%{opacity:0}}'
           '.rip{fill:none;stroke:#6fa8ff;stroke-width:2.2;opacity:0;transform-box:fill-box;transform-origin:center;animation:rip 5s ease-out infinite}'
           '@keyframes rip{0%,10%{opacity:0;transform:scale(.4)}22%{opacity:.8}60%{opacity:0;transform:scale(1.15)}100%{opacity:0}}')
    back = 'M-250 0 C-244 -34 -206 -58 -150 -68 C-70 -90 40 -82 120 -54 C170 -36 214 -16 250 0'
    fin = 'M96 -62 Q112 -96 134 -54'
    spout = 'M-92 -80 C-94 -140 -114 -184 -140 -204 M-92 -80 C-88 -140 -68 -184 -42 -204'
    drops = ''.join(f'<circle class="dr" cx="{x}" cy="{y}" r="3" style="animation-delay:{d}s"/>' for x, y, d in
                    [(-146, -200, 0), (-36, -204, .12), (-122, -214, .2), (-58, -216, .3), (-158, -184, .08)])
    body = ('<g transform="translate(960 640) scale(1.5)"><ellipse class="rip" cx="0" cy="3" rx="280" ry="16"/>'
            '<g clip-path="url(#aboveRel)"></g></g>'
            '<g clip-path="url(#above)"><g transform="translate(960 640) scale(1.5)"><g class="rise">'
            f'<path class="d" pathLength="1" stroke="#6fa8ff" stroke-width="2.8" style="animation:none;stroke-dashoffset:0;opacity:1" d="{back}"/>'
            f'<path class="d" pathLength="1" stroke="#6fa8ff" stroke-width="2.8" style="animation:none;stroke-dashoffset:0;opacity:1" d="{fin}"/>'
            f'<path class="d" pathLength="1" stroke="#6fa8ff" stroke-width="2.2" style="animation:none;stroke-dashoffset:0;opacity:1" d="M-112 -76 q8 -6 16 0 M-206 -34 a3 3 0 1 0 .1 0"/>'
            '</g></g></g>'
            f'<g transform="translate(960 640) scale(1.5)"><g class="rise"><path class="sp" pathLength="1" d="{spout}"/>{drops}</g></g>')
    body = body.replace('<g clip-path="url(#aboveRel)"></g>', '')
    return page('Whale spout sample', css, body, 'WHALE')


# ------------------------------------------------------------------- gulls
def gull_svg():
    up = 'M-64 -2 Q-34 -30 0 -4 Q34 -30 64 -2'
    down = 'M-64 16 Q-34 -6 0 -4 Q34 -6 64 16'
    css = (f'.fl{{fill:none;stroke:#eaf6ff;stroke-width:3;stroke-linecap:round;stroke-linejoin:round;animation:flap 1s ease-in-out infinite alternate}}'
           f'@keyframes flap{{from{{d:path("{up}")}}to{{d:path("{down}")}}}}'
           '.fly{animation:fly 9s linear both}@keyframes fly{from{transform:translateX(-260px)}to{transform:translateX(2200px)}}'
           '.bobg{animation:bobg 2.6s ease-in-out infinite alternate}@keyframes bobg{from{transform:translateY(-14px)}to{transform:translateY(14px)}}')
    flock = ''
    for dx, dy, sc, ph in ((0, 0, 1.0, 0), (-110, 46, .8, .35), (-200, -26, .65, .6), (-300, 30, .55, .15)):
        flock += (f'<g transform="translate({dx * 1.7:.0f} {dy * 1.7:.0f}) scale({sc * 1.7:.2f})"><path class="fl" d="{up}" style="animation-delay:-{ph}s"/></g>')
    light = ('<path class="d" pathLength="1" stroke="#ffd166" stroke-width="2.6" style="animation-delay:.2s" d="M1560 640 L1572 440 H1608 L1620 640 M1566 520 H1614 M1570 470 H1610"/>'
             '<path class="d" pathLength="1" stroke="#ffd166" stroke-width="2.6" style="animation-delay:.6s" d="M1566 440 L1590 400 L1612 440 M1590 400 V380 M1576 440 V418 H1604 V440"/>')
    body = light + f'<g transform="translate(0 430)"><g class="fly"><g class="bobg">{flock}</g></g></g>'
    return page('Seagull sample', css, body, 'SEAGULL')


for name, fn in (('dolphin', dolphin_svg), ('whale', whale_svg), ('gull', gull_svg)):
    open(os.path.join(OUT, f'{name}_sample.svg'), 'w', encoding='utf-8').write(fn())
print('ok')
