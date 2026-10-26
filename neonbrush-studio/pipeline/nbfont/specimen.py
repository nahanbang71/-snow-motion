"""Preview images (so a human can check the result): mono via FreeType, colour via PNG composite."""
from PIL import Image, ImageDraw, ImageFont

from . import layout as lay

LINES = ['ABCDEFGHIJKLM', 'NOPQRSTUVWXYZ', '0123456789 ,\'!?', 'The quick brown fox']


def _lines(have):
    out = []
    for line in LINES:
        t = ''.join(c for c in line if c == ' ' or c.upper() in have or c in have)
        if t.strip():
            out.append(t)
    return out


def mono(font_path, out_png, bg='#202124', fg='#ffffff', size=120):
    from fontTools.ttLib import TTFont
    have = {chr(c) for c in TTFont(font_path).getBestCmap()}
    lines = _lines(have)
    f = ImageFont.truetype(font_path, size)
    im = Image.new('RGB', (1800, int((len(lines) + .4) * size * 1.35)), bg)
    d = ImageDraw.Draw(im)
    for i, line in enumerate(lines):
        d.text((40, 20 + i * size * 1.35), line, font=f, fill=fg)
    im.save(out_png)


def color(arrays, place, out_png, bg='#202124', size=120):
    """Typeset with the original PNGs (what an OpenType-SVG capable app shows)."""
    s = size / lay.UPM
    lines = _lines(set(arrays))
    im = Image.new('RGBA', (1800, int((len(lines) + .4) * size * 1.35)), bg)
    for i, line in enumerate(lines):
        pen = 40.0
        base = 20 + i * size * 1.35 + size * 0.95
        for c in line:
            c = c.upper() if c.isalpha() else c
            if c == ' ':
                pen += lay.SPACE * s; continue
            if c not in arrays:
                continue
            p = place[c]
            ks = p['scale'] * s
            g = Image.fromarray(arrays[c]).resize((round(1024 * ks), round(1024 * ks)), Image.LANCZOS)
            x = pen + (lay.SB - p['x0'] * p['scale']) * s
            y = base - p['ybase'] * ks
            im.alpha_composite(g, (int(x), int(y))) if x >= 0 and y >= 0 else im.paste(g, (int(x), int(y)), g)
            pen += p['adv'] * s
    im.convert('RGB').save(out_png)
