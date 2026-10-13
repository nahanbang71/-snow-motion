"""Second film: Mediterranean-to-Middle-East landmarks as laser elevations (base y=0, up is negative)."""
import math
import random

from europe_kit import P, arc_pts, arch_pts, catmull, f, poly_arches
from europe_sites import RECT, crenel, cone, gwin, rwin, waves
import world_sites as WS

ME = {}      # id -> dict(name, country, w, h, el())


def site(id, name, country, w, h, lon, lat, label):
    def deco(fn):
        ME[id] = dict(name=name, country=country, w=w, h=h, el=fn, lon=lon, lat=lat, label=label)
        return fn
    return deco


def circ(cx, cy, r):
    return f'M{f(cx - r)} {f(cy)} a{r} {r} 0 1 0 {2 * r} 0 a{r} {r} 0 1 0 {-2 * r} 0'


@site('marrakech', 'KOUTOUBIA', 'MARRAKECH · MOROCCO', 880, 570, -7.99, 31.63, 'MARRAKECH')
def marrakech():
    el = [RECT(-80, 0, 80, -400) + ' M-80 -400 H80']
    for yb, h in ((-30, 110), (-190, 100)):
        el.append(' '.join(gwin(x, yb, 30, h - 30) for x in (-48, -16, 16, 48)))
    el.append(P([(-80 + i * 20, -355 if i % 2 == 0 else -385) for i in range(9)]) + ' ' + ' '.join(rwin(x, -300, 16, 40) for x in (-50, -18, 18, 50)))
    el.append(RECT(-45, -400, 45, -470) + ' M-45 -430 H45 ' + ' '.join(gwin(x, -405, 14, 22) for x in (-22, 0, 22)))
    el.append(' '.join(circ(0, y, 12) for y in (-482, -506, -526)) + ' M0 -536 V-570')
    for sgn in (-1, 1):
        a, b = (80, 440) if sgn > 0 else (-440, -80)
        el.append(f'M{a} 0 V-110 H{b} V0 ' + ' '.join(f'M{x} -110 L{x + 12} -132 L{x + 24} -110' for x in range(min(a, b), max(a, b) - 24, 24)))
        el.append(poly_arches([sgn * x for x in range(120, 420, 56)], -2, 34, 80))
    return el


@site('eljem', 'EL JEM', 'AMPHITHEATRE · TUNISIA', 760, 330, 10.71, 35.30, 'EL JEM')
def eljem():
    xs = [-340 + 56 * i for i in range(13)]
    return ['M-380 0 V-250 L-340 -290 L-300 -272 L-250 -330 H380 V0', 'M-380 -110 H380 M-380 -220 H380 M-420 0 H420',
            poly_arches(xs, -2, 36, 92), poly_arches(xs, -112, 36, 92), poly_arches(xs[2:], -222, 36, 92),
            ' '.join(f'M{x - 7} -326 v16 h14 v-16' for x in xs[3:] if x % 2 == 0)]


@site('giza', 'PYRAMIDS OF GIZA', 'EGYPT', 1500, 400, 31.13, 29.98, 'GIZA')
def giza():
    return WS.giza()


@site('karnak', 'KARNAK', 'LUXOR · EGYPT', 1000, 560, 32.66, 25.72, 'KARNAK')
def karnak():
    el = ['M-500 0 L-485 -300 H-395 L-380 0 ' + 'M-320 0 L-335 -300 H-245 L-260 0 M-500 -300 H-245 M-380 0 V-120 H-320 V0',
          ' '.join(f'M{x} -60 V-270' for x in (-465, -440, -415, -300, -275, -300 + 25)),
          'M-190 0 V-30 H-110 V0 M-175 -30 L-165 -440 H-135 L-125 -30 M-165 -440 L-150 -490 L-135 -440 ' + ' '.join(f'M-155 {y} h10' for y in range(-90, -420, -50))]
    for k, x in enumerate((20, 140, 260, 380, 500)):
        h = 430 if k in (1, 2, 3) else 320
        el.append(f'M{x - 28} 0 V{-h} M{x + 28} 0 V{-h} M{x - 28} {-h * .3:.0f} H{x + 28} M{x - 28} {-h * .62:.0f} H{x + 28} '
                  f'M{x - 28} {-h} C{x - 42} {-h - 35} {x - 22} {-h - 55} {x} {-h - 60} C{x + 22} {-h - 55} {x + 42} {-h - 35} {x + 28} {-h} M{x - 56} {-h - 8} H{x + 56}')
    el.append('M-520 0 H540')
    return el


@site('abusimbel', 'ABU SIMBEL', 'NUBIA · EGYPT', 680, 430, 31.62, 22.34, 'ABU SIMBEL')
def abusimbel():
    el = ['M-340 0 L-300 -400 H300 L340 0', 'M-300 -400 H300 M-310 -378 H310 ' + ' '.join(f'M{x} -400 v-18 M{x - 5} -410 h10' for x in range(-270, 280, 40))]
    for x in (-230, -120, 120, 230):
        el.append(f'M{x - 26} -330 H{x + 26} L{x + 18} -362 H{x - 18} Z M{x - 22} -330 L{x - 18} -262 H{x + 18} L{x + 22} -330 M{x - 12} -302 h8 M{x + 4} -302 h8 M{x} -296 v14 M{x - 8} -272 h16 '
                  f'M{x - 46} -262 L{x - 40} -140 H{x + 40} L{x + 46} -262 Z M{x - 42} -140 V0 H{x - 8} V-140 M{x + 8} -140 V0 H{x + 42} V-140')
    el.append('M-34 0 V-130 H34 V0 M-30 -150 H30 V-200 H-30 Z M-30 -175 H30')
    return el


@site('petra', 'PETRA', 'AL-KHAZNEH · JORDAN', 620, 560, 35.44, 30.33, 'PETRA')
def petra():
    el = ['M-310 0 V-470 L-280 -520 L-200 -500 L-120 -550 L0 -530 L140 -556 L230 -510 L310 -470 V0']
    el.append(' '.join(f'M{x - 14} -10 V-210 M{x + 14} -10 V-210 M{x - 21} -210 H{x + 21} V-228 H{x - 21} Z' for x in (-150, -90, -30, 30, 90, 150)))
    el.append('M-180 -228 H180 V-262 H-180 Z M-170 -262 L0 -330 L170 -262 M-30 -10 V-130 H30 V-10 M-20 -150 H20 V-196 H-20 Z')
    el.append('M-60 -262 V-420 H60 V-262 M-72 -420 L0 -490 L72 -420 M0 -490 V-512 M-6 -512 h12 ' + ' '.join(f'M{x} -270 V-415' for x in (-40, -13, 13, 40)))
    el.append('M-190 -262 L-190 -340 L-80 -380 M190 -262 L190 -340 L80 -380 M-140 -262 V-330 M140 -262 V-330')
    el.append('M-340 0 H340')
    return el


@site('jerusalem', 'OLD CITY', 'JERUSALEM', 840, 430, 35.23, 31.78, 'JERUSALEM')
def jerusalem():
    el = [RECT(-170, 0, 170, -190) + ' M-170 -110 H170 M-170 -190 H170 ' + poly_arches([x for x in range(-140, 150, 40)], -2, 26, 74)]
    el.append(' '.join(gwin(x, -112, 14, 44) for x in range(-140, 150, 28)))
    el.append('M-110 -190 V-250 H110 V-190 ' + ' '.join(f'M{x} -194 V-246' for x in range(-90, 100, 30)))
    el.append('M-110 -250 C-110 -410 110 -410 110 -250 M0 -386 V-420 M-10 -436 a12 12 0 1 1 6 18')
    el.append('M-110 -250 C-60 -330 60 -330 110 -250')
    el.append('M220 0 V-60 H340 V0 M215 -60 C215 -140 345 -140 345 -60 M280 -118 V-140')
    for sgn in (-1, 1):
        a, b = (180, 440) if sgn > 0 else (-440, -180)
        el.append(f'M{a} 0 V-90 H{b} V0 ' + ' '.join(f'M{x} -90 v-16 h12 v16' for x in range(min(a, b), max(a, b) - 24, 24)))
    el.append(' '.join(f'M{x} 0 V-120 L{x + 8} -150 L{x + 16} -120' for x in (-400, -372)))
    return el


@site('baalbek', 'BAALBEK', 'LEBANON', 840, 540, 36.20, 34.00, 'BAALBEK')
def baalbek():
    el = ['M-380 0 V-110 H380 V0 M-380 -55 H380 ' + ' '.join(f'M{x} 0 V-110' for x in range(-330, 380, 110)), 'M-430 0 H430']
    for k in range(6):
        x = -225 + 90 * k
        el.append(f'M{x - 26} -110 V-460 M{x + 26} -110 V-460 M{x - 9} -114 V-455 M{x + 9} -114 V-455 M{x - 34} -460 H{x + 34} V-490 H{x - 34} Z '
                  f'M{x - 34} -490 c-14 -10 -14 -26 0 -28 M{x + 34} -490 c14 -10 14 -26 0 -28')
    el.append('M-260 -496 H260 V-540 H-260 Z M-260 -518 H260 ' + ' '.join(f'M{x} -496 V-540' for x in range(-240, 260, 40)))
    el.append('M300 0 V-60 H360 V0 M300 -20 H360')
    return el


@site('palmyra', 'PALMYRA', 'SYRIA', 1000, 300, 38.27, 34.55, 'PALMYRA')
def palmyra():
    el = ['M-190 0 V-290 H190 V0 M-190 -270 H190 M-60 0 V-170 A60 60 0 0 1 60 -170 V0 M-155 0 V-115 A35 35 0 0 1 -85 -115 V0 M85 0 V-115 A35 35 0 0 1 155 -115 V0',
          ' '.join(f'M{x} -270 V-290 M{x - 9} -290 h18' for x in range(-170, 180, 34))]
    for sgn in (-1, 1):
        for k in range(5):
            x = sgn * (260 + 62 * k)
            h = 260 - 12 * k
            top = h if not (k == 2 or k == 4) else h - 60
            el.append(f'M{x - 15} 0 V{-top} M{x + 15} 0 V{-top}' + (f' M{x - 22} {-top} H{x + 22} V{-top - 16} H{x - 22} Z' if top == h else f' M{x - 15} {-top} L{x - 4} {-top - 12} L{x + 15} {-top}'))
    el.append('M-540 0 H540')
    return el


@site('ephesus', 'LIBRARY OF CELSUS', 'EPHESUS · TURKIYE', 620, 330, 27.34, 37.94, 'EPHESUS')
def ephesus():
    xs = [-245 + 70 * i for i in range(8)]
    el = ['M-300 0 H300 V-30 H-300 Z M-300 -30 H300 M-290 -40 H290']
    el.append(' '.join(f'M{x - 7} -40 V-150 M{x + 7} -40 V-150 M{x - 12} -150 H{x + 12}' for x in xs))
    el.append(' '.join(f'M{x - 20} -42 V-120 H{x + 20} V-42' for x in (-140, 0, 140)))
    el.append('M-290 -150 H290 V-168 H-290 Z')
    el.append(' '.join(f'M{x - 7} -168 V-262 M{x + 7} -168 V-262 M{x - 12} -262 H{x + 12}' for x in xs))
    el.append(' '.join(f'M{x - 17} -172 V-232 H{x + 17} V-172 M{x - 17} -232 a17 17 0 0 1 34 0' for x in (-210, -70, 70, 210)))
    el.append('M-290 -262 H290 V-280 H-290 Z M-175 -280 L-140 -312 L-105 -280 M-35 -280 a35 35 0 0 1 70 0 M105 -280 L140 -312 L175 -280')
    return el


@site('pamukkale', 'PAMUKKALE', 'HIERAPOLIS · TURKIYE', 780, 520, 29.12, 37.92, 'PAMUKKALE')
def pamukkale():
    el = []
    for i in range(6):
        w = 760 - i * 70
        y = -60 - i * 62
        n = int(w / 76)
        x0 = -w / 2
        el.append(f'M{f(x0)} {y} ' + ' '.join('a38 20 0 0 0 76 0' for _ in range(n)))
        el.append(' '.join(f'M{f(x0 + 76 * k)} {y} v{22 + (k * 7) % 14}' for k in range(1, n)))
    el.append(' '.join(f'M{x} -372 V-440 M{x - 9} -440 h18' for x in (-300, -260, -220, -140)))
    el.append('M-390 0 C-380 -150 -350 -300 -300 -372 M390 0 C380 -150 350 -300 300 -372 M-300 -372 H300')
    el.append('M-380 0 H380 M-380 -20 q40 -14 80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0')
    return el


@site('cappadocia', 'CAPPADOCIA', 'GOREME · TURKIYE', 1560, 450, 34.83, 38.64, 'CAPPADOCIA')
def cappadocia():
    return WS.cappadocia()


@site('nemrut', 'MOUNT NEMRUT', 'ADIYAMAN · TURKIYE', 800, 420, 38.74, 37.98, 'NEMRUT')
def nemrut():
    el = ['M-440 0 C-400 -40 -380 -90 -350 -150 M440 0 C400 -40 380 -90 350 -150']
    for x in (-300, -150, 0, 150, 300):
        el.append(f'M{x - 46} 0 V-130 H{x + 46} V0 M{x - 46} -130 L{x - 38} -204 H{x + 38} L{x + 46} -130 M{x - 60} -50 H{x + 60}')
        el.append(f'M{x - 32} -204 V-262 C{x - 32} -318 {x + 32} -318 {x + 32} -262 V-204 M{x - 34} -300 L{x} -352 L{x + 34} -300 M{x - 16} -262 h10 M{x + 6} -262 h10 M{x} -256 v14 M{x - 12} -222 h24')
    el.append('M-420 0 H430 M-350 -20 L-330 -30 L-300 -18')
    return el


@site('ur', 'ZIGGURAT OF UR', 'IRAQ', 680, 420, 46.10, 30.96, 'UR')
def ur():
    el = ['M-320 0 V-120 H320 V0 M-320 -120 L-300 -134 H300 L320 -120', 'M-220 -134 V-244 H220 V-134 M-210 -244 L-200 -258 H200 L210 -244',
          'M-130 -258 V-352 H130 V-258 M-140 -352 H140 M-60 -352 V-400 H60 V-352 M-70 -400 H70']
    el.append('M-110 0 L-40 -134 H40 L110 0 M-60 0 L-24 -134 M0 0 V-134 M60 0 L24 -134 ' + ' '.join(f'M{-110 + 5 * k} {-k * 14} H{110 - 5 * k}' for k in range(1, 9)))
    el.append(' '.join(f'M{x} -20 V-110' for x in (-260, -200, 200, 260)))
    el.append('M-380 0 H380')
    return el


@site('persepolis', 'PERSEPOLIS', 'IRAN', 700, 480, 52.89, 29.93, 'PERSEPOLIS')
def persepolis():
    el = ['M-360 0 V-40 H360 V0 M-340 -40 V-60 H340 V-40']
    for x in (-240, -80, 80, 240):
        el.append(f'M{x - 22} -60 V-330 M{x + 22} -60 V-330 ' + ' '.join(f'M{x + d} -64 V-326' for d in (-8, 0, 8)) + f' M{x - 28} -330 H{x + 28} V-346 H{x - 28} Z')
        el.append(f'M{x - 30} -346 c-18 -4 -18 -26 0 -28 M{x + 30} -346 c18 -4 18 -26 0 -28 M{x - 30} -374 H{x + 30} '
                  f'M{x - 56} -374 C{x - 76} -400 {x - 60} -430 {x - 34} -420 L{x - 24} -374 M{x + 56} -374 C{x + 76} -400 {x + 60} -430 {x + 34} -420 L{x + 24} -374 '
                  f'M{x - 40} -416 q-10 -22 -22 -14 M{x + 40} -416 q10 -22 22 -14')
    return el


@site('isfahan', 'SHAH MOSQUE', 'ISFAHAN · IRAN', 700, 520, 51.68, 32.66, 'ISFAHAN')
def isfahan():
    el = ['M-170 0 V-330 H170 V0 M-170 -330 L-150 -350 H150 L170 -330']
    el.append('M-90 0 V-200 C-90 -300 90 -300 90 -200 V0 M-60 0 V-190 C-60 -260 60 -260 60 -190 V0')
    el.append(' '.join(gwin(x, yb, 16, 30) for yb in (-270, -300) for x in (-60, -30, 0, 30, 60)))
    el.append('M-90 -330 C-150 -420 -90 -520 0 -520 C90 -520 150 -420 90 -330 M0 -520 V-550 M-120 -420 H120')
    for sgn in (-1, 1):
        x = sgn * 220
        el.append(f'M{x - 14} 0 V-400 M{x + 14} 0 V-400 M{x - 20} -300 H{x + 20} M{x - 14} -400 H{x + 14} L{x} -450 Z M{x - 18} -300 V-316 H{x + 18} V-300 ' + ' '.join(f'M{x - 14} {y} L{x + 14} {y - 10}' for y in (-60, -120, -180, -240)))
    el.append('M-260 0 H260')
    return el


@site('hegra', 'HEGRA', 'AL-ULA · SAUDI ARABIA', 800, 430, 37.95, 26.79, 'HEGRA')
def hegra():
    rnd = random.Random(4)
    el = ['M-400 0 C-380 -60 -350 -160 -300 -190 C-250 -200 -200 -150 -190 -60 L-170 0', 'M170 0 C190 -80 220 -170 280 -200 C340 -190 370 -100 400 0']
    el.append('M-150 0 L-140 -330 L-120 -420 L-60 -440 L40 -432 L110 -420 L140 -340 L150 0')
    el.append('M-110 0 V-250 H110 V0 M-110 -250 H110 M-120 -270 H120 M-110 -290 H110 V-310 H-110 Z ' + ' '.join(f'M{x - 7} -250 V-290 M{x + 7} -250 V-290' for x in (-90, 90)))
    el.append('M-34 0 V-150 H34 V0 M-34 -150 H34 M-24 -170 H24 V-216 H-24 Z M-110 -310 l8 -14 h14 l8 -14 h14 M110 -310 l-8 -14 h-14 l-8 -14 h-14')
    el.append('M-420 0 H420')
    return el


@site('abudhabi', 'SHEIKH ZAYED MOSQUE', 'ABU DHABI · UAE', 1000, 480, 54.47, 24.41, 'ABU DHABI')
def abudhabi():
    el = ['M-440 0 V-120 H440 V0 M-440 -120 H440 ' + poly_arches([x for x in range(-400, 410, 50)], -2, 34, 90) + ' M-480 0 H480']
    el.append('M-150 -120 V-190 H150 V-120 M-150 -190 C-150 -380 150 -380 150 -190 M0 -366 V-410 M-8 -416 a8 8 0 1 0 16 0 ' + ' '.join(f'M{x} -190 C{x * .7:.0f} -280 {x * .35:.0f} -340 0 -366' for x in (-110, -60, 60, 110)))
    for sgn in (-1, 1):
        for x, r in ((250, 70), (360, 52)):
            cx = sgn * x
            el.append(f'M{cx - r} -120 V-150 H{cx + r} V-120 M{cx - r} -150 C{cx - r} {-150 - r * 2} {cx + r} {-150 - r * 2} {cx + r} -150 M{cx} {-150 - r * 1.5} V{-150 - r * 1.5 - 20}')
        mx = sgn * 470
        el.append(f'M{mx - 10} 0 V-330 M{mx + 10} 0 V-330 M{mx - 16} -250 H{mx + 16} M{mx - 10} -330 C{mx - 10} -350 {mx + 10} -350 {mx + 10} -330 M{mx} -350 V-372')
    el.append(waves(-500, 500, 0, 40, 6))
    return el


@site('burj', 'BURJ KHALIFA', 'DUBAI · UAE', 860, 720, 55.27, 25.20, 'DUBAI')
def burj():
    tiers = [(70, 0, -80), (60, -80, -170), (50, -170, -270), (42, -270, -370), (34, -370, -470), (26, -470, -560), (18, -560, -620)]
    left = f'M{-tiers[0][0]} 0 ' + ' '.join(f'V{t[2]} H{-(tiers[i + 1][0] if i + 1 < len(tiers) else 6)}' for i, t in enumerate(tiers))
    right = ' '.join(f'V{t[2]} H{(tiers[i + 1][0] if i + 1 < len(tiers) else 6)}' for i, t in enumerate(tiers))
    el = [f'M{-tiers[0][0]} 0 ' + ' '.join(f'V{t[2]} H{-(tiers[i + 1][0] if i + 1 < len(tiers) else 6)}' for i, t in enumerate(tiers)) + ' L0 -740 L6 -620',
          'M70 0 ' + ' '.join(f'V{t[2]} H{(tiers[i + 1][0] if i + 1 < len(tiers) else 6)}' for i, t in enumerate(tiers)) + ' L0 -740']
    el.append(' '.join(f'M{x} -8 V-600' for x in (-20, 0, 20)) + ' M0 -620 V-740')
    rnd = random.Random(2)
    sk = ''
    for sgn in (-1, 1):
        x = 130
        while x < 430:
            w = rnd.randint(34, 56)
            h = rnd.randint(70, 250)
            sk += f'M{sgn * x} 0 V{-h} H{sgn * (x + w)} V0 '
            x += w + 6
    el.append(sk)
    el.append(waves(-440, 440, 0, 40, 6))
    return el


@site('meteora', 'METEORA', 'THESSALY · GREECE', 860, 640, 21.63, 39.72, 'METEORA')
def meteora():
    rnd = random.Random(6)
    el = []

    def pillar(cx, bw, tw, h):
        L = [(cx - bw / 2, 0), (cx - bw * .46, -h * .35), (cx - tw / 2 - 10, -h * .8), (cx - tw / 2, -h)]
        R = [(cx + bw / 2, 0), (cx + bw * .46, -h * .35), (cx + tw / 2 + 10, -h * .8), (cx + tw / 2, -h)]
        top = [(cx - tw / 2, -h), (cx - tw * .2, -h - rnd.randint(4, 12)), (cx + tw * .2, -h - rnd.randint(2, 10)), (cx + tw / 2, -h)]
        return P(L) + ' ' + P(R) + ' ' + P(top)
    spec = [(-330, 190, 120, 470), (-100, 160, 100, 360), (140, 210, 130, 520), (360, 170, 110, 330)]
    for cx, bw, tw, h in spec:
        el.append(pillar(cx, bw, tw, h))
        el.append(' '.join(f'M{cx + d * bw * .3:.0f} {-h * .1:.0f} L{cx + d * tw * .3:.0f} {-h * .92:.0f}' for d in (-1, 0, 1)))
    for cx, h, tw in ((-330, 470, 120), (140, 520, 130), (360, 330, 110)):
        el.append(f'M{cx - 46} {-h} V{-h - 46} H{cx + 46} V{-h} M{cx - 54} {-h - 46} L{cx} {-h - 84} L{cx + 54} {-h - 46} M{cx + 18} {-h - 46} V{-h - 76} H{cx + 38} V{-h - 46} ' + ' '.join(rwin(cx + d, -h - 4, 8, 20) for d in (-26, -4)))
    el.append('M-440 0 Q-300 -30 -120 -6 T200 -10 T440 0')
    return el
