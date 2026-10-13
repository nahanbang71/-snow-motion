#!/usr/bin/env python3
"""Intro: illustrated-map style overview of ALL the landmarks on a map of Europe (neon line-art version of the Turkey-map reference):
land, 20 landmark icons popping in west->east with city labels, sea names, sailboats, compass, big title, a balloon crossing the map.
-> 열기구풍경/overview.svg (16 s)"""
import math
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import korea_sites as MS  # noqa: E402
import gen_balloon_designs as BD  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, '열기구풍경')
FONT = "font-family=\"'Helvetica Neue', Arial, sans-serif\""
GOLD, ACC, BLUE = '#ffd166', '#ff4fd8', '#4d6bb8'
f = BD.f

S, KX, LON0, LAT0, CX, CY = 150.0, math.cos(math.radians(36)), 128.3, 36.0, 1000.0, 555.0
proj = lambda lon, lat: (CX + (lon - LON0) * KX * S, CY + (LAT0 - lat) * S)

CITIES = {k: (m['lon'], m['lat'], m['label'], m['w'], m['h']) for k, m in MS.KR.items()}
SEAS = [('YELLOW SEA', 125.0, 35.9), ('EAST SEA', 130.3, 38.3), ('SOUTH SEA', 129.3, 33.5)]


def land():
    js = open(os.path.join(ROOT, '세계지도비행', 'data.js'), encoding='utf-8').read()
    d = re.search(r'const LAND="(.*?)";', js, re.S).group(1)
    return d


def layout(items):
    """spread the icons so they do not overlap; each icon is pulled back toward its city"""
    for it in items:
        it['x'], it['y'] = it['cx'], it['cy'] - 18                                   # base centre
    for _ in range(500):
        moved = False
        for a in items:
            for b in items:
                if a is b:
                    continue
                ax0, ax1, ay0, ay1 = a['x'] - a['w'] / 2 - 8, a['x'] + a['w'] / 2 + 46, a['y'] - a['h'] - 20, a['y'] + 38
                bx0, bx1, by0, by1 = b['x'] - b['w'] / 2 - 8, b['x'] + b['w'] / 2 + 46, b['y'] - b['h'] - 20, b['y'] + 38
                ox, oy = min(ax1, bx1) - max(ax0, bx0), min(ay1, by1) - max(ay0, by0)
                if ox > 0 and oy > 0:
                    if ox < oy:
                        d = (-1 if a['x'] < b['x'] else 1) * (ox / 2 + .5)
                        a['x'] += d; b['x'] -= d
                    else:
                        d = (-1 if a['y'] < b['y'] else 1) * (oy / 2 + .5)
                        a['y'] += d; b['y'] -= d
                    moved = True
        for it in items:
            it['x'] += (it['cx'] - it['x']) * .004
            it['y'] += (it['cy'] - 18 - it['y']) * .004
            it['x'] = min(1780, max(110, it['x']))
            it['y'] = min(1000, max(it['h'] + 70, it['y']))
        if not moved:
            break
    return items


def build():
    items = []
    for sid, (lon, lat, label, w0, h0) in CITIES.items():
        sc = min(100 / h0, 120 / w0) * 1.1
        cx, cy = proj(lon, lat)
        items.append(dict(id=sid, label=label, cx=cx, cy=cy, w=w0 * sc, h=h0 * sc, sc=sc, lon=lon))
    layout(items)
    order = sorted(items, key=lambda i: i['lon'])
    icons, labels, leads, dots = '', '', '', ''
    for n, it in enumerate(order):
        el = MS.KR[it['id']]['el']()
        t0 = 1.4 + n * .27
        sw = 2.3 / it['sc']
        paths = ''.join(f'<path class="ic" pathLength="1" stroke-width="{sw:.2f}" style="animation-delay:{t0 + k * .03:.2f}s" d="{d}"/>' for k, d in enumerate(el))
        icons += (f'<g transform="translate({it["x"]:.1f} {it["y"]:.1f}) scale({it["sc"]:.3f})"><g class="pop" style="animation-delay:{t0:.2f}s">{paths}</g></g>')
        labels += (f'<text class="lb" x="{it["x"]:.1f}" y="{it["y"] + 22:.1f}" style="animation-delay:{t0 + .5:.2f}s" text-anchor="middle">{it["label"]}</text>')
        dots += (f'<circle class="dot" cx="{it["cx"]:.1f}" cy="{it["cy"]:.1f}" r="5" style="animation-delay:{t0 + .2:.2f}s"/>')
        if math.hypot(it['x'] - it['cx'], it['y'] - it['cy']) > 26:
            leads += f'<path class="ld" d="M{it["x"]:.1f} {it["y"] + 28:.1f} L{it["cx"]:.1f} {it["cy"]:.1f}" style="animation-delay:{t0 + .3:.2f}s"/>'
    sx = KX * S
    land_t = f'translate({CX - LON0 * sx:.1f} {CY + LAT0 * S:.1f}) scale({sx:.3f} {S:.3f})'
    seas = ''.join(f'<text class="sea" x="{proj(lo, la)[0]:.0f}" y="{proj(lo, la)[1]:.0f}" text-anchor="middle" style="animation-delay:{.6 + k * .2}s">{nm}</text>' for k, (nm, lo, la) in enumerate(SEAS))
    import airport_bg as AB
    boats = ''.join(f'<path class="bt" d="{AB.sail(*proj(lo, la), sz)}" style="animation-delay:{2 + k * .5}s"/>' for k, (lo, la, sz) in enumerate(((124.9, 37.2, 15), (125.2, 34.6, 14), (130.1, 36.2, 14), (130.4, 38.6, 13), (128.4, 33.3, 12), (130.4, 34.0, 13))))
    rnd = random.Random(5)
    stars = ''.join(f'<circle class="star" cx="{rnd.randint(20, 1900)}" cy="{rnd.randint(20, 1060)}" r="{rnd.choice((1, 1.2, 1.6))}" style="animation-duration:{rnd.uniform(3, 7):.1f}s;animation-delay:-{rnd.uniform(0, 6):.1f}s"/>' for _ in range(70))
    # balloon (design C)
    k = [0]

    def p(d, color, w=4.2, op=1):
        s = f'<path class="bd" pathLength="1" stroke="{color}" stroke-width="{w}" opacity="{op}" style="animation-delay:{6.4 + k[0] * .04:.2f}s" d="{d}"/>'
        k[0] += 1
        return s
    mouth, ropes, basket, flame = BD.gear('')
    bal = p(BD.outline(), GOLD, 5) + ''.join(p(BD.band(y, 34), BD.CH[i], 5) for i, y in enumerate((-176, -112, -50, 12, 76))) + p(mouth, GOLD, 4) + p(ropes, GOLD, 3.2) + p(basket, GOLD, 4.4)
    comp = ('<g transform="translate(150 600)"><circle class="cp" r="62"/><path class="cp" d="M0 -62 V-50 M0 62 V50 M-62 0 H-50 M62 0 H50" />'
            '<g class="needle"><path class="nd" d="M0 -56 L9 0 L-9 0 Z"/><path class="nt" d="M0 56 L9 0 L-9 0 Z"/></g><circle class="cp" r="5"/>'
            '<text class="cl" y="-78" text-anchor="middle">N</text><text class="cl" y="100" text-anchor="middle">S</text><text class="cl" x="86" y="8" text-anchor="middle">E</text><text class="cl" x="-86" y="8" text-anchor="middle">W</text></g>')
    PTS = [(230, 520), (540, 380), (840, 470), (1140, 330), (1440, 470), (1720, 340)]
    BR = [(math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1]))) % 360) for a, b in zip(PTS, PTS[1:])]
    BR = [BR[0]] + BR + [BR[-1]]
    NDL = ''.join(f'{k * 20}%{{transform:rotate({BR[min(k, len(BR) - 1)]:.1f}deg)}}' for k in range(6))
    FLY = ''.join(f'{k * 20}%{{transform:translate({x}px,{y}px)}}' for k, (x, y) in enumerate(PTS))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
<title>Korea landmarks overview</title>
<defs>
<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
@keyframes fi{{from{{opacity:0}}to{{opacity:1}}}}@keyframes fo{{from{{opacity:1}}to{{opacity:0}}}}
@keyframes draw{{0%{{stroke-dashoffset:1;opacity:0}}1%{{opacity:1}}100%{{stroke-dashoffset:0;opacity:1}}}}
.land{{fill:#0b1430;stroke:{BLUE};stroke-width:1.2;vector-effect:non-scaling-stroke;opacity:0;animation:fi 1.4s ease-out both}}
.ic,.bd{{fill:none;stroke:{GOLD};stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;opacity:0;animation:draw .9s cubic-bezier(.12,.7,.3,1) both}}
.bd{{animation-duration:1.2s}}
.pop{{transform-box:fill-box;transform-origin:50% 100%;animation:pop .7s cubic-bezier(.2,1.4,.4,1) both}}@keyframes pop{{from{{transform:scale(.55)}}to{{transform:scale(1)}}}}
.lb{{fill:#dfe9ff;font-size:19px;letter-spacing:3px;opacity:0;animation:fi .5s ease-out both;{FONT.replace('font-family=','font-family:').replace('"','')}}}
.dot{{fill:#05060d;stroke:{ACC};stroke-width:3;opacity:0;animation:fi .4s ease-out both}}
.ld{{fill:none;stroke:{ACC};stroke-width:1.4;stroke-dasharray:4 5;opacity:0;animation:fi .6s ease-out both}}
.sea{{fill:none;stroke:#6f8fdc;stroke-width:1.3;font-size:24px;letter-spacing:12px;opacity:0;animation:fi 1.2s ease-out both;{FONT.replace('font-family=','font-family:').replace('"','')}}}
.bt{{fill:none;stroke:#ffb03a;stroke-width:2;stroke-linejoin:round;opacity:0;animation:fi .8s ease-out both}}
.ttl{{fill:none;stroke:{GOLD};stroke-width:2.4;opacity:0;animation:fi 1s ease-out .4s both;{FONT.replace('font-family=','font-family:').replace('"','')}}}
.sub{{fill:none;stroke:{ACC};stroke-width:1.5;opacity:0;animation:fi 1s ease-out 1s both;{FONT.replace('font-family=','font-family:').replace('"','')}}}
.cp{{fill:none;stroke:#8fb0ff;stroke-width:2.2;stroke-linejoin:round;opacity:0;animation:fi 1s ease-out 6s both}}
.nd{{fill:none;stroke:#ffd166;stroke-width:3;stroke-linejoin:round;opacity:0;animation:fi 1s ease-out 6s both}}
.nt{{fill:none;stroke:#ff4fd8;stroke-width:3;stroke-linejoin:round;opacity:0;animation:fi 1s ease-out 6s both}}
.cl{{fill:#8fb0ff;font-size:24px;opacity:0;animation:fi 1s ease-out 6s both;{FONT.replace('font-family=','font-family:').replace('"','')}}}
.fly{{animation:fly 9s cubic-bezier(.4,0,.6,1) 6.2s both}}
.needle{{transform:rotate({BR[0]:.1f}deg);animation:ndl 9s cubic-bezier(.4,0,.6,1) 6.2s both}}@keyframes ndl{{{NDL}}}
@keyframes fly{{{FLY}}}
.bob{{animation:bob 3.4s ease-in-out infinite alternate}}@keyframes bob{{from{{transform:translateY(-8px) rotate(-1.4deg)}}to{{transform:translateY(8px) rotate(1.4deg)}}}}
.flame{{fill:none;stroke:#ff9a3c;stroke-width:3;opacity:0;transform-box:fill-box;transform-origin:50% 100%;animation:fi .8s ease-out 7.2s both,flk 2.4s ease-in-out 8s infinite alternate}}@keyframes flk{{from{{transform:scale(1,1)}}to{{transform:scale(1.08,1.14)}}}}
.star{{fill:#b9c9ff;opacity:.2;animation:tws 5s ease-in-out infinite alternate}}@keyframes tws{{from{{opacity:.1}}to{{opacity:.7}}}}
.all{{animation:fo .9s linear 15.1s both}}
</style>
</defs>
<rect width="1920" height="1080" fill="#05060d"/>
<g class="all">
<g>{stars}</g>
<path class="land" transform="{land_t}" d="{land()}"/>
<g filter="url(#glow)">
{seas}{boats}{leads}{dots}{icons}{labels}{comp}
<text class="ttl" x="60" y="1000" text-anchor="start" font-size="84" letter-spacing="8">KOREA</text>
<text class="sub" x="64" y="1046" text-anchor="start" font-size="20" letter-spacing="10">20 LANDMARKS · 1 BALLOON</text>
<g class="fly"><g transform="scale(.44)"><g class="bob">{bal}<path class="flame" d="{flame}"/></g></g></g>
</g></g>
</svg>
'''


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'overview_korea.svg'), 'w', encoding='utf-8').write(build())
    print('ok')
