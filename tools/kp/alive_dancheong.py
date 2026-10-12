"""07 단청문양 - dynamic versions (dancheong colours: blue / red / yellow / white / green)"""
import math
from core import *
from alive import alive_svg, piv, grp

DB, DR, DY, DW, DG = BLUE, RED, YELLOW, WHITE, GREEN


def meoricho():
    def band(r, n, col):
        s = ''
        for i in range(n):
            a0, a1 = (i - .5) * 360 / n, (i + .5) * 360 / n
            x0, y0 = pt(r, a0)
            x1, y1 = pt(r, a1)
            s += P(f"M{f(x0)} {f(y0)} A{r} {r} 0 0 1 {f(x1)} {f(y1)}", col[0], 4)
            xm, ym = pt(r - 9, i * 360 / n)
            s += grp('a-tw', DOT(xm, ym, WHITE[0], 6), f'animation-delay:{i * .2:.2f}s')
        return s
    bands = grp('a-b1', band(86, 16, GREEN)) + grp('a-b2', band(68, 14, BLUE)) + grp('a-b3', band(50, 12, YELLOW))
    bud = around(8, lambda k: PL(drop(30, 11, r0=10), RED, 3.8)) + P(circle(10), WHITE[0], 3.4) + DOT(0, 0, YELLOW[0], 7)
    leaves = around(8, lambda k: P(lens(14, 4, r0=38), WHITE[0], 2.4), start=22.5)
    css = '''.a-b1{animation:spin 50s linear infinite}
.a-b2{animation:spinr 36s linear infinite}
.a-b3{animation:spin 24s linear infinite}
.a-bud{animation:bud 2.6s ease-in-out infinite}
.a-tw{animation:glow 1.4s ease-in-out infinite alternate}
@keyframes bud{0%,100%{transform:scale(1)}50%{transform:scale(1.14)}}'''
    return alive_svg(bands + grp('a-bud', bud) + leaves, 'Meoricho - alive', css, bg=('#0c3a2c', '#021410'), fr=('dancheong', None), flycol='#d4fff0')


def geummun():
    sq = lambda r, off, col, w: P(poly([pt(r, a + off) for a in range(0, 360, 90)], True), col[0], w)
    layers = (grp('a-q1', sq(94, 0, RED, 4.2) + sq(94, 45, BLUE, 4.2)) + grp('a-q2', sq(66, 0, YELLOW, 4) + sq(66, 45, GREEN, 4))
              + grp('a-q3', sq(40, 0, WHITE, 3.4)) + grp('a-q4', around(8, lambda k: P(circle(7, 0, -80), WHITE[0], 2.6)) + around(8, lambda k: DOT(0, -54, YELLOW[1], 6), start=22.5)))
    core = P(circle(14), RED[0], 3.6) + grp('a-pulse', DOT(0, 0, RED[1], 8))
    css = '''.a-q1{animation:spin 40s linear infinite}
.a-q2{animation:spinr 28s linear infinite}
.a-q3{animation:spin 16s linear infinite}
.a-q4{animation:spinr 55s linear infinite}
.a-hue{animation:hue 12s linear infinite}
.a-pulse{animation:glow 1.2s ease-in-out infinite alternate}
@keyframes hue{to{filter:hue-rotate(360deg)}}'''
    return alive_svg(grp('a-hue', layers + core), 'Geummun - alive', css, bg=('#10285a', '#03060f'), fr=('octagon', GOLD), flycol='#c2e0ff')


def yeonhwa():
    s = ''
    for k, (ln, w, r0, col, w2) in enumerate(((78, 28, 24, BLUE, 4.2), (56, 19, 28, RED, 3.8), (34, 11, 32, YELLOW, 3.4))):
        s += grp(f'a-pl{k}', around(8, lambda i, ln=ln, w=w, r0=r0, col=col, w2=w2: P(drop(ln, w, r0=r0), col[0], w2) + (P("M0 -34 L0 -60", WHITE[0], 2) if k == 1 else '')))
    s += around(8, lambda k: P(lens(30, 6, r0=34), GREEN[0], 3), start=22.5)
    s += grp('a-seed', P(circle(18), YELLOW[0], 3.8) + P(circle(9), WHITE[0], 2.6))
    css = '''.a-pl0{animation:wave 3.2s ease-in-out infinite}
.a-pl1{animation:wave 3.2s ease-in-out infinite .35s}
.a-pl2{animation:wave 3.2s ease-in-out infinite .7s}
.a-seed{animation:glow 1.6s ease-in-out infinite alternate}
@keyframes wave{0%,100%{transform:scale(1) rotate(0)}50%{transform:scale(1.1) rotate(6deg)}}'''
    return alive_svg(grp('a-slow', s), 'Dancheong lotus - alive', css + '\n.a-slow{animation:spin 80s linear infinite}', bg=('#3a0a14', '#0f0205'), fr=('dancheong', None), flycol='#ffd1e6')


def bosanghwa():
    petals = around(8, lambda k: P(drop(70, 26, r0=24), RED[0], 4.2) + P(drop(40, 14, r0=34), BLUE[0], 3.4))
    curls = ''.join(G(f"rotate({k * 45})", G("translate(0 -56)", grp('a-curl', P(spiral(0, 0, 11, 2.5, 1.6, a0=-90), WHITE[0], 3)))) for k in range(8))
    leaves = ''.join(G(f"rotate({22.5 + k * 45})", piv('a-sway', 0, -40, P(lens(36, 7, r0=40), GREEN[0], 3.4) + P(spiral(0, -86, 6, 1.5, 1.4), WHITE[0], 2.4), f'animation-delay:{k * .15:.2f}s')) for k in range(8))
    core = P(circle(18), YELLOW[0], 3.8) + P(circle(9), YELLOW[1], 2.2) + grp('a-pulse', DOT(0, 0, WHITE[0], 6))
    css = '''.a-curl{animation:spin 4s linear infinite}
.a-sway{animation:sway 2.4s ease-in-out infinite alternate}
.a-pulse{animation:glow 1.3s ease-in-out infinite alternate}
.a-turn{animation:spin 60s linear infinite}
@keyframes sway{from{transform:rotate(-6deg)}to{transform:rotate(6deg)}}'''
    return alive_svg(grp('a-turn', petals + curls + leaves) + core, 'Dancheong bosanghwa - alive', css, bg=('#0a2a3a', '#02080f'), fr=('petal', RED), flycol='#ffd1e6')


DANCHEONG = {'meoricho': meoricho, 'geummun': geummun, 'yeonhwa-dancheong': yeonhwa, 'bosanghwa-dancheong': bosanghwa}
