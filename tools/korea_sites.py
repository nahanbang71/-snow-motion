"""Third film: Korea only. 20 landmarks as laser elevations (base y=0, up is negative). Registry KR."""
import math
import random

from europe_kit import P, arc_pts, arch_pts, catmull, f, poly_arches
from europe_sites import RECT, crenel, gwin, rwin, waves

KR = {}


def site(id, name, sub, w, h, lon, lat, label):
    def deco(fn):
        KR[id] = dict(name=name, country=sub, w=w, h=h, el=fn, lon=lon, lat=lat, label=label)
        return fn
    return deco


def circ(cx, cy, r):
    return f'M{f(cx - r)} {f(cy)} a{r} {r} 0 1 0 {2 * r} 0 a{r} {r} 0 1 0 {-2 * r} 0'


def roof(cx, yb, w, h, ov=34, rise=16):
    """hanok hip-and-gable roof with up-turned eaves; yb = eave line; returns list of paths"""
    x0, x1 = cx - w / 2, cx + w / 2
    top = [f'M{f(x0 - ov)} {f(yb - rise)} Q{f(x0 - ov * .35)} {f(yb + 4)} {f(x0 + 8)} {f(yb)} L{f(cx - w * .27)} {f(yb - h)} H{f(cx + w * .27)} L{f(x1 - 8)} {f(yb)} Q{f(x1 + ov * .35)} {f(yb + 4)} {f(x1 + ov)} {f(yb - rise)}']
    under = [f'M{f(x0 + 8)} {f(yb)} H{f(x1 - 8)}']
    tiles = ' '.join(f'M{f(cx + k * w * .09)} {f(yb - h)} L{f(cx + k * w * .12)} {f(yb)}' for k in range(-2, 3))
    return top + under + [tiles]


def hall(cx, yb, w, rh, ph, n=5, door=True):
    """pavilion body: pillars + roof. yb = floor level, ph = pillar height, rh = roof height"""
    el = []
    el += roof(cx, yb - ph, w, rh)
    xs = [cx - w / 2 + 14 + i * (w - 28) / (n - 1) for i in range(n)]
    el.append(' '.join(f'M{f(x)} {f(yb)} V{f(yb - ph)}' for x in xs))
    el.append(f'M{f(cx - w / 2 + 14)} {f(yb - ph * .8)} H{f(cx + w / 2 - 14)} M{f(cx - w / 2 + 14)} {f(yb - ph + 14)} H{f(cx + w / 2 - 14)}')
    el.append(' '.join(f'M{f(x)} {f(yb - ph + 14)} v-10 h14' for x in xs[:-1]))
    if door:
        for i in range(n - 1):
            xm = (xs[i] + xs[i + 1]) / 2
            el.append(f'M{f(xm - 16)} {f(yb)} V{f(yb - ph * .66)} H{f(xm + 16)} V{f(yb)} M{f(xm)} {f(yb)} V{f(yb - ph * .66)} M{f(xm - 16)} {f(yb - ph * .33)} H{f(xm + 16)}')
    return el


# ---------------------------------------------------------------- Seoul
@site('geunjeong', 'GEUNJEONGJEON', 'GYEONGBOKGUNG · SEOUL', 880, 470, 126.977, 37.580, 'GYEONGBOKGUNG')
def geunjeong():
    el = ['M-400 0 H400 M-380 -26 H380 V0 M-350 -52 H350 V-26 M-330 -52 H330', 'M-60 0 L-48 -26 H48 L60 0 M-60 -26 L-48 -52 H48 L60 -26 M-26 0 V-52']
    el.append(' '.join(f'M{x} -26 v-26 M{x - 6} -52 h12' for x in range(-340, 341, 40) if abs(x) > 80))
    el += hall(0, -52, 600, 78, 72, 7)
    el += roof(0, -190, 440, 66)
    el.append(' '.join(f'M{x} -124 V-190' for x in (-160, -80, 0, 80, 160)) + ' M-210 -150 H210')
    el.append('M-20 -256 L0 -276 L20 -256')
    return el


@site('namsan', 'N SEOUL TOWER', 'NAMSAN · SEOUL', 560, 780, 126.988, 37.551, 'N SEOUL TOWER')
def namsan():
    el = ['M-280 0 C-230 -40 -150 -90 -60 -110 H60 C150 -90 230 -40 280 0 M-280 0 H280']
    el.append('M-16 -110 L-12 -300 M16 -110 L12 -300 M-12 -300 H12')
    el.append('M-44 -300 L-14 -320 H14 L44 -300 L36 -276 H-36 Z M-52 -324 H52 L60 -340 H-60 Z M-60 -340 L-46 -372 H46 L60 -340 M-46 -372 H46')
    el.append('M-44 -300 H44 M-30 -276 L-20 -300 M30 -276 L20 -300 M-30 -340 V-324 M-10 -340 V-324 M10 -340 V-324 M30 -340 V-324')
    el.append('M-8 -372 V-640 M8 -372 V-640 M-8 -640 L0 -660 L8 -640 M-8 -420 H8 M-8 -480 H8 M-8 -540 H8 M-8 -600 H8')
    el.append('M-150 -60 q20 -40 36 -12 M110 -64 q24 -34 40 -6 M-100 -34 l0 -22 M-92 -34 l0 -22')
    return el


# ---------------------------------------------------------------- Gyeonggi / Incheon
@site('hwaseong', 'HWASEONG FORTRESS', 'PALDALMUN · SUWON', 1000, 440, 127.010, 37.286, 'SUWON')
def hwaseong():
    el = ['M-500 0 V-120 H-230 M230 -120 H500 V0 M-500 0 H500', crenel(-500, -230, -120, 20, 22), crenel(230, 500, -120, 20, 22)]
    el.append('M-230 0 V-170 H230 V0 M-230 -170 L-210 -190 H210 L230 -170')
    el.append(' '.join(f'M{x} -170 v-12 h14 v12' for x in range(-200, 200, 50)))
    el.append('M-90 0 V-80 C-90 -140 90 -140 90 -80 V0 M-60 0 V-70 C-60 -112 60 -112 60 -70 V0')
    el += hall(0, -190, 330, 80, 70, 5)
    el += roof(0, -330, 230, 60)
    el.append(' '.join(f'M{x} -260 V-330' for x in (-80, 0, 80)))
    el.append(' '.join(f'M{x} {y} h46 v-26 h-46 Z' for x, y in ((-440, -150), (-360, -150), (360, -150), (430, -150))))
    return el


@site('ganghwa', 'GANGHWA DOLMEN', 'GOCHANG-RI · INCHEON', 720, 400, 126.430, 37.730, 'GANGHWA')
def ganghwa():
    el = ['M-330 -190 C-300 -300 -160 -340 20 -336 C190 -332 300 -300 340 -210 C250 -170 -200 -160 -330 -190 Z']
    el.append('M-250 -195 L-230 -60 L-170 0 H-110 L-95 -170 M170 -178 L190 -60 L230 0 H290 L300 -205')
    el.append('M-110 0 H170 M-60 -120 q40 -34 90 -6 M-120 -250 q80 -30 150 -10 M40 -270 q60 -20 110 4')
    el.append(' '.join(f'M{x} 0 q6 -22 14 -2 M{x + 12} 0 q6 -14 12 0' for x in (-340, -300, 330, 360)))
    el.append('M-380 0 H400')
    return el


@site('imjingak', 'FREEDOM BRIDGE', 'IMJINGAK · PAJU', 1000, 320, 126.740, 37.890, 'IMJINGAK')
def imjingak():
    el = ['M-480 0 H480 M-480 -26 H480']
    el.append('M-440 -26 V-190 H440 V-26')
    xs = list(range(-440, 441, 88))
    el.append(' '.join(f'M{x} -26 V-190' for x in xs))
    el.append(' '.join(f'M{xs[i]} -26 L{xs[i + 1]} -190' if i % 2 == 0 else f'M{xs[i]} -190 L{xs[i + 1]} -26' for i in range(len(xs) - 1)))
    el.append('M-440 -190 H440 M-440 -150 H440')
    el.append(' '.join(f'M{x} -190 v-18' for x in range(-440, 441, 22)))
    el.append(' '.join(f'M{x} 0 V-60 M{x - 8} -60 h16' for x in (-480, 480)))
    el.append(' '.join(f'M{x} -226 q10 20 -4 44 q18 -10 4 -44' for x in (-300, -120, 90, 280)))
    return el


# ---------------------------------------------------------------- Gangwon / Gyeongbuk
@site('ulsan', 'ULSANBAWI', 'SEORAKSAN · GANGWON', 900, 700, 128.430, 38.120, 'SEORAKSAN')
def ulsan():
    pts = [(-430, 0), (-400, -130), (-350, -170), (-330, -300), (-280, -330), (-250, -460), (-200, -430), (-170, -560), (-110, -600), (-80, -520), (-40, -640), (20, -690),
           (60, -600), (110, -640), (150, -520), (200, -560), (230, -420), (290, -400), (320, -250), (370, -230), (400, -110), (430, 0)]
    el = [P(pts)]
    el.append('M-250 -460 L-240 -300 L-290 -250 M-170 -560 L-150 -380 M-40 -640 L-30 -440 L-70 -380 M60 -600 L80 -420 M150 -520 L170 -330 L130 -260 M230 -420 L240 -280')
    el.append('M-430 0 H430 M-330 -300 L-300 -270 M200 -560 L220 -500 M-110 -600 L-90 -540')
    el.append('M-380 -26 q10 -30 22 -4 M-370 -26 v-14 M-340 -26 q10 -36 24 -4 M300 -26 q10 -30 22 -4')
    return el


@site('hahoe', 'HAHOE VILLAGE', 'ANDONG · GYEONGBUK', 920, 400, 128.520, 36.540, 'ANDONG')
def hahoe():
    el = []
    for cx, yb, w, h in ((-300, -20, 190, 100), (-60, -50, 210, 112), (210, -24, 200, 106)):
        el.append(f'M{cx - w / 2} {yb} V{yb - 62} H{cx + w / 2} V{yb} M{cx - w / 2 - 14} {yb - 62} C{cx - w * .4} {yb - 62 - h} {cx + w * .4} {yb - 62 - h} {cx + w / 2 + 14} {yb - 62}')
        el.append(f'M{cx - w / 2 + 10} {yb - 62} C{cx - w * .3} {yb - 62 - h * .6} {cx + w * .3} {yb - 62 - h * .6} {cx + w / 2 - 10} {yb - 62} '
                  + ' '.join(f'M{cx + k * 28} {yb - 62 - h * .72 + abs(k) * 6} v{h * .36}' for k in range(-3, 4)))
        el.append(f'M{cx - 26} {yb} V{yb - 46} H{cx + 26} V{yb} M{cx} {yb} V{yb - 46} M{cx - w / 2 + 14} {yb - 20} h30 v-24 h-30 Z')
        el.append(f'M{cx + w / 2 - 36} {yb - 62 - h * .5} v-36 h14 v36')
    el.append('M-440 0 H440 M-440 -20 H-400 M-210 -20 H-160 M60 -24 H120 M330 -24 H440')
    el.append('M380 -24 V-170 M380 -110 L330 -150 M380 -130 L430 -166 M380 -90 L340 -124 M380 -160 q-40 -26 -70 -10 M380 -160 q40 -26 70 -10')
    el.append('M-440 14 C-300 40 -140 -6 0 24 S320 6 440 24')
    return el


@site('haeinsa', 'HAEINSA', 'JANGGYEONG PANJEON · GYEONGNAM', 940, 380, 128.100, 35.800, 'HAEINSA')
def haeinsa():
    el = ['M-460 0 H460 M-440 -30 H440 V0 M-420 -56 H420 V-30']
    el += roof(-210, -56, 380, 56, 30, 12) + roof(210, -56, 380, 56, 30, 12)
    for cx in (-210, 210):
        el.append(f'M{cx - 170} -56 V-170 H{cx + 170} V-56')
        el.append(' '.join(f'M{cx + k * 42} -56 V-170' for k in range(-3, 4)))
        el.append(' '.join(f'M{cx + k * 42 - 15} -76 h30 v62 h-30 Z M{cx + k * 42 - 15} -106 h30 M{cx + k * 42 - 15} -136 h30' for k in (-3, -1, 1, 3)))
    el += roof(0, -170, 640, 70, 36, 14)
    el.append('M-20 0 V-30 M20 0 V-30')
    el.append('M-300 -240 V-300 M300 -240 V-300 M-320 -300 H-280 M280 -300 H320')
    return el


@site('bulguksa', 'BULGUKSA', 'DABOTAP · SEOKGATAP · GYEONGJU', 920, 540, 129.330, 35.790, 'BULGUKSA')
def bulguksa():
    el = ['M-460 0 H460 M-440 -34 H440 V0 M-420 -68 H420 V-34 M-40 0 V-34 M40 0 V-34 M-40 -34 V-68 M40 -34 V-68']
    el.append(' '.join(f'M{x} -34 L{x + 8} -68' for x in range(-400, 401, 40) if abs(x) > 60))
    # Seokgatap
    el.append('M-340 -68 H-130 M-320 -68 V-92 H-150 V-68 M-310 -92 V-100 H-160 V-92')
    for y0, ww in ((-100, 120), (-210, 100), (-310, 80)):
        c = -235
        el.append(f'M{c - ww / 2 - 20} {y0 - 8} L{c - ww / 2} {y0 - 14} H{c + ww / 2} L{c + ww / 2 + 20} {y0 - 8} M{c - ww / 2 + 4} {y0 - 14} V{y0 - 70} H{c + ww / 2 - 4} V{y0 - 14}')
    el.append('M-262 -390 H-208 M-235 -390 V-452 M-244 -420 H-226 M-240 -436 H-230')
    # Dabotap
    el.append('M130 -68 H340 M150 -68 V-100 H320 V-68 M142 -100 H328')
    el.append('M170 -100 V-166 H300 V-100 M160 -166 L170 -178 H300 L310 -166 M150 -166 H320')
    el.append(' '.join(f'M{x} -100 V-166' for x in (200, 235, 270)))
    el.append('M190 -178 L200 -204 H270 L280 -178 M200 -204 L206 -220 H264 L270 -204')
    el.append('M200 -220 q35 -34 70 0 M196 -220 H274 M180 -226 q55 -50 110 0')
    el.append('M215 -246 q20 -26 40 0 M235 -246 V-274 M225 -274 H245 M230 -282 H240 M235 -282 V-310')
    return el


@site('cheomseongdae', 'CHEOMSEONGDAE', 'GYEONGJU', 560, 580, 129.220, 35.830, 'GYEONGJU')
def cheomseongdae():
    el = ['M-170 0 H170 M-150 -26 H150 V0 M-150 -26 L-130 -50 H130 L150 -26']
    prof = [(-110, -50), (-102, -120), (-84, -210), (-66, -290), (-58, -330), (-70, -380), (-90, -420), (-96, -440), (96, -440), (90, -420), (70, -380), (58, -330), (66, -290), (84, -210), (102, -120), (110, -50)]
    el.append(P(prof[:8]) + ' ' + 'M' + ' L'.join(f'{f(x)} {f(y)}' for x, y in prof[8:]))
    for k in range(1, 13):
        y = -50 - k * 29
        pf = lambda y: 110 - (110 - 58) * min(1, max(0, (y + 50) / -280)) if y > -330 else 58 + (96 - 58) * min(1, (-330 - y) / 110)
        w = pf(y) * (1 if y > -440 else 1)
        el.append(f'M{-w:.0f} {y} H{w:.0f}')
    el.append(circ(0, -208, 24) + ' M-24 -208 H24')
    el.append('M-96 -440 H96 M-100 -456 H100 M-100 -472 H100 M-96 -440 L-100 -456 M96 -440 L100 -456')
    el.append('M-86 -440 V-410 M86 -440 V-410 M-50 -472 V-500 M50 -472 V-500')
    return el


# ---------------------------------------------------------------- Jeolla / Chungnam
@site('jeonju', 'JEONJU HANOK', 'PUNGNAMMUN · JEONJU', 960, 460, 127.150, 35.820, 'JEONJU')
def jeonju():
    el = ['M-480 0 H480']
    el += hall(0, -110, 400, 80, 76, 5)
    el += roof(0, -276, 320, 62)
    el.append(' '.join(f'M{x} -190 V-276' for x in (-120, -40, 40, 120)) + ' M-150 -240 H150')
    el.append('M-230 0 V-110 H230 V0 M-230 -110 L-210 -122 H210 L230 -110 M-70 0 V-60 C-70 -112 70 -112 70 -60 V0')
    for cx in (-370, 370):
        el += roof(cx, -90, 180, 54, 28, 12)
        el.append(f'M{cx - 80} -90 V0 M{cx + 80} -90 V0 M{cx - 50} 0 V-60 H{cx + 50} V0 M{cx} 0 V-60')
    el.append('M-480 -20 H-460 M460 -20 H480')
    return el


@site('gongsan', 'GONGSANSEONG', 'GONGJU · CHUNGNAM', 960, 440, 127.120, 36.460, 'GONGJU')
def gongsan():
    el = ['M-480 0 C-420 -50 -300 -90 -150 -110 L150 -150 C300 -170 420 -150 480 -100']
    el.append('M-480 0 H480')
    el.append(crenel(-340, -150, -92, 14, 20))
    el.append('M-150 -110 V-200 M-150 -200 H80 V-168 M-100 -128 V-210 M80 -144 V-200')
    el += roof(-20, -200, 280, 64, 30, 12)
    el.append(' '.join(f'M{x} -200 V-134' for x in (-140, -80, -20, 40, 100)) + ' M-150 -170 H110')
    el.append('M-50 -110 V-134 H10 V-110')
    el.append('M200 -140 L240 -230 L280 -140 M240 -230 V-270 M230 -250 l10 -14 l10 14')
    el.append('M-330 -30 q16 -26 34 -4 M300 -60 q16 -26 34 -4')
    return el


@site('boseong', 'BOSEONG TEA FIELDS', 'DAEHAN DAEBONG · JEONNAM', 1060, 420, 127.080, 34.720, 'BOSEONG')
def boseong():
    el = ['M-520 0 C-420 -140 -300 -240 -160 -250 C-20 -260 90 -170 180 -110 C280 -150 400 -190 520 -120 L520 0 H-520']
    for k, ph in enumerate((-30, -60, -90, -120, -150, -180, -210, -235)):
        a = 400 - k * 36
        el.append(f'M{-a} {ph + 8} C{-a * .5} {ph - 28 + k * 2} {a * .3} {ph - 26 + k * 2} {a} {ph + 12}')
    el.append(' '.join(f'M{x} -250 V-300 M{x - 16} -276 L{x} -300 L{x + 16} -276 M{x - 20} -262 L{x} -300 L{x + 20} -262' for x in (-420, -390, 380, 410)))
    el.append(' '.join(f'M{x} -112 V-160 M{x - 12} -136 L{x} -160 L{x + 12} -136' for x in (330, 355, 450, 475)))
    return el


@site('suncheon', 'SUNCHEON BAY', 'REED FIELDS · JEONNAM', 960, 340, 127.510, 34.890, 'SUNCHEON')
def suncheon():
    el = ['M-480 0 H480']
    rnd = random.Random(8)
    for k in range(70):
        x = -450 + k * 13 + rnd.randint(-4, 4)
        h = rnd.randint(70, 150) * (1 if abs(x) > 80 else .5)
        el.append(f'M{x} 0 C{x + 4} {-h * .5} {x - 8} {-h * .8} {x + rnd.randint(-14, 14)} {-h}')
    el.append('M-30 0 C-14 -30 14 -30 30 0 M-70 -28 C-30 -50 30 -50 70 -28')
    el.append('M-200 -200 V-300 M-200 -260 H-120 M-120 -300 V-260 M-220 -300 H-100 L-110 -320 H-210 Z')
    el.append('M-240 -190 q50 -26 100 0 t100 0 t100 0')
    return el


# ---------------------------------------------------------------- Busan / Ulleung / Dokdo
@site('gwangan', 'GWANGAN BRIDGE', 'BUSAN', 1240, 440, 129.130, 35.150, 'BUSAN')
def gwangan():
    el = ['M-620 -70 H620 M-620 -84 H620']
    for x in (-250, 250):
        el.append(f'M{x - 10} 0 V-380 M{x + 10} 0 V-380 M{x - 10} -380 H{x + 10} M{x - 10} -300 H{x + 10} M{x - 10} -220 H{x + 10} M{x - 10} -140 H{x + 10}')
    el.append('M-250 -380 C-420 -150 -560 -90 -620 -84 M250 -380 C420 -150 560 -90 620 -84 M-250 -380 C-120 -90 120 -90 250 -380')
    el.append(' '.join(f'M{x} {-84 - ((x + 250) ** 2) / 4 / 1500 * 0 - 0} V{y}' for x, y in ((-560, -118), (-500, -150), (-440, -190), (-380, -240), (-320, -300))))
    el.append(' '.join(f'M{x} -84 V{-84 - (abs(x) * 0.0) - 20 - 28 * math.sin(math.pi * (x + 250) / 500)}' for x in range(-230, 231, 46)))
    el.append(' '.join(f'M{x} -84 V{y}' for x, y in ((560, -118), (500, -150), (440, -190), (380, -240), (320, -300))))
    el.append('M-620 -50 H620 M-620 -20 q30 -14 60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0')
    el.append(' '.join(f'M{x} -70 V0' for x in range(-560, 561, 70) if abs(abs(x) - 250) > 20))
    return el


@site('yonggung', 'HAEDONG YONGGUNGSA', 'SEASIDE TEMPLE · BUSAN', 860, 520, 129.220, 35.190, 'YONGGUNGSA')
def yonggung():
    el = ['M-430 0 C-380 -60 -300 -80 -200 -90 C-120 -100 -60 -110 0 -110 C60 -110 120 -100 200 -80 C290 -60 340 -30 430 0']
    el.append('M-430 0 H430')
    el += hall(-40, -110, 300, 70, 66, 4)
    el += roof(-40, -246, 220, 56)
    el.append(' '.join(f'M{x} -176 V-246' for x in (-120, -40, 40)))
    el += hall(240, -80, 120, 40, 44, 3, False)
    el.append('M-340 -92 L-250 -96 M-260 -100 V-130 M-340 -100 V-134 M-340 -134 H-260')
    el.append('M-340 -92 V-30')
    el.append('M-430 -20 q30 -14 60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0')
    el.append(circ(-210, -230, 20) + ' M-210 -250 V-210 M-230 -230 H-190')
    return el


@site('seongsan', 'SEONGSAN ILCHULBONG', 'JEJU', 1180, 460, 126.940, 33.460, 'JEJU')
def seongsan():
    pts = [(-540, 0), (-460, -20), (-380, -80), (-330, -160), (-300, -250), (-280, -330), (-250, -352), (-210, -332), (-180, -362), (-140, -336), (-100, -366), (-60, -340), (-20, -372), (20, -340),
           (60, -368), (100, -336), (140, -362), (180, -330), (220, -352), (260, -330), (290, -250), (330, -160), (390, -80), (470, -20), (540, 0)]
    el = [P(pts)]
    el.append('M-290 -330 L-264 -270 L-280 -200 M-180 -362 L-170 -300 M-60 -340 L-50 -270 M60 -368 L70 -300 L56 -240 M180 -330 L174 -270 M260 -330 L250 -250')
    el.append('M-460 -20 C-380 -50 -320 -60 -300 -110 M460 -20 C380 -50 320 -60 300 -110 M-540 0 H540')
    el.append('M-400 -50 C-340 -86 -300 -96 -290 -150 M400 -50 C340 -86 300 -96 290 -150')
    el.append('M-520 -14 q16 -20 34 0 M440 -12 q18 -22 38 0 M-100 -26 q16 -24 36 0')
    return el


@site('hallasan', 'HALLASAN', 'DOL HAREUBANG · JEJU', 960, 580, 126.530, 33.360, 'HALLASAN')
def hallasan():
    el = ['M-470 0 C-400 -40 -340 -170 -270 -250 C-240 -290 -220 -300 -190 -300 C-150 -300 -120 -260 -90 -210 M470 0 C400 -40 330 -120 270 -190 C225 -230 175 -215 90 -150 M-470 0 H470']
    el.append('M-290 -268 C-250 -250 -210 -250 -170 -276 M-340 -150 C-280 -170 -230 -150 -180 -190 M-400 -60 C-330 -90 -270 -80 -220 -120 M380 -60 C320 -90 280 -100 240 -130')
    # dol hareubang
    el.append('M-90 0 V-90 C-90 -150 -70 -190 -70 -230 C-70 -250 -50 -266 0 -266 C50 -266 70 -250 70 -230 C70 -190 90 -150 90 -90 V0')
    el.append('M-70 -230 C-72 -290 -50 -336 0 -336 C50 -336 72 -290 70 -230 M-84 -262 C-84 -270 -80 -290 -80 -290')
    el.append('M-76 -330 C-40 -384 40 -384 76 -330 M-60 -352 H60 M-46 -246 H46')
    el.append('M-40 -300 q-12 -14 -28 0 M40 -300 q12 -14 28 0 M-6 -290 V-262 M-14 -268 H14 M-26 -226 q26 16 52 0')
    el.append('M-70 -118 L-34 -150 L-20 -140 M70 -118 L34 -150 L20 -140')
    return el


@site('ulleung', 'ULLEUNGDO', 'EAST SEA · GYEONGBUK', 1080, 480, 130.900, 37.500, 'ULLEUNGDO')
def ulleung():
    el = ['M-500 0 C-470 -60 -420 -100 -360 -110 C-300 -190 -230 -250 -160 -280 C-100 -330 -40 -352 20 -332 C70 -352 130 -320 180 -270 C240 -240 300 -170 340 -100 C410 -90 470 -50 500 0']
    el.append('M-500 0 H500 M-160 -280 L-150 -200 L-190 -140 M20 -332 L40 -230 L8 -150 M180 -270 L170 -190 L210 -130')
    el.append('M-400 -80 C-300 -110 -240 -90 -200 -140 M300 -90 C240 -110 200 -90 170 -130')
    # squid boats with light strings
    for x in (-380, -200, 40, 260, 420):
        el.append(f'M{x - 36} -12 H{x + 36} L{x + 24} 8 H{x - 24} Z M{x} -12 V-44 M{x - 10} -36 H{x + 10}')
        el.append(' '.join(f'M{x + k * 14} -34 v10' for k in range(-2, 3)))
    el.append('M-500 20 q30 -14 60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0')
    return el


@site('dokdo', 'DOKDO', 'EAST SEA · KOREA', 960, 380, 131.870, 37.240, 'DOKDO')
def dokdo():
    el = ['M-470 0 C-440 -50 -410 -110 -370 -150 C-340 -190 -300 -200 -270 -180 C-240 -196 -210 -170 -190 -120 C-160 -90 -150 -40 -140 0']
    el.append('M170 0 C190 -60 220 -130 250 -180 C280 -230 320 -250 350 -226 C380 -240 400 -200 410 -150 C430 -120 450 -60 470 0')
    el.append('M-470 0 H470 M-370 -150 L-350 -90 L-380 -40 M-270 -180 L-264 -110 M250 -180 L262 -110 L240 -50 M350 -226 L352 -150')
    el.append('M-210 -118 V-170 M-218 -170 H-202 M-214 -184 H-206')
    el.append('M300 -240 V-290 M290 -290 H310 M296 -300 H304 M300 -300 V-320')
    el.append('M-140 6 q20 -14 40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0')
    el.append('M-480 12 q30 -14 60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0')
    return el
