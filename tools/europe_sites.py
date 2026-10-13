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
