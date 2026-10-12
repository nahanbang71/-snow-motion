"""02 동물문 (bonghwang is generated from the supplied line drawing by tools/colorize_phoenix.py)"""
import math
from core import *


def ring_pts(a0, a1, R, wave=0.0, waves=3, n=90):
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(pt(R + wave * math.sin(t * waves * 2 * math.pi), a0 + (a1 - a0) * t))
    return out


def tang(pts, i):
    x0, y0 = pts[max(i - 1, 0)]
    x1, y1 = pts[min(i + 1, len(pts) - 1)]
    L = math.hypot(x1 - x0, y1 - y0) or 1
    return (x1 - x0) / L, (y1 - y0) / L


def scales(pts, wfn, col, step=3, off=0):
    s = ''
    n = len(pts) - 1
    for i in range(3 + off, n - 2, step):
        tx, ty = tang(pts, i)
        nx, ny = -ty, tx
        w = wfn(i / n) * .75
        x, y = pts[i]
        s += P(f"M{f(x + nx * w)} {f(y + ny * w)} Q{f(x + tx * 5)} {f(y + ty * 5)} {f(x - nx * w)} {f(y - ny * w)}", col, 1.6)
    return s


def fish_scales(pts, wfn, col):
    s = ''
    n = len(pts) - 1
    for i in range(4, n - 4, 4):
        tx, ty = tang(pts, i)
        nx, ny = -ty, tx
        w = wfn(i / n)
        for row in (-.62, 0, .62):
            j = i + (2 if row == 0 else 0)
            if j >= n - 3:
                continue
            x, y = pts[j]
            cx, cy = x + nx * row * w, y + ny * row * w
            tx2, ty2 = tang(pts, j)
            s += P(f"M{f(cx + nx * 4)} {f(cy + ny * 4)} Q{f(cx + tx2 * 6)} {f(cy + ty2 * 6)} {f(cx - nx * 4)} {f(cy - ny * 4)}", col, 1.6)
    return s


def yong():
    n = 90
    c = ring_pts(36, 336, 64, wave=4, waves=2, n=n)
    wfn = lambda t: 3.5 + 13 * (1 - t) ** .6
    l, r = ribbon(c, wfn)
    s = P(poly(l + r[::-1], True), TEAL[0], 4)
    s += scales(c, wfn, TEAL[1], 4)
    # dorsal spikes on the outer side
    for i in range(14, n - 6, 6):
        x, y = c[i]
        L = math.hypot(x, y)
        ox, oy = x / L, y / L
        tx, ty = tang(c, i)
        w = wfn(i / n)
        s += P(poly([(x + ox * w, y + oy * w), (x + ox * (w + 9) + tx * 5, y + oy * (w + 9) + ty * 5), (x + ox * w + tx * 9, y + oy * w + ty * 9)]), ORANGE[0], 2.6)
    # legs with claws
    for i in (22, 42, 62):
        x, y = c[i]
        L = math.hypot(x, y)
        ix, iy = -x / L, -y / L
        tx, ty = tang(c, i)
        w = wfn(i / n)
        bx, by = x + ix * w, y + iy * w
        ex, ey = bx + ix * 15 + tx * 5, by + iy * 15 + ty * 5
        s += P(f"M{f(bx)} {f(by)} Q{f(bx + ix * 8 + tx * 8)} {f(by + iy * 8 + ty * 8)} {f(ex)} {f(ey)}", TEAL[0], 3.6)
        for k in (-1, 0, 1):
            cx, cy = ex + ix * 6 + tx * k * 6, ey + iy * 6 + ty * k * 6
            s += P(f"M{f(ex)} {f(ey)} L{f(cx)} {f(cy)}", GOLD[0], 2.4)
    # head at the start of the body, facing against the travel direction
    hx, hy = c[0]
    tx, ty = tang(c, 0)
    ang = math.degrees(math.atan2(-ty, -tx))
    head = (P("M0 -9 C10 -13 24 -11 34 -6 C39 -4 39 1 34 3 C26 7 12 9 0 9 Z", GOLD[0], 3.6)
            + P("M33 0 C24 2 14 3 2 2", GOLD[1], 1.6)
            + DOT(31, -5, RED[0], 4)
            + P(circle(3, 14, -5), RED[0], 2.4) + DOT(14, -5, WHITE[1], 3)
            + P("M6 -10 C0 -22 -10 -26 -20 -24", ORANGE[0], 3) + P("M11 -11 C9 -25 1 -33 -8 -35", ORANGE[0], 3)
            + P("M33 3 C44 9 54 20 62 18", PINK[0], 2) + P("M33 -2 C47 -10 58 -4 64 -12", PINK[0], 2)
            + P("M0 -9 C-9 -5 -17 -10 -25 -5", RED[0], 3) + P("M0 9 C-9 6 -16 10 -24 6", RED[0], 3))
    s += G(f"translate({f(hx)} {f(hy)}) rotate({f(ang)}) scale(1.45)", head)
    # pearl in the middle
    s += P(circle(15), YELLOW[0], 4) + P(spiral(0, 0, 11, 2, 1.4), YELLOW[1], 2.4)
    s += around(8, lambda k: P(lens(12, 3, r0=19), ORANGE[0], 2.6))
    return s


def hak():
    s = P(circle(18, 46, 48), GOLD[0], 3) + P(circle(11, 46, 48), GOLD[1], 1.6)
    # body
    s += G("rotate(-8)", P("M-30 6 C-30 -8 -6 -12 18 -6 C30 -2 30 10 14 12 C-6 16 -30 16 -30 6Z", WHITE[0], 4))
    # neck + head
    neck = bez((18, -4), (40, -14), (30, -40), (50, -36), 20)
    l, r = ribbon(neck, lambda t: 4.2 - 1.6 * t)
    s += P(poly(l + r[::-1], True), WHITE[0], 3.4)
    s += P(circle(5, 53, -37), WHITE[0], 3.4) + P("M57 -38 L76 -34", ORANGE[0], 3) + DOT(54, -38, RED[0], 4) + P("M49 -42 Q53 -50 58 -43", RED[0], 3)
    # wings
    s += P("M0 -6 C-6 -38 -30 -70 -76 -68 C-62 -58 -62 -48 -70 -40 C-56 -40 -52 -32 -56 -24 C-42 -28 -32 -20 -24 -10Z", BLUE[0], 4)
    s += P("M0 8 C-8 34 -34 56 -76 56 C-62 48 -62 38 -70 32 C-56 34 -50 28 -52 20 C-38 24 -28 18 -22 12Z", BLUE[0], 4)
    for a in (-58, -42, -26):
        x, y = pt(70, a)
        s += P(f"M-2 -4 L{f(-60 + (a + 58) * .1)} {f(-62 + (a + 58) * 1.4)}", BLUE[1], 1.6)
    for y2 in (22, 34, 46):
        s += P(f"M-2 8 L-64 {y2 + 2}", BLUE[1], 1.6)
    # tail and legs
    s += P("M-30 6 L-56 6 L-52 12 L-60 14 L-30 14", WHITE[0], 3) 
    s += P("M-26 14 L-72 30", ORANGE[0], 2.6) + P("M-22 14 L-70 38", ORANGE[0], 2.6)
    return G("translate(4 4)", s)


def geobuk():
    s = P("M0 -54 C34 -54 46 -20 46 4 C46 36 26 56 0 56 C-26 56 -46 36 -46 4 C-46 -20 -34 -54 0 -54Z", GREEN[0], 4.4)
    s += P("M0 -46 C28 -46 38 -18 38 4 C38 30 22 48 0 48 C-22 48 -38 30 -38 4 C-38 -18 -28 -46 0 -46Z", GREEN[1], 1.6)
    # hexagon (gwigapmun) shell pattern
    def hexa(cx, cy, r):
        return poly([(cx + r * math.cos(math.radians(60 * i + 30)), cy + r * math.sin(math.radians(60 * i + 30))) for i in range(6)], True)
    s += P(hexa(0, 2, 15), YELLOW[0], 3.4)
    for k in range(6):
        cx, cy = pt(26, k * 60)
        s += P(hexa(cx, cy + 2, 15), YELLOW[0], 3.4)
    # head, tail, flippers
    s += P(circle(12, 0, -64), TEAL[0], 4) + DOT(-5, -66, WHITE[1], 5) + DOT(5, -66, WHITE[1], 5)
    s += P("M-6 -54 L-6 -50 M6 -54 L6 -50", TEAL[0], 3)
    s += P("M-6 56 L0 72 L6 56", TEAL[0], 3.4)
    for a, l in ((-52, 36), (52, 36)):
        s += G(f"translate({f(math.sin(math.radians(a)) * 44)} -30) rotate({a * 1.0 + (-20 if a < 0 else 20)})", PL(lens(l, 10), TEAL, 3.4))
    for a in (-128, 128):
        s += G(f"translate({f(math.sin(math.radians(a)) * 38)} 40) rotate({a * .8})", PL(lens(30, 9), TEAL, 3.4))
    return G("scale(1.1)", s)


def horangi():
    half = (
        P("M0 -52 C-34 -54 -60 -34 -60 -2 C-60 30 -36 52 0 52", ORANGE[0], 4.4)
        + P("M-36 -40 C-48 -58 -64 -52 -62 -34", ORANGE[0], 4) + P("M-40 -40 C-48 -50 -56 -48 -57 -38", ORANGE[1], 1.6)
        # stripes on the cheek
        + P("M-60 -6 L-42 -2 L-58 2Z", RED[0], 2.6) + P("M-58 12 L-42 14 L-54 20Z", RED[0], 2.6) + P("M-52 28 L-38 28 L-46 34Z", RED[0], 2.6)
        + P("M-24 -48 L-18 -34 L-28 -36Z", RED[0], 2.6) + P("M-40 -34 L-34 -22 L-44 -24Z", RED[0], 2.6)
        # eye and brow
        + P("M-30 -16 C-26 -26 -12 -26 -8 -16 C-12 -8 -26 -8 -30 -16Z", GOLD[0], 3.4) + DOT(-19, -16, RED[0], 8) + DOT(-19, -16, WHITE[1], 3)
        + P("M-34 -28 C-24 -34 -12 -34 -6 -28", ORANGE[1], 2.4)
        # muzzle
        + P("M0 14 C-8 10 -18 12 -22 20 C-26 30 -12 36 0 32", WHITE[0], 3.2)
        + P("M0 26 C-4 34 -10 38 -16 36", ORANGE[1], 2.4) + P("M-12 22 L-30 20 M-12 26 L-30 28", WHITE[1], 1.6)
    )
    s = mirror(half)
    s += P("M-9 6 L9 6 L0 16Z", PINK[0], 3.4)
    s += P("M0 16 L0 26", WHITE[1], 2.4)
    s += P("M-14 -42 L14 -42", YELLOW[0], 3.4) + P("M-9 -34 L9 -34", YELLOW[0], 3.4) + P("M-13 -26 L13 -26", YELLOW[0], 3.4) + P("M0 -42 L0 -26", YELLOW[0], 3.4)
    return G("scale(1.2)", s)


def _antler(side):
    s = P("M10 -36 C22 -52 34 -62 40 -78", GOLD[0], 3.8) + P("M10 -36 C22 -52 34 -62 40 -78", GOLD[1], 1.4)
    for (x, y, ex, ey) in [(18, -48, 36, -50), (27, -58, 48, -62), (34, -68, 52, -80), (40, -78, 34, -96), (40, -78, 48, -94)]:
        s += P(f"M{x} {y} Q{(x + ex) / 2 + 2} {(y + ey) / 2 - 3} {ex} {ey}", GOLD[0], 3)
    return s


def saseum():
    s = P("M0 54 C-16 44 -26 20 -26 -10 C-26 -30 -10 -38 0 -38 C10 -38 26 -30 26 -10 C26 20 16 44 0 54Z", ORANGE[0], 4.4)
    s += P("M0 46 C-12 38 -20 18 -20 -8 C-20 -24 -8 -31 0 -31 C8 -31 20 -24 20 -8 C20 18 12 38 0 46Z", ORANGE[1], 1.4)
    half = (_antler(1) + G("translate(26 -20) rotate(72)", PL(lens(30, 9), TEAL, 3.4))
            + P(circle(4.5, 12, -4), WHITE[0], 3) + DOT(12, -4, WHITE[1], 4)
            + P("M8 -24 L14 -22 M12 -16 L18 -14", WHITE[1], 2))
    s += mirror(half)
    s += P("M-6 46 C-4 52 4 52 6 46", PINK[0], 3.4) + DOT(0, 48, PINK[0], 7)
    for x, y in [(0, -30), (-6, -22), (6, -22), (0, -14)]:
        s += DOT(x, y, GOLD[1], 4)
    return G("scale(1.05)", s)


def ingeo():
    n = 90
    c = ring_pts(24, 330, 60, wave=4, waves=2, n=n)
    wfn = lambda t: 2 + 15 * math.sin(math.pi * min(1, t * 1.15 + .08)) ** .8
    l, r = ribbon(c, wfn)
    s = P(poly(l + r[::-1], True), ORANGE[0], 4.2) + P(poly(c), ORANGE[1], 1.2)
    for row in (-.55, 0, .55):
        pass
    s += fish_scales(c, wfn, GOLD[1])
    # tail fin
    ex, ey = c[-1]
    tx, ty = tang(c, n)
    ang = math.degrees(math.atan2(ty, tx)) + 90
    s += G(f"translate({f(ex)} {f(ey)}) rotate({f(ang)})", ''.join(P(f"M0 0 L{f(30 * math.sin(math.radians(a)))} {f(-30 * math.cos(math.radians(a)))}", RED[0], 3) for a in range(-50, 51, 25)) + P("M-24 -24 Q0 -38 24 -24", RED[0], 3))
    # dorsal / pectoral fins
    for i in range(30, 62, 4):
        x, y = c[i]
        L = math.hypot(x, y)
        ox, oy = x / L, y / L
        w = wfn(i / n)
        s += P(f"M{f(x + ox * w)} {f(y + oy * w)} L{f(x + ox * (w + 9))} {f(y + oy * (w + 9))}", RED[0], 2.6)
    # head: eye, mouth, whiskers
    hx, hy = c[3]
    tx, ty = tang(c, 3)
    ang = math.degrees(math.atan2(-ty, -tx))
    s += G(f"translate({f(hx)} {f(hy)}) rotate({f(ang)})", P(circle(3.4, 8, -5), WHITE[0], 2.6) + DOT(8, -5, RED[0], 4)
           + P("M16 0 C22 2 26 8 34 8", PINK[0], 2) + P("M16 -2 C24 -8 30 -6 38 -12", PINK[0], 2))
    # water waves in the middle
    for k, y in enumerate((-14, 0, 14)):
        s += P(f"M{-26 + 4 * k} {y} q6 -8 13 0 t13 0 t13 0", BLUE[0], 3.2)
    return s


def bakjwi():
    wing = (P("M12 -6 C32 -44 62 -54 94 -42 C86 -30 90 -22 82 -10 C76 -20 68 -16 60 2 C56 -8 46 -6 38 12 C32 2 24 4 14 18", RED[0], 4)
            + P("M10 -2 L92 -40 M10 0 L80 -9 M10 4 L58 3 M10 10 L36 12", PINK[1], 1.6)
            + P(circle(5, 52, -22), YELLOW[0], 2.8))
    s = mirror(wing)
    s += P("M0 -4 C-12 6 -10 28 0 40 C10 28 12 6 0 -4Z", RED[0], 4)
    s += P(circle(11, 0, -22), RED[0], 4) + P("M-9 -30 L-12 -42 L-3 -34 M9 -30 L12 -42 L3 -34", RED[0], 3.4)
    s += DOT(-4, -22, YELLOW[0], 5) + DOT(4, -22, YELLOW[0], 5) + P("M-4 -16 L-2 -11 M4 -16 L2 -11", WHITE[0], 2.2)
    s += P("M0 40 C-6 52 -2 60 0 62 C2 60 6 52 0 40", RED[1], 2.4)
    return s


def nabi():
    wing = (P("M6 -4 C18 -48 62 -72 88 -58 C100 -40 80 -14 46 -6Z", VIOLET[0], 4)
            + P("M6 4 C30 6 62 18 66 46 C64 68 28 70 12 40Z", PINK[0], 4)
            + P(circle(12, 56, -36), TEAL[0], 3.2) + P(circle(5.5, 56, -36), TEAL[1], 2) + P(circle(9, 40, 38), TEAL[0], 3)
            + P("M8 -4 L84 -52 M8 -2 L70 -22 M8 6 L60 36 M8 8 L40 52", VIOLET[1], 1.6))
    s = mirror(wing)
    s += P("M0 -22 C-8 -10 -8 26 0 44 C8 26 8 -10 0 -22Z", GOLD[0], 4) + P(circle(7, 0, -28), GOLD[0], 3.4)
    s += P("M-3 -34 C-6 -54 -18 -66 -28 -62", GOLD[0], 2.8) + P("M3 -34 C6 -54 18 -66 28 -62", GOLD[0], 2.8)
    s += DOT(-28, -62, GOLD[1], 6) + DOT(28, -62, GOLD[1], 6)
    return s


def girin():
    body = P("M-48 -6 C-48 -26 -6 -30 22 -22 C42 -16 42 14 22 20 C-8 28 -48 18 -48 -6Z", ORANGE[0], 4.2)
    s = body
    for r in range(3):
        for i in range(6 - r):
            s += P(f"M{-40 + i * 12 + r * 6} {-8 + r * 9} q4 -4 8 0", ORANGE[1], 1.5)
    neck = bez((22, -18), (40, -24), (40, -44), (52, -54), 20)
    l, r = ribbon(neck, lambda t: 9 - 3 * t)
    s += P(poly(l + r[::-1], True), ORANGE[0], 3.8)
    # head (dragon-like) with horn
    s += P("M46 -56 C54 -66 70 -64 80 -56 C82 -52 80 -48 74 -47 C66 -44 54 -44 46 -50Z", GOLD[0], 3.6)
    s += DOT(60, -57, RED[0], 5) + P("M52 -62 C48 -76 40 -84 30 -82", RED[0], 3.2)
    s += P("M80 -52 C88 -50 92 -42 98 -44", PINK[0], 2)
    # mane flames
    for i, (x, y) in enumerate([(30, -26), (36, -36), (42, -46)]):
        s += P(f"M{x} {y} c-12 -4 -14 -14 -6 -18", GOLD[0], 3)
    # legs and hooves
    for x0, x1 in ((22, 28), (8, 8), (-28, -32), (-18, -14)):
        l2, r2 = ribbon(bez((x0, 18), (x0, 36), (x1, 48), (x1, 64), 10), lambda t: 5 - 1.4 * t)
        s += P(poly(l2 + r2[::-1], True), ORANGE[0], 3.4) + P(poly([(x1 - 6, 64), (x1 + 6, 64), (x1 + 4, 72), (x1 - 4, 72)], True), RED[0], 3)
    # tail
    s += P("M-48 -6 C-62 -16 -70 -34 -60 -46 C-58 -34 -52 -30 -46 -26", GOLD[0], 3.6) + P("M-60 -46 C-70 -50 -74 -40 -68 -34", GOLD[0], 2.6)
    # shoulder & haunch scrolls
    s += P(spiral(10, 0, 3, 13, 1.6), TEAL[0], 3) + P(spiral(-28, -2, 3, 13, 1.6, a0=90), TEAL[0], 3)
    return G("scale(1.05) translate(-6 8)", s)


def haetae():
    # flame mane
    mane = around(16, lambda k: P("M0 -42 C-10 -56 -4 -70 4 -80 C6 -66 14 -60 10 -44", ORANGE[0], 3.6) + P("M0 -46 C-4 -58 0 -66 4 -74", ORANGE[1], 1.4))
    s = spin(mane, 'cw')
    s += P(circle(42, 0, 8), GOLD[0], 4.4) + P(circle(36, 0, 8), GOLD[1], 1.4)
    half = (P("M-30 -6 C-22 -16 -8 -14 -4 -4 C-8 4 -22 6 -30 -6Z", WHITE[0], 3.4) + DOT(-17, -6, RED[0], 9) + DOT(-17, -6, WHITE[1], 3.4)
            + P("M-36 -18 C-26 -26 -10 -24 -6 -16", RED[0], 4)
            + P("M-4 22 C-14 18 -24 22 -28 30 C-22 40 -10 38 -4 34", GOLD[1], 2.6)
            + P("M-34 -2 C-46 4 -48 16 -40 22", ORANGE[0], 3) + P(spiral(-42, 28, 2, 8, 1.4), ORANGE[0], 2.6))
    s += mirror(half)
    s += P("M-10 12 L10 12 C8 22 -8 22 -10 12Z", PINK[0], 3.4)
    s += P("M-18 32 C-10 42 10 42 18 32", RED[0], 3.4) + P("M-11 34 L-8 42 L-5 36 M5 36 L8 42 L11 34", WHITE[0], 2.6)
    s += P("M0 -36 C-8 -50 4 -62 0 -78", PINK[0], 4) + P("M0 -36 C-8 -50 4 -62 0 -78", PINK[1], 1.4)
    return s


PATTERNS = {
    'yong': ('02_동물문', '용', yong), 'hak': ('02_동물문', '학', hak), 'geobuk': ('02_동물문', '거북', geobuk),
    'horangi': ('02_동물문', '호랑이', horangi), 'saseum': ('02_동물문', '사슴', saseum), 'ingeo': ('02_동물문', '잉어', ingeo),
    'bakjwi': ('02_동물문', '박쥐(복)', bakjwi), 'nabi': ('02_동물문', '나비', nabi), 'girin': ('02_동물문', '기린', girin),
    'haetae': ('02_동물문', '해태', haetae),
}
