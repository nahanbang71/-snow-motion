"""Shared helpers for the Korean traditional pattern medallions (neon / laser line art).

A pattern is a function returning an SVG fragment drawn around (0,0) inside radius ~100.
`grow_svg` wraps it in the standard animation: starts as a dot, grows and flies out of the screen.
"""
import math

# palette: (main, light)
RED = ('#ff3860', '#ffb3c1')
PINK = ('#ff7eb6', '#ffd1e6')
MAGENTA = ('#ff4fd8', '#ffc1f2')
ORANGE = ('#ff9a3c', '#ffd4a8')
GOLD = ('#ffd76a', '#fff1c4')
YELLOW = ('#ffe14a', '#fff4b0')
GREEN = ('#8dffb4', '#e0ffe9')
TEAL = ('#3df2c0', '#d4fff0')
BLUE = ('#5aa9ff', '#c2e0ff')
VIOLET = ('#b48cff', '#e6d6ff')
WHITE = ('#f2f6ff', '#ffffff')

DUR = 8.0
S0, S1 = 0.004, 13.0


def f(v):
    return f"{v:.1f}"


def pt(r, deg):
    """polar point, 0 deg = up, clockwise"""
    a = math.radians(deg - 90)
    return r * math.cos(a), r * math.sin(a)


def P(d, c, w=4.4):
    return f'<path class="l" stroke="{c}" stroke-width="{w}" d="{d}"/>'


def PL(d, col, w=4.4, echo=True):
    """main stroke + thin light echo (neon tube look)"""
    s = P(d, col[0], w)
    if echo:
        s += P(d, col[1], 1.6)
    return s


def DOT(x, y, c, w=7):
    return P(f"M{f(x)} {f(y)} l0 0", c, w)


def circle(r, cx=0, cy=0):
    return f"M{f(cx - r)} {f(cy)} a{f(r)} {f(r)} 0 1 0 {f(2 * r)} 0 a{f(r)} {f(r)} 0 1 0 {f(-2 * r)} 0"


def poly(pts, close=False):
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + ("Z" if close else "")


def smooth(pts, close=False):
    """quadratic-midpoint smoothing through points"""
    n = len(pts)
    if n < 3:
        return poly(pts, close)
    if close:
        mid = [((pts[i][0] + pts[(i + 1) % n][0]) / 2, (pts[i][1] + pts[(i + 1) % n][1]) / 2) for i in range(n)]
        d = f"M{f(mid[-1][0])} {f(mid[-1][1])}"
        for i in range(n):
            d += f"Q{f(pts[i][0])} {f(pts[i][1])} {f(mid[i][0])} {f(mid[i][1])}"
        return d + "Z"
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    for i in range(1, n - 1):
        mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
        d += f"Q{f(pts[i][0])} {f(pts[i][1])} {f(mx)} {f(my)}"
    return d + f"L{f(pts[-1][0])} {f(pts[-1][1])}"


def G(tf, inner):
    return f'<g transform="{tf}">{inner}</g>'


def around(n, fn, start=0):
    """repeat fn(k) rotated k*360/n degrees around the centre"""
    return ''.join(G(f"rotate({f(start + k * 360 / n)})", fn(k)) for k in range(n))


def mirror(inner):
    return inner + G("scale(-1 1)", inner)


def spin(inner, cls='cw'):
    return f'<g class="{cls}">{inner}</g>'


def clip(inner, r=100):
    return f'<g clip-path="url(#clipc)">{inner}</g>'


def frame(col=GOLD, beads=32, r1=126, r2=106):
    s = P(circle(r1), col[0], 3.4) + P(circle(r2), col[0], 3.4)
    for i in range(beads):
        x, y = pt((r1 + r2) / 2, i * 360 / beads)
        s += DOT(x, y, col[1])
    return s


def lens(l, w, r0=0):
    """pointed leaf pointing up from (0,-r0)"""
    return (f"M0 {f(-r0)} C{f(-w)} {f(-r0 - l * .3)} {f(-w)} {f(-r0 - l * .7)} 0 {f(-r0 - l)} "
            f"C{f(w)} {f(-r0 - l * .7)} {f(w)} {f(-r0 - l * .3)} 0 {f(-r0)}Z")


def drop(l, w, r0=0):
    """rounded petal (teardrop) pointing up"""
    return (f"M0 {f(-r0)} C{f(-w)} {f(-r0 - l * .1)} {f(-w * 1.05)} {f(-r0 - l * .65)} {f(-w * .3)} {f(-r0 - l * .95)} "
            f"C{f(-w * .1)} {f(-r0 - l)} {f(w * .1)} {f(-r0 - l)} {f(w * .3)} {f(-r0 - l * .95)} "
            f"C{f(w * 1.05)} {f(-r0 - l * .65)} {f(w)} {f(-r0 - l * .1)} 0 {f(-r0)}Z")


def spiral(cx, cy, r0, r1, turns, a0=0, steps=60, ccw=False):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        a = math.radians(a0) + (-1 if ccw else 1) * t * turns * 2 * math.pi
        r = r0 + (r1 - r0) * t
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly(pts)


def bez(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def ribbon(center, wfn):
    """closed outline around a centre-line (list of points) with half-width wfn(t)"""
    n = len(center)
    left, right = [], []
    for i, (x, y) in enumerate(center):
        x0, y0 = center[max(i - 1, 0)]
        x1, y1 = center[min(i + 1, n - 1)]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = wfn(i / (n - 1))
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return left, right


# ---------------------------------------------------------------- rendering
STYLE = '''.l{{fill:none;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}}
.grow{{transform-origin:0 0;animation:grow {dur}s linear forwards}}
.cw{{transform-origin:0 0;animation:cw {dur}s linear forwards}}
.ccw{{transform-origin:0 0;animation:ccw {dur}s linear forwards}}
.seed{{opacity:1;animation:seed 1.6s ease-in forwards}}
@keyframes grow{{{stops}}}
@keyframes cw{{to{{transform:rotate(45deg)}}}}
@keyframes ccw{{to{{transform:rotate(-45deg)}}}}
@keyframes seed{{to{{opacity:0}}}}'''

DEFS_COMMON = ('<radialGradient id="bg" cx="50%" cy="50%" r="75%"><stop offset="0" stop-color="#14183a"/>'
               '<stop offset="1" stop-color="#080a1a"/></radialGradient>'
               '<clipPath id="clipc"><circle r="102"/></clipPath>')


def grow_svg(inner, title, seed='#ffd1e6', with_frame=True):
    stops = ''.join(f"{i * 5}%{{transform:scale({S0 * (S1 / S0) ** ((i / 20) ** .72):.4f})}}" for i in range(21))
    style = STYLE.format(dur=DUR, stops=stops)
    body = (frame() if with_frame else '') + inner
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1920" height="1080">\n'
            f'<title>{title}</title>\n<defs>{DEFS_COMMON}\n'
            '<filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="5" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>\n'
            f'<style>{style}</style></defs>\n'
            '<rect width="1600" height="900" fill="url(#bg)"/>\n'
            '<g filter="url(#glow)"><g transform="translate(800 450)">\n'
            f'<path class="l seed" stroke="{seed}" stroke-width="12" d="M0 0 l0 0"/>\n'
            f'<g class="grow">{body}</g></g></g></svg>')
