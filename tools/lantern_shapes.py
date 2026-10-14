"""Hand-built line-art shapes for the lantern festival film (all return SVG markup in local coordinates).
Trees: base at (0,0), growing up (negative y).  Sculptures: base at (0,0), ~100 units tall, up = negative y.
Hanging lanterns: attach point at (0,0), hanging down (+y).
Classes (defined by the film): S = glowing outline with a soft fill (uses currentColor), N = outline only, T = tree silhouette.
"""
import math


def f(v):
    return f'{v:.1f}'


# ------------------------------ trees ------------------------------
def pine(h, rnd=None):
    """layered pine: stacked tiers with notched edges, a trunk and a few boughs"""
    w = .3 * h
    pts = [(0, -h)]
    for k in range(3):
        top = -h + k * h * .28
        pts += [(w * (.45 + k * .2) * .55, top + h * .3), (w * (.25 + k * .2) * .55, top + h * .3)]
    pts += [(w, -h * .1)]
    seq = pts + [(-x, y) for x, y in reversed(pts[1:])]
    d = 'M' + ' L'.join(f'{f(x)} {f(y)}' for x, y in seq) + ' Z'
    trunk = f'M{f(-.05*h)} {f(-h*.1)} L{f(-.05*h)} 0 M{f(.05*h)} {f(-h*.1)} L{f(.05*h)} 0'
    boughs = ''.join(f'M0 {f(-h*(.75-k*.2))} Q{f(w*(.35+k*.2))} {f(-h*(.68-k*.2))} {f(w*(.55+k*.2))} {f(-h*(.52-k*.2))}'
                     f'M0 {f(-h*(.75-k*.2))} Q{f(-w*(.35+k*.2))} {f(-h*(.68-k*.2))} {f(-w*(.55+k*.2))} {f(-h*(.52-k*.2))}' for k in range(3))
    return (f'<path class="T" d="{d}"/><path class="N" d="{trunk}"/><path class="N tb" d="{boughs}"/>')


def round_tree(h, rnd):
    """broad-leaf tree: scalloped crown, forked trunk"""
    cy, rx, ry = -h * .66, h * .34, h * .3
    n = 9
    a0 = rnd.uniform(0, 6.28)
    pts = []
    for i in range(n):
        a = a0 + 2 * math.pi * i / n
        k = 1 + rnd.uniform(-.07, .07)
        pts.append((rx * math.cos(a) * k, cy + ry * math.sin(a) * k))
    d = f'M{f(pts[0][0])} {f(pts[0][1])}'
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        chord = math.hypot(x1 - x0, y1 - y0)
        rb = chord * .62
        d += f' A{f(rb)} {f(rb)} 0 0 1 {f(x1)} {f(y1)}'
    d += ' Z'
    trunk = (f'M{f(-.055*h)} 0 C{f(-.045*h)} {f(-.16*h)} {f(-.03*h)} {f(-.26*h)} {f(-.02*h)} {f(-.36*h)} '
             f'M{f(.055*h)} 0 C{f(.045*h)} {f(-.16*h)} {f(.03*h)} {f(-.26*h)} {f(.02*h)} {f(-.36*h)}')
    boughs = (f'M0 {f(-.34*h)} C{f(-.1*h)} {f(-.46*h)} {f(-.16*h)} {f(-.52*h)} {f(-.2*h)} {f(-.6*h)} '
              f'M0 {f(-.34*h)} C{f(.1*h)} {f(-.46*h)} {f(.16*h)} {f(-.52*h)} {f(.2*h)} {f(-.6*h)} '
              f'M0 {f(-.34*h)} L0 {f(-.62*h)}')
    return f'<path class="N tb" d="{trunk}"/><path class="T" d="{d}"/><path class="N tb" d="{boughs}"/>'


# ------------------------------ hanging lanterns ------------------------------
def tassel(x, y, n, ln, spread):
    d = ''
    for i in range(n):
        xx = x + (i - (n - 1) / 2) * spread
        d += f'M{f(xx)} {f(y)} l{f((i-(n-1)/2)*.8)} {f(ln*(.8+.2*math.sin(i*2.1)))} '
    return f'<path class="N" d="{d}"/>'


def lotus_hang(col='#ff4f7a', leaf='#7ddc5a'):
    """hanging lotus-bud lantern, ~62 tall (cord on top)"""
    petals = ('M0 12 C-9 20 -10 34 0 48 C10 34 9 20 0 12 Z'
              'M-2 16 C-14 16 -20 32 -14 48 C-8 44 -3 34 -2 16 Z M2 16 C14 16 20 32 14 48 C8 44 3 34 2 16 Z'
              'M-8 20 C-24 22 -28 40 -18 50 C-14 44 -10 34 -8 20 Z M8 20 C24 22 28 40 18 50 C14 44 10 34 8 20 Z')
    leaves = 'M-14 46 C-24 46 -30 56 -22 62 C-16 58 -12 52 -14 46 Z M14 46 C24 46 30 56 22 62 C16 58 12 52 14 46 Z M0 48 C-3 54 -3 60 0 64 C3 60 3 54 0 48 Z'
    return (f'<path class="N" d="M0 0 L0 12"/><path class="S" style="color:{col}" d="{petals}"/><path class="S" style="color:{leaf}" d="{leaves}"/>')


def hex_lantern(w, h, col, alt):
    top, bot = 22, 22 + h
    body = (f'M{f(-.45*w)} {top} L{f(.45*w)} {top} L{f(.55*w)} {top+6} L{f(.55*w)} {bot-6} L{f(.45*w)} {bot} L{f(-.45*w)} {bot} L{f(-.55*w)} {bot-6} L{f(-.55*w)} {top+6} Z')
    div = f'M{f(-.18*w)} {top} L{f(-.18*w)} {bot} M{f(.18*w)} {top} L{f(.18*w)} {bot}'
    pat = ''.join(f'M{f(cx)} {f(top+h*.5-h*.17)} l{f(w*.07)} {f(h*.17)} l{f(-w*.07)} {f(h*.17)} l{f(-w*.07)} {f(-h*.17)} Z' for cx in (-.36 * w, 0, .36 * w))
    cap = f'M{f(-.22*w)} 14 L{f(.22*w)} 14 L{f(.4*w)} {top} L{f(-.4*w)} {top} Z'
    return (f'<path class="N" d="M0 0 L0 14"/><path class="S" style="color:{alt}" d="{cap}"/><path class="S" style="color:{col}" d="{body}"/>'
            f'<path class="N" style="color:{alt}" d="{div}{pat}"/>' + tassel(0, bot, 5, 18 + h * .12, w * .16))


def round_lantern(r, col, alt):
    cy = 14 + r
    body = f'M{f(-r)} {f(cy)} a{f(r)} {f(r)} 0 1 0 {f(2*r)} 0 a{f(r)} {f(r)} 0 1 0 {f(-2*r)} 0'
    ribs = (f'M0 14 Q{f(r*.95)} {f(cy)} 0 {f(14+2*r)} M0 14 Q{f(-r*.95)} {f(cy)} 0 {f(14+2*r)} M0 14 Q{f(r*.5)} {f(cy)} 0 {f(14+2*r)} M0 14 Q{f(-r*.5)} {f(cy)} 0 {f(14+2*r)}'
            f' M{f(-r)} {f(cy)} Q0 {f(cy+r*.28)} {f(r)} {f(cy)}')
    cap = f'M{f(-r*.28)} 14 L{f(r*.28)} 14 L{f(r*.2)} 20 L{f(-r*.2)} 20 Z'
    return (f'<path class="N" d="M0 0 L0 14"/><path class="S" style="color:{col}" d="{body}"/><path class="N" style="color:{alt}" d="{ribs}"/>'
            f'<path class="S" style="color:{alt}" d="{cap}"/>' + tassel(0, 14 + 2 * r, 4, 16 + r * .5, r * .26))


def star_lantern(r, col, alt):
    cy = 14 + r
    pts = []
    for i in range(16):
        a = -math.pi / 2 + i * math.pi / 8
        rr = r if i % 2 == 0 else r * .52
        pts.append((rr * math.cos(a), cy + rr * math.sin(a)))
    body = 'M' + ' L'.join(f'{f(x)} {f(y)}' for x, y in pts) + ' Z'
    inner = f'M{f(-r*.28)} {f(cy)} a{f(r*.28)} {f(r*.28)} 0 1 0 {f(r*.56)} 0 a{f(r*.28)} {f(r*.28)} 0 1 0 {f(-r*.56)} 0'
    return (f'<path class="N" d="M0 0 L0 {f(14)}"/><path class="S" style="color:{col}" d="{body}"/><path class="S" style="color:{alt}" d="{inner}"/>'
            + tassel(0, cy + r, 4, 14 + r * .4, r * .2))


def drum_lantern(w, h, col, alt):
    top = 18
    body = (f'M{f(-w)} {top+8} a{f(w)} 7 0 0 1 {f(2*w)} 0 L{f(w)} {f(top+h)} a{f(w)} 7 0 0 1 {f(-2*w)} 0 Z')
    rings = (f'M{f(-w)} {f(top+h*.3)} a{f(w)} 7 0 0 0 {f(2*w)} 0 M{f(-w)} {f(top+h*.7)} a{f(w)} 7 0 0 0 {f(2*w)} 0')
    dia = ''.join(f'M{f(x)} {f(top+h*.5)} l{f(w*.12)} {f(-h*.14)} l{f(w*.12)} {f(h*.14)} l{f(-w*.12)} {f(h*.14)} Z' for x in (-.7 * w, -.2 * w, .3 * w))
    return (f'<path class="N" d="M0 0 L0 {top+2}"/><path class="S" style="color:{col}" d="{body}"/><path class="N" style="color:{alt}" d="{rings}{dia}"/>'
            + tassel(0, top + h + 7, 5, 16 + h * .1, w * .3))


def tag_strip(w, h, col):
    marks = ''.join(f'M{f(-w*.3)} {f(10+h*k/6)} L{f(w*.3)} {f(10+h*k/6)} ' for k in range(1, 6))
    return (f'<path class="N" d="M0 0 L0 10"/><path class="S" style="color:{col}" d="M{f(-w/2)} 10 L{f(w/2)} 10 L{f(w/2)} {f(10+h)} L0 {f(10+h-w*.4)} L{f(-w/2)} {f(10+h)} Z"/>'
            f'<path class="N" d="{marks}"/>')


# ------------------------------ standing sculptures (base at 0,0; up is negative) ------------------------------
def _petal(w, h):
    return f'M0 0 C{-w} {-h*.3:.0f} {-w*.9:.0f} {-h*.8:.0f} 0 {-h} C{w*.9:.0f} {-h*.8:.0f} {w} {-h*.3:.0f} 0 0 Z'


def sc_lotus(c, c2):
    out = ''
    for layer, (angles, w, h, colr) in enumerate([((-64, -32, 0, 32, 64), 18, 74, c), ((-48, -16, 16, 48), 16, 64, c2), ((-26, 0, 26), 14, 52, c)]):
        for a in angles:
            out += f'<g transform="translate(0 -10) rotate({a})"><path class="S" style="color:{colr}" d="{_petal(w, h)}"/>' \
                   f'<path class="N" style="color:{colr}" d="M0 {-h*.12:.0f} L0 {-h*.82:.0f}"/></g>'
    out += f'<path class="S" style="color:#7ddc5a" d="M-46 -4 Q0 12 46 -4 Q30 4 0 6 Q-30 4 -46 -4 Z"/>'
    out += f'<path class="S" style="color:#fff2b0" d="M-6 -12 Q0 -28 6 -12 Z"/>'
    return out


def sc_crane(c, c2):
    body = '<path class="S" style="color:%s" d="M-30 -46 C-24 -62 8 -64 22 -52 C26 -46 18 -38 0 -36 C-14 -34 -26 -34 -30 -46 Z"/>' % c
    neck = '<path class="N" style="color:%s" d="M16 -56 C34 -64 30 -86 38 -94 M20 -50 C38 -56 36 -80 44 -90"/>' % c
    head = '<path class="S" style="color:%s" d="M38 -94 a5 5 0 1 0 10 0 a5 5 0 1 0 -10 0"/><path class="N" d="M47 -95 L62 -91 L47 -90"/><path class="S" style="color:#ff5a4a" d="M40 -98 q3 -5 7 -1 q-3 1 -7 1 Z"/>' % c
    wing = ('<path class="S" style="color:%s" d="M-6 -56 C-30 -92 -74 -92 -96 -66 C-76 -68 -56 -60 -42 -50 C-30 -48 -16 -50 -6 -56 Z"/>'
            '<path class="N" style="color:%s" d="M-14 -58 C-38 -82 -66 -82 -84 -68 M-18 -54 C-40 -70 -62 -68 -76 -60 M-24 -50 C-42 -58 -58 -56 -68 -52"/>' % (c2, c))
    tail = '<path class="N" style="color:%s" d="M-28 -44 C-46 -38 -60 -28 -72 -22 M-26 -40 C-44 -30 -54 -20 -62 -14"/>' % c
    legs = '<path class="N" d="M-4 -36 L-6 -4 L-12 0 M6 -36 L4 -4 L-2 0"/>'
    return tail + wing + body + neck + head + legs


def sc_pagoda(c, c2):
    out = '<path class="S" style="color:%s" d="M-30 0 L30 0 L26 -10 L-26 -10 Z"/>' % c2
    y = -10
    for k, w in enumerate((30, 24, 18, 12)):
        h = 22
        out += (f'<path class="S" style="color:{c}" d="M{-w} {y} L{w} {y} L{w} {y-h} L{-w} {y-h} Z"/>'
                f'<path class="N" style="color:{c2}" d="M0 {y} L0 {y-h} M{-w*.5:.0f} {y} L{-w*.5:.0f} {y-h} M{w*.5:.0f} {y} L{w*.5:.0f} {y-h}"/>')
        y -= h
        out += (f'<path class="S" style="color:{c2}" d="M{-w-12} {y} Q{-w-2} {y-3} {-w+4} {y-8} L{w-4} {y-8} Q{w+2} {y-3} {w+12} {y} Z"/>')
        y -= 8
    out += f'<path class="N" style="color:{c2}" d="M0 {y} L0 {y-16} M-4 {y-8} L4 {y-8} M-3 {y-12} L3 {y-12}"/><circle class="N" style="color:{c2}" cx="0" cy="{y-18}" r="2.4"/>'
    return out


def sc_elephant(c, c2):
    body = '<path class="S" style="color:%s" d="M-38 -34 C-44 -64 -10 -76 20 -68 C40 -62 48 -46 46 -32 L46 -6 L34 -6 L32 -22 L-2 -22 L-4 -6 L-16 -6 L-18 -24 L-28 -6 L-40 -6 Z"/>' % c
    trunk = '<path class="S" style="color:%s" d="M42 -54 C60 -52 68 -36 62 -22 C58 -14 48 -16 50 -24 C52 -30 54 -34 46 -40 Z"/>' % c
    ear = '<path class="S" style="color:%s" d="M30 -62 C16 -72 6 -54 16 -42 C26 -44 34 -52 30 -62 Z"/>' % c2
    tusk = '<path class="N" style="color:#fff4d0" d="M52 -40 q12 2 14 14"/>'
    eye = '<circle cx="40" cy="-54" r="1.8" fill="#fff4d0" style="stroke:none"/>'
    blanket = '<path class="S" style="color:%s" d="M-30 -64 Q-6 -78 20 -66 L18 -50 Q-6 -58 -28 -48 Z"/><path class="N" style="color:#fff4d0" d="M-22 -58 l6 -4 l6 4 l6 -4 l6 4 l6 -4 l6 4"/>' % c2
    lotus = '<g transform="translate(-4 -70) scale(.42)">%s</g>' % sc_lotus('#ff8fc4', '#ffc4e0')
    return body + blanket + trunk + ear + tusk + eye + lotus


def sc_fish(c, c2):
    inner = (f'<path class="S" style="color:{c}" d="M-44 -50 C-24 -82 24 -82 44 -50 C24 -18 -24 -18 -44 -50 Z"/>'
             f'<path class="S" style="color:{c2}" d="M44 -50 L70 -72 Q60 -50 70 -28 Z"/>'
             f'<path class="S" style="color:{c2}" d="M-6 -78 Q4 -92 18 -78 Z"/><path class="S" style="color:{c2}" d="M-6 -22 Q4 -8 14 -24 Z"/>')
    scales = ''.join(f'M{x} {y} q8 8 0 16' for x in (-22, -8, 6, 20) for y in (-62, -48, -34) if abs(y + 48) + abs(x) < 52)
    eye = '<circle cx="-30" cy="-54" r="3" fill="#fff4d0" style="stroke:none"/>'
    spout = '<path class="N" style="color:#8fd8ff" d="M-52 -50 q-10 -6 -6 -14 M-52 -50 q-12 0 -12 -8"/>'
    stand = '<path class="S" style="color:#8fd8ff" d="M-40 0 Q-20 -14 0 -8 Q20 -14 40 0 Z"/><path class="N" style="color:#8fd8ff" d="M-14 -8 q4 -8 8 0 M6 -8 q4 -8 8 0"/>'
    return stand + f'<g transform="translate(0 -8) rotate(-14 0 -50)">{inner}<path class="N" style="color:{c2}" d="{scales}"/>{eye}{spout}</g>'


def sc_wheel(c, c2):
    spokes = ''.join(f'M0 -52 L{36*math.cos(math.radians(a)):.1f} {-52+36*math.sin(math.radians(a)):.1f}' for a in range(0, 360, 45))
    knobs = ''.join(f'<circle class="S" style="color:{c2}" cx="{42*math.cos(math.radians(a)):.1f}" cy="{-52+42*math.sin(math.radians(a)):.1f}" r="3.4"/>' for a in range(22, 360, 45))
    return (f'<path class="S" style="color:{c2}" d="M-26 0 L-8 -20 L8 -20 L26 0 Z"/><path class="N" style="color:{c2}" d="M0 -20 L0 -18"/>'
            f'<circle class="S" style="color:{c}" cx="0" cy="-52" r="34"/><circle class="N" style="color:{c2}" cx="0" cy="-52" r="26"/>'
            f'<circle class="S" style="color:{c2}" cx="0" cy="-52" r="8"/><path class="N" style="color:{c2}" d="{spokes}"/>{knobs}')


SCULPT = {'lotus': sc_lotus, 'crane': sc_crane, 'pagoda': sc_pagoda, 'elephant': sc_elephant, 'fish': sc_fish, 'wheel': sc_wheel}
