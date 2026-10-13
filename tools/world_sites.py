"""Extra heritage landscapes drawn as laser elevations (base y=0, up is negative): Cappadocia, Giza."""
import math
import random

from europe_kit import P, f


def cappadocia():
    from europe_kit import catmull
    rnd = random.Random(9)
    el = []
    # broad tuff cone with a small cap rock (right half: x/(w/2), y/h)
    prof = [(1.0, 0), (.9, -.08), (.72, -.28), (.54, -.52), (.42, -.7), (.34, -.8), (.42, -.83), (.42, -.91), (.26, -.97), (0, -1.0)]

    def chimney(cx, h, w, tilt=0):
        poly = [(cx - (w / 2) * px + tilt * (-py), py * h) for px, py in prof] + [(cx + (w / 2) * px + tilt * (-py), py * h) for px, py in reversed(prof[:-1])]
        poly = [(x + rnd.uniform(-1.5, 1.5), y + rnd.uniform(-1.5, 1.5)) for x, y in poly]
        body = P(catmull(poly, 6))
        flute = f'M{f(cx - w * .3)} {f(-h * .4)} Q{f(cx)} {f(-h * .34)} {f(cx + w * .3)} {f(-h * .4)} M{f(cx - w * .2)} {f(-h * .6)} Q{f(cx)} {f(-h * .55)} {f(cx + w * .2)} {f(-h * .6)}'
        door = f'M{f(cx - 6)} {f(-h * .16)} V{f(-h * .24)} a6 6 0 0 1 12 0 V{f(-h * .16)}'
        cap = f'M{f(cx - w * .26)} {f(-h * .79)} Q{f(cx)} {f(-h * .73)} {f(cx + w * .26)} {f(-h * .79)}'
        return body, flute + ' ' + door + ' ' + cap
    el.append('M-780 0 C-640 -150 -420 -190 -240 -90 L-120 0')                        # soft mounds behind
    el.append('M160 0 C300 -170 560 -210 780 0')
    spec = [(-500, 220, 190, 3), (-340, 290, 220, -2), (-170, 350, 250, 2), (-10, 260, 200, -3), (150, 330, 240, 2), (310, 400, 270, -2), (470, 270, 210, 3), (610, 210, 180, -2)]
    for cx, h, w, t in sorted(spec, key=lambda q: q[1]):
        b, st = chimney(cx, h, w, t)
        el += [b, st]
    el.append('M-780 0 Q-560 -22 -340 -8 T60 -10 T420 -6 T780 0')
    return el


def giza():
    el = []

    def pyramid(cx, base_w, h, x_shift=0):
        d = f'M{f(cx - base_w / 2)} 0 L{f(cx)} {f(-h)} L{f(cx + base_w / 2)} 0'
        courses = ''
        for k in range(1, int(h / 26)):
            y = k * 26
            half = base_w / 2 * (1 - y / h)
            courses += f'M{f(cx - half)} {f(-y)} H{f(cx + half)} '
        edge = f'M{f(cx)} {f(-h)} L{f(cx + base_w * .1)} 0'
        return [d, courses.strip(), edge]
    el += pyramid(190, 470, 330)
    el += pyramid(520, 250, 160)
    el += pyramid(-260, 560, 400)
    el.append('M-800 0 Q-600 -22 -400 -8 T0 -10 T400 -6 T800 0')
    # sphinx (foreground, left)
    el.append('M-760 0 V-46 C-740 -52 -700 -52 -660 -46 L-600 -48 V0 M-660 -46 C-662 -80 -650 -102 -626 -104 C-604 -102 -594 -84 -598 -60 M-632 -104 C-640 -116 -622 -126 -610 -112')
    return el
