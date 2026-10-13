#!/usr/bin/env python3
"""Europe-from-a-balloon film: title (8 s) + 20 landmark scenes (14 s each) + credits (12 s) = 300 s -> 유럽열기구/유럽_열기구_5분.mp4"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_balloon_designs as BD  # noqa: E402
import gen_europe as GE  # noqa: E402

ROOT = os.path.join(HERE, '..', '유럽열기구')
SVG, PARTS = os.path.join(ROOT, 'svg'), os.path.join(ROOT, 'parts')
os.makedirs(PARTS, exist_ok=True)
ORDER = ['edinburgh', 'stonehenge', 'london', 'amsterdam', 'eiffel', 'mont', 'lisbon', 'barcelona', 'rome', 'pisa', 'venice',
         'cologne', 'neuschwanstein', 'prague', 'vienna', 'budapest', 'dubrovnik', 'athens', 'istanbul', 'moscow']
GOLD, ACC = GE.GOLD, GE.ACC
FONT = GE.FONT


def title_svg():
    cols = BD.CH
    k = [0]

    def p(d, color, w=2.6):
        s = f'<path class="d" pathLength="1" stroke="{color}" stroke-width="{w}" style="animation-delay:{k[0] * .08:.2f}s" d="{d}"/>'
        k[0] += 1
        return s
    mouth, ropes, basket, flame = BD.gear('')
    g = p(BD.outline(), GOLD, 3.2) + ''.join(p(BD.band(y, 34), cols[i], 3.4) for i, y in enumerate((-176, -112, -50, 12, 76)))
    g += ''.join(p(BD.meridian(s), '#8a7a52', 1.6) for s in (-.5, 0, .5)) + p(mouth, GOLD, 2.8) + p(ropes, GOLD, 2.2) + p(basket, GOLD, 3)
    bars = ''.join(f'<path class="d" pathLength="1" stroke="{c}" stroke-width="6" style="animation-delay:{3.4 + i * .25:.2f}s;animation-duration:.8s" d="M{660 + i * 120} 880 H{740 + i * 120}"/>' for i, c in enumerate(cols))
    rnd = __import__('random').Random(5)
    stars = ''.join(f'<circle class="star" cx="{rnd.randint(20, 1900)}" cy="{rnd.randint(30, 1050)}" r="{rnd.choice((1, 1.2, 1.6, 2))}" style="animation-duration:{rnd.uniform(3, 7):.1f}s;animation-delay:-{rnd.uniform(0, 6):.1f}s"/>' for _ in range(90))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080"><title>Europe from above, title</title>
<defs><filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>.d{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;opacity:0;animation:draw 1.4s cubic-bezier(.12,.7,.3,1) both}}
@keyframes draw{{0%{{stroke-dashoffset:1;opacity:0}}1%{{opacity:1}}100%{{stroke-dashoffset:0;opacity:1}}}}
.flame{{fill:none;stroke:#ff9a3c;stroke-width:2.6;stroke-linejoin:round;opacity:0;transform-box:fill-box;transform-origin:50% 100%;animation:fi 1s ease-out 1.6s both,flk 2.4s ease-in-out 2.6s infinite alternate}}
@keyframes fi{{from{{opacity:0}}to{{opacity:1}}}}@keyframes flk{{from{{transform:scale(1,1)}}to{{transform:scale(1.07,1.12)}}}}
.bob{{animation:bob 4s ease-in-out infinite alternate}}@keyframes bob{{from{{transform:translateY(-8px) rotate(-1deg)}}to{{transform:translateY(8px) rotate(1deg)}}}}
.t{{fill:none;text-anchor:middle;opacity:0;animation:fi 1s ease-out both}}
.star{{fill:#b9c9ff;opacity:.2;animation:tws 5s ease-in-out infinite alternate}}@keyframes tws{{from{{opacity:.1}}to{{opacity:.7}}}}
.all{{animation:out 1s linear 7s both}}@keyframes out{{from{{opacity:1}}to{{opacity:0}}}}</style></defs>
<rect width="1920" height="1080" fill="#05060d"/>
<g filter="url(#glow)" class="all"><g>{stars}</g>
<g transform="translate(960 330) scale(.95)"><g class="bob">{g}<path class="flame" d="{flame}"/></g></g>
<text class="t" stroke="{cols[0]}" stroke-width="2" x="960" y="740" font-size="110" letter-spacing="18" {FONT} style="animation-delay:1.8s">EUROPE FROM ABOVE</text>
<text class="t" stroke="{cols[4]}" stroke-width="1.8" x="960" y="810" font-size="32" letter-spacing="16" {FONT} style="animation-delay:2.6s">HOT-AIR BALLOON · LASER LINE ART</text>{bars}</g></svg>
'''


def credits_svg():
    cols = BD.CH
    lines = [('CREDITS', 90, 300, cols[0], 'none', 22, 0.2), ('EUROPE FROM ABOVE — LASER LINE ART', 40, 430, cols[4], 'none', 8, 1.0),
             ('ElevenSeoul', 56, 580, cols[1], 'none', 14, 2.2),
             ('Daesan Oh', 44, 660, cols[3], 'none', 14, 3.4),
             ('Thank you for floating with us', 36, 780, cols[2], 'none', 6, 5.0)]
    t = ''
    for txt, size, y, c, fill, ls, d in lines:
        attr = f'fill="none" stroke="{c}" stroke-width="1.8"' if fill == 'none' else f'fill="{fill}"'
        t += f'<text class="t" {attr} x="960" y="{y}" font-size="{size}" letter-spacing="{ls}" {FONT} style="animation-delay:{d}s">{txt}</text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080"><title>Europe from above, credits</title>
<defs><filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>.t{{text-anchor:middle;opacity:0;animation:fi 1s ease-out both}}@keyframes fi{{from{{opacity:0}}to{{opacity:1}}}}.all{{animation:out 1s linear 11s both}}@keyframes out{{from{{opacity:1}}to{{opacity:0}}}}</style></defs>
<rect width="1920" height="1080" fill="#05060d"/><g filter="url(#glow)" class="all">{t}</g></svg>
'''


def main():
    open(os.path.join(SVG, 'title.svg'), 'w', encoding='utf-8').write(title_svg())
    open(os.path.join(SVG, 'credits.svg'), 'w', encoding='utf-8').write(credits_svg())
    seq = [('title', 8)] + [(i, 14) for i in ORDER] + [('credits', 12)]
    assert sum(s for _, s in seq) == 300, sum(s for _, s in seq)

    def run(job):
        i, (name, sec) = job
        out = os.path.join(PARTS, f'{i:02d}_{name}.mp4')
        if not os.path.exists(out):
            subprocess.run(['node', os.path.join(HERE, 'render_airport.js'), 'video', os.path.join(SVG, f'{name}.svg'), out + '.tmp.mp4', str(sec)], check=True)
            os.rename(out + '.tmp.mp4', out)
        print('done', out, flush=True)
    with ThreadPoolExecutor(int(os.environ.get('JOBS', 4))) as ex:
        list(ex.map(run, list(enumerate(seq))))
    lst = os.path.join(PARTS, 'list.txt')
    open(lst, 'w').write(''.join("file '%s'\n" % os.path.abspath(os.path.join(PARTS, f'{i:02d}_{n}.mp4')) for i, (n, _) in enumerate(seq)))
    final = os.path.join(ROOT, '유럽_열기구_5분.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-movflags', '+faststart', final], check=True)
    print('joined', final)


if __name__ == '__main__':
    main()
