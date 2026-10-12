"""'Alive' versions of the animal medallions: dot -> grow -> hold while the animal moves -> fly out of the screen."""
import math
import random
import re
from core import *
from animals import ring_pts, tang, fish_scales, scales

DUR = 12.0


def piv(cls, x, y, content, style=''):
    """group that animates around the pivot (x, y) of its content"""
    st = f' style="{style}"' if style else ''
    return G(f"translate({f(x)} {f(y)})", f'<g class="{cls}"{st}>' + G(f"translate({f(-x)} {f(-y)})", content) + '</g>')


def grp(cls, content, style=''):
    st = f' style="{style}"' if style else ''
    return f'<g class="{cls}"{st}>{content}</g>'


BASE_CSS = '''.l{fill:none;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}
g[class^="a-"]{transform-origin:0 0}
.a-eye{transform-box:fill-box;transform-origin:center}
.a-fb{transform-box:fill-box;transform-origin:center}
.a-bob{animation:bob 2.6s ease-in-out infinite}
.a-breathe{animation:breathe 3.4s ease-in-out infinite}
.a-blink{transform-box:fill-box;transform-origin:center;animation:blink 4.6s infinite}
.a-glow{animation:glow 2.2s ease-in-out infinite alternate}
.a-glow2{animation:glow 3.1s ease-in-out infinite alternate}
.a-spin{animation:spin 6s linear infinite}
.a-spinr{animation:spinr 6s linear infinite}
.a-ripple{transform-box:fill-box;transform-origin:center;animation:ripple 3.6s ease-out infinite}
.fly{fill:var(--fly,#fff1c4);opacity:0;animation:twinkle 3s ease-in-out infinite}
.seed{opacity:1;animation:seed 1.6s ease-in forwards}
@keyframes seed{to{opacity:0}}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}
@keyframes breathe{0%,100%{transform:scale(1)}50%{transform:scale(1.02)}}
@keyframes blink{0%,90%,100%{transform:scaleY(1)}93%{transform:scaleY(.08)}96%{transform:scaleY(1)}}
@keyframes glow{from{opacity:.45}to{opacity:1}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes spinr{to{transform:rotate(-360deg)}}
@keyframes ripple{0%{transform:scale(.55);opacity:.8}100%{transform:scale(1.35);opacity:0}}
@keyframes twinkle{0%,100%{opacity:0;transform:translateY(0)}50%{opacity:.95;transform:translateY(-5px)}}'''


def scale_at(t, hold):
    if t <= 3:
        return S0 * (hold / S0) ** ((t / 3) ** .72)
    if t <= 9:
        return hold + (t - 3) / 6 * .3
    return (hold + .3) * (S1 * 1.2 / (hold + .3)) ** (((t - 9) / 3) ** 1.5)


def alive_svg(inner, title, css='', hold=3.9, width_mul=1.9, flies=True, seed='#ffd1e6', bg=('#14183a', '#080a1a'), fr=('gold', GOLD), hue=0, flycol='#fff1c4'):
    stops = ''.join(f"{t / DUR * 100:.2f}%{{transform:scale({scale_at(t, hold):.4f})}}" for t in [i * .25 for i in range(int(DUR / .25) + 1)])
    rnd = random.Random(title)
    fl = ''
    if flies:
        for i in range(14):
            x, y = pt(rnd.uniform(66, 98), rnd.uniform(0, 360))
            fl += f'<circle class="fly" cx="{f(x)}" cy="{f(y)}" r="1.6" style="animation-delay:{rnd.uniform(0, 3):.2f}s;animation-duration:{rnd.uniform(2.2, 4):.2f}s"/>'
    body = make_frame(fr[0], fr[1]) + inner + fl
    if hue:
        body = f'<g style="filter:hue-rotate({hue}deg)">{body}</g>'
    body = re.sub(r'stroke-width="([\d.]+)"', lambda m: f'stroke-width="{float(m.group(1)) * width_mul:.1f}"', body)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1920" height="1080"><title>{title}</title>'
            f'<defs>{DEFS_COMMON.replace("#14183a", bg[0]).replace("#080a1a", bg[1])}<filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="5" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            f'<style>:root{{--fly:{flycol}}}\n{BASE_CSS}\n.grow{{transform-origin:0 0;animation:grow {DUR}s linear forwards}}\n@keyframes grow{{{stops}}}\n{css}</style></defs>'
            '<rect width="1600" height="900" fill="url(#bg)"/><g filter="url(#glow)"><g transform="translate(800 450)">'
            f'<path class="l seed" stroke="{seed}" stroke-width="12" d="M0 0 l0 0"/><g class="grow">{body}</g></g></g></svg>')


# ------------------------------------------------------------------ crane
def hak():
    sun = grp('a-glow', P(circle(18, 46, 48), GOLD[0], 3) + P(circle(11, 46, 48), GOLD[1], 1.6))
    streaks = ''.join(grp('a-streak', P(f"M{x} {y} l24 0", WHITE[1], 1.8), f'animation-delay:{d}s') for x, y, d in ((52, 24, 0), (38, 62, 1.1), (62, 70, 2.0)))
    wingU = (P("M0 -6 C-6 -38 -30 -70 -76 -68 C-62 -58 -62 -48 -70 -40 C-56 -40 -52 -32 -56 -24 C-42 -28 -32 -20 -24 -10Z", BLUE[0], 4)
             + ''.join(P(f"M-2 -4 L{f(-60 + (a + 58) * .1)} {f(-62 + (a + 58) * 1.4)}", BLUE[1], 1.6) for a in (-58, -42, -26)))
    wingL = (P("M0 8 C-8 34 -34 56 -76 56 C-62 48 -62 38 -70 32 C-56 34 -50 28 -52 20 C-38 24 -28 18 -22 12Z", BLUE[0], 4)
             + ''.join(P(f"M-2 8 L-64 {y + 2}", BLUE[1], 1.6) for y in (22, 34, 46)))
    body = G("rotate(-8)", P("M-30 6 C-30 -8 -6 -12 18 -6 C30 -2 30 10 14 12 C-6 16 -30 16 -30 6Z", WHITE[0], 4))
    neck = bez((18, -4), (40, -14), (30, -40), (50, -36), 20)
    l, r = ribbon(neck, lambda t: 4.2 - 1.6 * t)
    head = (P(poly(l + r[::-1], True), WHITE[0], 3.4) + P(circle(5, 53, -37), WHITE[0], 3.4) + P("M57 -38 L76 -34", ORANGE[0], 3)
            + grp('a-glow', DOT(54, -38, RED[0], 4)) + P("M49 -42 Q53 -50 58 -43", RED[0], 3))
    legs = P("M-26 14 L-72 30", ORANGE[0], 2.6) + P("M-22 14 L-70 38", ORANGE[0], 2.6)
    tail = P("M-30 6 L-56 6 L-52 12 L-60 14 L-30 14", WHITE[0], 3)
    s = (piv('a-flapU', 0, -6, wingU) + piv('a-flapL', 0, 8, wingL) + body + piv('a-neck', 18, -4, head)
         + piv('a-legs', -26, 14, legs) + piv('a-tailw', -30, 8, tail))
    s = grp('a-bob', G("translate(4 4)", s))
    css = '''.a-flapU{animation:flapU 1.5s ease-in-out infinite}
.a-flapL{animation:flapL 1.5s ease-in-out infinite}
.a-neck{animation:neck 3.2s ease-in-out infinite}
.a-legs{animation:legs 1.5s ease-in-out infinite}
.a-tailw{animation:legs 1.5s ease-in-out infinite reverse}
.a-streak{animation:streak 3s linear infinite;opacity:0}
@keyframes flapU{0%,100%{transform:rotate(9deg)}50%{transform:rotate(-12deg)}}
@keyframes flapL{0%,100%{transform:rotate(-9deg)}50%{transform:rotate(12deg)}}
@keyframes neck{0%,100%{transform:rotate(-2.5deg)}50%{transform:rotate(3deg)}}
@keyframes legs{0%,100%{transform:rotate(-3deg)}50%{transform:rotate(4deg)}}
@keyframes streak{0%{transform:translateX(0);opacity:0}20%{opacity:.8}100%{transform:translateX(-48px);opacity:0}}'''
    return alive_svg(sun + streaks + s, 'Crane - alive', css)


# ------------------------------------------------------------------ dragon
def yong():
    n = 90
    c = ring_pts(36, 336, 64, wave=4, waves=2, n=n)
    wfn = lambda t: 3.5 + 13 * (1 - t) ** .6
    l, r = ribbon(c, wfn)
    body = P(poly(l + r[::-1], True), TEAL[0], 4) + grp('a-glow2', scales(c, wfn, TEAL[1], 4))
    sp = ''
    for k, i in enumerate(range(14, n - 6, 6)):
        x, y = c[i]
        L = math.hypot(x, y)
        ox, oy = x / L, y / L
        tx, ty = tang(c, i)
        w = wfn(i / n)
        sp += grp('a-glow', P(poly([(x + ox * w, y + oy * w), (x + ox * (w + 9) + tx * 5, y + oy * (w + 9) + ty * 5), (x + ox * w + tx * 9, y + oy * w + ty * 9)]), ORANGE[0], 2.6),
                  f'animation-delay:{k * .25:.2f}s')
    legs = ''
    for i in (22, 42, 62):
        x, y = c[i]
        L = math.hypot(x, y)
        ix, iy = -x / L, -y / L
        tx, ty = tang(c, i)
        w = wfn(i / n)
        bx, by = x + ix * w, y + iy * w
        ex, ey = bx + ix * 15 + tx * 5, by + iy * 15 + ty * 5
        leg = P(f"M{f(bx)} {f(by)} Q{f(bx + ix * 8 + tx * 8)} {f(by + iy * 8 + ty * 8)} {f(ex)} {f(ey)}", TEAL[0], 3.6)
        for k in (-1, 0, 1):
            leg += P(f"M{f(ex)} {f(ey)} L{f(ex + ix * 6 + tx * k * 6)} {f(ey + iy * 6 + ty * k * 6)}", GOLD[0], 2.4)
        legs += piv('a-leg', bx, by, leg, f'animation-delay:{i * .02:.2f}s')
    hx, hy = c[0]
    tx, ty = tang(c, 0)
    ang = math.degrees(math.atan2(-ty, -tx))
    head = (P("M0 -9 C10 -13 24 -11 34 -6 C39 -4 39 1 34 3 C26 7 12 9 0 9 Z", GOLD[0], 3.6) + P("M33 0 C24 2 14 3 2 2", GOLD[1], 1.6)
            + DOT(31, -5, RED[0], 4) + grp('a-glow', P(circle(3, 14, -5), RED[0], 2.4) + DOT(14, -5, WHITE[1], 3))
            + P("M6 -10 C0 -22 -10 -26 -20 -24", ORANGE[0], 3) + P("M11 -11 C9 -25 1 -33 -8 -35", ORANGE[0], 3)
            + piv('a-whisk', 33, 0, P("M33 3 C44 9 54 20 62 18", PINK[0], 2) + P("M33 -2 C47 -10 58 -4 64 -12", PINK[0], 2))
            + piv('a-mane', 0, 0, P("M0 -9 C-9 -5 -17 -10 -25 -5", RED[0], 3) + P("M0 9 C-9 6 -16 10 -24 6", RED[0], 3)))
    head_g = grp('a-bob', G(f"translate({f(hx)} {f(hy)}) rotate({f(ang)}) scale(1.45)", head))
    swim = grp('a-swimr', body + sp + legs + head_g)
    pearl = (grp('a-pulse', P(circle(15), YELLOW[0], 4) + P(spiral(0, 0, 11, 2, 1.4), YELLOW[1], 2.4))
             + grp('a-spin', around(8, lambda k: P(lens(12, 3, r0=19), ORANGE[0], 2.6))))
    css = '''.a-swimr{animation:spin 30s linear infinite}
.a-pulse{animation:pulse 2.4s ease-in-out infinite}
.a-leg{animation:leg 1.8s ease-in-out infinite}
.a-whisk{animation:whisk 1.8s ease-in-out infinite alternate}
.a-mane{animation:whisk 1.2s ease-in-out infinite alternate-reverse}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.14)}}
@keyframes leg{0%,100%{transform:rotate(-8deg)}50%{transform:rotate(8deg)}}
@keyframes whisk{from{transform:rotate(-5deg)}to{transform:rotate(6deg)}}'''
    return alive_svg(swim + pearl, 'Dragon - alive', css)


# ------------------------------------------------------------------ turtle
def geobuk():
    def hexa(cx, cy, r):
        return poly([(cx + r * math.cos(math.radians(60 * i + 30)), cy + r * math.sin(math.radians(60 * i + 30))) for i in range(6)], True)
    ripples = ''.join(grp('a-ripple', P(circle(70), BLUE[0], 2), f'animation-delay:{d}s') for d in (0, 1.2, 2.4))
    shell = (P("M0 -54 C34 -54 46 -20 46 4 C46 36 26 56 0 56 C-26 56 -46 36 -46 4 C-46 -20 -34 -54 0 -54Z", GREEN[0], 4.4)
             + P("M0 -46 C28 -46 38 -18 38 4 C38 30 22 48 0 48 C-22 48 -38 30 -38 4 C-38 -18 -28 -46 0 -46Z", GREEN[1], 1.6))
    hexes = grp('a-glow', P(hexa(0, 2, 15), YELLOW[0], 3.4), 'animation-delay:0s')
    for k in range(6):
        cx, cy = pt(26, k * 60)
        hexes += grp('a-glow', P(hexa(cx, cy + 2, 15), YELLOW[0], 3.4), f'animation-delay:{(k + 1) * .35:.2f}s')
    head = (P(circle(12, 0, -64), TEAL[0], 4) + grp('a-blink', DOT(-5, -66, WHITE[1], 5) + DOT(5, -66, WHITE[1], 5)) + P("M-6 -54 L-6 -50 M6 -54 L6 -50", TEAL[0], 3))
    tail = P("M-6 56 L0 72 L6 56", TEAL[0], 3.4)
    flips = ''
    for a, l in ((-52, 36), (52, 36)):
        flips += G(f"translate({f(math.sin(math.radians(a)) * 44)} -30) rotate({a + (-20 if a < 0 else 20)})",
                   grp('a-flipF', PL(lens(l, 10), TEAL, 3.4), 'animation-direction:' + ('normal' if a < 0 else 'reverse')))
    for a in (-128, 128):
        flips += G(f"translate({f(math.sin(math.radians(a)) * 38)} 40) rotate({a * .8})",
                   grp('a-flipR', PL(lens(30, 9), TEAL, 3.4), 'animation-direction:' + ('reverse' if a < 0 else 'normal')))
    s = grp('a-bob', G("scale(1.1)", grp('a-breathe', shell + hexes) + piv('a-head', 0, -52, head) + piv('a-tailw', 0, 56, tail) + flips))
    css = '''.a-head{animation:headb 3s ease-in-out infinite}
.a-tailw{animation:whisk 1.6s ease-in-out infinite alternate}
.a-flipF{animation:flipF 2.4s ease-in-out infinite}
.a-flipR{animation:flipF 2.4s ease-in-out infinite reverse}
@keyframes headb{0%,100%{transform:translateY(0) rotate(-3deg)}50%{transform:translateY(-3px) rotate(3deg)}}
@keyframes whisk{from{transform:rotate(-9deg)}to{transform:rotate(9deg)}}
@keyframes flipF{0%,100%{transform:rotate(-14deg)}50%{transform:rotate(14deg)}}'''
    return alive_svg(ripples + s, 'Turtle - alive', css)


# ------------------------------------------------------------------ deer
def saseum():
    def antler():
        s = P("M10 -36 C22 -52 34 -62 40 -78", GOLD[0], 3.8) + P("M10 -36 C22 -52 34 -62 40 -78", GOLD[1], 1.4)
        for k, (x, y, ex, ey) in enumerate([(18, -48, 36, -50), (27, -58, 48, -62), (34, -68, 52, -80), (40, -78, 34, -96), (40, -78, 48, -94)]):
            s += grp('a-glow', P(f"M{x} {y} Q{(x + ex) / 2 + 2} {(y + ey) / 2 - 3} {ex} {ey}", GOLD[0], 3), f'animation-delay:{k * .3:.2f}s')
            s += grp('a-glow', DOT(ex, ey, YELLOW[1], 5), f'animation-delay:{k * .3 + .5:.2f}s')
        return s
    face = (P("M0 54 C-16 44 -26 20 -26 -10 C-26 -30 -10 -38 0 -38 C10 -38 26 -30 26 -10 C26 20 16 44 0 54Z", ORANGE[0], 4.4)
            + P("M0 46 C-12 38 -20 18 -20 -8 C-20 -24 -8 -31 0 -31 C8 -31 20 -24 20 -8 C20 18 12 38 0 46Z", ORANGE[1], 1.4))
    half = (antler()
            + G("translate(26 -20) rotate(72)", grp('a-ear', PL(lens(30, 9), TEAL, 3.4)))
            + grp('a-blink', P(circle(4.5, 12, -4), WHITE[0], 3) + DOT(12, -4, WHITE[1], 4))
            + P("M8 -24 L14 -22 M12 -16 L18 -14", WHITE[1], 2))
    nose = grp('a-nose', P("M-6 46 C-4 52 4 52 6 46", PINK[0], 3.4) + DOT(0, 48, PINK[0], 7))
    spots = ''.join(grp('a-glow', DOT(x, y, GOLD[1], 4), f'animation-delay:{i * .4}s') for i, (x, y) in enumerate([(0, -30), (-6, -22), (6, -22), (0, -14)]))
    s = G("scale(1.05)", grp('a-breathe', face + mirror(half) + nose + spots))
    css = '''.a-ear{animation:ear 4.3s infinite}
.a-nose{transform-box:fill-box;transform-origin:center;animation:nose 2.2s ease-in-out infinite}
@keyframes ear{0%,55%,70%,100%{transform:rotate(0)}60%{transform:rotate(-10deg)}65%{transform:rotate(3deg)}}
@keyframes nose{0%,100%{transform:scale(1)}50%{transform:scale(1.25)}}'''
    return alive_svg(s, 'Deer - alive', css)


# ------------------------------------------------------------------ carp
def ingeo():
    n = 90
    c = ring_pts(24, 330, 60, wave=4, waves=2, n=n)
    wfn = lambda t: 2 + 15 * math.sin(math.pi * min(1, t * 1.15 + .08)) ** .8
    l, r = ribbon(c, wfn)
    body = P(poly(l + r[::-1], True), ORANGE[0], 4.2) + P(poly(c), ORANGE[1], 1.2) + grp('a-glow2', fish_scales(c, wfn, GOLD[1]))
    ex, ey = c[-1]
    tx, ty = tang(c, n)
    ang = math.degrees(math.atan2(ty, tx)) + 90
    tail = G(f"translate({f(ex)} {f(ey)}) rotate({f(ang)})", grp('a-tailf', ''.join(P(f"M0 0 L{f(30 * math.sin(math.radians(a)))} {f(-30 * math.cos(math.radians(a)))}", RED[0], 3) for a in range(-50, 51, 25))
                                                              + P("M-24 -24 Q0 -38 24 -24", RED[0], 3)))
    fins = ''
    for k, i in enumerate(range(30, 62, 4)):
        x, y = c[i]
        L = math.hypot(x, y)
        ox, oy = x / L, y / L
        w = wfn(i / n)
        fins += grp('a-glow', P(f"M{f(x + ox * w)} {f(y + oy * w)} L{f(x + ox * (w + 9))} {f(y + oy * (w + 9))}", RED[0], 2.6), f'animation-delay:{k * .2:.1f}s')
    hx, hy = c[3]
    htx, hty = tang(c, 3)
    hang = math.degrees(math.atan2(-hty, -htx))
    head = G(f"translate({f(hx)} {f(hy)}) rotate({f(hang)})", grp('a-blink', P(circle(3.4, 8, -5), WHITE[0], 2.6) + DOT(8, -5, RED[0], 4))
             + piv('a-whisk', 16, 0, P("M16 0 C22 2 26 8 34 8", PINK[0], 2) + P("M16 -2 C24 -8 30 -6 38 -12", PINK[0], 2)))
    swim = grp('a-swimr', body + tail + fins + head)
    waves = ''.join(grp('a-wave', P(f"M{-26 + 4 * k} {y} q6 -8 13 0 t13 0 t13 0", BLUE[0], 3.2), f'animation-delay:{k * .5}s') for k, y in enumerate((-14, 0, 14)))
    bubbles = ''.join(grp('a-bubble', P(circle(3, x, 10), BLUE[1], 1.6), f'animation-delay:{d}s') for x, d in ((-8, 0), (6, 1.1), (0, 2.1)))
    css = '''.a-swimr{animation:spin 36s linear infinite}
.a-tailf{animation:tailf 1s ease-in-out infinite alternate}
.a-whisk{animation:whisk 1.4s ease-in-out infinite alternate}
.a-wave{animation:wave 3s ease-in-out infinite alternate}
.a-bubble{animation:bubble 3.2s ease-in infinite;opacity:0}
@keyframes tailf{from{transform:rotate(-14deg)}to{transform:rotate(14deg)}}
@keyframes whisk{from{transform:rotate(-8deg)}to{transform:rotate(8deg)}}
@keyframes wave{from{transform:translateX(-6px)}to{transform:translateX(6px)}}
@keyframes bubble{0%{transform:translateY(0);opacity:0}20%{opacity:.9}100%{transform:translateY(-34px);opacity:0}}'''
    return alive_svg(waves + bubbles + swim, 'Carp - alive', css)


# ------------------------------------------------------------------ bat
def bakjwi():
    wing = (P("M12 -6 C32 -44 62 -54 94 -42 C86 -30 90 -22 82 -10 C76 -20 68 -16 60 2 C56 -8 46 -6 38 12 C32 2 24 4 14 18", RED[0], 4)
            + P("M10 -2 L92 -40 M10 0 L80 -9 M10 4 L58 3 M10 10 L36 12", PINK[1], 1.6) + grp('a-glow', P(circle(5, 52, -22), YELLOW[0], 2.8)))
    wings = mirror(piv('a-flap', 10, 0, wing))
    body = (P("M0 -4 C-12 6 -10 28 0 40 C10 28 12 6 0 -4Z", RED[0], 4) + P(circle(11, 0, -22), RED[0], 4)
            + piv('a-ear', -6, -30, P("M-9 -30 L-12 -42 L-3 -34", RED[0], 3.4)) + piv('a-earr', 6, -30, P("M9 -30 L12 -42 L3 -34", RED[0], 3.4))
            + grp('a-blink', DOT(-4, -22, YELLOW[0], 5) + DOT(4, -22, YELLOW[0], 5)) + P("M-4 -16 L-2 -11 M4 -16 L2 -11", WHITE[0], 2.2)
            + P("M0 40 C-6 52 -2 60 0 62 C2 60 6 52 0 40", RED[1], 2.4))
    s = grp('a-bobb', wings + body)
    css = '''.a-flap{animation:flap 1.3s ease-in-out infinite}
.a-bobb{animation:bobb 1.3s ease-in-out infinite}
.a-ear{animation:ear 4s infinite}
.a-earr{animation:ear 4s infinite 1.6s}
@keyframes flap{0%,100%{transform:rotate(12deg)}50%{transform:rotate(-20deg)}}
@keyframes bobb{0%,100%{transform:translateY(5px)}50%{transform:translateY(-5px)}}
@keyframes ear{0%,60%,100%{transform:rotate(0)}65%{transform:rotate(-12deg)}72%{transform:rotate(2deg)}}'''
    return alive_svg(s, 'Bat - alive', css)


# ------------------------------------------------------------------ butterfly
def nabi():
    wing = (P("M6 -4 C18 -48 62 -72 88 -58 C100 -40 80 -14 46 -6Z", VIOLET[0], 4) + P("M6 4 C30 6 62 18 66 46 C64 68 28 70 12 40Z", PINK[0], 4)
            + grp('a-glow', P(circle(12, 56, -36), TEAL[0], 3.2) + P(circle(5.5, 56, -36), TEAL[1], 2)) + grp('a-glow2', P(circle(9, 40, 38), TEAL[0], 3))
            + P("M8 -4 L84 -52 M8 -2 L70 -22 M8 6 L60 36 M8 8 L40 52", VIOLET[1], 1.6))
    wings = mirror(piv('a-flapx', 4, 0, wing))
    body = (P("M0 -22 C-8 -10 -8 26 0 44 C8 26 8 -10 0 -22Z", GOLD[0], 4) + P(circle(7, 0, -28), GOLD[0], 3.4)
            + piv('a-antl', -3, -34, P("M-3 -34 C-6 -54 -18 -66 -28 -62", GOLD[0], 2.8) + DOT(-28, -62, GOLD[1], 6))
            + piv('a-antr', 3, -34, P("M3 -34 C6 -54 18 -66 28 -62", GOLD[0], 2.8) + DOT(28, -62, GOLD[1], 6)))
    dust = ''.join(grp('a-dust', DOT(x, 40, GOLD[1], 5), f'animation-delay:{d}s') for x, d in ((-30, 0), (24, .8), (-8, 1.6), (36, 2.3)))
    s = grp('a-bobb', wings + body)
    css = '''.a-flapx{animation:flapx 1.1s ease-in-out infinite}
.a-bobb{animation:bobb 2.2s ease-in-out infinite}
.a-antl{animation:antl 2s ease-in-out infinite alternate}
.a-antr{animation:antl 2s ease-in-out infinite alternate-reverse}
.a-dust{animation:dust 2.6s ease-in infinite;opacity:0}
@keyframes flapx{0%,100%{transform:scaleX(1)}50%{transform:scaleX(.3)}}
@keyframes bobb{0%,100%{transform:translateY(4px) rotate(-1.5deg)}50%{transform:translateY(-4px) rotate(1.5deg)}}
@keyframes antl{from{transform:rotate(-7deg)}to{transform:rotate(7deg)}}
@keyframes dust{0%{transform:translateY(0);opacity:0}20%{opacity:.9}100%{transform:translateY(34px);opacity:0}}'''
    return alive_svg(dust + s, 'Butterfly - alive', css)


# ------------------------------------------------------------------ qilin
def girin():
    s = P("M-48 -6 C-48 -26 -6 -30 22 -22 C42 -16 42 14 22 20 C-8 28 -48 18 -48 -6Z", ORANGE[0], 4.2)
    sc = ''
    for r in range(3):
        for i in range(6 - r):
            sc += P(f"M{-40 + i * 12 + r * 6} {-8 + r * 9} q4 -4 8 0", ORANGE[1], 1.5)
    body = s + grp('a-glow2', sc)
    neck = bez((22, -18), (40, -24), (40, -44), (52, -54), 20)
    l, r = ribbon(neck, lambda t: 9 - 3 * t)
    head = (P(poly(l + r[::-1], True), ORANGE[0], 3.8) + P("M46 -56 C54 -66 70 -64 80 -56 C82 -52 80 -48 74 -47 C66 -44 54 -44 46 -50Z", GOLD[0], 3.6)
            + grp('a-glow', DOT(60, -57, RED[0], 5)) + P("M52 -62 C48 -76 40 -84 30 -82", RED[0], 3.2) + P("M80 -52 C88 -50 92 -42 98 -44", PINK[0], 2))
    mane = ''.join(grp('a-flick', P(f"M{x} {y} c-12 -4 -14 -14 -6 -18", GOLD[0], 3), f'animation-delay:{i * .25:.2f}s') for i, (x, y) in enumerate([(30, -26), (36, -36), (42, -46)]))
    legs = ''
    for k, (x0, x1) in enumerate(((22, 28), (8, 8), (-28, -32), (-18, -14))):
        l2, r2 = ribbon(bez((x0, 18), (x0, 36), (x1, 48), (x1, 64), 10), lambda t: 5 - 1.4 * t)
        leg = P(poly(l2 + r2[::-1], True), ORANGE[0], 3.4) + P(poly([(x1 - 6, 64), (x1 + 6, 64), (x1 + 4, 72), (x1 - 4, 72)], True), RED[0], 3)
        legs += piv('a-step', x0, 18, leg, f'animation-delay:{(k % 2) * .6}s')
    tail = piv('a-tailw', -48, -6, P("M-48 -6 C-62 -16 -70 -34 -60 -46 C-58 -34 -52 -30 -46 -26", GOLD[0], 3.6) + P("M-60 -46 C-70 -50 -74 -40 -68 -34", GOLD[0], 2.6))
    scrolls = (G("translate(10 0)", grp('a-spin', P(spiral(0, 0, 3, 13, 1.6), TEAL[0], 3))) + G("translate(-28 -2)", grp('a-spinr', P(spiral(0, 0, 3, 13, 1.6, a0=90), TEAL[0], 3))))
    s = grp('a-bob', G("scale(1.05) translate(-6 8)", body + piv('a-neckg', 22, -18, head + mane) + legs + tail + scrolls))
    css = '''.a-step{animation:step 1.2s ease-in-out infinite}
.a-tailw{animation:whisk 1.4s ease-in-out infinite alternate}
.a-neckg{animation:whisk 3.2s ease-in-out infinite alternate;--x:1}
.a-flick{transform-box:fill-box;transform-origin:50% 100%;animation:flick .9s ease-in-out infinite alternate}
@keyframes step{0%,100%{transform:rotate(-7deg)}50%{transform:rotate(7deg)}}
@keyframes whisk{from{transform:rotate(-4deg)}to{transform:rotate(5deg)}}
@keyframes flick{from{transform:scale(1,.8)}to{transform:scale(1.1,1.15)}}'''
    return alive_svg(s, 'Qilin - alive', css)


# ------------------------------------------------------------------ haetae
def haetae():
    mane = ''.join(G(f"rotate({k * 22.5})", grp('a-flame', P("M0 -42 C-10 -56 -4 -70 4 -80 C6 -66 14 -60 10 -44", ORANGE[0], 3.6) + P("M0 -46 C-4 -58 0 -66 4 -74", ORANGE[1], 1.4),
                                              f'animation-delay:{k * .12:.2f}s')) for k in range(16))
    face = P(circle(42, 0, 8), GOLD[0], 4.4) + P(circle(36, 0, 8), GOLD[1], 1.4)
    half = (grp('a-blink', P("M-30 -6 C-22 -16 -8 -14 -4 -4 C-8 4 -22 6 -30 -6Z", WHITE[0], 3.4) + grp('a-glow', DOT(-17, -6, RED[0], 9)) + DOT(-17, -6, WHITE[1], 3.4))
            + piv('a-brow', -6, -16, P("M-36 -18 C-26 -26 -10 -24 -6 -16", RED[0], 4))
            + P("M-4 22 C-14 18 -24 22 -28 30 C-22 40 -10 38 -4 34", GOLD[1], 2.6)
            + P("M-34 -2 C-46 4 -48 16 -40 22", ORANGE[0], 3) + G("translate(-42 28)", grp('a-spin', P(spiral(0, 0, 2, 8, 1.4), ORANGE[0], 2.6))))
    jaw = grp('a-jaw', P("M-18 32 C-10 42 10 42 18 32", RED[0], 3.4) + P("M-11 34 L-8 42 L-5 36 M5 36 L8 42 L11 34", WHITE[0], 2.6))
    horn = grp('a-glow', P("M0 -36 C-8 -50 4 -62 0 -78", PINK[0], 4) + P("M0 -36 C-8 -50 4 -62 0 -78", PINK[1], 1.4))
    s = grp('a-breathe', mane + face + mirror(half) + P("M-10 12 L10 12 C8 22 -8 22 -10 12Z", PINK[0], 3.4) + jaw + horn)
    css = '''.a-flame{transform-box:fill-box;transform-origin:50% 100%;animation:flame 1.1s ease-in-out infinite alternate}
.a-brow{animation:brow 3.7s infinite}
.a-jaw{animation:jaw 3.4s ease-in-out infinite}
@keyframes flame{from{transform:scale(1,.88) rotate(-2deg)}to{transform:scale(1.08,1.1) rotate(2deg)}}
@keyframes brow{0%,60%,100%{transform:rotate(0)}66%{transform:rotate(-5deg)}72%{transform:rotate(0)}}
@keyframes jaw{0%,100%{transform:translateY(0)}50%{transform:translateY(2px)}}'''
    return alive_svg(s, 'Haetae - alive', css)


# ------------------------------------------------------------------ phoenix (laser beams running along the drawing)
def bonghwang(src_svg):
    ds = re.findall(r'<path class="d c" [^>]*d="([^"]+)"', open(src_svg, encoding='utf-8').read())
    defs_g = ('<linearGradient id="gph" gradientUnits="userSpaceOnUse" x1="0" y1="60" x2="0" y2="950">'
              '<stop offset="0" stop-color="#ff3860"/><stop offset=".2" stop-color="#ff9628"/><stop offset=".36" stop-color="#ffe14a"/>'
              '<stop offset=".52" stop-color="#3df2c0"/><stop offset=".68" stop-color="#5aa9ff"/><stop offset=".82" stop-color="#b48cff"/>'
              '<stop offset="1" stop-color="#ff4fd8"/></linearGradient>')
    lines = ''.join(f'<path class="l" stroke="url(#gph)" stroke-width="3.2" d="{d}"/>' for d in ds)
    rnd = random.Random(3)
    beams = ''
    for k, d in enumerate(ds):
        if rnd.random() < .45:
            beams += (f'<path class="l beam" pathLength="1" stroke="#fff" stroke-width="5.5" d="{d}" '
                      f'style="animation-delay:{rnd.uniform(0, 3):.2f}s;animation-duration:{rnd.uniform(1.6, 3.2):.2f}s"/>')
    body = grp('a-breathe', G("scale(.19) translate(-500 -500)", lines + beams))
    css = '''.beam{stroke-dasharray:.1 .9;stroke-dashoffset:.1;animation:run 2.4s linear infinite;opacity:.95}
@keyframes run{0%{stroke-dashoffset:.1}100%{stroke-dashoffset:-.9}}'''
    svg = alive_svg(body, 'Phoenix - alive', css, hold=3.9, width_mul=1.0, flies=True)
    return svg.replace('<defs>', '<defs>' + defs_g, 1)


ALIVE = {'hak': hak, 'yong': yong, 'geobuk': geobuk, 'saseum': saseum, 'ingeo': ingeo, 'bakjwi': bakjwi, 'nabi': nabi, 'girin': girin, 'haetae': haetae}
