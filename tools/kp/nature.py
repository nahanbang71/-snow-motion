"""03 자연문"""
import math
from core import *


def star4(cx, cy, r):
    return poly([(cx, cy - r), (cx + r * .25, cy - r * .25), (cx + r, cy), (cx + r * .25, cy + r * .25),
                 (cx, cy + r), (cx - r * .25, cy + r * .25), (cx - r, cy), (cx - r * .25, cy - r * .25)], True)


def hae():
    s = around(12, lambda k: PL(lens(40, 6, r0=36), YELLOW, 3.6))
    wav = lambda k: P("M" + " L".join(f"{f(x)} {f(y)}" for x, y in
                      [(7 * math.sin(i * .7), -34 - i * 3.6) for i in range(0, 14)]), ORANGE[0], 3.4)
    s += around(12, wav, start=15)
    s += P(circle(30), ORANGE[0], 4.4) + P(circle(22), YELLOW[0], 3.4) + P(spiral(0, 0, 16, 2, 1.5), YELLOW[1], 2.2)
    return spin(s, 'cw')


def dal():
    s = P("M-6 -56 A56 56 0 0 0 -6 56 A64 64 0 0 1 -6 -56Z", YELLOW[0], 4.6) + P("M-6 -50 A50 50 0 0 0 -6 50", YELLOW[1], 1.6)
    for x, y, r in [(34, -34, 9), (52, 4, 7), (30, 40, 8), (-52, -52, 5), (60, -18, 5)]:
        s += P(star4(x, y, r), GOLD[0], 3)
    for x, y in [(44, 22), (18, -58), (62, 28)]:
        s += DOT(x, y, GOLD[1], 6)
    # small cloud scrolls
    s += P(spiral(36, 62, 2, 9, 1.4), BLUE[0], 3) + P("M36 62 q-14 4 -30 0", BLUE[0], 3)
    return s


def _cloud(r_base):
    def unit(k):
        return (P(spiral(-17, -r_base - 8, 9, 2, 1.5, a0=0), TEAL[0], 3.4) + P(spiral(17, -r_base - 8, 9, 2, 1.5, a0=180, ccw=True), TEAL[0], 3.4)
                + P(f"M-17 {-r_base - 17} C-8 {-r_base - 30} 8 {-r_base - 30} 17 {-r_base - 17}", BLUE[0], 3.6)
                + P(f"M0 {-r_base - 6} C-4 {-r_base + 10} 6 {-r_base + 16} 2 {-r_base + 28}", BLUE[1], 2.2))
    return unit


def unmun():
    s = around(6, _cloud(46))
    s += around(6, lambda k: P(drop(18, 8, r0=14), VIOLET[0], 3), start=30)
    s += P(circle(8), WHITE[0], 3) + DOT(0, 0, WHITE[1], 6)
    return s


def san():
    s = P("M-100 50 L-62 -16 L-44 6 L-8 -50 L26 4 L48 -22 L100 50", GREEN[0], 4) + P("M-8 -50 L-4 -26 L-16 -4 L-8 18 M-62 -16 L-56 6 M48 -22 L52 0 L44 16", GREEN[1], 1.8)
    s += P("M-100 50 C-70 20 -50 24 -26 44 C-10 28 14 28 38 48 C60 34 80 36 100 50", TEAL[0], 3.8)
    s += P(circle(11, -44, -54), ORANGE[0], 3.8) + P(circle(5, -44, -54), YELLOW[0], 2.4)
    s += P("M-100 62 q12 -8 25 0 t25 0 t25 0 t25 0 t25 0 t25 0 t25 0 t25 0", BLUE[0], 3) + P("M-100 76 q12 -8 25 0 t25 0 t25 0 t25 0 t25 0 t25 0 t25 0 t25 0", BLUE[1], 2)
    s += P("M20 -60 q10 -8 20 0 q10 -8 20 0", WHITE[0], 2.4)
    return clip(s)


def supamun():
    s = ''
    for j in range(-6, 7):
        y = j * 16
        for i in range(-5, 6):
            x = i * 32 + (16 if j % 2 else 0)
            col = (BLUE, TEAL, VIOLET)[(i + j) % 3]
            for rr, w in ((16, 3.6), (11, 2.8), (6, 2.2)):
                s += P(f"M{x - rr} {y} A{rr} {rr} 0 0 1 {x + rr} {y}", col[0] if rr > 6 else col[1], w)
    return clip(s)


def _rock(pts, col):
    return P(smooth(pts, True), col[0], 4.2) + P(smooth([(x * .8, y * .8 - 2) for x, y in pts], True), col[1], 1.4)


def bawi():
    s = _rock([(-48, 40), (-52, 6), (-36, -22), (-12, -34), (12, -24), (28, 0), (30, 40)], VIOLET)
    s += _rock([(24, 44), (26, 20), (40, 4), (58, 10), (66, 28), (64, 44)], BLUE)
    s += _rock([(-70, 44), (-68, 24), (-58, 12), (-48, 16), (-46, 44)], BLUE)
    s += P("M-14 -18 L-8 0 L-16 14 L-8 30", VIOLET[1], 2.4) + P("M12 -10 L6 6 L14 22", VIOLET[1], 2.4)
    s += P("M-22 -4 L-30 8", VIOLET[1], 2.2)
    s += P("M-100 56 q12 -8 25 0 t25 0 t25 0 t25 0 t25 0 t25 0 t25 0 t25 0", TEAL[0], 3.2)
    s += P("M-100 70 q12 -8 25 0 t25 0 t25 0 t25 0 t25 0 t25 0 t25 0 t25 0", TEAL[1], 2.2)
    for x in (-20, -10, 40, 48):
        s += P(f"M{x} -30 q-2 -12 -8 -16 M{x} -30 q2 -12 8 -16", GREEN[0], 2.4)
    return clip(G('translate(0 -6) scale(1.3)', s))


FLAME = "M0 0 C-16 -22 8 -38 -2 -64 C20 -46 26 -22 0 0Z"


def bulkkot():
    s = around(8, lambda k: PL(f"M0 -26 C-12 -44 6 -58 -2 -84 C18 -66 22 -44 0 -26Z", RED, 4.2))
    s += around(8, lambda k: PL("M0 -26 C-8 -38 4 -48 -1 -64 C12 -52 14 -38 0 -26Z", ORANGE, 3.6), start=22.5)
    s += around(8, lambda k: PL("M0 -22 C-5 -30 2 -36 0 -46 C7 -38 8 -30 0 -22Z", YELLOW, 3), start=0)
    s += P(circle(14), YELLOW[0], 3.6) + P(spiral(0, 0, 10, 1.5, 1.3), YELLOW[1], 2)
    return spin(s, 'cw')


PATTERNS = {
    'hae': ('03_자연문', '해', hae), 'dal': ('03_자연문', '달', dal), 'unmun': ('03_자연문', '구름(운문)', unmun),
    'san': ('03_자연문', '산', san), 'supamun': ('03_자연문', '물결(수파문)', supamun), 'bawi': ('03_자연문', '바위', bawi),
    'bulkkot': ('03_자연문', '불꽃', bulkkot),
}
