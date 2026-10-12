"""06 특별묶음 - dynamic versions"""
import plants, animals, nature
from core import *
from alive import alive_svg, piv, grp


def tile(inner, x, y, sc, col=GOLD, delay=0.0, counter=None):
    t = G(f"scale({sc})", inner) + P(circle(100 * sc + 2), col[0], 1.8)
    t = grp('a-tile', t, f'animation-delay:{delay:.2f}s')
    if counter:
        t = grp(counter, t)
    return G(f"translate({f(x)} {f(y)})", t)


def sipjangsaeng():
    outer = [nature.hae, nature.san, nature.supamun, nature.bawi, nature.unmun, plants.sonamu, plants.yeongji]
    inner = [animals.geobuk, animals.hak, animals.saseum]
    o = ''.join(tile(fn(), *pt(68, k * 360 / 7), .27, delay=k * .5, counter='a-cspin') for k, fn in enumerate(outer))
    i = ''.join(tile(fn(), *pt(19, k * 120 + 60), .16, WHITE, k * .7, counter='a-cspinr') for k, fn in enumerate(inner))
    css = '''.a-ring1{animation:spin 70s linear infinite}
.a-ring2{animation:spinr 40s linear infinite}
.a-cspin{animation:spinr 70s linear infinite}
.a-cspinr{animation:spin 40s linear infinite}
.a-tile{animation:tile 3.8s ease-in-out infinite}
@keyframes tile{0%,100%{opacity:.75}50%{opacity:1}}'''
    return alive_svg(grp('a-ring1', o) + grp('a-ring2', i), 'Sipjangsaeng - alive', css, bg=('#16184a', '#04040f'), fr=('cloud', GOLD), flycol='#fff1c4')


def sagunja():
    s = ''
    for k, (fn, x, y) in enumerate(((plants.maehwa, -46, -46), (plants.nancho, 46, -46), (plants.gukhwa, -46, 46), (plants.daenamu, 46, 46))):
        s += G(f"translate({x} {y})", grp('a-breathe4', G("scale(.42)", fn()) + P(circle(44), GOLD[0], 1.8), f'animation-delay:{k * .8}s'))
    s += grp('a-spin', P(circle(8), GOLD[0], 3) + DOT(0, 0, GOLD[1], 6))
    css = '''.a-breathe4{animation:br4 3.6s ease-in-out infinite}
@keyframes br4{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}'''
    return alive_svg(s, 'Sagunja - alive', css, bg=('#102a30', '#030c10'), fr=('petal', GOLD), flycol='#d4fff0')


SPECIAL = {'sipjangsaeng': sipjangsaeng, 'sagunja': sagunja}
