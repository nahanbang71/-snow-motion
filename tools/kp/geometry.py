"""04 기하문"""
import math
from core import *


def hexa(cx, cy, r, rot=0):
    return poly([(cx + r * math.cos(math.radians(60 * i + rot)), cy + r * math.sin(math.radians(60 * i + rot))) for i in range(6)], True)


def gwigapmun():
    s = ''
    r = 21
    dx, dy = r * math.sqrt(3), r * 1.5
    for j in range(-6, 7):
        for i in range(-6, 7):
            cx = i * dx + (dx / 2 if j % 2 else 0)
            cy = j * dy
            col = (TEAL, GREEN, YELLOW)[(i + 2 * j) % 3] if (i, j) != (0, 0) else ORANGE
            s += P(hexa(cx, cy, r - 2, 30), col[0], 3.6) + P(hexa(cx, cy, r - 9, 30), col[1], 1.4)
    return clip(s)


def _meander(rot, col):
    pts = [(0, 0)]
    x = y = 0
    d = 13
    dirs = [(1, 0), (0, -1), (-1, 0), (0, 1)]
    k = 0
    for seg in range(1, 22):
        L = (seg + 1) // 2 * d
        dx, dy = dirs[k % 4]
        x, y = x + dx * L, y + dy * L
        pts.append((x, y))
        k += 1
    return G(f"rotate({rot})", P(poly(pts), col[0], 3.8) + P(poly(pts), col[1], 1.4))


def noemun():
    s = _meander(0, BLUE) + _meander(180, TEAL)
    s = G("translate(0 0)", s)
    return clip(G("translate(-4 6)", s))


def neunghyeongmun():
    s = ''
    d = 28
    for j in range(-6, 7):
        for i in range(-6, 7):
            cx, cy = i * d + (d / 2 if j % 2 else 0), j * d / 2 * 1.0
            col = VIOLET if (i + j) % 2 else PINK
            s += P(poly([(cx, cy - 15), (cx + 15, cy), (cx, cy + 15), (cx - 15, cy)], True), col[0], 3.6)
            s += P(poly([(cx, cy - 7), (cx + 7, cy), (cx, cy + 7), (cx - 7, cy)], True), col[1], 1.8)
    return clip(s)


def gyeokjamun():
    s = ''
    for k in range(-5, 6):
        v = k * 20
        s += P(f"M{v - 3} -110 L{v - 3} 110 M{v + 3} -110 L{v + 3} 110", ORANGE[0], 2.6)
        s += P(f"M-110 {v - 3} L110 {v - 3} M-110 {v + 3} L110 {v + 3}", ORANGE[0], 2.6)
    for i in range(-5, 6):
        for j in range(-5, 6):
            s += DOT(i * 20, j * 20, YELLOW[1], 5)
    s += P(circle(34), RED[0], 4) + P(circle(26), RED[1], 1.6)
    return clip(s)


def _trigram(solid):
    s = ''
    for k, y in enumerate((-72, -80, -88)):
        if solid[k]:
            s += P(f"M-13 {y} L13 {y}", GOLD[0], 3.4)
        else:
            s += P(f"M-13 {y} L-3 {y} M3 {y} L13 {y}", GOLD[0], 3.4)
    return s


def taegeuk():
    s = P(circle(46), WHITE[1], 1.6)
    s += P("M0 -46 A23 23 0 0 1 0 0 A23 23 0 0 0 0 46", RED[0], 4.6) + P("M0 -46 A46 46 0 0 1 0 46", RED[0], 4.6)
    s += P("M0 46 A46 46 0 0 1 0 -46", BLUE[0], 4.6) 
    s += P(circle(8, 0, -23), BLUE[0], 3.4) + P(circle(8, 0, 23), RED[0], 3.4)
    tri = [(1, 1, 1), (0, 1, 1), (1, 0, 1), (0, 0, 1), (1, 1, 0), (0, 1, 0), (1, 0, 0), (0, 0, 0)]
    s += around(8, lambda k: _trigram(tri[k]))
    return spin(s, 'cw')


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
        s += P(circle(13, ex, ey), COLS[k], 4.4) + DOT(ex, ey, LIGHT[k], 9)
    return G("scale(.85)", spin(s, 'cw'))


def yeonjumun():
    s = ''
    cols = [GOLD, PINK, TEAL, VIOLET]
    for ring_i, (r, n) in enumerate([(20, 8), (42, 16), (64, 24), (86, 32)]):
        for i in range(n):
            x, y = pt(r, i * 360 / n + (180 / n if ring_i % 2 else 0))
            s += DOT(x, y, cols[ring_i][0], 10) + DOT(x, y, cols[ring_i][1], 4)
        s += P(circle(r), cols[ring_i][0], 1.6)
    s += DOT(0, 0, YELLOW[0], 16) + DOT(0, 0, YELLOW[1], 7)
    return s


def chilbomun():
    s = ''
    r = 28
    d = r * math.sqrt(2)
    for j in range(-5, 6):
        for i in range(-5, 6):
            col = (BLUE, TEAL, GOLD, PINK)[(i % 2) + 2 * (j % 2)]
            s += P(circle(r, i * d, j * d), col[0], 3.6)
    s += P(circle(8), YELLOW[0], 3.6)
    return clip(s)


def manjamun():
    arm = "M0 0 L0 -62 L-34 -62"
    s = around(4, lambda k: P(arm, GOLD[0], 7.5) + P(arm, YELLOW[1], 2.4), start=0)
    s += P(circle(8), RED[0], 3.4) + DOT(0, 0, RED[1], 6)
    s += around(4, lambda k: P(drop(14, 7, r0=70), PINK[0], 3), start=45)
    return s


PATTERNS = {
    'gwigapmun': ('04_기하문', '귀갑문(거북등)', gwigapmun), 'noemun': ('04_기하문', '뇌문(번개)', noemun),
    'neunghyeongmun': ('04_기하문', '능형문', neunghyeongmun), 'gyeokjamun': ('04_기하문', '격자문', gyeokjamun),
    'taegeuk': ('04_기하문', '태극', taegeuk), 'samtaegeuk': ('04_기하문', '삼태극', samtaegeuk),
    'yeonjumun': ('04_기하문', '연주문', yeonjumun), 'chilbomun': ('04_기하문', '칠보문', chilbomun),
    'manjamun': ('04_기하문', '만(卍)자문', manjamun),
}
