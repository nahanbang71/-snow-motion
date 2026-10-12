"""06 특별묶음: 십장생 (ten symbols of longevity) and 사군자 (four gentlemen) as medallion collages"""
import plants
import animals
import nature
from core import *


def tile(inner, x, y, sc, col=GOLD):
    return G(f"translate({f(x)} {f(y)}) scale({sc})", inner) + P(circle(100 * sc + 2, x, y), col[0], 1.8)


def sipjangsaeng():
    outer = [nature.hae, nature.san, nature.supamun, nature.bawi, nature.unmun, plants.sonamu, plants.yeongji]
    inner = [animals.geobuk, animals.hak, animals.saseum]
    s = ''
    for k, fn in enumerate(outer):
        x, y = pt(66, k * 360 / 7)
        s += tile(fn(), x, y, .29)
    for k, fn in enumerate(inner):
        x, y = pt(22, k * 120 + 60)
        s += tile(fn(), x, y, .2, WHITE)
    return s


def sagunja():
    s = ''
    for fn, x, y in ((plants.maehwa, -46, -46), (plants.nancho, 46, -46), (plants.gukhwa, -46, 46), (plants.daenamu, 46, 46)):
        s += tile(fn(), x, y, .42)
    s += P(circle(8), GOLD[0], 3) + DOT(0, 0, GOLD[1], 6)
    return s


PATTERNS = {
    'sipjangsaeng': ('06_특별묶음', '십장생(10)', sipjangsaeng), 'sagunja': ('06_특별묶음', '사군자(4)', sagunja),
}
