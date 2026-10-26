"""Post-build verification: cmap coverage, HarfBuzz shaping (typing check), OpenType-SVG sanity."""
import base64
import io
import re
import xml.etree.ElementTree as ET

import uharfbuzz as hb
from PIL import Image
from fontTools.ttLib import TTFont

SAMPLE = 'THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG 0123456789'


def verify(path, chars, color=False):
    res = {'file': path, 'ok': True, 'errors': []}
    t = TTFont(path)
    cmap = t.getBestCmap()
    order = t.getGlyphOrder()
    for ch in chars:
        if ord(ch) not in cmap:
            res['errors'].append(f'missing cmap for {ch!r}')
        if ch.isascii() and ch.isalpha() and ord(ch.lower()) not in cmap:
            res['errors'].append(f'missing lowercase cmap for {ch!r}')
    # shape typed text through HarfBuzz and compare with hmtx advances
    face = hb.Face(hb.Blob.from_file_path(path))
    font = hb.Font(face)
    text = ''.join(c for c in SAMPLE if ord(c) in cmap)
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(font, buf, {})
    got = [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]
    want = [cmap[ord(c)] for c in text]
    if got != want:
        res['errors'].append('HarfBuzz glyph sequence differs from cmap')
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        if pos.x_advance != t['hmtx'][order[info.codepoint]][0]:
            res['errors'].append('advance mismatch'); break
    res['shaped'] = len(got)
    if color:
        if 'SVG ' not in t:
            res['errors'].append('no SVG table')
        else:
            n = 0
            for d in t['SVG '].docList:
                root = ET.fromstring(d.data)
                img = root.find('.//{http://www.w3.org/2000/svg}image')
                href = img.get('{http://www.w3.org/1999/xlink}href')
                png = Image.open(io.BytesIO(base64.b64decode(re.sub(r'^data:image/png;base64,', '', href))))
                gid = d.startGlyphID
                if root.find('.//{http://www.w3.org/2000/svg}g').get('id') != f'glyph{gid}':
                    res['errors'].append(f'svg id mismatch gid {gid}')
                if png.mode != 'RGBA':
                    res['errors'].append(f'svg png not RGBA gid {gid}')
                n += 1
            res['svg_docs'] = n
    res['ok'] = not res['errors']
    return res
