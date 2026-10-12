"""05 문자·길상문 - dynamic versions: laser light running along the character outlines"""
import math
from fontTools.ttLib import TTCollection
from fontTools.pens.svgPathPen import SVGPathPen
from core import *
from alive import alive_svg, piv, grp
import text as T

_FONT = None


def glyph_d(ch, size, cx=0, cy=0):
    global _FONT
    if _FONT is None:
        _FONT = TTCollection('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc').fonts[0]
    gs = _FONT.getGlyphSet()
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.0f}")
    gs[_FONT.getBestCmap()[ord(ch)]].draw(pen)
    k = size / _FONT['head'].unitsPerEm
    return pen.getCommands(), f"translate({f(cx - size / 2)} {f(cy + size * .42)}) scale({k:.4f} {-k:.4f})"


def laser_glyph(ch, size, col, cx=0, cy=0, delay=0.0, beam='#ffffff'):
    d, tf = glyph_d(ch, size, cx, cy)
    return G(tf, f'<path class="l" stroke="{col[0]}" stroke-width="4.2" d="{d}"/>'
             f'<path class="l a-beam" pathLength="1" stroke="{beam}" stroke-width="5" d="{d}" style="animation-delay:{delay}s"/>'
             f'<path class="l a-beam" pathLength="1" stroke="{col[1]}" stroke-width="5" d="{d}" style="animation-delay:{delay + 1.4}s"/>')


BEAM_CSS = '''.a-beam{stroke-dasharray:.06 .94;stroke-dashoffset:.06;animation:beam 2.8s linear infinite}
.a-dots{animation:spin 40s linear infinite}
.a-dotsr{animation:spinr 28s linear infinite}
@keyframes beam{from{stroke-dashoffset:.06}to{stroke-dashoffset:-.94}}'''


def _single(ch, col, frame_kind, bg, fly):
    ring = grp('a-dots', around(8, lambda k: DOT(0, -90, col[1], 7), start=22.5)) + grp('a-dotsr', around(12, lambda k: DOT(0, -78, col[0], 4), start=0)) + P(circle(84), col[0], 1.6)
    glow = grp('a-glow', laser_glyph(ch, 130, col).replace('stroke-width="4.2"', 'stroke-width="6"').replace('class="l a-beam"', 'class="l a-beam" opacity="0"') if False else '')
    inner = ring + grp('a-glowp', laser_glyph(ch, 130, col))
    css = BEAM_CSS + '\n.a-glowp{animation:gp 2.4s ease-in-out infinite alternate}\n@keyframes gp{from{opacity:.7}to{opacity:1}}'
    return alive_svg(inner, f'{ch} - alive', css, bg=bg, fr=frame_kind, flycol=fly)


def su():
    return _single('壽', RED, ('cloud', GOLD), ('#4a0a18', '#120208'), '#ffb3c1')


def bok():
    return _single('福', ORANGE, ('petal', GOLD), ('#4a2a08', '#120802'), '#ffd4a8')


def hui():
    return _single('喜', PINK, ('ticks', PINK), ('#40103a', '#10030e'), '#ffc1f2')


def ssanghui():
    return _single('囍', RED, ('octagon', GOLD), ('#4a0a10', '#140205'), '#ffb3c1')


def subokgangnyeong():
    s = ''
    for k, (ch, x, y, col) in enumerate((('壽', -42, -42, RED), ('福', 42, -42, ORANGE), ('康', -42, 42, TEAL), ('寧', 42, 42, BLUE))):
        s += grp('a-seq', laser_glyph(ch, 74, col, x, y, delay=k * .7), f'animation-delay:{k * 1.1:.1f}s')
    s += grp('a-dots', P(circle(14), GOLD[0], 3) + around(6, lambda k: DOT(0, -22, GOLD[1], 6)))
    css = BEAM_CSS + '\n.a-seq{animation:seq 4.4s ease-in-out infinite}\n@keyframes seq{0%,100%{opacity:.55}25%{opacity:1}50%{opacity:.7}}'
    return alive_svg(s, 'Subokgangnyeong - alive', css, bg=('#1c1050', '#05030f'), fr=('dancheong', None), flycol='#ffe0a0')


def palbo():
    icons = [T._wheel, T._conch, T._parasol, T._canopy, T._lotus, T._vase, T._fish, T._knot]
    s = ''
    for k, fn in enumerate(icons):
        x, y = pt(66, k * 45)
        s += G(f"translate({f(x)} {f(y)})", grp('a-icon', G("scale(1.45)", fn()) + P(circle(25), GOLD[0], 1.4), f'animation-delay:{k * .45:.2f}s'))
    s += P(circle(30), GOLD[0], 3.4) + grp('a-dots', P(spiral(0, 0, 24, 3, 2.2), GOLD[1], 1.8))
    css = BEAM_CSS + '''
.a-icon{animation:icon 3.6s ease-in-out infinite}
@keyframes icon{0%,100%{transform:scale(1)}50%{transform:scale(1.18)}}'''
    return alive_svg(grp('a-ringturn', s), 'Palbo - alive', css + '\n.a-ringturn{animation:spin 90s linear infinite}', bg=('#2a1050', '#07030f'), fr=('gold', GOLD), flycol='#e6d6ff')


TEXT = {'su': su, 'bok': bok, 'hui': hui, 'ssanghui': ssanghui, 'subokgangnyeong': subokgangnyeong, 'palbo': palbo}
