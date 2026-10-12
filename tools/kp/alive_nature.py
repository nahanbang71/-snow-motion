"""03 자연문 - dynamic versions (varied frames / backgrounds / motion)"""
import math
import random
from core import *
from alive import alive_svg, piv, grp, BASE_CSS
from nature import star4


def scene_svg(inner, title, css='', bg=('#0a1a3a', '#03060f'), dur=12):
    """full-bleed 1600x900 scene (no grow); fades in"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1920" height="1080"><title>{title}</title>'
            f'<defs><radialGradient id="bg" cx="50%" cy="50%" r="75%"><stop offset="0" stop-color="{bg[0]}"/><stop offset="1" stop-color="{bg[1]}"/></radialGradient>'
            '<filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="3.2" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            f'<style>{BASE_CSS}\n.scene{{opacity:0;animation:fadein 1.6s ease-out forwards}}@keyframes fadein{{to{{opacity:1}}}}\n{css}</style></defs>'
            f'<rect width="1600" height="900" fill="url(#bg)"/><g class="scene" filter="url(#glow)">{inner}</g></svg>')


# ------------------------------------------------------------------ sun
def hae():
    straight = around(12, lambda k: PL(lens(44, 7, r0=36), YELLOW, 3.6))
    wavy = around(12, lambda k: P("M" + " L".join(f"{f(x)} {f(y)}" for x, y in [(8 * math.sin(i * .7), -36 - i * 4) for i in range(0, 15)]), ORANGE[0], 3.4), start=15)
    flares = around(24, lambda k: P(poly([(0, -92), (-5, -82), (5, -82)], True), RED[0], 2.6), start=0)
    core = P(circle(30), ORANGE[0], 4.4) + P(circle(22), YELLOW[0], 3.4) + P(spiral(0, 0, 16, 2, 1.5), YELLOW[1], 2.2)
    rip = ''.join(grp('a-ripple2', P(circle(36), YELLOW[0], 2), f'animation-delay:{d}s') for d in (0, 1.1, 2.2))
    inner = (rip + grp('a-rot1', straight) + grp('a-rot2', wavy) + grp('a-rot3', flares) + grp('a-pulse', core))
    css = '''.a-rot1{animation:spin 50s linear infinite}
.a-rot2{animation:spinr 32s linear infinite}
.a-rot3{animation:spin 90s linear infinite}
.a-pulse{animation:pulse 2.6s ease-in-out infinite}
.a-ripple2{transform-box:fill-box;transform-origin:center;animation:rip2 3.3s ease-out infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.12)}}
@keyframes rip2{0%{transform:scale(1);opacity:.8}100%{transform:scale(2.7);opacity:0}}'''
    return alive_svg(inner, 'Sun - alive', css, bg=('#3a1700', '#100500'), fr=('ticks', ORANGE), flycol='#ffd27a')


# ------------------------------------------------------------------ moon
def dal():
    moon = (P("M-6 -56 A56 56 0 0 0 -6 56 A64 64 0 0 1 -6 -56Z", YELLOW[0], 4.6) + P("M-6 -50 A50 50 0 0 0 -6 50", YELLOW[1], 1.6))
    stars = ''
    for i, (x, y, r) in enumerate([(34, -34, 9), (52, 4, 7), (30, 40, 8), (-52, -52, 5), (60, -18, 5), (8, -66, 4)]):
        stars += piv('a-star', x, y, P(star4(x, y, r), GOLD[0], 3), f'animation-delay:{i * .45:.2f}s')
    cloud = lambda y, d: grp('a-cloud', P(spiral(-26, y, 2, 9, 1.4), BLUE[0], 3) + P(f"M-26 {y} q14 4 30 0 q10 -8 20 0", BLUE[0], 3), f'animation-delay:{d}s')
    shoot = grp('a-shoot', P("M-80 -70 L-40 -50", WHITE[0], 3) + P("M-80 -70 L-60 -60", WHITE[1], 1.4), 'animation-delay:3.2s')
    inner = (cloud(62, 0) + cloud(-74, 4.5) + shoot + piv('a-rock', 0, 0, moon) + stars)
    css = '''.a-star{transform-box:fill-box;transform-origin:center;animation:tw2 2.4s ease-in-out infinite}
.a-rock{animation:rock 6s ease-in-out infinite alternate}
.a-cloud{animation:cloud 11s linear infinite;opacity:0}
.a-shoot{animation:shoot 7s ease-in infinite;opacity:0}
@keyframes tw2{0%,100%{transform:scale(.5) rotate(0);opacity:.4}50%{transform:scale(1.25) rotate(25deg);opacity:1}}
@keyframes rock{from{transform:rotate(-4deg)}to{transform:rotate(4deg)}}
@keyframes cloud{0%{transform:translateX(-50px);opacity:0}15%{opacity:.9}85%{opacity:.9}100%{transform:translateX(120px);opacity:0}}
@keyframes shoot{0%{transform:translate(0,0);opacity:0}8%{opacity:1}30%{transform:translate(120px,70px);opacity:0}100%{opacity:0}}'''
    return alive_svg(inner, 'Moon - alive', css, bg=('#0d1840', '#02030c'), fr=('ticks', BLUE), flycol='#bfe0ff')


# ------------------------------------------------------------------ cloud
def unmun():
    def unit(k):
        r = 46
        return (piv('a-curl', -17, -r - 8, P(spiral(-17, -r - 8, 9, 2, 1.5, a0=0), TEAL[0], 3.4)) + piv('a-curlr', 17, -r - 8, P(spiral(17, -r - 8, 9, 2, 1.5, a0=180, ccw=True), TEAL[0], 3.4))
                + P(f"M-17 {-r - 17} C-8 {-r - 30} 8 {-r - 30} 17 {-r - 17}", BLUE[0], 3.6)
                + P(f"M0 {-r - 6} C-4 {-r + 10} 6 {-r + 16} 2 {-r + 28}", BLUE[1], 2.2))
    clouds = around(6, unit)
    petals = around(6, lambda k: P(drop(18, 8, r0=14), VIOLET[0], 3), start=30)
    inner = (grp('a-drift', clouds) + grp('a-drift2', petals) + P(circle(8), WHITE[0], 3) + grp('a-glow', DOT(0, 0, WHITE[1], 6)))
    css = '''.a-drift{animation:spin 44s linear infinite}
.a-drift2{animation:spinr 28s linear infinite}
.a-curl{animation:spin 5s linear infinite}
.a-curlr{animation:spinr 5s linear infinite}'''
    return alive_svg(inner, 'Cloud - alive', css, bg=('#10285a', '#030a1c'), fr=('cloud', TEAL), flycol='#bff7ff')


# ------------------------------------------------------------------ mountain landscape (full-bleed)
def san_scene():
    rnd = random.Random(8)
    sky = ''.join(DOT(rnd.randint(40, 1560), rnd.randint(30, 360), '#fff1c4', rnd.choice([3, 4, 5])).replace('class="l"', 'class="l a-star2" style="animation-delay:%.1fs"' % rnd.uniform(0, 3)) for _ in range(40))
    sun = (grp('a-sun', P(circle(70, 0, 0), ORANGE[0], 4) + P(circle(52, 0, 0), YELLOW[0], 3) + around(16, lambda k: P(lens(34, 6, r0=82), YELLOW[0], 3))))
    sun = G("translate(1180 330)", sun)

    def ridge(pts, col, dx):
        return grp('a-ridge', P(poly(pts), col[0], 4) + P(poly([(x, y + 14) for x, y in pts]), col[1], 1.6), f'--dx:{dx}px')
    far = ridge([(-80, 560), (160, 430), (300, 500), (520, 340), (760, 480), (980, 380), (1200, 500), (1420, 400), (1680, 520)], VIOLET, 22)
    mid = ridge([(-80, 640), (200, 520), (420, 600), (700, 450), (960, 590), (1240, 500), (1500, 610), (1700, 560)], TEAL, -30)
    near = ridge([(-80, 740), (260, 640), (520, 720), (860, 620), (1160, 730), (1480, 650), (1700, 720)], GREEN, 40)
    mist = ''.join(grp('a-mist', P(f"M{x} {y} q60 -14 120 0 t120 0 t120 0", WHITE[1], 2.4), f'animation-delay:{d}s') for x, y, d in ((120, 560, 0), (720, 520, 3), (1100, 600, 6), (300, 660, 8)))
    birds = ''.join(grp('a-bird', P(f"M0 0 q12 -14 24 0 q12 -14 24 0", WHITE[0], 3), f'animation-delay:{d}s;--y:{y}px') for d, y in ((0, 140), (2.5, 190), (5, 110)))
    water = ''.join(grp('a-water', P(f"M-100 {y} q40 -12 80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0", BLUE[0] if k % 2 else BLUE[1], 3),
                    f'animation-delay:{k * .6}s;animation-direction:{"normal" if k % 2 else "reverse"}') for k, y in enumerate(range(790, 890, 24)))
    inner = sky + sun + far + mid + near + mist + birds + water
    css = '''.a-star2{animation:tw3 2.8s ease-in-out infinite}
.a-sun{animation:spin 90s linear infinite}
.a-ridge{animation:ridge 14s ease-in-out infinite alternate}
.a-mist{animation:mist 12s linear infinite}
.a-bird{animation:bird 12s linear infinite;opacity:0}
.a-water{animation:water 4s linear infinite}
@keyframes tw3{0%,100%{opacity:.2}50%{opacity:1}}
@keyframes ridge{from{transform:translateX(0)}to{transform:translateX(var(--dx))}}
@keyframes mist{0%{transform:translateX(-160px);opacity:0}20%{opacity:.8}80%{opacity:.8}100%{transform:translateX(160px);opacity:0}}
@keyframes bird{0%{transform:translate(1600px,var(--y));opacity:0}8%{opacity:1}92%{opacity:1}100%{transform:translate(-100px,calc(var(--y) - 60px));opacity:0}}
@keyframes water{from{transform:translateX(0)}to{transform:translateX(-160px)}}'''
    return scene_svg(inner, 'Mountains - alive', css, bg=('#1a1450', '#03040e'))


# ------------------------------------------------------------------ waves (seigaiha, full-bleed)
def supamun_full():
    rows = ''
    r0 = 40
    for j in range(-1, 30):
        y = j * 34
        cols = (BLUE, TEAL, VIOLET)[j % 3]
        row = ''
        for i in range(-2, 26):
            x = i * 2 * r0 + (r0 if j % 2 else 0)
            for rr, w, c in ((r0, 3.4, cols[0]), (r0 * .68, 2.6, cols[0]), (r0 * .36, 2, cols[1])):
                row += P(f"M{f(x - rr)} {y} A{f(rr)} {f(rr)} 0 0 1 {f(x + rr)} {y}", c, w)
        rows += grp('a-row', row, f'animation-direction:{"normal" if j % 2 else "reverse"};animation-delay:{j * -.4}s')
    css = '''.a-row{animation:rowmove 7s linear infinite}
@keyframes rowmove{from{transform:translateX(0)}to{transform:translateX(-160px)}}'''
    return scene_svg(rows, 'Waves - alive', css, bg=('#0a2c58', '#020a1c'))


# ------------------------------------------------------------------ rock
def bawi():
    def rock(pts, col):
        return P(smooth(pts, True), col[0], 4.2) + P(smooth([(x * .8, y * .8 - 2) for x, y in pts], True), col[1], 1.4)
    rocks = (rock([(-48, 40), (-52, 6), (-36, -22), (-12, -34), (12, -24), (28, 0), (30, 40)], VIOLET)
             + rock([(24, 44), (26, 20), (40, 4), (58, 10), (66, 28), (64, 44)], BLUE) + rock([(-70, 44), (-68, 24), (-58, 12), (-48, 16), (-46, 44)], BLUE)
             + P("M-14 -18 L-8 0 L-16 14 L-8 30", VIOLET[1], 2.4) + P("M12 -10 L6 6 L14 22", VIOLET[1], 2.4))
    glints = ''.join(grp('a-gl', P(star4(x, y, 6), WHITE[1], 2), f'animation-delay:{d}s') for x, y, d in ((-20, -18, 0), (14, -6, .8), (50, 14, 1.6), (-58, 18, 2.4)))
    grass = ''.join(piv('a-sway', x, -30, P(f"M{x} -30 q-2 -12 -8 -16 M{x} -30 q2 -12 8 -16", GREEN[0], 2.4), f'animation-delay:{x * .02:.2f}s') for x in (-20, -10, 40, 48))
    waves = ''.join(grp('a-wv', P(f"M-130 {y} q12 -8 25 0 t25 0 t25 0 t25 0 t25 0 t25 0 t25 0 t25 0 t25 0 t25 0 t25 0", c, 3.2), f'animation-delay:{k * -.7}s')
                    for k, (y, c) in enumerate(((56, TEAL[0]), (70, TEAL[1]), (84, BLUE[0]))))
    drops = ''.join(grp('a-drop', DOT(x, 30, BLUE[1], 4), f'animation-delay:{d}s') for x, d in ((-30, 0), (10, 1.3), (40, 2.6)))
    from core import clip
    inner = clip(grp('a-bobr', G("translate(0 -6) scale(1.3)", rocks + glints + grass + waves)) + drops)
    css = '''.a-gl{transform-box:fill-box;transform-origin:center;animation:tw2 2.6s ease-in-out infinite}
.a-sway{animation:sway 2.6s ease-in-out infinite alternate}
.a-wv{animation:wv 3.6s linear infinite}
.a-bobr{animation:bobr 5s ease-in-out infinite alternate}
.a-drop{animation:drop 3s ease-in infinite;opacity:0}
@keyframes tw2{0%,100%{transform:scale(.4);opacity:.3}50%{transform:scale(1.3);opacity:1}}
@keyframes sway{from{transform:rotate(-8deg)}to{transform:rotate(8deg)}}
@keyframes wv{from{transform:translateX(0)}to{transform:translateX(-50px)}}
@keyframes bobr{from{transform:translateY(-2px)}to{transform:translateY(3px)}}
@keyframes drop{0%{transform:translateY(0);opacity:0}15%{opacity:.9}100%{transform:translateY(24px);opacity:0}}'''
    return alive_svg(inner, 'Rock - alive', css, bg=('#0a3a3a', '#021214'), fr=('petal', TEAL), flycol='#d4fff0')


# ------------------------------------------------------------------ flame
def bulkkot():
    outer = around(8, lambda k: PL("M0 -26 C-12 -44 6 -58 -2 -84 C18 -66 22 -44 0 -26Z", RED, 4.2))
    mid = around(8, lambda k: PL("M0 -26 C-8 -38 4 -48 -1 -64 C12 -52 14 -38 0 -26Z", ORANGE, 3.6), start=22.5)
    inn = around(8, lambda k: PL("M0 -22 C-5 -30 2 -36 0 -46 C7 -38 8 -30 0 -22Z", YELLOW, 3), start=0)
    # each flame tongue flickers on its own
    def flick(items, cls):
        return ''.join(G(f"rotate({a})", grp(cls, i, f'animation-delay:{k * .13:.2f}s')) for k, (a, i) in enumerate(items))
    outer = flick([(k * 45, PL("M0 -26 C-12 -44 6 -58 -2 -84 C18 -66 22 -44 0 -26Z", RED, 4.2)) for k in range(8)], 'a-fl')
    mid = flick([(22.5 + k * 45, PL("M0 -26 C-8 -38 4 -48 -1 -64 C12 -52 14 -38 0 -26Z", ORANGE, 3.6)) for k in range(8)], 'a-fl2')
    inn = flick([(k * 45, PL("M0 -22 C-5 -30 2 -36 0 -46 C7 -38 8 -30 0 -22Z", YELLOW, 3)) for k in range(8)], 'a-fl3')
    rnd = random.Random(2)
    embers = ''.join(grp('a-ember', DOT(rnd.uniform(-40, 40), rnd.uniform(0, 70), ORANGE[1], 4), f'animation-delay:{rnd.uniform(0, 3):.2f}s;animation-duration:{rnd.uniform(2, 3.6):.1f}s') for _ in range(18))
    inner = grp('a-turn', outer + mid) + grp('a-turnr', inn) + P(circle(14), YELLOW[0], 3.6) + grp('a-pulse', P(spiral(0, 0, 10, 1.5, 1.3), YELLOW[1], 2)) + embers
    css = '''.a-turn{animation:spin 40s linear infinite}
.a-turnr{animation:spinr 26s linear infinite}
.a-fl{transform-box:fill-box;transform-origin:50% 100%;animation:fl 1.1s ease-in-out infinite alternate}
.a-fl2{transform-box:fill-box;transform-origin:50% 100%;animation:fl 0.8s ease-in-out infinite alternate}
.a-fl3{transform-box:fill-box;transform-origin:50% 100%;animation:fl 0.6s ease-in-out infinite alternate}
.a-pulse{animation:pulse 1.6s ease-in-out infinite}
.a-ember{animation:ember 2.8s ease-out infinite;opacity:0}
@keyframes fl{from{transform:scale(1,.82) rotate(-3deg)}to{transform:scale(1.1,1.15) rotate(3deg)}}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.2)}}
@keyframes ember{0%{transform:translateY(0);opacity:0}15%{opacity:1}100%{transform:translateY(-70px);opacity:0}}'''
    return alive_svg(inner, 'Flame - alive', css, bg=('#3a0a0e', '#0f0204'), fr=('none', ORANGE), flycol='#ffb070')


NATURE = {'hae': hae, 'dal': dal, 'unmun': unmun, 'san': san_scene, 'supamun': supamun_full, 'bawi': bawi, 'bulkkot': bulkkot}
