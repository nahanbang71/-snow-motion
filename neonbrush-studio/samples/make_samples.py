#!/usr/bin/env python3
"""Generate synthetic test packs + photos (so the whole system can be verified without the real artwork).
  samples/TestMono.zip   white brush-like glyphs, A-Z 0-9 , ' ! ? & @
  samples/TestNeon.zip   neon glow glyphs (cyan/magenta) -> colour font path
  samples/images/*.png   3 test photos for the batch watermarker
"""
import io
import os
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_CANDIDATES = ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
                   '/Library/Fonts/Arial Bold.ttf', 'C:/Windows/Fonts/arialbd.ttf']
CHARS = {**{c: c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'}, 'COMMA': ',', 'APOS': "'", 'EXCL': '!', 'QUEST': '?', 'AMP': '&', 'AT': '@'}
N = 1024


def font(size):
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default(size)


def mono_glyph(ch):
    im = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font(780)
    d.text((N / 2, N / 2), ch, font=f, fill=(255, 255, 255, 255), anchor='mm')
    return im


def neon_glyph(ch):
    mask = Image.new('L', (N, N), 0)
    ImageDraw.Draw(mask).text((N / 2, N / 2), ch, font=font(700), fill=255, anchor='mm', stroke_width=0)
    core = mask.filter(ImageFilter.MinFilter(15))
    ring = Image.composite(Image.new('L', (N, N), 255), Image.new('L', (N, N), 0), mask.point(lambda v: 255 if v > 128 else 0))
    glow = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    for r, col, a in ((60, (255, 0, 200), 120), (30, (255, 60, 220), 170), (12, (80, 240, 255), 230)):
        layer = Image.new('RGBA', (N, N), col + (0,))
        layer.putalpha(mask.filter(ImageFilter.GaussianBlur(r)).point(lambda v, a=a: min(255, v * a // 160)))
        glow.alpha_composite(layer)
    body = Image.new('RGBA', (N, N), (255, 255, 255, 0))
    body.putalpha(core)
    glow.alpha_composite(body)
    return glow


def zip_pack(path, fn):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for stem, ch in CHARS.items():
            b = io.BytesIO()
            fn(ch).save(b, 'PNG')
            z.writestr(f'{stem}.png', b.getvalue())


def photos(outdir):
    os.makedirs(outdir, exist_ok=True)
    for name, (w, h), (c1, c2) in (('photo_a', (800, 600), ((20, 80, 160), (240, 160, 60))), ('photo_b', (1200, 900), ((10, 120, 90), (200, 230, 120))),
                                   ('photo_c', (640, 640), ((120, 20, 90), (250, 120, 150)))):
        im = Image.new('RGB', (w, h))
        px = im.load()
        for y in range(h):
            for x in range(w):
                t = (x / w + y / h) / 2
                px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        im.save(os.path.join(outdir, name + '.png'))


def main():
    zip_pack(os.path.join(HERE, 'TestMono.zip'), mono_glyph)
    zip_pack(os.path.join(HERE, 'TestNeon.zip'), neon_glyph)
    photos(os.path.join(HERE, 'images'))
    print('samples written to', HERE)


if __name__ == '__main__':
    sys.exit(main())
