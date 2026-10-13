"""Landmark elevations (laser line art, base y=0, up is negative) and aerial layouts for the European balloon film."""
import math
import random

from europe_kit import Aerial, P, arc_pts, arch_pts, box, catmull, cross_shape, f, offset_line, poly_arches, rot

SITES = []      # dict(id, name, country, aerial(), elev(), scale)


def site(id, name, country, scale=1.0):
    def deco(fn):
        SITES.append(dict(id=id, name=name, country=country, scale=scale, build=fn))
        return fn
    return deco


# ------------------------------------------------------------------ Athens
@site('athens', 'ACROPOLIS', 'ATHENS · GREECE', 1.15)
def athens():
    A = Aerial(11)
    A.grid(60, (22, 112), skip=lambda x, y: ((x - 960) / 420) ** 2 + ((y - 540) / 290) ** 2 < 1)
    for k, (rx, ry) in enumerate(((430, 300), (350, 240), (270, 185), (190, 130))):
        A.blob(960, 540, rx, ry, .1, 30 + k, 'green')
    A.rect(790, 430, 200, 120, -25, 'green')                 # Ancient Agora
    A.line([(560, 760), (720, 700), (880, 690), (1040, 700), (1200, 760)], 'sec')   # Odeon / theatre terrace
    A.rect(900, 520, 54, 34, 8, 'sec')                         # Erechtheion
    A.rect(820, 560, 50, 40, -6, 'sec')                        # Propylaea
    A.foot_shape([box(962, 540, 150, 68, 8), box(962, 540, 128, 46, 8)])
    el = []
    el.append('M-420 0 H420 V-16 H404 V-32 H388 V-48 H-388 V-32 H-404 V-16 H-420 Z')
    for i in range(8):
        x = -343 + i * 98
        top = -300 if i != 6 else -190
        el.append(f'M{x - 22} -48 V{top} M{x + 22} -48 V{top} M{x - 8} -52 V{top + 4} M{x + 8} -52 V{top + 4}' + (f' M{x - 31} -300 H{x + 31} V-320 H{x - 31} Z' if i != 6 else f' M{x - 22} {top} L{x - 6} {top - 14} L{x + 10} {top - 4} L{x + 22} {top}'))
    el.append('M-410 -320 H410 V-366 H-410 Z M-410 -340 H410 ' + ' '.join(f'M{x} -340 V-366 M{x + 8} -340 V-366 M{x + 16} -340 V-366' for x in range(-390, 400, 52)))
    el.append('M-420 -366 L0 -480 L420 -366 Z M-380 -372 L0 -468 L380 -372')
    el.append('M-460 0 q20 -10 40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0')
    return A, el


# -------------------------------------------------------------------- Rome
@site('rome', 'COLOSSEUM', 'ROME · ITALY', 1.0)
def rome():
    A = Aerial(12)
    A.grid(70, (35, 125))
    A.river([(-100, 340), (200, 450), (420, 380), (520, 520), (640, 760), (780, 1000), (900, 1200)], 34)
    A.ellipse(640, 640, 170, 60, -30, 'green')               # Circus Maximus
    A.rect(790, 520, 250, 80, -22, 'green')                  # Roman Forum
    A.line([(640, 300), (760, 380), (860, 460), (930, 520)], 'sec')   # Via dei Fori Imperiali
    A.rect(900, 640, 36, 24, 15, 'sec')                      # Arch of Constantine
    out = rot([(960 + 96 * math.cos(math.radians(a)), 540 + 74 * math.sin(math.radians(a))) for a in range(0, 360, 10)], 20, 960, 540)
    inn = rot([(960 + 54 * math.cos(math.radians(a)), 540 + 36 * math.sin(math.radians(a))) for a in range(0, 360, 10)], 20, 960, 540)
    A.foot_shape([out, inn])
    el = []
    el.append('M-400 0 V-420 H130 L180 -382 L250 -360 L300 -300 L360 -252 L400 -240 V0')
    el.append('M-440 0 H440')
    el.append('M-400 -120 H400 M-400 -240 H300')
    xs = [-340 + 68 * i for i in range(11)]
    el.append(poly_arches(xs, -4, 44, 96))
    el.append(poly_arches(xs[:10], -124, 44, 96))
    el.append(poly_arches(xs[:8], -244, 44, 96))
    el.append(' '.join(f'M{x - 8} -380 h16 v30 h-16 Z' for x in xs[:7]))
    el.append('M-400 -360 H110 M-400 -420 H130')
    return A, el


# -------------------------------------------------------------------- Pisa
@site('pisa', 'LEANING TOWER', 'PISA · ITALY', 1.25)
def pisa():
    A = Aerial(13)
    A.grid(60, (15, 105))
    A.river([(-100, 880), (300, 940), (700, 900), (1100, 960), (1500, 900), (2020, 960)], 40)
    A.rect(960, 520, 760, 330, 0, 'green')                    # Piazza dei Miracoli lawn
    A.sec += [P(cross_shape(770, 500, 230, 70, 90, 0), True)]   # cathedral
    A.sec += [P(arc_pts(640, 560, 46, 46, 0, 360, 30), True)]   # baptistery
    A.rect(1010, 380, 460, 50, 0, 'sec')                       # camposanto
    A.foot_shape([arc_pts(960, 540, 34, 34, 0, 360, 24), arc_pts(960, 540, 22, 22, 0, 360, 24)])
    ang = 4.5
    R = lambda pts: rot(pts, ang, 0, 0)
    el = []
    el.append(P(R([(-75, 0), (-75, -400), (75, -400), (75, 0)])) + ' ' + P(R([(-52, -400), (-52, -470), (52, -470), (52, -400)])) + ' ' + P(R([(-60, -470), (60, -470)])))
    el.append(' '.join(P(R([(-75, y), (75, y)])) for y in (-70, -122, -174, -226, -278, -330)))
    for lv, (yb, h) in enumerate(((0, 70), (-70, 52), (-122, 52), (-174, 52), (-226, 52), (-278, 52), (-330, 70))):
        xs = [-60 + 17.1 * i for i in range(8)] if lv else [-62 + 20.7 * i for i in range(7)]
        el.append(' '.join(P(R(arch_pts(x, yb - 4, 11, h - 14, 8))) for x in xs))
    el.append(' '.join(P(R(arch_pts(x, -402, 14, 50, 8))) for x in (-34, -11, 11, 34)))
    el.append(P(R([(-62, -470), (-44, -486), (44, -486), (62, -470)])) + ' ' + P(R([(-12, -486), (0, -508), (12, -486)])))
    el.append('M-160 0 H160 M-200 8 H200')
    return A, el


# ------------------------------------------------------------------ Venice
@site('venice', "ST MARK'S", 'VENICE · ITALY', 1.0)
def venice():
    A = Aerial(14)
    A.grid(45, (30, 120), box=(100, 80, 1820, 1000))
    A.river([(-100, 140), (260, 260), (520, 420), (700, 330), (900, 470), (1100, 700), (1300, 820), (1500, 760), (1760, 900), (2020, 1000)], 56)
    for pts in (((300, 700), (480, 600), (600, 640)), ((1400, 300), (1250, 420), (1150, 520)), ((600, 880), (800, 800), (950, 780))):
        A.river(list(pts), 14)
    A.rect(900, 580, 190, 100, -30, 'green')                   # Piazza San Marco
    A.foot_shape([box(990, 520, 112, 70, -30), box(930, 640, 22, 22, -30)])
    for k, (cx, cy, rx, ry) in enumerate(((560, 760, 150, 90), (1360, 640, 170, 100), (1180, 250, 140, 80))):
        A.blob(cx, cy, rx, ry, .15, 40 + k, 'sec')
    el = []
    el.append('M225 0 V-380 H295 V0 ' + ' '.join(f'M{x} -10 V-370' for x in (242, 260, 278)) + ' M225 -200 H295 M225 -300 H295')
    el.append('M232 -380 V-440 H288 V-380 M232 -440 H288 ' + ' '.join(P(arch_pts(x, -380, 12, 50, 8)) for x in (244, 256, 268, 280)))
    el.append('M236 -440 V-470 H284 V-440 M236 -470 L260 -552 L284 -470 M260 -552 V-572 M252 -564 H268')
    el.append('M-380 0 V-170 H150 V0 ' + poly_arches([-320, -215, -110, -5, 100], 0, 78, 120))
    el.append('M-380 -170 H150 ' + ' '.join(P(arch_pts(x, -172, 46, 70, 8)) for x in (-320, -215, -110, -5, 100)))
    el.append(' '.join(f'M{x - 46} -250 C{x - 46} -292 {x - 8} -300 {x} -336 C{x + 8} -300 {x + 46} -292 {x + 46} -250' for x in (-320, -215, -110, -5, 100)) + ' M-380 -250 H150')
    el.append(' '.join(f'M{x - 46} -300 V-330 A46 46 0 0 1 {x + 46} -330 V-300 M{x} -376 V-396' for x in (-250, -110, 30)))
    el.append('M-440 0 H440 M-440 16 q20 -8 40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0')
    return A, el


# ================================================================ batch 2 helpers
def RECT(x0, y0, x1, y1):
    return f'M{f(x0)} {f(y0)} H{f(x1)} V{f(y1)} H{f(x0)} Z'


def crenel(x0, x1, y, h=14, w=16):
    d = f'M{f(x0)} {f(y)}'
    x = x0
    while x < x1:
        d += f' V{f(y - h)} H{f(min(x + w, x1))} V{f(y)} H{f(min(x + 2 * w, x1))}'
        x += 2 * w
    return d


def gwin(x, yb, w, h):
    """pointed (gothic) window"""
    return f'M{f(x - w / 2)} {f(yb)} V{f(yb - h)} L{f(x)} {f(yb - h - w * .75)} L{f(x + w / 2)} {f(yb - h)} V{f(yb)}'


def rwin(x, yb, w, h):
    return f'M{f(x - w / 2)} {f(yb)} V{f(yb - h)} H{f(x + w / 2)} V{f(yb)}'


def cone(cx, yb, w, h):
    return f'M{f(cx - w / 2)} {f(yb)} L{f(cx)} {f(yb - h)} L{f(cx + w / 2)} {f(yb)}'


def waves(x0, x1, y, step=40, amp=8):
    n = int((x1 - x0) / step)
    return f'M{x0} {y} q{step / 2:g} {-amp} {step} 0' + ''.join(f' t{step} 0' for _ in range(n - 1))


def qpt(p0, p1, p2, t):
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])


def onion(cx, yb, w, h, stripes=(-.55, 0, .55)):
    R = []
    p0, p1, p2, p3 = (w / 2, 0), (w * .98, -h * .12), (w * .62, -h * .55), (0, -h)
    for i in range(21):
        t = i / 20
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        R.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    L = [(-x, y) for x, y in R]
    out = P([(cx + x, yb + y) for x, y in R] + [(cx + x, yb + y) for x, y in reversed(L[:-1])] + [(cx - w / 2, yb)], True)
    st = ' '.join(P([(cx + s * x, yb + y) for x, y in R]) for s in stripes)
    return out, st, f'M{f(cx)} {f(yb - h)} V{f(yb - h - h * .22)} M{f(cx - 5)} {f(yb - h - h * .12)} H{f(cx + 5)}'


# ================================================================== London
@site('london', 'TOWER BRIDGE', 'LONDON · UNITED KINGDOM', 1.0)
def london():
    A = Aerial(21)
    A.grid(70, (28, 118))
    A.river([(-100, 360), (300, 420), (640, 470), (900, 560), (1200, 590), (1600, 500), (2020, 560)], 96)
    A.sec += [P(box(740, 360, 190, 150, -10), True), P(box(740, 360, 120, 90, -10), True)]       # Tower of London
    A.green.append(P(box(1160, 640, 210, 120, 8), True))
    A.line([(1010, 520), (1010, 640)], 'sec')                                              # approach roads
    A.foot_shape([box(960, 545, 40, 130, 4), box(960, 500, 34, 34, 4), box(960, 592, 34, 34, 4)])
    el = []
    for cx in (-170, 170):
        el.append(f'M{cx - 55} 0 V-330 M{cx + 55} 0 V-330 M{cx - 55} -110 H{cx + 55} M{cx - 55} -300 H{cx + 55}')
        el.append(f'M{cx - 64} -330 H{cx + 64} M{cx - 64} -330 L{cx} -440 L{cx + 64} -330 M{cx} -440 V-470')
        el.append(f'M{cx - 64} -330 V-352 L{cx - 52} -380 L{cx - 40} -352 V-330 M{cx + 64} -330 V-352 L{cx + 52} -380 L{cx + 40} -352 V-330')
        el.append(' '.join(gwin(cx + dx, yb, 18, 46) for dx in (-30, 0, 30) for yb in (-150, -230)))
        el.append(' '.join(gwin(cx + dx, -4, 26, 70) for dx in (-26, 26)))
    el.append('M-115 -70 H115 M-440 -70 H-225 M225 -70 H440 M-440 -84 H440')
    el.append('M-115 -270 H115 M-115 -292 H115 ' + ' '.join(f'M{x} -270 L{x + 20} -292' for x in range(-115, 115, 20)))
    for sgn in (-1, 1):
        p0, p1, p2 = (sgn * 440, -90), (sgn * 330, -210), (sgn * 225, -292)
        el.append(f'M{f(p0[0])} {f(p0[1])} Q{f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])}')
        hg = ''
        for t in (.2, .35, .5, .65, .8):
            x, y = qpt(p0, p1, p2, t)
            hg += f'M{f(x)} {f(y)} V-72 '
        el.append(hg.strip())
    el.append(waves(-480, 480, 0, 40, 7))
    return A, el


# ================================================================ Stonehenge
@site('stonehenge', 'STONEHENGE', 'WILTSHIRE · ENGLAND', 1.0)
def stonehenge():
    A = Aerial(22)
    for k in range(6):
        A.blob(960 + (k - 3) * 140, 540 + ((k * 97) % 300) - 150, 340, 230, .12, 50 + k, 'green')
    A.line([(-100, 740), (500, 700), (1100, 760), (2020, 700)], 'streets')
    A.line([(1100, 250), (1040, 330), (1010, 420), (985, 470)], 'sec')                      # the Avenue
    for r in (150, 160):
        A.green.append(P(arc_pts(960, 540, r, r, 0, 360, 40), True))                           # bank + ditch
    A.rect(1060, 395, 12, 30, 30, 'sec')                                                     # Heel Stone
    out = [P(rot(box(960 + 88 * math.cos(math.radians(a)), 540 + 88 * math.sin(math.radians(a)), 26, 11, a + 90), 0), True) for a in range(0, 360, 12)]
    horse = []
    for k in range(5):
        a = math.radians(-60 + k * 30 + 180)
        horse.append(box(960 + 46 * math.cos(a), 540 + 46 * math.sin(a), 22, 12, math.degrees(a) + 90))
    A.foot = ' '.join(out) + ' ' + ' '.join(P(s, True) for s in horse)
    rnd = random.Random(7)

    def stone(x, w, h):
        pts = [(x - w / 2, 0), (x - w / 2 - rnd.uniform(0, 8), -h * .25), (x - w / 2 + rnd.uniform(-6, 6), -h * .6), (x - w / 2 + rnd.uniform(4, 12), -h), (x + w / 2 - rnd.uniform(4, 12), -h - rnd.uniform(0, 12)), (x + w / 2 + rnd.uniform(-6, 6), -h * .7), (x + w / 2 + rnd.uniform(0, 8), -h * .3), (x + w / 2, 0)]
        return P(pts)

    def lintel(x0, x1, y, t):
        return P([(x0 - 14, y), (x0 - 10, y - t), (x1 + 10, y - t - 5), (x1 + 14, y)], True)
    el = []
    ups = [-420, -310, -200, 160, 270, 380]
    for x in ups:
        el.append(stone(x, 54, 270 + rnd.randint(-12, 12)))
    for a, b in ((-420, -310), (-310, -200), (160, 270), (270, 380)):
        el.append(lintel(a, b, -270, 52))
    el.append(stone(-80, 70, 390) + ' ' + stone(80, 70, 390))
    el.append(lintel(-80, 80, -390, 58))
    el.append('M-500 0 H500 ' + ' '.join(f'M{x} 0 l-6 -14 M{x} 0 l4 -18 M{x} 0 l12 -12' for x in range(-470, 480, 70)))
    return A, el


# ================================================================ Edinburgh
@site('edinburgh', 'EDINBURGH CASTLE', 'SCOTLAND · UNITED KINGDOM', 1.0)
def edinburgh():
    A = Aerial(23)
    A.grid(70, (24, 114), skip=lambda x, y: ((x - 960) / 300) ** 2 + ((y - 540) / 200) ** 2 < 1)
    for k, (rx, ry) in enumerate(((400, 250), (320, 195), (240, 140))):
        A.blob(960, 540, rx, ry, .14, 60 + k, 'green')
    A.rect(900, 770, 700, 130, -4, 'green')                                                  # Princes Street Gardens
    A.line([(1160, 560), (1400, 640), (1700, 720), (2020, 780)], 'sec')                      # Royal Mile
    A.foot_shape([[(880, 520), (960, 490), (1030, 515), (1060, 560), (1010, 600), (930, 590), (890, 565)], [(930, 535), (990, 525), (1005, 555), (950, 570)]])
    el = []
    el.append(P([(-480, 0), (-470, -60), (-440, -110), (-430, -170), (-380, -215), (-300, -235), (0, -240), (300, -232), (380, -200), (420, -150), (450, -90), (480, 0)]))
    el.append(RECT(-410, -240, -270, -330) + ' ' + crenel(-410, -270, -330, 16, 20))                            # Half Moon Battery
    el.append(RECT(-150, -240, 150, -350) + ' M-150 -300 H150 ' + ' '.join(rwin(x, -250, 14, 28) + ' ' + rwin(x, -310, 14, 28) for x in range(-120, 150, 40)))
    el.append('M-160 -350 H160 M-160 -350 L-120 -400 H120 L160 -350')
    el.append(RECT(160, -240, 310, -310) + ' M155 -310 L235 -365 L315 -310 ' + ' '.join(rwin(x, -250, 16, 30) for x in (195, 235, 275)))      # Great Hall
    el.append(RECT(-50, -350, 50, -470) + ' M-60 -470 H60 ' + crenel(-60, 60, -470, 14, 15) + ' M-12 -484 L0 -520 L12 -484 M0 -520 V-550 L26 -540 L0 -530')   # Crown tower + flag
    el.append(RECT(335, -235, 395, -290) + ' M330 -290 L365 -325 L400 -290')                                  # chapel
    el.append(crenel(-270, -150, -240, 12, 14) + ' ' + crenel(310, 420, -230, 12, 14))
    el.append('M-90 -240 V-270 A16 16 0 0 1 -58 -270 V-240')
    return A, el


# ============================================================ Mont-Saint-Michel
@site('mont', 'MONT-SAINT-MICHEL', 'NORMANDY · FRANCE', 1.0)
def mont():
    A = Aerial(24)
    for k in range(16):
        A.line([(-100, 80 + k * 70), (500, 100 + k * 70 + 12 * (k % 3)), (1100, 70 + k * 70), (2020, 100 + k * 70)], 'water')
    A.line([(160, 1080), (400, 880), (640, 740), (800, 640)], 'sec')                          # causeway
    A.green.append(P(arc_pts(960, 540, 190, 190, 0, 360, 36), True))
    for r in (150, 110, 70):
        A.green.append(P(arc_pts(960, 540, r, r * .98, 0, 360, 32), True))
    A.foot_shape([box(962, 540, 56, 30, 20), arc_pts(962, 540, 20, 20, 0, 360, 16)])
    el = []
    el.append('M-340 0 C-290 -40 -210 -140 -140 -220 C-100 -270 -50 -300 0 -330 C50 -300 100 -270 140 -220 C210 -140 290 -40 340 0')
    for k, yy in enumerate((-60, -110, -160, -205)):
        wd = 330 - (-yy) * 0.9
        xs = [x for x in range(int(-wd + 20), int(wd - 20), 38)]
        el.append(' '.join(f'M{x - 14} {yy} V{yy - 20} L{x} {yy - 36} L{x + 14} {yy - 20} V{yy}' for x in xs) + f' M{-wd} {yy} H{wd}')
    el.append('M-48 -300 H48 V-410 H-48 Z M-48 -340 H48 ' + ' '.join(gwin(x, -345, 12, 36) + ' ' + gwin(x, -395, 12, 14) for x in (-24, 0, 24)))
    el.append('M-34 -410 L0 -515 L34 -410 M0 -515 V-545 M-9 -532 H9 M-70 -330 L-48 -380 M70 -330 L48 -380')
    el.append(crenel(-340, 340, -22, 12, 18) + ' M-340 0 V-22 M340 0 V-22')
    el.append(waves(-480, 480, 0, 40, 7))
    return A, el


# ================================================================ Amsterdam
@site('amsterdam', 'CANAL HOUSES', 'AMSTERDAM · NETHERLANDS', 1.0)
def amsterdam():
    A = Aerial(25)
    A.grid(55, (20, 110))
    for k, r in enumerate((330, 440, 550, 660)):
        A.water.append(P(arc_pts(960, 1100, r, r * .86, 200, 340, 40)))
        A.water.append(P(arc_pts(960, 1100, r + 26, (r + 26) * .86, 200, 340, 40)))
    for k in range(9):
        a = math.radians(200 + k * 17.5)
        A.streets.append(f'M{f(960 + 300 * math.cos(a))} {f(1100 + 258 * math.sin(a))} L{f(960 + 700 * math.cos(a))} {f(1100 + 602 * math.sin(a))}')
    A.foot_shape([box(960, 548, 150, 24, 0), box(960, 574, 150, 18, 0)])
    rnd = random.Random(3)
    el = []
    ws = [100, 92, 112, 96, 106, 90, 102]
    hs = [330, 362, 312, 372, 340, 322, 352]
    x = -sum(ws) / 2
    for i, (w, h) in enumerate(zip(ws, hs)):
        x0, x1, yb = x, x + w, -34
        t = i % 4
        if t == 0:      # step gable
            top = [(x0, -h), (x0, -h - 20), (x0 + w * .2, -h - 20), (x0 + w * .2, -h - 40), (x0 + w * .36, -h - 40), (x0 + w * .36, -h - 60), (x0 + w * .64, -h - 60), (x0 + w * .64, -h - 40), (x0 + w * .8, -h - 40), (x0 + w * .8, -h - 20), (x1, -h - 20), (x1, -h)]
            d = P([(x0, yb)] + top + [(x1, yb)])
        elif t == 1:    # bell gable
            d = f'M{x0} {yb} V{-h} C{x0} {-h - 30} {x0 + w * .28} {-h - 34} {x0 + w * .34} {-h - 62} C{x0 + w * .4} {-h - 86} {x0 + w * .6} {-h - 86} {x0 + w * .66} {-h - 62} C{x0 + w * .72} {-h - 34} {x1} {-h - 30} {x1} {-h} V{yb}'
        elif t == 2:    # neck gable
            d = P([(x0, yb), (x0, -h), (x0, -h - 20), (x0 + w * .3, -h - 20), (x0 + w * .3, -h - 70), (x0 + w * .7, -h - 70), (x0 + w * .7, -h - 20), (x1, -h - 20), (x1, -h), (x1, yb)])
        else:           # spout gable
            d = P([(x0, yb), (x0, -h), (x0 + w / 2, -h - 64), (x1, -h), (x1, yb)])
        el.append(d)
        rows = 4
        win = ''
        for r in range(rows):
            for c in range(2 if w < 100 else 3):
                cx = x0 + w * (c + 1) / ((2 if w < 100 else 3) + 1)
                win += ' ' + rwin(cx, yb - 28 - r * 70, 18, 44)
        el.append(win.strip())
        x += w
    el.append('M-380 -34 H380')
    el.append('M300 0 Q420 -110 540 0 M310 -14 H530')
    el.append(waves(-480, 560, 0, 40, 6) + ' ' + waves(-460, 460, 18, 40, 5))
    return A, el


# ================================================================== Cologne
@site('cologne', 'COLOGNE CATHEDRAL', 'COLOGNE · GERMANY', 0.95)
def cologne():
    A = Aerial(31)
    A.grid(80, (10, 100))
    A.river([(1500, -100), (1440, 250), (1380, 520), (1450, 800), (1560, 1200)], 150)                    # Rhine
    A.line([(1250, 360), (1700, 340)], 'sec', False)                                                     # Hohenzollern bridge
    A.green.append(P(box(1000, 700, 260, 130, 6), True))
    A.foot_shape([cross_shape(960, 540, 230, 44, 70, 90), box(880, 540, 38, 50, 0)])
    el = []
    for cx in (-135, 135):
        el.append(f'M{cx - 75} 0 V-250 H{cx + 75} V0 M{cx - 75} -250 L{cx - 55} -330 H{cx + 55} L{cx + 75} -250')
        el.append(' '.join(gwin(cx + dx, -4, 20, 70) for dx in (-40, 0, 40)) + ' ' + ' '.join(gwin(cx + dx, -120, 20, 60) for dx in (-40, 0, 40)) + ' ' + ' '.join(gwin(cx + dx, -230, 18, 40) for dx in (-35, 35)))
        el.append(f'M{cx - 55} -330 L{cx - 6} -590 H{cx + 6} L{cx + 55} -330 M{cx - 6} -590 L{cx} -620 L{cx + 6} -590')
        lat = ''
        for k in range(8):
            yy = -330 - k * 32
            w1 = 55 - k * 6.2
            lat += f'M{cx - w1} {yy} L{cx + w1 - 6} {yy - 32} M{cx + w1} {yy} L{cx - w1 + 6} {yy - 32} '
        el.append(lat.strip())
        el.append(' '.join(f'M{cx - 55 + (k * 6.2)} {-330 - k * 32} l-9 -4 M{cx + 55 - (k * 6.2)} {-330 - k * 32} l9 -4' for k in range(1, 8)))
        el.append(f'M{cx - 90} 0 V-170 L{cx - 82} -200 L{cx - 74} -170 M{cx + 90} 0 V-170 L{cx + 82} -200 L{cx + 74} -170')
    el.append('M-60 0 V-170 L0 -250 L60 -170 V0 M-40 0 V-150 L0 -205 L40 -150 V0 M-60 -260 a60 60 0 0 1 120 0')
    el.append('M-60 -330 L0 -400 L60 -330 M0 -400 V-430')
    el.append('M-420 0 H420')
    return A, el


# ============================================================ Neuschwanstein
@site('neuschwanstein', 'NEUSCHWANSTEIN', 'BAVARIA · GERMANY', 1.0)
def neuschwanstein():
    A = Aerial(32)
    for k, (rx, ry) in enumerate(((620, 400), (520, 330), (420, 260), (320, 200), (220, 140))):
        A.blob(960, 540, rx, ry, .16, 70 + k, 'green')
    A.blob(420, 780, 260, 150, .2, 78, 'water')                                                          # Alpsee
    A.blob(1480, 260, 160, 90, .2, 79, 'water')
    A.line([(1100, 640), (1200, 520), (1290, 410)], 'sec')                                              # Marienbruecke
    A.foot_shape([[(900, 520), (990, 505), (1030, 540), (1010, 570), (930, 585), (895, 560)], arc_pts(905, 520, 16, 16, 0, 360, 14), arc_pts(1030, 545, 14, 14, 0, 360, 14)])
    el = []
    el.append(P([(-470, 0), (-455, -60), (-420, -100), (-380, -90), (-330, -130), (-260, -120), (-200, -150), (-120, -140), (-40, -170), (40, -160), (120, -175), (200, -150), (280, -160), (340, -120), (400, -100), (450, -50), (470, 0)]))
    el.append(RECT(-140, -170, 110, -330) + ' M-140 -330 L-15 -410 L110 -330 ' + ' '.join(gwin(x, -190 - r * 46, 14, 26) for x in range(-110, 110, 38) for r in range(3)))
    el.append(RECT(-250, -150, -190, -360) + ' ' + cone(-220, -360, 86, 110) + ' ' + ' '.join(rwin(-220, -200 - r * 50, 14, 24) for r in range(3)))
    el.append(RECT(150, -170, 205, -350) + ' ' + cone(177, -350, 80, 100) + ' ' + ' '.join(rwin(177, -220 - r * 50, 12, 22) for r in range(3)))
    el.append(RECT(-330, -125, -295, -240) + ' ' + cone(-312, -240, 56, 70) + ' ' + RECT(-110, -330, -75, -430) + ' ' + cone(-92, -430, 52, 70))
    el.append(RECT(255, -158, 325, -235) + ' M250 -235 L290 -285 L330 -235 ' + RECT(110, -250, 150, -330) + ' ' + cone(130, -330, 52, 70))
    el.append(' '.join(f'M{x} -330 V-345 M{x - 6} -345 H{x + 6}' for x in (-120, 60)))
    return A, el


# ================================================================== Prague
@site('prague', 'PRAGUE CASTLE', 'PRAGUE · CZECHIA', 1.0)
def prague():
    A = Aerial(33)
    A.grid(70, (20, 110), skip=lambda x, y: x > 1100 and y < 440)
    A.river([(1700, -100), (1500, 200), (1300, 520), (1280, 820), (1500, 1100), (1650, 1250)], 110)
    A.line([(1180, 620), (1360, 640)], 'sec', False)
    A.sec += [P([(840, 470), (1080, 440), (1120, 530), (1040, 590), (860, 580)], True)]                 # castle complex
    A.green.append(P(box(700, 760, 260, 160, 20), True))
    A.foot_shape([cross_shape(930, 520, 130, 34, 56, 0)])
    el = []
    el.append('M-480 0 C-380 -20 -300 -120 -180 -180 L180 -180 C300 -120 380 -20 480 0')
    el.append(RECT(-330, -180, 20, -270) + ' M-330 -225 H20 ' + ' '.join(rwin(x, -190, 14, 26) + ' ' + rwin(x, -234, 14, 26) for x in range(-310, 10, 36)) + ' M-340 -270 L-310 -300 H30 L20 -270')
    el.append(RECT(30, -180, 330, -250) + ' ' + ' '.join(rwin(x, -190, 14, 26) + ' ' + rwin(x, -224, 14, 22) for x in range(52, 330, 36)) + ' M24 -250 L60 -280 H330')
    el.append('M-150 -270 L-150 -330 H-20 V-270 M-150 -330 L-85 -400 L-20 -330 ' + ' '.join(gwin(x, -285, 12, 26) for x in (-130, -100, -70, -40)))
    el.append('M60 -250 V-380 H150 V-250 M52 -380 H158 L105 -440 Z M105 -440 V-510 L125 -540 L105 -570 L85 -540 Z M70 -300 H140')
    el.append('M-420 -150 L-380 -190 M-200 -180 L-210 -190 M-110 -330 V-250 M-30 -330 V-250')
    el.append(RECT(-280, -300, -250, -330) + ' ' + cone(-265, -330, 40, 50) + ' ' + RECT(250, -250, 280, -290) + ' ' + cone(265, -290, 40, 50))
    return A, el


# =================================================================== Vienna
@site('vienna', 'SCHONBRUNN', 'VIENNA · AUSTRIA', 0.95)
def vienna():
    A = Aerial(34)
    A.grid(60, (15, 105), skip=lambda x, y: ((x - 960) / 620) ** 2 + ((y - 540) / 440) ** 2 < 1)
    for i in range(8):                                                                                  # parterres
        A.rect(960, 700 + i * 0, 520 - i * 56, 300 - i * 32, 0, 'green')
    A.ellipse(960, 720, 70, 40, 0, 'water')
    A.ellipse(960, 880, 120, 60, 0, 'water')
    for k in range(7):
        A.streets.append(f'M{960 - 250 + k * 83} 570 V860')
    A.rect(960, 1010, 140, 70, 0, 'sec')                                                                # Gloriette
    A.foot_shape([[(780, 500), (1140, 500), (1140, 560), (1060, 560), (1060, 620), (860, 620), (860, 560), (780, 560)]])
    el = []
    el.append(RECT(-440, 0, 440, -150))
    el.append(RECT(-170, -150, 170, -230) + ' M-170 -230 L-130 -290 H130 L170 -230 M-120 -290 L-120 -310 H120 L120 -290')
    el.append('M-90 -230 L0 -300 L90 -230 Z M-60 -240 L0 -285 L60 -240')
    el.append(poly_arches([x for x in range(-410, 420, 56)], -2, 36, 78))
    el.append(' '.join(rwin(x, -86, 18, 40) for x in range(-410, 420, 56)) + ' M-440 -86 H440')
    el.append(' '.join(rwin(x, -160, 22, 50) for x in range(-150, 160, 46)) + ' M-170 -150 H170')
    el.append(RECT(-440, -150, -380, -210) + ' M-446 -210 H-374 L-410 -250 Z ' + RECT(380, -150, 440, -210) + ' M374 -210 H446 L410 -250 Z')
    el.append('M0 -310 V-340 L24 -332 L0 -324 M-60 0 V-66 M60 0 V-66')
    return A, el


# ================================================================= Budapest
@site('budapest', 'PARLIAMENT', 'BUDAPEST · HUNGARY', 0.95)
def budapest():
    A = Aerial(35)
    A.grid(80, (25, 115), skip=lambda x, y: x > 1180)
    A.river([(1500, -100), (1380, 260), (1320, 560), (1380, 860), (1500, 1200)], 190)
    A.line([(1260, 360), (1700, 340)], 'sec', False)
    A.green.append(P(box(780, 700, 220, 160, 0), True))
    A.foot_shape([box(1010, 540, 80, 330, 0), box(1010, 540, 66, 66, 0)])
    A.sec += [P(box(1010, 450, 30, 100, 0), True), P(box(1010, 630, 30, 100, 0), True)]
    el = []
    el.append(RECT(-200, 0, 200, -250) + ' M-200 -250 L-160 -300 H160 L200 -250')
    el.append('M-70 -250 V-340 H70 V-250 M-70 -340 C-70 -430 70 -430 70 -340 M0 -410 V-520 M-8 -440 H8 M-30 -400 C-30 -420 30 -420 30 -400 ' + ' '.join(gwin(x, -260, 10, 40) for x in (-50, -25, 0, 25, 50)))
    el.append(poly_arches([x for x in range(-170, 180, 50)], -2, 30, 110) + ' ' + ' '.join(gwin(x, -140, 18, 58) for x in range(-170, 180, 50)) + ' M-200 -136 H200')
    for sgn in (-1, 1):
        el.append(f'M{sgn * 200} 0 V-170 H{sgn * 440} V0 ' + poly_arches([sgn * x for x in range(230, 440, 46)], -2, 28, 80) + ' ' + ' '.join(gwin(sgn * x, -100, 14, 44) for x in range(230, 440, 46)))
        el.append(f'M{sgn * 200} -170 L{sgn * 200} -215 L{sgn * 190} -240 ' + ' '.join(f'M{sgn * x - 8} -170 L{sgn * x} -204 L{sgn * x + 8} -170' for x in range(230, 440, 46)))
        el.append(RECT(sgn * 440 - 36, -170, sgn * 440 + 36, -300) + ' ' + cone(sgn * 440, -300, 90, 110) + ' ' + ' '.join(gwin(sgn * 440, yb, 14, 36) for yb in (-190, -250)))
    el.append(' '.join(f'M{x - 12} -300 L{x} -350 L{x + 12} -300' for x in (-130, -100, 100, 130)))
    el.append('M-460 0 H460')
    return A, el


# ================================================================== Moscow
@site('moscow', "ST BASIL'S", 'MOSCOW · RUSSIA', 1.0)
def moscow():
    A = Aerial(36)
    A.grid(60, (0, 90), skip=lambda x, y: 600 < x < 1500 and 300 < y < 800)
    A.river([(-100, 900), (500, 870), (1000, 950), (1500, 880), (2020, 920)], 120)
    A.rect(960, 560, 700, 260, 0, 'green')                                                              # Red Square
    A.sec += [P([(560, 280), (1400, 250), (1480, 420), (1460, 830), (700, 860), (560, 700)], True)]      # Kremlin wall
    for tx, ty in ((560, 280), (900, 262), (1400, 250), (1480, 640), (1060, 845), (700, 860), (560, 700)):
        A.sec.append(P(box(tx, ty, 26, 26, 0), True))
    cs = [(960, 540, 34)] + [(960 + 66 * math.cos(math.radians(a)), 540 + 66 * math.sin(math.radians(a)), 20) for a in range(0, 360, 45)]
    A.foot = ' '.join(P(arc_pts(x, y, r, r, 0, 360, 16), True) for x, y, r in cs)
    el = []
    out, st, fin = onion(0, -240, 130, 120, (-.5, 0, .5))
    el.append(f'M-70 0 V-240 H70 V0 ' + gwin(0, -4, 30, 90) + ' M-70 -120 H70 M-70 -240 L0 -380 L70 -240 M-35 -240 L0 -380 L35 -240')
    o, s_, fn = onion(0, -380, 70, 90, (-.4, 0, .4))
    el.append(o + ' ' + s_ + ' ' + fn)
    for x, bh, dw, dh in ((-340, 150, 84, 100), (-250, 190, 84, 104), (-160, 130, 80, 96), (160, 130, 80, 96), (250, 190, 84, 104), (340, 150, 84, 100)):
        el.append(f'M{x - 40} 0 V{-bh} H{x + 40} V0 ' + gwin(x, -4, 22, 60) + f' M{x - 40} {-bh + 22} H{x + 40}')
        o, s_, fn = onion(x, -bh - 16, dw, dh)
        el.append(f'M{x - 30} {-bh} V{-bh - 16} H{x + 30} V{-bh} ' + o + ' ' + s_ + ' ' + fn)
    el.append('M-420 0 H420')
    return A, el


# ================================================================= Istanbul
@site('istanbul', 'HAGIA SOPHIA', 'ISTANBUL · TURKIYE', 1.0)
def istanbul():
    A = Aerial(37)
    A.grid(70, (30, 120), skip=lambda x, y: x > 1500)
    A.river([(2020, -100), (1700, 300), (1620, 700), (1760, 1000), (2020, 1200)], 200)
    A.blob(1460, 120, 220, 70, .18, 90, 'water')
    A.green.append(P(box(860, 700, 340, 120, -10), True))                                                # Sultanahmet Park
    for k, (dx, dy) in enumerate(((-90, 120), (90, 160), (-110, 200), (110, 240))):
        A.sec.append(P(arc_pts(740 + k * 20 + dx / 4, 880 + dy / 6, 10, 10, 0, 360, 10), True))
    A.sec.append(P(box(780, 880, 120, 90, -10), True))                                                    # Blue Mosque
    A.foot_shape([box(960, 540, 140, 100, 0), arc_pts(960, 540, 44, 44, 0, 360, 24), arc_pts(886, 484, 10, 10, 0, 360, 10), arc_pts(1034, 484, 10, 10, 0, 360, 10), arc_pts(886, 596, 10, 10, 0, 360, 10), arc_pts(1034, 596, 10, 10, 0, 360, 10)])
    el = []
    el.append('M-300 0 V-150 H300 V0 ' + poly_arches([x for x in range(-250, 260, 62)], -2, 38, 100) + ' M-300 -100 H300')
    el.append('M-150 -150 V-290 H150 V-150 M-150 -290 C-150 -400 150 -400 150 -290 ' + ' '.join(f'M{x} -290 V-318' for x in range(-132, 140, 12)))
    el.append('M-150 -190 C-300 -190 -320 -150 -320 -150 M150 -190 C300 -190 320 -150 320 -150 M-150 -250 C-250 -250 -280 -200 -290 -150 M150 -250 C250 -250 280 -200 290 -150')
    el.append('M-300 -150 L-330 -60 L-300 0 M300 -150 L330 -60 L300 0 M-150 -150 L-190 -60 M150 -150 L190 -60')
    for sgn in (-1, 1):
        x = sgn * 400
        el.append(f'M{x - 13} 0 V-420 M{x + 13} 0 V-420 M{x - 18} -300 H{x + 18} M{x - 18} -360 H{x + 18} M{x - 13} -420 L{x} -490 L{x + 13} -420 M{x} -490 V-505 M{x - 8} -515 a8 8 0 1 1 10 4')
    el.append('M-460 0 H460')
    return A, el


# ================================================================ Dubrovnik
@site('dubrovnik', 'DUBROVNIK', 'CROATIA · ADRIATIC', 1.0)
def dubrovnik():
    A = Aerial(38)
    for k in range(14):
        A.line([(-100, 60 + k * 80), (500, 80 + k * 80 + 14 * (k % 3)), (1100, 60 + k * 80), (2020, 90 + k * 80)], 'water')
    A.sec.append(P(box(960, 540, 700, 330, 0), True))
    A.grid(55, (0, 90), box=(640, 380, 1280, 700))
    A.line([(640, 540), (1280, 540)], 'streets', False)
    for x, y in ((650, 395), (1270, 395), (650, 685), (1270, 685), (960, 380)):
        A.sec.append(P(arc_pts(x, y, 22, 22, 0, 360, 14), True))
    A.foot_shape([box(680, 405, 70, 70, 0), arc_pts(680, 405, 24, 24, 0, 360, 18)])
    el = []
    el.append(P([(-480, 0), (-470, -50), (-430, -80), (-300, -90), (-100, -85), (100, -90), (320, -86), (450, -70), (480, 0)]))
    el.append(RECT(-460, -90, 460, -200) + ' ' + crenel(-460, 460, -200, 14, 18) + ' ' + ' '.join(rwin(x, -110, 12, 26) for x in range(-300, 460, 70)))
    el.append(RECT(-340, -90, -190, -330) + ' M-352 -300 H-178 ' + crenel(-352, -178, -330, 16, 15) + ' M-352 -300 V-330 M-178 -300 V-330 ' + ' '.join(rwin(x, -120 - r * 60, 12, 28) for x in (-300, -265, -230, -195) for r in range(2) if x % 2 == 0 or r == 0))
    el.append(RECT(250, -90, 340, -270) + ' ' + crenel(244, 346, -270, 14, 14) + ' ' + rwin(295, -130, 16, 36) + ' ' + rwin(295, -200, 16, 36))
    el.append(' '.join(f'M{x} -200 L{x + 22} -236 L{x + 44} -200' for x in (-140, -80, -20, 40, 100, 160)))
    el.append('M-20 -200 V-330 H20 V-200 M-26 -330 L0 -420 L26 -330 M0 -420 V-445')
    el.append(waves(-500, 500, 0, 40, 7) + ' ' + waves(-480, 480, 16, 40, 5))
    return A, el


# ================================================================ Barcelona
@site('barcelona', 'SAGRADA FAMILIA', 'BARCELONA · SPAIN', 0.95)
def barcelona():
    A = Aerial(39)
    for i in range(-5, 7):
        for j in range(-4, 5):
            cx, cy = 960 + i * 150, 540 + j * 150
            if abs(cx - 960) < 130 and abs(cy - 540) < 130:
                continue
            A.streets.append(P(rot([(cx - 55, cy - 70), (cx + 55, cy - 70), (cx + 70, cy - 55), (cx + 70, cy + 55), (cx + 55, cy + 70), (cx - 55, cy + 70), (cx - 70, cy + 55), (cx - 70, cy - 55)], 0, cx, cy), True))
    A.line([(-100, 1000), (2020, 80)], 'sec', False)                                                    # Avinguda Diagonal
    A.foot_shape([cross_shape(960, 540, 190, 40, 70, 0), arc_pts(960, 440, 36, 24, 180, 360, 12) + arc_pts(960, 440, 36, 24, 0, 180, 12)])
    el = []

    def spire(cx, h, w):
        left = [(cx - w / 2 + (w / 2 - 6) * (y / h) ** 1.6, -y) for y in range(0, int(h) + 1, 20)]
        right = [(cx + w / 2 - (w / 2 - 6) * (y / h) ** 1.6, -y) for y in range(0, int(h) + 1, 20)]
        out = P(left + [(cx, -h - 28)] + list(reversed(right)))
        det = ' '.join(f'M{f(cx - w / 2 * (1 - y / h) - 0)} {-y} H{f(cx + w / 2 * (1 - y / h))}' for y in range(60, int(h), 70))
        win = ' '.join(f'M{cx - 5} {-y} a5 11 0 1 0 10 0 a5 11 0 1 0 -10 0' for y in range(40, int(h) - 40, 48))
        fin = f'M{cx} {-h - 28} V{-h - 52} M{cx - 9} {-h - 42} H{cx + 9} M{cx - 14} {-h - 14} a14 14 0 1 0 28 0 a14 14 0 1 0 -28 0'
        return [out, det, win, fin]
    for cx, h, w in ((0, 500, 80), (-130, 400, 62), (130, 400, 62), (-250, 340, 54), (250, 340, 54), (-350, 280, 48), (350, 280, 48)):
        el += spire(cx, h, w)
    el.append('M-420 0 V-120 H420 V0 M-420 -120 L-380 -170 H380 L420 -120 ' + ' '.join(gwin(x, -4, 30, 86) for x in (-300, -150, 0, 150, 300)) + ' ' + ' '.join(f'M{x} -120 V-170' for x in range(-360, 380, 60)))
    el.append('M-460 0 H460')
    return A, el


# =================================================================== Lisbon
@site('lisbon', 'BELEM TOWER', 'LISBON · PORTUGAL', 1.05)
def lisbon():
    A = Aerial(40)
    A.grid(70, (10, 100), skip=lambda x, y: y > 760)
    A.river([(-100, 880), (500, 840), (1000, 900), (1500, 860), (2020, 900)], 20)
    for k in range(7):
        A.line([(-100, 800 + k * 55), (500, 820 + k * 55), (1100, 800 + k * 55), (2020, 830 + k * 55)], 'water')
    A.sec.append(P(box(700, 420, 520, 80, -4), True))                                                    # Jeronimos Monastery
    A.green.append(P(box(1300, 600, 300, 150, 0), True))
    A.foot_shape([box(960, 560, 70, 70, 0), box(960, 560, 110, 20, 0), box(960, 605, 160, 36, 0)])
    el = []
    el.append(RECT(-380, 0, 380, -80) + ' ' + poly_arches([x for x in range(-340, 360, 80)], -2, 44, 52) + ' ' + crenel(-380, 380, -80, 14, 16))
    el.append('M-100 -80 V-170 H100 V-80 M-100 -170 H100 M-100 -250 H100 M-100 -330 H100 M-100 -170 V-410 M100 -170 V-410 M-110 -410 H110 ' + crenel(-110, 110, -410, 14, 14))
    for lv, yb in enumerate((-80, -170, -250)):
        el.append(' '.join(P(arch_pts(x, yb - 4, 28, 54, 8)) for x in (-60, 0, 60)))
    for sgn in (-1, 1):
        x = sgn * 100
        el.append(f'M{x - 20} -250 V-340 H{x + 20} V-250 M{x - 24} -340 H{x + 24} M{x - 20} -340 C{x - 28} -380 {x + 28} -380 {x + 20} -340')
    el.append(' '.join(f'M{cx} {cy} a9 9 0 1 0 18 0 a9 9 0 1 0 -18 0 M{cx + 9} {cy - 6} V{cy + 6} M{cx + 3} {cy} H{cx + 15}' for cx, cy in ((-90, -135), (-9, -135), (72, -135), (-90, -215), (72, -215))))
    el.append('M-34 -410 C-34 -440 34 -440 34 -410 M0 -430 V-460')
    el.append(waves(-500, 500, 0, 40, 7) + ' ' + waves(-480, 480, 16, 40, 5))
    return A, el


# ===================================================================== Paris
import gen_balloon_sample as _E  # noqa: E402


@site('eiffel', 'EIFFEL TOWER', 'PARIS · FRANCE', 1.2)
def eiffel():
    ae, foot = _E.aerial()
    A = Aerial(0)
    A.streets, A.water, A.green, A.foot = ae['streets'], ae['river'], ae['accent'], foot
    return A, _E.elevation()
