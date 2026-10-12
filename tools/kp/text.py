"""05 문자·길상문 (glyph outlines from WenQuanYi Zen Hei, converted to paths so no font is needed to view)"""
import math
from fontTools.ttLib import TTCollection
from fontTools.pens.svgPathPen import SVGPathPen
from core import *

_FONT = None


def glyph(ch, size, cx=0, cy=0, col=GOLD, w=4.2):
    """outline of a CJK character, fitted into a size x size box centred on (cx, cy)"""
    global _FONT
    if _FONT is None:
        _FONT = TTCollection('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc').fonts[0]
    gs = _FONT.getGlyphSet()
    name = _FONT.getBestCmap()[ord(ch)]
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.0f}")
    gs[name].draw(pen)
    upm = _FONT['head'].unitsPerEm
    k = size / upm
    tx, ty = cx - size / 2, cy + size * .42
    return G(f"translate({f(tx)} {f(ty)}) scale({k:.4f} {-k:.4f})",
             f'<path class="l" stroke="{col[0]}" stroke-width="{w}" d="{pen.getCommands()}"/>')


def _ring_deco():
    return around(8, lambda k: DOT(0, -90, GOLD[1], 6), start=22.5) + P(circle(84), GOLD[0], 1.6)


def su():
    return glyph('壽', 130, col=RED) + _ring_deco()


def bok():
    return glyph('福', 130, col=ORANGE) + _ring_deco()


def hui():
    return glyph('喜', 130, col=PINK) + _ring_deco()


def ssanghui():
    return glyph('囍', 134, col=RED) + _ring_deco()


def subokgangnyeong():
    s = ''
    for ch, x, y, col in (('壽', -42, -42, RED), ('福', 42, -42, ORANGE), ('康', -42, 42, TEAL), ('寧', 42, 42, BLUE)):
        s += glyph(ch, 74, x, y, col, 3.4)
    s += P(circle(12), GOLD[0], 3) + DOT(0, 0, GOLD[1], 7)
    return s


# --- eight treasures (palbo): wheel, conch, parasol, canopy, lotus, vase, twin fish, endless knot
def _wheel():
    return P(circle(14), GOLD[0], 3.2) + P(circle(5), GOLD[1], 2) + around(8, lambda k: P("M0 -5 L0 -14", GOLD[0], 2.6))


def _conch():
    return P(spiral(0, 2, 2, 13, 2, a0=-90), WHITE[0], 3.2) + P("M2 -12 C14 -12 16 6 4 14 C-8 18 -14 8 -12 -2", WHITE[1], 2.4)


def _parasol():
    return P("M-15 0 C-15 -16 15 -16 15 0Z", RED[0], 3.2) + P("M0 -14 L0 16 M0 16 q4 4 8 0", ORANGE[0], 2.6) + P("M-8 0 L-4 -13 M8 0 L4 -13", RED[1], 1.8)


def _canopy():
    return P("M-15 -8 L15 -8 L12 0 Q8 6 4 0 Q0 6 -4 0 Q-8 6 -12 0Z", VIOLET[0], 3.2) + P("M0 -8 L0 -16 M-4 -16 L4 -16", VIOLET[1], 2.4) + P("M-10 4 L-10 14 M10 4 L10 14", VIOLET[1], 2.2)


def _lotus():
    return around(5, lambda k: P(lens(16, 5, r0=0), PINK[0], 2.8), start=0)[:0] + ''.join(
        G(f"translate(0 8) rotate({a})", P(lens(18, 6), PINK[0], 2.8)) for a in (-50, -25, 0, 25, 50))


def _vase():
    return P("M-5 -14 L5 -14 L4 -8 C14 -2 14 12 6 14 L-6 14 C-14 12 -14 -2 -4 -8Z", TEAL[0], 3.2) + P("M-8 -2 L8 -2", TEAL[1], 1.8)


def _fish():
    return (P("M-14 0 C-8 -8 4 -8 10 0 C4 8 -8 8 -14 0Z", ORANGE[0], 3) + P("M10 0 L16 -6 L16 6Z", ORANGE[0], 2.6) + DOT(-9, -1, WHITE[1], 3.6)
            + G("translate(0 12) scale(-1 1)", P("M-14 0 C-8 -8 4 -8 10 0 C4 8 -8 8 -14 0Z", RED[0], 3) + P("M10 0 L16 -6 L16 6Z", RED[0], 2.6)))


def _knot():
    return P("M-12 -12 L12 -12 L12 12 L-12 12Z M-6 -12 L-6 12 M6 -12 L6 12 M-12 -6 L12 -6 M-12 6 L12 6", BLUE[0], 2.4) + P("M-6 -6 L6 -6 L6 6 L-6 6Z", BLUE[1], 2)


def palbo():
    icons = [_wheel, _conch, _parasol, _canopy, _lotus, _vase, _fish, _knot]
    s = ''
    for k, fn in enumerate(icons):
        x, y = pt(66, k * 45)
        s += G(f"translate({f(x)} {f(y)}) scale(1.45)", fn())
        s += P(circle(25, x, y), GOLD[0], 1.4)
    s += P(circle(30), GOLD[0], 3.4) + P(spiral(0, 0, 24, 3, 2.2), GOLD[1], 1.8)
    return s


PATTERNS = {
    'su': ('05_문자_길상문', '수(壽)', su), 'bok': ('05_문자_길상문', '복(福)', bok), 'hui': ('05_문자_길상문', '희(囍)', hui),
    'ssanghui': ('05_문자_길상문', '쌍희', ssanghui), 'subokgangnyeong': ('05_문자_길상문', '수복강녕', subokgangnyeong),
    'palbo': ('05_문자_길상문', '팔보', palbo),
}
