"""Normalised 'web pack' zips for NeonBrush Studio: trimmed, cleaned PNGs + pack.json with typographic metrics."""
import io
import json
import zipfile

from PIL import Image

from . import layout as lay
from .naming import glyph_name


def write_webpack(path, name, arrays, boxes, place, is_color, source='', max_px=768):
    meta = {'format': 'neonbrush-webpack', 'version': 1, 'name': name, 'source': source, 'upm': lay.UPM, 'cap': lay.CAP,
            'space': lay.SPACE, 'sideBearing': lay.SB, 'isColor': bool(is_color), 'glyphs': {}}
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED) as z:       # PNGs are already compressed
        for ch, rgba in sorted(arrays.items()):
            x0, y0, x1, y1 = boxes[ch]
            pad = 2
            x0, y0 = max(x0 - pad, 0), max(y0 - pad, 0)
            x1, y1 = min(x1 + pad, rgba.shape[1]), min(y1 + pad, rgba.shape[0])
            buf = io.BytesIO()
            im = Image.fromarray(rgba[y0:y1, x0:x1])
            if max(im.size) > max_px:                      # metrics are in font units, so the image can be downsampled freely
                r = max_px / max(im.size)
                im = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)
            im.save(buf, 'PNG', optimize=True)
            fn = glyph_name(ch) + '.png'
            z.writestr(fn, buf.getvalue())
            p = place[ch]
            ks = p['scale']
            # image rectangle in font units, relative to the pen position / baseline (y up)
            meta['glyphs'][ch] = {'file': fn, 'left': round((x0 - p['x0']) * ks + lay.SB, 2), 'top': round((p['ybase'] - y0) * ks, 2),
                                  'w': round((x1 - x0) * ks, 2), 'h': round((y1 - y0) * ks, 2), 'adv': p['adv']}
        z.writestr('pack.json', json.dumps(meta, ensure_ascii=False, indent=1))
    return meta
