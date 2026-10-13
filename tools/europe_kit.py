"""Shared geometry helpers for the European landmark scenes (aerial layout + laser elevation)."""
import math
import random

f = lambda v: ('%.1f' % v).rstrip('0').rstrip('.')


def P(pts, close=False):
    return 'M' + ' L'.join(f'{f(x)} {f(y)}' for x, y in pts) + (' Z' if close else '')


def rot(pts, deg, ox=0, oy=0):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [(ox + (x - ox) * c - (y - oy) * s, oy + (x - ox) * s + (y - oy) * c) for x, y in pts]


def arc_pts(cx, cy, rx, ry, a0, a1, n=24):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def arch_pts(xc, ybase, w, h, n=12):
    """round-headed arch as a polyline (screen y up is negative)"""
    r = w / 2
    pts = [(xc - r, ybase), (xc - r, ybase - h + r)] + [(xc + r * math.cos(math.radians(180 + 180 * i / n)), ybase - h + r + r * math.sin(math.radians(180 + 180 * i / n))) for i in range(n + 1)] + [(xc + r, ybase)]
    return pts


def poly_arches(xs, ybase, w, h):
    return ' '.join(P(arch_pts(x, ybase, w, h)) for x in xs)


def catmull(pts, n=10):
    out = []
    p = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(p) - 2):
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p[i][j]) + (-p[i - 1][j] + p[i + 1][j]) * t + (2 * p[i - 1][j] - 5 * p[i][j] + 4 * p[i + 1][j] - p[i + 2][j]) * t2 + (-p[i - 1][j] + 3 * p[i][j] - 3 * p[i + 1][j] + p[i + 2][j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def offset_line(pts, d):
    out = []
    for i in range(len(pts)):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        nx, ny = -(b[1] - a[1]), b[0] - a[0]
        m = math.hypot(nx, ny) or 1
        out.append((pts[i][0] + nx / m * d, pts[i][1] + ny / m * d))
    return out


class Aerial:
    """top-down layout: streets (blue), water (cyan), green areas, secondary buildings (amber), contour lines, footprint (gold)"""

    def __init__(self, seed):
        self.rnd = random.Random(seed)
        self.streets, self.water, self.green, self.sec, self.foot = [], [], [], [], ''

    def grid(self, n=70, angles=(38, 128), box=(-100, -60, 2020, 1140), skip=None):
        for _ in range(n):
            cx, cy = self.rnd.uniform(box[0], box[2]), self.rnd.uniform(box[1], box[3])
            if skip and skip(cx, cy):
                continue
            a = math.radians(self.rnd.choice(angles))
            L = self.rnd.uniform(70, 230)
            self.streets.append(f'M{f(cx - L * math.cos(a) / 2)} {f(cy - L * math.sin(a) / 2)} l{f(L * math.cos(a))} {f(L * math.sin(a))}')

    def radial(self, cx, cy, n=12, r0=46, L=900, rot0=15):
        self.green.append(f'M{f(cx - r0)} {f(cy)} a{r0} {r0} 0 1 0 {2 * r0} 0 a{r0} {r0} 0 1 0 {-2 * r0} 0')
        for k in range(n):
            a = math.radians(k * 360 / n + rot0)
            self.streets.append(f'M{f(cx + r0 * math.cos(a))} {f(cy + r0 * math.sin(a))} l{f(L * math.cos(a))} {f(L * math.sin(a))}')

    def river(self, pts, w=28):
        c = catmull(pts, 12)
        self.water += [P(offset_line(c, -w / 2)), P(offset_line(c, w / 2))]

    def line(self, pts, kind='streets', smooth=True):
        self.__dict__[kind].append(P(catmull(pts, 10) if smooth else pts))

    def rect(self, cx, cy, w, h, ang=0, kind='green'):
        pts = rot([(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)], ang, cx, cy)
        self.__dict__[kind].append(P(pts, True))

    def ellipse(self, cx, cy, rx, ry, ang=0, kind='green'):
        self.__dict__[kind].append(P(rot(arc_pts(cx, cy, rx, ry, 0, 360, 40), ang, cx, cy), True))

    def blob(self, cx, cy, rx, ry, wob=.18, seed=1, kind='green'):
        r = random.Random(seed)
        pts = [(cx + rx * (1 + r.uniform(-wob, wob)) * math.cos(math.radians(a)), cy + ry * (1 + r.uniform(-wob, wob)) * math.sin(math.radians(a))) for a in range(0, 360, 30)]
        c = catmull(pts + pts[:3], 8)
        self.__dict__[kind].append(P(c[8:-8] if len(c) > 40 else c, True))

    def foot_shape(self, shapes):
        """shapes: list of closed point lists (monument footprint, gold)"""
        self.foot = ' '.join(P(s, True) for s in shapes)

    def result(self):
        return dict(streets=self.streets, water=self.water, green=self.green, sec=self.sec), self.foot


def box(cx, cy, w, h, ang=0):
    return rot([(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)], ang, cx, cy)


def cross_shape(cx, cy, L, W, arm, ang=0):
    """latin cross footprint: nave length L, width W, transept span arm"""
    h, w = L / 2, W / 2
    pts = [(-w, -h), (w, -h), (w, -arm / 2 + 0), (arm, -arm / 2 + 0)]
    pts = [(-w, -h), (w, -h), (w, -W), (arm, -W), (arm, W), (w, W), (w, h), (-w, h), (-w, W), (-arm, W), (-arm, -W), (-w, -W)]
    return rot([(cx + x, cy + y) for x, y in pts], ang, cx, cy)
