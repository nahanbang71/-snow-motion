"""07 단청문양 (dancheong colours: blue, red, yellow, white, green)"""
import math
from core import *


def meoricho():
    s = ''
    for r, n, col in ((86, 16, GREEN), (68, 14, BLUE), (50, 12, YELLOW)):
        for i in range(n):
            a0, a1 = (i - .5) * 360 / n, (i + .5) * 360 / n
            x0, y0 = pt(r, a0)
            x1, y1 = pt(r, a1)
            s += P(f"M{f(x0)} {f(y0)} A{r} {r} 0 0 1 {f(x1)} {f(y1)}", col[0], 4)
            xm, ym = pt(r - 9, i * 360 / n)
            s += DOT(xm, ym, WHITE[0], 6)
    s = spin(s, 'cw')
    s += around(8, lambda k: PL(drop(30, 11, r0=10), RED, 3.8)) + P(circle(10), WHITE[0], 3.4) + DOT(0, 0, YELLOW[0], 7)
    s += around(8, lambda k: P(lens(14, 4, r0=38), WHITE[0], 2.4), start=22.5)
    return s


def geummun():
    s = P(poly([pt(94, a) for a in range(0, 360, 90)], True), RED[0], 4.2)
    s += P(poly([pt(94, a) for a in range(45, 360, 90)], True), BLUE[0], 4.2)
    s += P(poly([pt(66, a) for a in range(0, 360, 90)], True), YELLOW[0], 4)
    s += P(poly([pt(66, a) for a in range(45, 360, 90)], True), GREEN[0], 4)
    s += P(poly([pt(40, a) for a in range(0, 360, 90)], True), WHITE[0], 3.4)
    s += around(8, lambda k: P(circle(7, 0, -80), WHITE[0], 2.6), start=0)
    s += around(8, lambda k: DOT(0, -54, YELLOW[1], 6), start=22.5)
    s += P(circle(14), RED[0], 3.6) + DOT(0, 0, RED[1], 8)
    return spin(s, 'cw')


def yeonhwa_dancheong():
    s = around(8, lambda k: P(drop(78, 28, r0=24), BLUE[0], 4.2) + P(drop(56, 19, r0=28), RED[0], 3.8) + P(drop(34, 11, r0=32), YELLOW[0], 3.4)
               + P("M0 -34 L0 -60", WHITE[0], 2))
    s += around(8, lambda k: P(lens(30, 6, r0=34), GREEN[0], 3), start=22.5)
    s += P(circle(18), YELLOW[0], 3.8) + P(circle(9), WHITE[0], 2.6)
    return spin(s, 'cw')


def bosanghwa_dancheong():
    s = around(8, lambda k: P(drop(70, 26, r0=24), RED[0], 4.2) + P(spiral(0, -56, 11, 2.5, 1.6, a0=-90), WHITE[0], 3)
               + P(drop(40, 14, r0=34), BLUE[0], 3.4))
    s += around(8, lambda k: P(lens(36, 7, r0=40), GREEN[0], 3.4) + P(spiral(0, -86, 6, 1.5, 1.4), WHITE[0], 2.4), start=22.5)
    s += P(circle(18), YELLOW[0], 3.8) + P(circle(9), YELLOW[1], 2.2) + DOT(0, 0, WHITE[0], 6)
    return spin(s, 'cw')


PATTERNS = {
    'meoricho': ('07_단청문양', '머리초', meoricho), 'geummun': ('07_단청문양', '금문', geummun),
    'yeonhwa-dancheong': ('07_단청문양', '연화(단청)', yeonhwa_dancheong),
    'bosanghwa-dancheong': ('07_단청문양', '보상화(단청)', bosanghwa_dancheong),
}
