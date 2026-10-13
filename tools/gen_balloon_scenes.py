#!/usr/bin/env python3
"""Balloons drifting over a heritage landscape (like the Cappadocia photo): sky full of balloons, the site drawn below as laser
line art, name label.  14 s per scene -> 열기구풍경/<id>.svg      usage: python3 tools/gen_balloon_scenes.py [id ...]"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_balloon_designs as BD  # noqa: E402
import europe_sites as ES  # noqa: E402
import world_sites as WS  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '열기구풍경')
FONT = "font-family=\"'Helvetica Neue', Arial, sans-serif\""
GOLD, ACC = '#ffd166', '#ff4fd8'
f = BD.f

PAL = [  # (envelope outline, details, design)
    ('#ffd166', BD.CH, 'C'), ('#ff4fd8', '#ffd166', 'A'), ('#35f3ff', '#ff4fd8', 'B'), ('#39ff9c', '#ffd166', 'A'),
    ('#b78bff', '#35f3ff', 'C'), ('#ffb03a', '#ff5a8a', 'B'), ('#4d7cff', '#ffe14d', 'A')]


def balloon(design, main, alt, delay0):
    k = [0]

    def p(d, color, w=2.6, op=1):
        s = f'<path class="d" pathLength="1" stroke="{color}" stroke-width="{w}" opacity="{op}" style="animation-delay:{delay0 + k[0] * .05:.2f}s" d="{d}"/>'
        k[0] += 1
        return s
    mouth, ropes, basket, flame = BD.gear('')
    g = p(BD.outline(), main, 3.2)
    if design == 'C':
        for i, y in enumerate((-176, -112, -50, 12, 76)):
            g += p(BD.band(y, 34), alt[i % len(alt)] if isinstance(alt, (list, tuple)) else alt, 3.2)
        for s in (-.5, 0, .5):
            g += p(BD.meridian(s), '#8a7a52', 1.4, .8)
    elif design == 'A':
        for s in (-.55, 0, .55):
            g += p(BD.meridian(s), alt, 2.2)
        zz = [(s_ * BD.xr(y), y) for s_, y in [(-1 + 2 * i / 12, -52 if i % 2 == 0 else -14) for i in range(13)]]
        g += p(BD.poly(zz), main, 2.4)
        g += p(BD.band(-118, 26), alt, 2) + p(BD.band(34, 22), alt, 2)
    else:
        for c in [x * 0.5 for x in range(-6, 7)]:
            for sign in (1, -1):
                pts = []
                for i in range(41):
                    t = 0.1 + 0.82 * i / 40
                    y = BD.YTOP + t * (BD.YBOT - BD.YTOP)
                    sv = c + sign * 2.1 * (t - 0.5)
                    if abs(sv) <= 1:
                        pts.append((sv * BD.xr(y), y))
                if len(pts) > 3:
                    g += p(BD.poly(pts), alt if sign > 0 else main, 1.6, .9)
    g += p(mouth, main, 2.6) + p(ropes, GOLD, 2) + p(basket, GOLD, 2.8)
    return g + f'<path class="flame" d="{flame}" style="animation-delay:{delay0 + 1.5:.2f}s,{delay0 + 2.5:.2f}s"/>'


def scene(sid, name, sub, elev, scale, ridge_seed, bals=None, dur=14.0, compass=False):
    rnd = random.Random(ridge_seed)
    stars = ''.join(f'<circle class="star" cx="{rnd.randint(20, 1900)}" cy="{rnd.randint(20, 560)}" r="{rnd.choice((1, 1.2, 1.6, 2))}" '
                    f'style="animation-duration:{rnd.uniform(3, 7):.1f}s;animation-delay:-{rnd.uniform(0, 6):.1f}s"/>' for _ in range(90))
    # distant ridges
    ridges = ''
    for k, (base, amp, col) in enumerate(((760, 70, '#27346a'), (810, 55, '#34478a'))):
        pts = []
        x = -40
        while x < 1960:
            pts.append((x, base - rnd.uniform(amp * .3, amp)))
            x += rnd.randint(70, 140)
        ridges += f'<path class="rg" style="animation-delay:{.2 + k * .3}s;stroke:{col}" d="M{" L".join(f"{f(a)} {f(b)}" for a, b in pts)}"/>'
    ev = ''.join(f'<path class="e" pathLength="1" style="animation-delay:{.5 + i * .09:.2f}s" d="{d}"/>' for i, d in enumerate(elev))
    bals = bals or [(300, 250, .52, 0), (640, 150, .38, 1), (920, 300, .85, 2), (1250, 190, .5, 3), (1560, 330, 1.0, 4), (1790, 160, .36, 5), (1080, 120, .3, 6)]
    bl = ''
    for i, (cx, cy, sc, pi) in enumerate(bals):
        main, alt, des = PAL[pi % len(PAL)]
        dx = (-1) ** i * (60 + 14 * i)
        bl += (f'<g transform="translate({cx} {cy}) scale({sc})" opacity="{0.55 + 0.45 * min(1, sc):.2f}"><g class="dr" style="--dx:{dx}px;animation-delay:{.2 + i * .15:.2f}s">'
               f'<g class="bob" style="animation-delay:-{i * .9:.1f}s;animation-duration:{3.4 + i * .4:.1f}s">{balloon(des, main, alt, 1.0 + i * .35)}</g></g></g>')
    comp = ''
    if compass:                      # small compass, needle follows the balloons' eastward drift
        comp = ('<g transform="translate(1800 960)" opacity=".9"><circle class="cpc" r="46"/><path class="cpc" d="M0 -46 V-36 M0 46 V36 M-46 0 H-36 M46 0 H36"/>'
                '<g class="needle"><path class="nd" d="M0 -40 L7 0 L-7 0 Z"/><path class="nt" d="M0 40 L7 0 L-7 0 Z"/></g><circle class="cpc" r="4"/>'
                '<text class="cl" y="-58" text-anchor="middle">N</text></g>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
<title>{name}</title>
<defs>
<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
@keyframes fi{{from{{opacity:0}}to{{opacity:1}}}}
.d{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;opacity:0;animation:draw 1.1s cubic-bezier(.12,.7,.3,1) both}}
.e{{fill:none;stroke:{GOLD};stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;opacity:0;animation:draw 1.2s cubic-bezier(.12,.7,.3,1) both}}
@keyframes draw{{0%{{stroke-dashoffset:1;opacity:0}}1%{{opacity:1}}100%{{stroke-dashoffset:0;opacity:1}}}}
.rg{{fill:none;stroke-width:2;stroke-linejoin:round;opacity:0;animation:fi 1.4s ease-out both}}
.flame{{fill:none;stroke:#ff9a3c;stroke-width:3;stroke-linejoin:round;opacity:0;transform-box:fill-box;transform-origin:50% 100%;animation:fi .8s ease-out both,flk 2.4s ease-in-out infinite alternate}}
@keyframes flk{{from{{transform:scale(1,1)}}to{{transform:scale(1.08,1.14)}}}}
.dr{{animation:dr {dur}s linear both}}@keyframes dr{{from{{transform:translate(0,0)}}to{{transform:translate(var(--dx),-26px)}}}}
.bob{{animation:bob 4s ease-in-out infinite alternate}}@keyframes bob{{from{{transform:translateY(-12px) rotate(-1.4deg)}}to{{transform:translateY(12px) rotate(1.4deg)}}}}
.t{{fill:none;text-anchor:middle;opacity:0;animation:fi .9s ease-out both}}
.star{{fill:#b9c9ff;opacity:.2;animation:tws 5s ease-in-out infinite alternate}}@keyframes tws{{from{{opacity:.1}}to{{opacity:.7}}}}
.cpc{{fill:none;stroke:#8fb0ff;stroke-width:2;opacity:0;animation:fi 1s ease-out 1.5s both}}
.nd{{fill:none;stroke:{GOLD};stroke-width:2.6;stroke-linejoin:round;opacity:0;animation:fi 1s ease-out 1.5s both}}
.nt{{fill:none;stroke:{ACC};stroke-width:2.6;stroke-linejoin:round;opacity:0;animation:fi 1s ease-out 1.5s both}}
.cl{{fill:#8fb0ff;font-size:20px;opacity:0;animation:fi 1s ease-out 1.5s both;font-family:Arial,sans-serif}}
.needle{{transform:rotate(78deg);animation:ndl {dur}s ease-in-out both}}@keyframes ndl{{0%{{transform:rotate(78deg)}}35%{{transform:rotate(104deg)}}70%{{transform:rotate(70deg)}}100%{{transform:rotate(96deg)}}}}
.all{{animation:out .9s linear {dur - 0.9:.1f}s both}}@keyframes out{{from{{opacity:1}}to{{opacity:0}}}}
</style>
</defs>
<rect width="1920" height="1080" fill="#05060d"/>
<g filter="url(#glow)" class="all">
<g>{stars}</g>
{ridges}
<g transform="translate(960 930) scale({scale})">{ev}</g>
{bl}{comp}
<text class="t" stroke="{GOLD}" stroke-width="1.8" x="960" y="1010" font-size="62" letter-spacing="14" {FONT} style="animation-delay:3.2s">{name}</text>
<text class="t" stroke="{ACC}" stroke-width="1.4" x="960" y="1056" font-size="24" letter-spacing="10" {FONT} style="animation-delay:3.6s">{sub}</text>
</g>
</svg>
'''


BASE_BALS = [(300, 250, .52), (640, 150, .38), (920, 300, .85), (1250, 190, .5), (1560, 330, 1.0), (1790, 160, .36), (1080, 120, .3)]


def europe_scenes(dur):
    """all 20 European landmarks in the balloons-over-landscape layout"""
    import gen_europe_overview as GO
    out = {}
    for s in ES.SITES:
        w, h = GO.CITIES[s['id']][3], GO.CITIES[s['id']][4]
        sc = min(1150 / w, 560 / h)
        seed = sum(map(ord, s['id']))
        r = random.Random(seed)
        base = [(x, y, z) for (x, y, z) in BASE_BALS]
        base[2] = (520 + (seed % 2) * 880, 300, .85)            # keep the big centre balloon off the monument's top
        bals = [(max(70, min(1850, x + r.randint(-70, 70))), y + r.randint(-40, 50), z * r.uniform(.85, 1.15), (i + seed) % 7) for i, (x, y, z) in enumerate(base)]
        out[s['id']] = (s['name'], s['country'], (lambda b=s['build']: b()[1]), sc, seed, bals, dur)
    return out


def korea_scenes(dur):
    import korea_sites as KS
    out = {}
    for sid, m in KS.KR.items():
        sc = min(1150 / m['w'], 560 / m['h'])
        seed = sum(map(ord, sid))
        r = random.Random(seed)
        base = list(BASE_BALS)
        base[2] = (520 + (seed % 2) * 880, 300, .85)
        bals = [(max(70, min(1850, x + r.randint(-70, 70))), y + r.randint(-40, 50), z * r.uniform(.85, 1.15), (i + seed) % 7) for i, (x, y, z) in enumerate(base)]
        out[sid] = (m['name'], m['country'], m['el'], sc, seed, bals, dur)
    return out


def mideast_scenes(dur):
    """20 Mediterranean / Middle East landmarks"""
    import mideast_sites as MS
    out = {}
    for sid, m in MS.ME.items():
        sc = min(1150 / m['w'], 560 / m['h'])
        seed = sum(map(ord, sid))
        r = random.Random(seed)
        base = list(BASE_BALS)
        base[2] = (520 + (seed % 2) * 880, 300, .85)
        bals = [(max(70, min(1850, x + r.randint(-70, 70))), y + r.randint(-40, 50), z * r.uniform(.85, 1.15), (i + seed) % 7) for i, (x, y, z) in enumerate(base)]
        out[sid] = (m['name'], m['country'], m['el'], sc, seed, bals, dur)
    return out


SCENES = {
    'cappadocia': ('CAPPADOCIA', 'GOREME · TURKIYE', lambda: WS.cappadocia(), 1.5, 11),
    'giza': ('PYRAMIDS OF GIZA', 'EGYPT', lambda: WS.giza(), 1.15, 12),
    'rome': ('COLOSSEUM', 'ROME · ITALY', lambda: [s for s in ES.SITES if s['id'] == 'rome'][0]['build']()[1], 1.35, 13),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    want = sys.argv[1:]
    allsc = dict(europe_scenes(13.6))
    for sid, (name, sub, el, sc, seed) in SCENES.items():
        allsc.setdefault(sid, (name, sub, el, sc, seed, None, 14.0))
    kr = korea_scenes(13.6)
    for sid in [w for w in want if w in kr]:
        name, sub, el, sc, seed, bals, dur = kr[sid]
        os.makedirs(os.path.join(OUT, 'korea'), exist_ok=True)
        open(os.path.join(OUT, 'korea', f'{sid}.svg'), 'w', encoding='utf-8').write(scene(sid, name, sub, el(), sc, seed, bals, dur, compass=True))
        print('wrote', sid)
    want = [w for w in want if w not in kr]
    if sys.argv[1:] and not want:
        return
    me = mideast_scenes(13.6)
    for sid in want or list(allsc) + list(me):
        if sid in me:
            name, sub, el, sc, seed, bals, dur = me[sid]
            folder = os.path.join(OUT, 'mideast')
            os.makedirs(folder, exist_ok=True)
            open(os.path.join(folder, f'{sid}.svg'), 'w', encoding='utf-8').write(scene(sid, name, sub, el(), sc, seed, bals, dur))
            print('wrote', sid)
            continue
        name, sub, el, sc, seed, bals, dur = allsc[sid]
        folder = OUT if sid in SCENES and sid != 'rome' else os.path.join(OUT, 'europe')
        os.makedirs(folder, exist_ok=True)
        open(os.path.join(folder, f'{sid}.svg'), 'w', encoding='utf-8').write(scene(sid, name, sub, el(), sc, seed, bals, dur))
        print('wrote', sid)


if __name__ == '__main__':
    main()
