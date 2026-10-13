"""Per-airport background wings (canvas coords 1920x1080). Faint thin lines left and right of the landmark
(landmark occupies x 480..1440), horizon y=726. Keeps y>930 free for lyrics.
Each airport -> (sky paths [accent colour], ground paths [main colour])."""
import math
import random
from airport_data import f, circle, wave, palm

GY = 726
L0, L1, R0, R1 = 60, 450, 1470, 1860


def rnd(code, side):
    return random.Random(sum(map(ord, code + side)))


def stars(x0, x1, y0, y1, n, r):
    pts = []
    for _ in range(400):
        x, y = r.randint(x0, x1), r.randint(y0, y1)
        if all(math.hypot(x - a, y - b) > 60 for a, b in pts):
            pts.append((x, y))
        if len(pts) == n:
            break
    return [f'M{x - 6} {y} H{x + 6} M{x} {y - 6} V{y + 6}' for x, y in pts]


def crescent(cx, cy, r):
    return f'M{cx} {cy - r} A{r} {r} 0 1 0 {cx} {cy + r} A{int(r * .72)} {r} 0 1 1 {cx} {cy - r}'


def sun(cx, cy, r):
    return circle(cx, cy, r)


def cloud(x, y, spec):
    d = f'M{x} {y}'
    for q in spec:
        d += f' a{q} {q} 0 0 1 {2 * q} 0'
    return d


def hills(x0, x1, base, amp, r, step=(60, 100), sharp=True):
    pts = [(x0, base)]
    x = x0 + r.randint(*step)
    while x < x1 - 40:
        pts.append((x, base - r.randint(amp // 3, amp)))
        x += r.randint(*step)
    pts.append((x1, base))
    if sharp:
        return 'M' + ' L'.join(f'{a} {b}' for a, b in pts)
    d = f'M{pts[0][0]} {pts[0][1]}'
    for i in range(1, len(pts)):
        mx = (pts[i - 1][0] + pts[i][0]) / 2
        d += f' Q{f(pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * .5)} {pts[i - 1][1] if i % 2 else pts[i][1]} {f(pts[i][0])} {pts[i][1]}'
    return d


def skyline(x0, x1, base, r, hmax, wmin=26, wmax=44):
    d = f'M{x0} {base}'
    x = x0
    while x < x1:
        w = r.randint(wmin, wmax)
        h = r.randint(hmax // 4, hmax)
        w = min(w, x1 - x)
        d += f' V{base - h} H{x + w} V{base}'
        x += w
    return d


def dunes(x0, x1, base, r):
    d = f'M{x0} {base}'
    x = x0
    while x < x1 - 60:
        w = r.randint(110, 170)
        h = r.randint(30, 70)
        d += f' C{x + w * .3} {base - h} {x + w * .7} {base - h} {x + w} {base}'
        x += w
    return d


def waves(x0, x1, y, rows, amp=4, period=50):
    return ' '.join(wave(x0 + (i % 2) * 18, x1, y + i * 14, amp, period) for i in range(rows))


def sail(x, y, s):
    return (f'M{x - s} {y} H{x + s} L{x + s * .7} {y + s * .3} H{x - s * .7} Z M{x} {y} V{y - s * 1.8} '
            f'M{x} {y - s * 1.8} L{x + s * .9} {y - s * .2} H{x} M{x - 2} {y - s * 1.5} L{x - s * .7} {y - s * .2} H{x - 2}')


def dome(x, base, s, minaret=True):
    d = f'M{x - s} {base} V{base - s * .6} A{s} {s} 0 0 1 {x + s} {base - s * .6} V{base} M{x} {base - s * 1.6} V{base - s * 1.9}'
    if minaret:
        mx = x + s * 1.7
        d += f' M{mx - 6} {base} V{base - s * 2.2} L{mx} {base - s * 2.7} L{mx + 6} {base - s * 2.2} V{base}'
    return d


def gables(x0, x1, base, r):
    d = f'M{x0} {base}'
    x = x0
    while x < x1 - 30:
        w = r.randint(36, 52)
        h = r.randint(70, 120)
        d += f' V{base - h} L{x + w * .2} {base - h - 10} L{x + w * .35} {base - h - 6} L{x + w * .5} {base - h - 22} L{x + w * .65} {base - h - 6} L{x + w * .8} {base - h - 10} L{x + w} {base - h} V{base}'
        x += w
    return d


def rooftops(x0, x1, base, r):
    d = f'M{x0} {base}'
    x = x0
    while x < x1 - 30:
        w = r.randint(40, 60)
        h = r.randint(60, 100)
        d += f' V{base - h} L{x + w * .2} {base - h - 22} H{x + w * .8} L{x + w} {base - h} V{base}'
        d += f' M{x + w * .3} {base - h - 22} V{base - h - 34} H{x + w * .38} V{base - h - 22} M{x + w} {base}'
        x += w
    return d


def pines(xs, base, h):
    out = []
    for x in xs:
        t = h / 100
        out.append(f'M{x} {base} V{base - 10 * t} M{x - 26 * t} {base - 10 * t} L{x} {base - 60 * t} L{x + 26 * t} {base - 10 * t} '
                   f'M{x - 20 * t} {base - 45 * t} L{x} {base - 100 * t} L{x + 20 * t} {base - 45 * t}')
    return ' '.join(out)


def torii(x, base, s=60):
    return (f'M{x - s} {base} V{base - s * 1.5} M{x + s} {base} V{base - s * 1.5} M{x - s * 1.25} {base - s * 1.5} Q{x} {base - s * 1.8} {x + s * 1.25} {base - s * 1.5} '
            f'M{x - s * .9} {base - s} H{x + s * .9}')


def wall(x0, x1, base, h=50):
    d = f'M{x0} {base} V{base - h}'
    x = x0
    while x < x1 - 36:
        d += f' H{x + 18} V{base - h - 16} H{x + 36} V{base - h}'
        x += 36
    return d + f' H{x1} V{base}'


def spire(x, base, h):
    return (f'M{x - 26} {base} H{x + 26} M{x - 20} {base} V{base - h * .35} H{x + 20} V{base} M{x - 15} {base - h * .35} V{base - h * .6} H{x + 15} V{base - h * .35} '
            f'M{x - 9} {base - h * .6} L{x} {base - h} L{x + 9} {base - h * .6} Z')


def umbrella_pine(x, base, h):
    return f'M{x} {base} V{base - h * .7} M{x - h * .5} {base - h * .7} Q{x} {base - h * 1.2} {x + h * .5} {base - h * .7} Q{x} {base - h * .55} {x - h * .5} {base - h * .7}'


def gulls(x, y):
    return f'M{x} {y} q12 -14 24 0 q12 -14 24 0 M{x + 80} {y + 26} q9 -10 18 0 q9 -10 18 0'


def clock_tower(x, base):
    return (f'M{x - 20} {base} V{base - 150} M{x + 20} {base} V{base - 150} M{x - 26} {base - 150} H{x + 26} V{base - 200} H{x - 26} Z '
            f'M{x - 26} {base - 200} L{x} {base - 250} L{x + 26} {base - 200} M{x} {base - 250} V{base - 275}')


def arch_bridge(x0, x1, base):
    return f'M{x0} {base} Q{(x0 + x1) / 2} {base - 150} {x1} {base} M{x0} {base - 20} H{x1}'


def volcano(x, base, w, h):
    return f'M{x - w} {base} Q{x - w * .3} {base - h * .9} {x - w * .12} {base - h} H{x + w * .12} Q{x + w * .3} {base - h * .9} {x + w} {base}'


def condor(x, y):
    return f'M{x - 80} {y + 10} Q{x - 40} {y - 30} {x} {y} Q{x + 40} {y - 30} {x + 80} {y + 10}'


def build(code):
    """returns (sky, ground) path lists"""
    lr, rr = rnd(code, 'L'), rnd(code, 'R')
    sky, g = [], []
    S = lambda x0, x1, y0, y1, n, r: stars(x0, x1, y0, y1, n, r)
    if code == 'ICN':
        g += [hills(L0, L1, GY, 120, lr, sharp=False), hills(R0, R1, GY, 90, rr, sharp=False)]
        sky += [crescent(1720, 250, 40)]
    elif code == 'PKX':
        g += [wall(L0, L1, GY), wall(R0, R1, GY)]
        sky += [sun(1700, 260, 45), cloud(130, 220, (20, 28, 20))]
    elif code == 'HKG':
        g += [skyline(L0, L1, GY, lr, 230), skyline(R0, R1, GY, rr, 190), waves(R0, R1, GY + 22, 2)]
        sky += S(L0, L1, 160, 260, 3, lr)
    elif code == 'BKK':
        g += [spire(150, GY, 200), spire(330, GY, 150)] + [' '.join(palm(1640, GY, 170, 30)), ' '.join(palm(1760, GY, 130, -25))]
        sky += [cloud(1560, 240, (22, 30, 22))]
    elif code == 'KIX':
        g += [waves(L0, L1, GY - 40, 3), sail(250, GY - 46, 26), hills(R0, R1, GY, 100, rr, sharp=False)]
        sky += [crescent(1700, 240, 38)]
    elif code == 'SIN':
        g += [skyline(L0, L1, GY, lr, 170), skyline(R0, R1, GY, rr, 210)]
        sky += S(R0, R1, 150, 300, 4, rr)
    elif code == 'HND':
        g += [torii(240, GY, 55), waves(R0, R1, GY - 30, 3)]
        sky += [sun(1700, 260, 48), cloud(120, 240, (22, 30, 22))]
    elif code == 'DXB':
        g += [dunes(L0, L1, GY, lr), skyline(R0, R1, GY, rr, 200, 18, 28)]
        sky += [sun(1700, 270, 55)]
    elif code == 'DOH':
        g += [sail(250, GY - 40, 34), waves(L0, L1, GY - 34, 3), skyline(R0, R1, GY, rr, 190, 20, 30)]
        sky += [crescent(1700, 250, 40)]
    elif code == 'IST':
        g += [dome(190, GY, 55), dome(330, GY, 34, False), dome(1600, GY, 60), waves(1470, 1860, GY - 30, 2)]
        sky += [crescent(1760, 230, 36), crescent(300, 220, 30)]
    elif code == 'CAI':
        g += [dunes(L0, L1, GY, lr), dunes(R0, R1, GY, rr), ' '.join(palm(380, GY, 120, 15))]
        sky += S(R0, R1, 150, 320, 5, rr)
    elif code == 'CPT':
        g += [waves(L0, L1, GY - 40, 3), waves(R0, R1, GY - 40, 3)]
        sky += [gulls(150, 240), sun(1700, 260, 45)]
    elif code == 'LHR':
        g += [clock_tower(240, GY)]
        sky += [cloud(1560, 230, (24, 34, 24)), cloud(1640, 300, (20, 28)), cloud(130, 240, (20, 28))]
    elif code == 'CDG':
        g += [rooftops(L0, L1, GY, lr), rooftops(R0, R1, GY, rr)]
        sky += S(R0, R1, 150, 300, 4, rr)
    elif code == 'AMS':
        g += [gables(L0, L1, GY, lr), gables(R0, R1, GY, rr), waves(L0, L1, GY + 20, 2)]
        sky += [cloud(1640, 240, (22, 30, 22))]
    elif code == 'MAD':
        g += [hills(L0, L1, GY, 70, lr, sharp=False), hills(R0, R1, GY, 70, rr, sharp=False)]
        sky += [sun(1700, 270, 60), cloud(130, 240, (22, 30, 22))]
    elif code == 'FCO':
        g += [umbrella_pine(170, GY, 150), umbrella_pine(330, GY, 110), dome(1650, GY, 70, False), umbrella_pine(1790, GY, 130)]
        sky += S(L0, L1, 160, 280, 3, lr)
    elif code == 'ZRH':
        g += [hills(L0, L1, GY, 110, lr), waves(R0, R1, GY - 40, 3), spire(1760, GY, 180)]
        sky += S(R0, R1, 150, 280, 3, rr)
    elif code == 'JFK':
        g += [skyline(L0, L1, GY, lr, 260), skyline(R0, R1, GY, rr, 230)]
        sky += S(L0, L1, 150, 270, 3, lr) + S(R0, R1, 150, 270, 3, rr)
    elif code == 'LAX':
        g += [' '.join(palm(130, GY, 210, 20)), ' '.join(palm(250, GY, 170, -15)), ' '.join(palm(370, GY, 230, 18)), hills(R0, R1, GY, 90, rr, sharp=False)]
        sky += [sun(1700, 270, 55)]
    elif code == 'SFO':
        g += [hills(L0, L1, GY, 120, lr, sharp=False), hills(R0, R1, GY, 90, rr, sharp=False), waves(L0, L1, GY - 60, 2, 3, 70), waves(R0, R1, GY - 80, 2, 3, 70)]
        sky += []
    elif code == 'DEN':
        g += [hills(L0, L1, GY, 230, lr), hills(R0, R1, GY, 200, rr), pines([150, 220, 300], GY, 80), pines([1700, 1780], GY, 90)]
        sky += S(R0, R1, 150, 300, 3, rr)
    elif code == 'YVR':
        g += [hills(L0, L1, GY, 180, lr), pines([160, 230], GY, 80), waves(R0, R1, GY - 30, 3), sail(1700, GY - 36, 30)]
        sky += [cloud(1560, 240, (22, 30, 22))]
    elif code == 'MIA':
        g += [skyline(L0, L1, GY, lr, 110, 30, 50), waves(L0, L1, GY + 20, 2), sail(1700, GY - 36, 32), waves(R0, R1, GY - 30, 3)]
        sky += [cloud(1560, 230, (24, 34, 24)), cloud(120, 250, (20, 28))]
    elif code == 'GIG':
        g += [hills(L0, L1, GY, 110, lr, sharp=False), waves(L0, L1, GY - 34, 2), ' '.join(palm(1640, GY, 170, 25)), waves(R0, R1, GY - 30, 2)]
        sky += [cloud(1580, 240, (22, 30, 22))]
    elif code == 'SCL':
        g += [hills(L0, L1, GY, 250, lr), hills(R0, R1, GY, 270, rr)]
        sky += [condor(1700, 250)] + S(L0, L1, 150, 280, 3, lr)
    elif code == 'EZE':
        g += [skyline(L0, L1, GY, lr, 80, 30, 50), 'M' + f'{R0} {GY - 14} H{R1} M{R0 + 60} {GY - 30} H{R1 - 40}']
        sky += [sun(1700, 270, 55), cloud(120, 240, (22, 30, 22))]
    elif code == 'SYD':
        g += [waves(L0, L1, GY - 34, 3), sail(180, GY - 40, 28), sail(320, GY - 40, 22), arch_bridge(R0, R1, GY - 10), waves(R0, R1, GY + 14, 2)]
        sky += [cloud(130, 240, (22, 30, 22))]
    elif code == 'AKL':
        g += [sail(150, GY - 36, 30), sail(260, GY - 36, 24), sail(360, GY - 36, 28), waves(L0, L1, GY - 20, 2), volcano(1650, GY, 190, 120), waves(R0, R1, GY - 20, 2)]
        sky += [cloud(1560, 240, (22, 30, 22))]
    elif code == 'HNL':
        g += [waves(L0, L1, GY - 30, 3), sail(250, GY - 36, 28), ' '.join(palm(1650, GY, 190, 28)), ' '.join(palm(1770, GY, 140, -22))]
        sky += [sun(300, 270, 50)]
    return sky, g
