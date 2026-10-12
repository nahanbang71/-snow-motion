"""04 기하문 - dynamic versions: wallpaper-style full-bleed scenes and rotating medallions"""
import math
import random
from core import *
from alive import alive_svg, piv, grp
from alive_nature import scene_svg


def hexa(cx, cy, r, rot=30):
    return poly([(cx + r * math.cos(math.radians(60 * i + rot)), cy + r * math.sin(math.radians(60 * i + rot))) for i in range(6)], True)


# ------------------------------------------------------------------ tortoise-shell hexagons: a wave of light runs through the lattice
def gwigapmun():
    R = 60
    dx, dy = R * math.sqrt(3), R * 1.5
    s = ''
    for j in range(-1, 11):
        for i in range(-1, 16):
            cx = i * dx + (dx / 2 if j % 2 else 0)
            cy = j * dy
            col = (TEAL, GREEN, YELLOW)[(i + 2 * j) % 3]
            d = math.hypot(cx - 800, cy - 450) / 900
            fill = f'<path class="a-cell" d="{poly([(cx + (R - 8) * math.cos(math.radians(60 * k + 30)), cy + (R - 8) * math.sin(math.radians(60 * k + 30))) for k in range(6)], True)}" fill="{col[0]}" style="animation-delay:{d * 3:.2f}s"/>'
            s += fill + P(hexa(cx, cy, R - 4), col[0], 3.4) + P(hexa(cx, cy, R - 16), col[1], 1.4)
    css = '''.a-cell{opacity:0;animation:cellw 3.6s ease-in-out infinite}
@keyframes cellw{0%,100%{opacity:0}35%{opacity:.55}60%{opacity:0}}'''
    return scene_svg(s, 'Gwigapmun - alive', css, bg=('#06281f', '#010a07'))


# ------------------------------------------------------------------ lightning key pattern (noemun): spiral hooks with light running through them
def noemun():
    unit = [(0, 0), (48, 0), (48, 48), (6, 48), (6, 12), (42, 12), (42, 42), (12, 42), (12, 18), (36, 18), (36, 36), (18, 36), (18, 24), (30, 24)]
    s = ''
    rnd = random.Random(4)
    for j in range(0, 16):
        for i in range(-1, 28):
            x, y = i * 58 + 4, j * 58 + 2
            flip = (i + j) % 2
            pts = [((48 - px) if flip else px, py) for px, py in unit]
            d = poly([(x + px, y + py) for px, py in pts])
            col = (BLUE, VIOLET, TEAL)[(i + j) % 3]
            s += P(d, col[0], 3.4)
            s += f'<path class="l a-run" pathLength="1" stroke="#fff" stroke-width="3" d="{d}" style="animation-delay:{rnd.uniform(0, 3):.2f}s;animation-duration:{rnd.uniform(1.4, 2.8):.2f}s"/>'
    css = '''.a-run{stroke-dasharray:.2 .8;stroke-dashoffset:.2;animation:run 2s linear infinite}
@keyframes run{from{stroke-dashoffset:.2}to{stroke-dashoffset:-.8}}'''
    return scene_svg(s, 'Noemun - alive', css, bg=('#1d1050', '#040212'))


# ------------------------------------------------------------------ diamonds (neunghyeongmun): the lattice drifts diagonally
def neunghyeongmun():
    d = 80
    s = ''
    for j in range(-3, 30):
        for i in range(-3, 24):
            cx, cy = i * d + (d / 2 if j % 2 else 0), j * d * .55
            col = VIOLET if (i + j) % 2 else PINK
            s += P(poly([(cx, cy - 42), (cx + 40, cy), (cx, cy + 42), (cx - 40, cy)], True), col[0], 3.6)
            s += grp('a-dia', P(poly([(cx, cy - 20), (cx + 19, cy), (cx, cy + 20), (cx - 19, cy)], True), col[1], 2.2), f'animation-delay:{((i * 7 + j * 3) % 10) * .25:.2f}s')
    css = f'''.a-drift{{animation:drift 8s linear infinite}}
.a-dia{{transform-box:fill-box;transform-origin:center;animation:dia 2.5s ease-in-out infinite}}
@keyframes drift{{from{{transform:translate(0,0)}}to{{transform:translate({-d}px,{-d * .55 * 2}px)}}}}
@keyframes dia{{0%,100%{{transform:scale(.5);opacity:.4}}50%{{transform:scale(1.35);opacity:1}}}}'''
    return scene_svg(grp('a-drift', s), 'Neunghyeongmun - alive', css, bg=('#2a0f4a', '#06020f'))


# ------------------------------------------------------------------ lattice window (gyeokjamun): pulses of light run along the bars
def gyeokjamun():
    s = ''
    rnd = random.Random(6)
    sp = 64
    for k in range(-1, 26):
        x = k * sp
        for off in (-3, 3):
            d = f"M{x + off} -20 L{x + off} 920"
            s += P(d, ORANGE[0], 2.6)
        s += f'<path class="l a-run2" pathLength="1" stroke="#fff3c4" stroke-width="4" d="M{x} -20 L{x} 920" style="animation-delay:{rnd.uniform(0, 4):.2f}s;animation-duration:{rnd.uniform(2, 4):.2f}s"/>'
    for k in range(-1, 16):
        y = k * sp
        for off in (-3, 3):
            s += P(f"M-20 {y + off} L1620 {y + off}", ORANGE[0], 2.6)
        s += f'<path class="l a-run2" pathLength="1" stroke="#fff3c4" stroke-width="4" d="M-20 {y} L1620 {y}" style="animation-delay:{rnd.uniform(0, 4):.2f}s;animation-duration:{rnd.uniform(2, 4):.2f}s"/>'
    for i in range(0, 26):
        for j in range(0, 15):
            s += grp('a-dot', DOT(i * sp, j * sp, YELLOW[1], 8), f'animation-delay:{((i + j) % 12) * .25:.2f}s')
    s += grp('a-spin', P(circle(120, 800, 450), RED[0], 6) + P(circle(98, 800, 450), RED[1], 2.4)).replace('<g class="a-spin"', '<g class="a-spinc"')
    css = '''.a-run2{stroke-dasharray:.07 .93;stroke-dashoffset:.07;animation:run 3s linear infinite}
.a-dot{animation:glow 1.8s ease-in-out infinite alternate}
.a-spinc{transform-origin:800px 450px;animation:spin 20s linear infinite}
@keyframes run{from{stroke-dashoffset:.07}to{stroke-dashoffset:-.93}}'''
    return scene_svg(s, 'Gyeokjamun - alive', css, bg=('#3a1a05', '#0d0502'))


# ------------------------------------------------------------------ taegeuk with trigrams
def taegeuk():
    def tri(solid):
        s = ''
        for k, y in enumerate((-72, -80, -88)):
            s += P(f"M-13 {y} L13 {y}", GOLD[0], 3.4) if solid[k] else P(f"M-13 {y} L-3 {y} M3 {y} L13 {y}", GOLD[0], 3.4)
        return s
    tris = [(1, 1, 1), (0, 1, 1), (1, 0, 1), (0, 0, 1), (1, 1, 0), (0, 1, 0), (1, 0, 0), (0, 0, 0)]
    core = (P(circle(46), WHITE[1], 1.6) + P("M0 -46 A23 23 0 0 1 0 0 A23 23 0 0 0 0 46", RED[0], 4.6) + P("M0 -46 A46 46 0 0 1 0 46", RED[0], 4.6)
            + P("M0 46 A46 46 0 0 1 0 -46", BLUE[0], 4.6) + P(circle(8, 0, -23), BLUE[0], 3.4) + P(circle(8, 0, 23), RED[0], 3.4))
    ring = ''.join(G(f"rotate({k * 45})", grp('a-tg', tri(tris[k]), f'animation-delay:{k * .4:.2f}s')) for k in range(8))
    inner = grp('a-core', core) + grp('a-ring', ring) + grp('a-pulse', P(circle(60), VIOLET[0], 1.4))
    css = '''.a-core{animation:spin 14s linear infinite}
.a-ring{animation:spinr 60s linear infinite}
.a-tg{animation:glow 3.2s ease-in-out infinite alternate}
.a-pulse{animation:glow 1.8s ease-in-out infinite alternate}'''
    return alive_svg(inner, 'Taegeuk - alive', css, bg=('#24104a', '#06030f'), fr=('octagon', GOLD), flycol='#e6d6ff')


def samtaegeuk():
    COLS = [RED[0], BLUE[0], YELLOW[0]]
    LIGHT = [RED[1], BLUE[1], YELLOW[1]]
    R = 108
    s = ''
    for k in range(3):
        a0 = k * 120
        x0, y0 = pt(R, a0 + 90)
        x1, y1 = pt(R, a0 + 210)
        s += P(f"M{f(x0)} {f(y0)} A{R} {R} 0 0 1 {f(x1)} {f(y1)}", COLS[k], 4.4)
        arm = [(R * t * math.cos(math.radians(a0 - 100 * (1 - t))), R * t * math.sin(math.radians(a0 - 100 * (1 - t)))) for t in [i / 40 for i in range(41)]]
        s += P(poly(arm), COLS[k], 4.4)
        s += P(poly([(R * t * .93 * math.cos(math.radians(a0 - 100 * (1 - t) + 9)), R * t * .93 * math.sin(math.radians(a0 - 100 * (1 - t) + 9)))
                     for t in [.15 + i / 40 * .8 for i in range(41)]]), LIGHT[k], 2.2)
        ex, ey = R * .6 * math.cos(math.radians(a0 + 20)), R * .6 * math.sin(math.radians(a0 + 20))
        s += P(circle(13, ex, ey), COLS[k], 4.4) + grp('a-eye2', DOT(ex, ey, LIGHT[k], 9), f'animation-delay:{k * .5}s')
    inner = G("scale(.85)", grp('a-spin3', s))
    css = '''.a-spin3{animation:spin 10s linear infinite}
.a-eye2{animation:glow 1.4s ease-in-out infinite alternate}'''
    return alive_svg(inner, 'Samtaegeuk - alive', css, bg=('#10204a', '#030510'), fr=('dancheong', None))


def yeonjumun():
    s = ''
    cols = [GOLD, PINK, TEAL, VIOLET]
    for ring_i, (r, n) in enumerate([(20, 8), (42, 16), (64, 24), (86, 32)]):
        beads = ''
        for i in range(n):
            x, y = pt(r, i * 360 / n + (180 / n if ring_i % 2 else 0))
            beads += grp('a-bead', DOT(x, y, cols[ring_i][0], 10) + DOT(x, y, cols[ring_i][1], 4), f'animation-delay:{i * .12:.2f}s')
        s += grp('a-rr' if ring_i % 2 else 'a-rl', beads + P(circle(r), cols[ring_i][0], 1.6), f'animation-duration:{18 + ring_i * 7}s')
    s += grp('a-pulse', DOT(0, 0, YELLOW[0], 16) + DOT(0, 0, YELLOW[1], 7))
    css = '''.a-rl{animation:spin 20s linear infinite}
.a-rr{animation:spinr 20s linear infinite}
.a-bead{animation:glow 1.6s ease-in-out infinite alternate}
.a-pulse{animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.3)}}'''
    return alive_svg(s, 'Yeonjumun - alive', css, bg=('#06304a', '#010a14'), fr=('none', GOLD), flycol='#bfe0ff')


# ------------------------------------------------------------------ overlapping circles (chilbomun): breathing lattice
def chilbomun():
    r = 46
    d = r * math.sqrt(2)
    s = ''
    for j in range(-2, 17):
        for i in range(-2, 28):
            col = (BLUE, TEAL, GOLD, PINK)[(i % 2) + 2 * (j % 2)]
            dist = math.hypot(i * d - 800, j * d - 450) / 900
            s += grp('a-circ', P(circle(r, i * d, j * d), col[0], 3.6), f'animation-delay:{dist * 2.5:.2f}s;transform-origin:{f(i * d)}px {f(j * d)}px')
    css = '''.a-circ{transform-box:view-box;animation:circ 3.2s ease-in-out infinite}
@keyframes circ{0%,100%{transform:scale(1);opacity:.55}50%{transform:scale(1.12);opacity:1}}'''
    return scene_svg(s, 'Chilbomun - alive', css, bg=('#0a1a50', '#020510'))


def manjamun():
    arm = "M0 0 L0 -62 L-34 -62"
    cross = around(4, lambda k: P(arm, GOLD[0], 7.5) + P(arm, YELLOW[1], 2.4))
    drops = around(4, lambda k: P(drop(14, 7, r0=70), PINK[0], 3), start=45)
    dashes = ''.join(G(f"rotate({k * 15})", P("M0 -88 L0 -80", GOLD[1], 2.4)) for k in range(24))
    inner = grp('a-spin4', cross + P(circle(8), RED[0], 3.4) + DOT(0, 0, RED[1], 6)) + grp('a-spinr4', drops) + grp('a-slow', dashes)
    css = '''.a-spin4{animation:spin 22s linear infinite}
.a-spinr4{animation:spinr 16s linear infinite}
.a-slow{animation:spin 80s linear infinite}'''
    return alive_svg(inner, 'Manjamun - alive', css, bg=('#40280a', '#100803'), fr=('ticks', GOLD), flycol='#ffe0a0')


GEO = {'gwigapmun': gwigapmun, 'noemun': noemun, 'neunghyeongmun': neunghyeongmun, 'gyeokjamun': gyeokjamun, 'taegeuk': taegeuk,
       'samtaegeuk': samtaegeuk, 'yeonjumun': yeonjumun, 'chilbomun': chilbomun, 'manjamun': manjamun}
