"""01 식물문"""
import math
from core import *


def yeonhwa():
    s = around(8, lambda k: PL(lens(58, 12, r0=40), VIOLET, 4.4, False) + P(lens(44, 6, r0=52), VIOLET[1], 2.2), start=22.5)
    s += around(8, lambda k: P("M0 -30 C-24 -46 -24 -80 -7 -100 L0 -92 L7 -100 C24 -80 24 -46 0 -30Z", PINK[0], 4.4)
               + P("M0 -42 C-12 -54 -12 -74 0 -88 C12 -74 12 -54 0 -42Z", PINK[1], 2.2))
    s = spin(s, 'cw')
    s += P(circle(27), YELLOW[0], 4.4) + P(circle(18), YELLOW[1], 2.2) + DOT(0, 0, YELLOW[1], 8)
    for i in range(6):
        x, y = pt(10, i * 60)
        s += DOT(x, y, YELLOW[1], 6)
    return s


def moran():
    s = around(8, lambda k: PL(drop(60, 28, r0=28), PINK))
    s += around(8, lambda k: PL(drop(46, 22, r0=18), MAGENTA), start=22.5)
    s += around(6, lambda k: PL(drop(30, 15, r0=8), PINK), start=15)
    s += around(8, lambda k: P(lens(22, 6, r0=80), TEAL[0], 3.4), start=22.5)
    s += P(circle(8), GOLD[0], 3.4)
    for i in range(8):
        x, y = pt(13, i * 45)
        s += DOT(x, y, GOLD[1], 5)
    return spin(s, 'cw')


def gukhwa():
    s = around(24, lambda k: PL(lens(72, 8, r0=22), YELLOW, 3.6))
    s += around(24, lambda k: PL(lens(50, 7, r0=16), ORANGE, 3.4), start=7.5)
    s += around(12, lambda k: PL(lens(28, 6, r0=8), GOLD, 3.2), start=0)
    s += P(circle(11), ORANGE[0], 3.6)
    for i in range(7):
        x, y = (0, 0) if i == 0 else pt(6, i * 60)
        s += DOT(x, y, YELLOW[1], 5)
    return spin(s, 'cw')


def maehwa():
    s = around(5, lambda k: P(circle(25, 0, -40), WHITE[0], 4.4) + P(circle(14, 0, -42), PINK[0], 2.2), start=0)
    s += around(10, lambda k: P("M0 0 L0 -24", GOLD[0], 2.4) + DOT(0, -26, GOLD[1], 6))
    s += DOT(0, 0, GOLD[1], 9)
    # twig ring with buds
    s += around(5, lambda k: P(circle(10, 0, -86), PINK[0], 3.6) + DOT(0, -86, PINK[1], 6)
               + P("M0 -76 C-4 -64 -2 -62 0 -62", PINK[1], 1.6), start=36)
    return spin(s, 'cw')


def dangcho():
    def unit(k):
        e = pt(70, 48)
        c = pt(56, 48)
        stem = P("M" + " L".join(f"{f(x)} {f(y)}" for x, y in [pt(70 + 8 * math.sin(math.radians(a * 7.5)), a) for a in range(0, 49, 4)]),
                 TEAL[0], 3.8)
        curl = P(spiral(c[0], c[1], 14, 2.5, 1.6, a0=48 - 90), GREEN[0], 3.6)
        leaf1 = G("rotate(20)", PL(lens(26, 9, r0=70), GREEN, 3.2))
        px, py = pt(70, 36)
        leaf2 = G(f"translate({f(px)} {f(py)}) rotate(215)", PL(lens(24, 8), GREEN, 3.2))
        return stem + curl + leaf1 + leaf2
    s = around(6, unit)
    s += around(6, lambda k: P(drop(20, 9, r0=14), PINK[0], 3.4), start=0)
    s += P(circle(8), PINK[1], 2.4)
    return spin(s, 'cw')


def bosanghwa():
    s = around(8, lambda k: PL(drop(68, 26, r0=26), RED, 4.4)
               + P(spiral(0, -62, 11, 2.5, 1.5, a0=-90), GOLD[0], 3))
    s += around(8, lambda k: PL(lens(44, 9, r0=34), TEAL, 3.6), start=22.5)
    s += P(lobed(22, 8, .1), GOLD[0], 3.6) + P(circle(11), GOLD[1], 2.2) + DOT(0, 0, GOLD[1], 8)
    return spin(s, 'cw')


def lobed(R, n, amp, steps=120):
    return poly([(R * (1 + amp * math.cos(n * 2 * math.pi * i / steps)) * math.sin(2 * math.pi * i / steps),
                  -R * (1 + amp * math.cos(n * 2 * math.pi * i / steps)) * math.cos(2 * math.pi * i / steps))
                 for i in range(steps)], True)


def podo():
    s = ''
    for r in range(5):
        cnt = 5 - r
        y = -26 + r * 17
        for i in range(cnt):
            x = (i - (cnt - 1) / 2) * 19
            s += P(circle(9.2, x, y), VIOLET[0] if (r + i) % 2 else BLUE[0], 3.8)
            s += DOT(x - 3, y - 3, WHITE[1], 3.5)
    s += P("M0 -36 C2 -50 -4 -58 -14 -64", TEAL[0], 4)
    s += P("M0 -36 C4 -50 12 -56 30 -58", TEAL[0], 3)
    # leaves (three-lobed)
    def leaf(tf):
        return G(tf, ''.join(G(f"rotate({a})", PL(lens(26, 9), GREEN, 3.2)) for a in (-50, 0, 50)))
    s += leaf("translate(-16 -66) rotate(-30)")
    s += leaf("translate(32 -58) rotate(50)")
    s += P(spiral(-52, -30, 3, 14, 1.6, a0=0), GREEN[0], 3) + P("M-14 -64 C-34 -56 -52 -44 -52 -30", GREEN[0], 2.4)
    s += P(spiral(52, 6, 3, 13, 1.6, a0=180), GREEN[0], 3)
    return G('translate(0 4) scale(1.2)', s)


def seokryu():
    s = P(circle(42, 0, 12), RED[0], 4.6) + P(circle(36, 0, 12), RED[1], 1.6)
    s += P("M-16 -26 L-11 -44 L-4 -32 L0 -48 L4 -32 L11 -44 L16 -26", ORANGE[0], 4)
    # opened part with seeds
    s += P("M-24 8 C-16 -6 16 -6 24 8", PINK[0], 3) 
    for r, y in enumerate([2, 15, 28]):
        cnt = 4 - (1 if r == 2 else 0)
        for i in range(cnt):
            x = (i - (cnt - 1) / 2) * 13
            s += P(circle(5.2, x, y), PINK[0], 2.8) + DOT(x, y, PINK[1], 3)
    s += G("translate(-8 -30) rotate(-55)", PL(lens(40, 10), TEAL, 3.4))
    s += G("translate(8 -30) rotate(55)", PL(lens(40, 10), GREEN, 3.4))
    return G('translate(0 6) scale(1.5)', s)


def daenamu():
    s = ''
    for x, off in [(-34, 0), (0, 14), (34, 6)]:
        s += P(f"M{x - 5} -100 L{x - 5} 100", TEAL[0], 3.6) + P(f"M{x + 5} -100 L{x + 5} 100", TEAL[0], 3.6)
        for j in range(-4, 5):
            y = off + j * 34
            s += P(f"M{x - 7} {y} Q{x} {y + 5} {x + 7} {y}", TEAL[1], 2.6)
        for y in (off - 70, off - 36, off - 2):
            for a in (-62, -28, 28, 62):
                s += G(f"translate({x} {y}) rotate({a})", PL(lens(32, 6), GREEN, 3))
    return clip(s)


def sonamu():
    trunk = bez((-8, 100), (30, 60), (-34, 10), (4, -40), 20)
    l, r = ribbon(trunk, lambda t: 6 - 3 * t)
    s = P(poly(l + r[::-1], True), ORANGE[0], 3.8)
    s += P(poly(trunk), ORANGE[1], 1.4)
    s += P("M4 -40 C8 -52 -6 -60 -30 -50", ORANGE[0], 3.2) + P("M-6 20 C20 18 30 4 34 -12", ORANGE[0], 3.2)
    s += P("M-18 50 C-34 40 -40 30 -34 10", ORANGE[0], 3.2)

    def tuft(cx, cy, rad):
        t = ''
        for a in range(-80, 81, 16):
            x1, y1 = pt(rad * .35, a)
            x2, y2 = pt(rad, a)
            t += P(f"M{f(cx + x1)} {f(cy + y1)} L{f(cx + x2)} {f(cy + y2)}", GREEN[0], 3.2)
        return t + P(f"M{f(cx + pt(rad, -85)[0])} {f(cy + pt(rad, -85)[1])} A{rad} {rad} 0 0 1 {f(cx + pt(rad, 85)[0])} {f(cy + pt(rad, 85)[1])}", GREEN[1], 1.6)
    s += tuft(-30, -52, 40) + tuft(4, -62, 32) + tuft(36, -22, 36) + tuft(-34, 4, 34) + tuft(-30, 32, 24)
    return clip(s)


def nancho():
    s = ''
    for a, ln, w, col in [(-62, 90, 9, TEAL), (-34, 100, 8, GREEN), (-8, 96, 7, TEAL), (24, 100, 8, GREEN), (58, 90, 9, TEAL)]:
        end = pt(ln, a)
        c1 = (0, 30)
        c = bez((0, 70), (a * .1, 20), (pt(ln * .8, a)[0] * .9, pt(ln * .8, a)[1] + 20), (end[0] * 1.0, end[1] + 10), 24)
        l, r = ribbon(c, lambda t: w * math.sin(math.pi * (t * .9 + .05)) + .5)
        s += P(poly(l + r[::-1], True), col[0], 3.6) + P(poly(c), col[1], 1.2)
    stem = bez((4, 70), (14, 20), (26, -30), (8, -70), 20)
    s += P(poly(stem), VIOLET[0], 2.6)
    for i, (t, sz) in enumerate([(.45, 9), (.7, 8), (.95, 7)]):
        px, py = stem[int(t * 20)]
        for k in range(5):
            s += G(f"translate({f(px)} {f(py)}) rotate({k * 72 + 20})", P(drop(sz * 1.2, sz * .55), PINK[0], 2.6))
        s += DOT(px, py, YELLOW[1], 5)
    return clip(s)


def yeongji():
    def cap(cx, cy, rx, ry, rot, col):
        t = G(f"translate({cx} {cy}) rotate({rot})",
              P(f"M{-rx} 0 C{-rx} {-ry * 1.4} {rx} {-ry * 1.4} {rx} 0 C{rx * .8} {ry * .8} {-rx * .8} {ry * .8} {-rx} 0Z", col[0], 4.2)
              + ''.join(P(f"M{-rx * k} 0 C{-rx * k} {-ry * 1.1 * k} {rx * k} {-ry * 1.1 * k} {rx * k} 0", col[1], 1.8) for k in (.7, .4)))
        return t
    s = ''
    for pts, w in [(bez((6, 70), (10, 40), (-6, 20), (0, -6), 16), 5), (bez((6, 72), (20, 50), (40, 36), (44, 20), 16), 4),
                   (bez((4, 72), (-12, 56), (-34, 44), (-44, 24), 16), 4)]:
        l, r = ribbon(pts, lambda t, w=w: w * (1 - .4 * t))
        s += P(poly(l + r[::-1], True), ORANGE[0], 3.4)
    s += cap(0, -22, 44, 24, 0, RED) + cap(46, 12, 26, 16, 14, ORANGE) + cap(-46, 14, 26, 16, -14, ORANGE)
    s += P(spiral(-70, -52, 2, 10, 1.4), TEAL[0], 3) + P(spiral(70, -52, 2, 10, 1.4, a0=180), TEAL[0], 3)
    return clip(G('translate(0 6) scale(1.2)', s))


PATTERNS = {
    'yeonhwa': ('01_식물문', '연화문', yeonhwa), 'moran': ('01_식물문', '모란문', moran),
    'gukhwa': ('01_식물문', '국화문', gukhwa), 'maehwa': ('01_식물문', '매화문', maehwa),
    'dangcho': ('01_식물문', '당초문', dangcho), 'bosanghwa': ('01_식물문', '보상화문', bosanghwa),
    'podo': ('01_식물문', '포도문', podo), 'seokryu': ('01_식물문', '석류문', seokryu),
    'daenamu': ('01_식물문', '대나무', daenamu), 'sonamu': ('01_식물문', '소나무', sonamu),
    'nancho': ('01_식물문', '난초', nancho), 'yeongji': ('01_식물문', '영지(불로초)', yeongji),
}
