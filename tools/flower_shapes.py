"""Base neon line-art flower shapes.

Every shape draws into a builder `B` using local coordinates (head centre = 0,0,
tip of a petal points to -y) and returns a meta dict:
  top    : y offset (local) where the stem should end (None = no stem)
  hy, tx : where the head is placed on the 800x600 canvas (default 190 / 230)
  extra  : raw global SVG drawn before the head (ripples ...)
  leaves : False to skip the leaves
"""
import math
import random


def a(x):
    return round(x, 1)


def circ(cx, cy, r):
    return f"M{a(cx - r)} {a(cy)}a{a(r)} {a(r)} 0 1 0 {a(2 * r)} 0a{a(r)} {a(r)} 0 1 0 {a(-2 * r)} 0"


def teardrop(w, l):
    return (f"M0 0 C{a(-w)} {a(-.1 * l)} {a(-1.05 * w)} {a(-.65 * l)} {a(-.3 * w)} {a(-.95 * l)} "
            f"C{a(-.1 * w)} {a(-l)} {a(.1 * w)} {a(-l)} {a(.3 * w)} {a(-.95 * l)} "
            f"C{a(1.05 * w)} {a(-.65 * l)} {a(w)} {a(-.1 * l)} 0 0Z")


def lens(w, l):
    return (f"M0 0 C{a(-w)} {a(-.3 * l)} {a(-w)} {a(-.7 * l)} 0 {a(-l)} "
            f"C{a(w)} {a(-.7 * l)} {a(w)} {a(-.3 * l)} 0 0Z")


def notched(w, l):
    return (f"M0 0 C{a(-.9 * w)} {a(-.25 * l)} {a(-1.1 * w)} {a(-.7 * l)} {a(-.55 * w)} {a(-l)} "
            f"L0 {a(-.84 * l)} L{a(.55 * w)} {a(-l)} "
            f"C{a(1.1 * w)} {a(-.7 * l)} {a(.9 * w)} {a(-.25 * l)} 0 0Z")


PETAL = {'lens': lens, 'round': teardrop, 'notch': notched}


def lobed(R, n, amp, steps=120):
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        r = R * (1 + amp * math.cos(n * t))
        pts.append((r * math.sin(t), -r * math.cos(t)))
    return "M" + " L".join(f"{a(x)} {a(y)}" for x, y in pts) + "Z"


class B:
    """Sequential SVG builder; every element gets a staggered animation delay."""

    def __init__(s, t0=2.0, k=1.0):
        s.t = t0
        s.k = k  # time compression factor (intro mosaic draws flowers quickly)
        s.o = []

    def p(s, d, cls='pet', step=.07, dur=.7, at=None):
        step, dur = step * s.k, dur * s.k
        t = s.t if at is None else at
        s.o.append(f'<path class="d {cls}" pathLength="1" style="--s:{t:.2f}s;--t:{dur}s" d="{d}"/>')
        if at is None:
            s.t += step

    def dot(s, x, y, r=2, cls='dotc', step=.006):
        step *= s.k
        s.o.append(f'<circle class="fi {cls}" cx="{a(x)}" cy="{a(y)}" r="{r}" style="--s:{s.t:.2f}s"/>')
        s.t += step

    def g(s, tf):
        s.o.append(f'<g transform="{tf}">')

    def e(s):
        s.o.append('</g>')

    def out(s):
        return ''.join(s.o)


def ring(b, n, d, rot0=0, r0=0, cls='pet', step=.07):
    for i in range(n):
        ang = rot0 + i * 360 / n
        b.g(f'rotate({a(ang)}) translate(0 {a(-r0)})')
        b.p(d, cls, step)
        b.e()


def line(x1, y1, x2, y2):
    return f"M{a(x1)} {a(y1)} L{a(x2)} {a(y2)}"


def phyllo(b, R, size=1.3):
    n = int(R * R / 8)
    for i in range(n):
        r = R * math.sqrt((i + .5) / n) * .93
        ang = i * 2.39996
        b.dot(r * math.cos(ang), r * math.sin(ang), size, step=.004)


# ---------------------------------------------------------------- shapes

def rose(b, **k):
    for n, w, l, rot, r0 in [(5, 44, 66, 0, 2), (5, 34, 50, 36, 2), (4, 24, 34, 18, 0)]:
        ring(b, n, teardrop(w, l), rot, r0)
    pts = []
    for i in range(61):
        t = i / 60
        ang = t * 2.6 * 2 * math.pi
        rad = 3 + t * 20
        pts.append((rad * math.cos(ang), rad * math.sin(ang)))
    b.p("M" + " L".join(f"{a(x)} {a(y)}" for x, y in pts), 'pet2', dur=1)
    return dict(top=58)


def tulip(b, **k):
    b.p("M0 50 C-44 46 -50 0 -40 -62 C-24 -48 -12 -34 -4 -14 C-2 20 0 40 0 50Z", step=.25, dur=1)
    b.p("M0 50 C44 46 50 0 40 -62 C24 -48 12 -34 4 -14 C2 20 0 40 0 50Z", step=.25, dur=1)
    b.p("M0 50 C-26 30 -30 -20 0 -76 C30 -20 26 30 0 50Z", 'pet', step=.3, dur=1)
    b.p("M0 40 C-10 10 -8 -25 0 -52", 'pet2', step=.2)
    return dict(top=46)


def daisy(b, count=20, length=55, width=7, center=16, layers=1, kind='lens', dots=True, cr=None):
    for L in range(layers):
        ln = length * (1 - .22 * L)
        ring(b, count, PETAL[kind](width, ln), L * 180 / count, center * .8,
             'pet' if L == 0 else 'pet2', step=.03)
    b.p(circ(0, 0, center), 'pet2')
    if dots:
        phyllo(b, center * .9)
    return dict(top=center * .8 + length * .9)


def cherry(b, petals=5, notch=True, layers=1, w=28, l=62):
    kind = notched if notch else teardrop
    ring(b, petals, kind(w, l), 0, 4)
    if layers > 1:
        ring(b, petals, kind(w * .8, l * .78), 180 / petals, 3, 'pet2')
    for i in range(10):
        ang = math.radians(i * 36 + 8)
        ln = 20 + (i % 2) * 9
        b.p(line(0, 0, ln * math.sin(ang), -ln * math.cos(ang)), 'pet2', step=.03, dur=.4)
        b.dot(ln * math.sin(ang), -ln * math.cos(ang), 2.2, step=.01)
    b.p(circ(0, 0, 4), 'pet2')
    return dict(top=l * .8)


def lotus(b, **k):
    for n, l, w, span in [(7, 74, 17, 78), (5, 62, 15, 52), (3, 50, 13, 26)]:
        for i in range(n):
            ang = -span + i * 2 * span / (n - 1)
            b.g(f'rotate({a(ang)})')
            b.p(lens(w, l), 'pet' if n != 3 else 'pet2', step=.1)
            b.e()
    rip = B(0.5)
    for rx, ry, dl in [(125, 20, .5), (88, 14, .9), (54, 8, 1.3)]:
        rip.p(f"M{235 - rx} 408 a{rx} {ry} 0 1 0 {2 * rx} 0 a{rx} {ry} 0 1 0 {-2 * rx} 0", 'rip', dur=1.2, at=dl)
    return dict(top=None, hy=400, extra=rip.out(), leaves=False)


def _floret(b, kind, s):
    if kind == 'lav':
        b.p(f"M0 0 C{a(-12 * s)} {a(-10 * s)} {a(-12 * s)} {a(-30 * s)} 0 {a(-42 * s)} "
            f"C{a(12 * s)} {a(-30 * s)} {a(12 * s)} {a(-10 * s)} 0 0Z", step=.05, dur=.6)
        b.p(f"M0 {a(-4 * s)} C{a(-5 * s)} {a(-14 * s)} {a(-5 * s)} {a(-26 * s)} 0 {a(-34 * s)} "
            f"C{a(5 * s)} {a(-26 * s)} {a(5 * s)} {a(-14 * s)} 0 {a(-4 * s)}Z", 'pet2', step=.02, dur=.5)
    elif kind == 'delph':
        b.p(teardrop(13 * s, 24 * s), step=.05, dur=.6)
        b.g('rotate(-70)')
        b.p(teardrop(9 * s, 18 * s), 'pet2', step=.02, dur=.5)
        b.e()
        b.g('rotate(70)')
        b.p(teardrop(9 * s, 18 * s), 'pet2', step=.02, dur=.5)
        b.e()
        b.dot(0, -3 * s, 2, step=.02)
    elif kind == 'snap':
        b.p(teardrop(16 * s, 30 * s), step=.05, dur=.6)
        b.p(f"M{a(-8 * s)} {a(-8 * s)} Q0 {a(6 * s)} {a(8 * s)} {a(-8 * s)}", 'pet2', step=.02, dur=.4)
    else:  # stock
        for r in (0, 90, 180, 270):
            b.g(f'rotate({r})')
            b.p(teardrop(7 * s, 13 * s), step=.012, dur=.4)
            b.e()
        b.dot(0, 0, 2, step=.01)


def spike(b, kind='lav', **k):
    n = 9
    for i in range(n):
        y = 90 - i * 22
        s = 1 - i * .05
        for side in (-1, 1):
            b.g(f'translate({a(side * 12 * s)} {y}) rotate({a(side * (25 + i))})')
            _floret(b, kind, s)
            b.e()
    b.g('translate(0 -100)')
    b.p(lens(9, 34), step=.1)
    b.e()
    return dict(top=-98)


def trumpet(b, kind='glory', **k):
    if kind == 'hibiscus':
        ring(b, 5, teardrop(44, 70), 0, 2, step=.15)
        for i in range(5):
            ang = math.radians(i * 72 + 36)
            b.p(line(0, 0, 26 * math.sin(ang), -26 * math.cos(ang)), 'pet2', step=.03, dur=.4)
        b.p("M0 0 C3 -20 4 -34 5 -52", 'pet2', step=.2)
        for i in range(6):
            ang = i * 1.05
            b.dot(5 + 7 * math.cos(ang), -52 + 7 * math.sin(ang), 2.2, step=.03)
        return dict(top=60)
    amp, n = (.05, 5) if kind == 'glory' else (.09, 5)
    R = 66
    b.p(lobed(R, n, amp), step=.4, dur=1.2)
    if kind == 'petunia':
        b.p(lobed(R * .62, n, amp * .8), 'pet2', step=.3, dur=1)
    b.p(circ(0, 0, 20), 'pet2')
    for i in range(n):
        ang = math.radians(i * 360 / n)
        b.p(line(22 * math.sin(ang), -22 * math.cos(ang), (R - 4) * math.sin(ang), -(R - 4) * math.cos(ang)),
            'pet2', step=.08, dur=.5)
    b.dot(0, 0, 4)
    return dict(top=R * .95)


PEONY_RINGS = {
    'peony': (teardrop, [(9, 34, 60, 0, 14), (8, 28, 48, 20, 8), (7, 22, 36, 10, 4), (6, 16, 26, 0, 0)]),
    'camellia': (teardrop, [(6, 36, 56, 0, 8), (6, 28, 44, 30, 4), (5, 20, 30, 10, 0)]),
    'dahlia': (lens, [(14, 16, 62, 0, 8), (12, 14, 50, 15, 5), (10, 12, 38, 0, 3), (8, 10, 26, 10, 0)]),
    'carnation': (notched, [(10, 30, 56, 0, 12), (9, 26, 44, 18, 8), (8, 20, 32, 10, 4), (6, 14, 22, 0, 0)]),
    'ranunculus': (teardrop, [(14, 20, 52, 0, 10), (12, 18, 42, 15, 6), (10, 15, 32, 0, 3), (8, 12, 22, 0, 0)]),
    'zinnia': (teardrop, [(14, 18, 60, 0, 6), (12, 16, 48, 12, 4), (10, 14, 36, 0, 2), (8, 11, 24, 10, 0)]),
}


def peony(b, kind='peony', **k):
    petal, rings = PEONY_RINGS[kind]
    for n, w, l, rot, r0 in rings:
        ring(b, n, petal(w, l), rot, r0, step=.05)
    if kind == 'camellia':
        for i in range(14):
            ang = i * 2.4
            b.dot(9 * math.cos(ang), 9 * math.sin(ang), 1.8, step=.02)
    else:
        b.p(circ(0, 0, 4), 'pet2')
    return dict(top=58)


def bell(b, kind='bell', n=5, size=1.0, **k):
    b.p("M230 560 C226 440 228 300 232 235 C236 175 190 130 130 150", 'stem', at=0, dur=2.2)
    P = [(232, 235), (236, 175), (190, 130), (130, 150)]
    for i in range(n):
        t = .22 + .72 * i / max(n - 1, 1)
        u = 1 - t
        x = u ** 3 * P[0][0] + 3 * u * u * t * P[1][0] + 3 * u * t * t * P[2][0] + t ** 3 * P[3][0]
        y = u ** 3 * P[0][1] + 3 * u * u * t * P[1][1] + 3 * u * t * t * P[2][1] + t ** 3 * P[3][1]
        s = size * (1.1 - .45 * i / max(n - 1, 1))
        b.g(f'translate({a(x)} {a(y)})')
        b.p(f"M0 0 Q4 {a(10 * s)} 0 {a(14 * s)}", 'pet2', step=.05, dur=.4)
        b.g(f'translate(0 {a(14 * s)})')
        if kind == 'heart':
            b.p(f"M0 0 C{a(-16 * s)} {a(-12 * s)} {a(-30 * s)} {a(10 * s)} 0 {a(34 * s)} "
                f"C{a(30 * s)} {a(10 * s)} {a(16 * s)} {a(-12 * s)} 0 0Z", step=.1, dur=.8)
            b.p(f"M0 {a(34 * s)} L0 {a(46 * s)}", 'pet2', step=.05, dur=.3)
            b.dot(0, 49 * s, 2.4)
        else:
            b.p(f"M0 0 C{a(-15 * s)} 0 {a(-17 * s)} {a(20 * s)} {a(-24 * s)} {a(34 * s)} "
                f"Q0 {a(42 * s)} {a(24 * s)} {a(34 * s)} C{a(17 * s)} {a(20 * s)} {a(15 * s)} 0 0 0Z",
                step=.1, dur=.8)
            b.p(f"M{a(-24 * s)} {a(34 * s)} Q0 {a(26 * s)} {a(24 * s)} {a(34 * s)}", 'pet2', step=.05, dur=.4)
        b.e()
        b.e()
    return dict(top=None, hy=0, tx=0)


def poppy(b, count=4, w=52, l=68, pointed=False, **k):
    petal = lens if pointed else teardrop
    ring(b, count, petal(w, l), 0, 4, step=.12)
    ring(b, count, petal(w * .66, l * .66), 180 / count, 3, 'pet2', step=.08)
    b.p(circ(0, 0, 8), 'pet2')
    for i in range(14):
        ang = i * 360 / 14
        r = math.radians(ang)
        b.dot(16 * math.cos(r), 16 * math.sin(r), 1.8, step=.02)
    return dict(top=l * .9)


def pansy(b, **k):
    for ang, w, l in [(-30, 36, 58), (30, 36, 58), (-78, 34, 52), (78, 34, 52)]:
        b.g(f'rotate({ang})')
        b.p(teardrop(w, l), step=.12)
        b.e()
    b.g('rotate(180)')
    b.p(teardrop(46, 66), step=.15)
    b.e()
    for ang in (150, 180, 210):
        r = math.radians(ang)
        b.p(line(6 * math.sin(r), -6 * math.cos(r), 32 * math.sin(r), -32 * math.cos(r)), 'pet2', step=.04, dur=.4)
    b.p(circ(0, 0, 6), 'pet2')
    return dict(top=62)


def iris(b, **k):
    ring(b, 3, teardrop(30, 62), 120, 4, step=.14)
    ring(b, 3, lens(18, 66), 60, 2, 'pet2', step=.14)
    for i in range(3):
        ang = math.radians(120 + i * 120)
        b.p(line(8 * math.sin(ang), -8 * math.cos(ang), 40 * math.sin(ang), -40 * math.cos(ang)), 'pet2', step=.05, dur=.4)
    return dict(top=58)


def hydrangea(b, florets=19, pr=9, sp=26, seed=1, scatter=False, **k):
    pos = [(0, 0)]
    if florets > 1:
        pos += [(sp * math.cos(i * math.pi / 3), sp * math.sin(i * math.pi / 3)) for i in range(6)]
    if florets > 7:
        pos += [(2 * sp * math.cos(i * math.pi / 6), 2 * sp * math.sin(i * math.pi / 6)) for i in range(12)]
    if scatter:
        rnd = random.Random(seed)
        pos = []
        while len(pos) < florets:
            x, y = rnd.uniform(-70, 70), rnd.uniform(-70, 70)
            if x * x + y * y < 70 * 70:
                pos.append((x, y))
    for i, (x, y) in enumerate(pos[:florets]):
        b.g(f'translate({a(x)} {a(y)}) rotate({i * 17})')
        ring(b, 4, teardrop(pr * .8, pr * 1.7), 0, 1, step=.012)
        b.dot(0, 0, 1.6, step=.01)
        b.e()
    return dict(top=70)


def daffodil(b, **k):
    ring(b, 6, teardrop(26, 62), 0, 6, step=.12)
    b.p(lobed(22, 6, .12), 'pet2', step=.3)
    b.p(circ(0, 0, 14), 'pet2')
    b.dot(0, 0, 3)
    return dict(top=62)


def orchid(b, **k):
    for ang, w, l in [(0, 22, 60), (120, 22, 56), (-120, 22, 56)]:
        b.g(f'rotate({ang})')
        b.p(lens(w, l), 'pet2', step=.1)
        b.e()
    for ang in (-80, 80):
        b.g(f'rotate({ang})')
        b.p(teardrop(50, 62), step=.15)
        b.e()
    b.g('rotate(180)')
    b.p(lens(16, 34), step=.1)
    b.e()
    b.p("M0 -4 C-6 -12 6 -12 0 -4", 'pet2')
    b.p(circ(0, 0, 6), 'pet2')
    return dict(top=62)


def crest(b, **k):
    def arcs(R, n, sweep_to_close, th0=160, th1=20, cy=10):
        pts = [(R * math.cos(math.radians(th0 + (th1 - th0) * i / n)),
                -R * math.sin(math.radians(th0 + (th1 - th0) * i / n)) + cy) for i in range(n + 1)]
        ch = math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
        r = ch / 2 * 1.06
        d = f"M{a(pts[0][0])} {a(pts[0][1])}"
        for x, y in pts[1:]:
            d += f" A{a(r)} {a(r)} 0 0 1 {a(x)} {a(y)}"
        return d + (" L26 52 L-26 52Z" if sweep_to_close else "")
    b.p(arcs(62, 8, True), step=.5, dur=1.4)
    b.p(arcs(46, 6, False), 'pet2', step=.3, dur=1)
    b.p(arcs(30, 4, False), 'pet2', step=.3, dur=1)
    return dict(top=50)


def lily(b, w=20, l=72, **k):
    ring(b, 6, lens(w, l), 0, 4, step=.12)
    ring(b, 6, lens(w * .7, l * .72), 30, 3, 'pet2', step=.08)
    for i in range(6):
        ang = math.radians(i * 60 + 30)
        ln = 28 + (i % 2) * 6
        b.p(line(0, 0, ln * math.sin(ang), -ln * math.cos(ang)), 'pet2', step=.03, dur=.4)
        b.dot(ln * math.sin(ang), -ln * math.cos(ang), 2.4, step=.02)
    return dict(top=l * .8)


def anthurium(b, **k):
    b.p("M0 60 C-72 18 -56 -56 0 -22 C56 -56 72 18 0 60Z", step=.5, dur=1.4)
    b.p("M0 54 L0 -12", 'pet2', step=.1)
    for x in (-24, 24):
        b.p(f"M0 50 C{x} 30 {x * 1.3} 0 {x * 1.2} -20", 'pet2', step=.1)
    b.p("M0 20 C14 0 18 -30 10 -58", 'pet2', step=.4, dur=1)
    for i in range(9):
        t = i / 8
        b.dot(12 * t * math.sin(t * 2.2) + 6 * t, 20 - 76 * t, 2, step=.04)
    return dict(top=56)


SHAPES = dict(rose=rose, tulip=tulip, daisy=daisy, cherry=cherry, lotus=lotus, spike=spike,
              trumpet=trumpet, peony=peony, bell=bell, poppy=poppy, pansy=pansy, iris=iris,
              hydrangea=hydrangea, daffodil=daffodil, orchid=orchid, crest=crest, lily=lily,
              anthurium=anthurium)
