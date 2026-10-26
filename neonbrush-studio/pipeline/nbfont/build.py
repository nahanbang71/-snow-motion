"""Pack -> cleaned glyph arrays -> TTF / OTF (mono) and OpenType-SVG colour OTF."""
import base64
import io
import os

import numpy as np
from PIL import Image
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables.S_V_G_ import SVGDocument

from . import clean as cl, layout as lay, vector
from .naming import glyph_name

ASCENT, DESCENT = 900, -250


# ---------------------------------------------------------------- preparation
def prepare(pack):
    """Decode + clean every glyph. Returns (arrays, boxes, report)."""
    arrays, boxes, rep = {}, {}, {}
    opt = pack.options
    for ch, data in pack.glyphs.items():
        rgba = cl.load_rgba(data)
        rgba, info = cl.clean(rgba)
        if opt.get('clean') == 'neighbors':
            rgba, i2 = cl.keep_center_groups(rgba, opt.get('gap', 3), opt.get('band', 48))
            info.update(i2)
        bb = cl.bbox(rgba, 60)
        if bb is None:
            rep[ch] = {'error': 'empty glyph'}
            continue
        arrays[ch], boxes[ch], rep[ch] = rgba, bb, info
    return arrays, boxes, rep


def is_color_pack(arrays):
    """True when a noticeable share of opaque pixels is chromatic (neon / multi-colour art; white/black/grey packs score 0)."""
    tot = col = 0
    for rgba in arrays.values():
        m = rgba[..., 3] > 200
        rgb = rgba[..., :3][m].astype(int)
        if len(rgb):
            tot += len(rgb)
            col += int(((rgb.max(1) - rgb.min(1)) > 30).sum())
    return tot > 0 and col / tot > 0.01


# ---------------------------------------------------------------- outlines
def _signed_area(rec):
    total, pts = 0.0, []
    for op, args in rec.value:
        if op in ('moveTo', 'lineTo', 'curveTo', 'qCurveTo'):
            pts.extend(a for a in args if a is not None)
        elif op == 'closePath':
            n = len(pts)
            total += sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) / 2
            pts = []
    return total


def make_glyphs(arrays, place, opt):
    tt, cff, adv, names = {}, {}, {}, {}
    thr = opt.get('threshold', 96)
    for ch, rgba in arrays.items():
        p = place[ch]
        ks, x0, yb = p['scale'], p['x0'], p['ybase']
        plist = vector.trace(rgba, thr, mono_source=opt.get('mono_source', 'alpha'))
        tf = lambda x, y: (round((x / vector.SS - x0) * ks + lay.SB), round((yb - y / vector.SS) * ks))
        rec = RecordingPen(); vector.replay(plist, tf, rec)
        flip = _signed_area(rec) > 0                  # TrueType: outer contours clockwise; CFF: counter-clockwise
        g = TTGlyphPen(None)
        rec.replay(Cu2QuPen(ReverseContourPen(g) if flip else g, max_err=1.0, reverse_direction=False))
        tt[ch] = g.glyph()
        c = T2CharStringPen(p['adv'], None)
        rec.replay(c if flip else ReverseContourPen(c))
        cff[ch] = c.getCharString()
        adv[ch] = p['adv']
    return tt, cff, adv


def _cmap(chars, lower):
    cmap = {0x20: 'space'}
    for ch in chars:
        gn = glyph_name(ch)
        cmap[ord(ch)] = gn
        if ch.isascii() and ch.isalpha() and lower:
            cmap[ord(ch.lower())] = gn
        if ch == "'":
            cmap[0x2019] = gn
        if ch == '"':
            cmap[0x201D] = gn
    return cmap


def _notdef(pen):
    pen.moveTo((50, 0)); pen.lineTo((50, 700)); pen.lineTo((450, 700)); pen.lineTo((450, 0)); pen.closePath()
    pen.moveTo((100, 50)); pen.lineTo((400, 50)); pen.lineTo((400, 650)); pen.lineTo((100, 650)); pen.closePath()


def _assemble(kind, family, style, chars, glyphs, adv, svg_docs=None, lower=True, version='1.000'):
    tt, cff = glyphs
    order = ['.notdef', 'space'] + [glyph_name(c) for c in chars]
    nd_tt, nd_cf = TTGlyphPen(None), T2CharStringPen(lay.UPM // 2, None)
    _notdef(nd_tt); _notdef(nd_cf)
    sp_tt, sp_cf = TTGlyphPen(None), T2CharStringPen(lay.SPACE, None)
    advs = {'.notdef': lay.UPM // 2, 'space': lay.SPACE}
    gl_tt = {'.notdef': nd_tt.glyph(), 'space': sp_tt.glyph()}
    gl_cf = {'.notdef': nd_cf.getCharString(), 'space': sp_cf.getCharString()}
    for c in chars:
        n = glyph_name(c)
        gl_tt[n], gl_cf[n], advs[n] = tt[c], cff[c], adv[c]
    ps = ''.join(ch for ch in family if ch.isalnum()) + '-' + style.replace(' ', '')
    names = {'familyName': family, 'styleName': style, 'uniqueFontIdentifier': f'{ps};{version}', 'fullName': f'{family} {style}'.strip(),
             'psName': ps, 'version': f'Version {version}'}
    fb = FontBuilder(lay.UPM, isTTF=(kind == 'ttf'))
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(_cmap(chars, lower))
    if kind == 'ttf':
        fb.setupGlyf(gl_tt)
    else:
        fb.setupCFF(ps, {'FullName': names['fullName']}, gl_cf, {})
    fb.setupHorizontalMetrics({g: (advs[g], 0) for g in order})
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupNameTable(names)
    fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=DESCENT, sTypoLineGap=0, usWinAscent=1000, usWinDescent=300,
                sCapHeight=lay.CAP, sxHeight=lay.CAP, achVendID='NONE', fsType=0)
    fb.setupPost()
    font = fb.font
    if kind == 'ttf':
        for g in order:
            gl = font['glyf'][g]
            gl.recalcBounds(font['glyf'])
            font['hmtx'][g] = (advs[g], getattr(gl, 'xMin', 0))
    if svg_docs:
        t = newTable('SVG ')
        t.docList = [SVGDocument(doc, gid, gid, False) for gid, doc in sorted(svg_docs(order).items())]
        font['SVG '] = t
    return font


# ---------------------------------------------------------------- colour (OpenType-SVG)
def svg_documents(arrays, place, svg_px=384):
    """Returns f(order) -> {gid: svg document} with the original PNG embedded as a data URI."""
    def build(order):
        docs = {}
        for ch, rgba in arrays.items():
            gid = order.index(glyph_name(ch))
            p = place[ch]
            ks, x0, yb = p['scale'], p['x0'], p['ybase']
            bb = cl.bbox(rgba, 8)
            pad = 4
            cx0, cy0 = max(bb[0] - pad, 0), max(bb[1] - pad, 0)
            cx1, cy1 = min(bb[2] + pad, rgba.shape[1]), min(bb[3] + pad, rgba.shape[0])
            im = Image.fromarray(rgba[cy0:cy1, cx0:cx1])
            r = min(1.0, svg_px / max(im.size))
            if r < 1:
                im = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)
            buf = io.BytesIO(); im.save(buf, 'PNG', optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode()
            x = (cx0 - x0) * ks + lay.SB
            y = -(yb - cy0) * ks
            w, h = (cx1 - cx0) * ks, (cy1 - cy0) * ks
            docs[gid] = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
                         f'<g id="glyph{gid}"><image x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                         f'xlink:href="data:image/png;base64,{b64}"/></g></svg>')
        return docs
    return build


# ---------------------------------------------------------------- driver
def build_pack(pack, outdir, color='auto', svg_px=384, lower=True, log=print):
    """Build every font for one pack. Returns a report dict."""
    arrays, boxes, rep = prepare(pack)
    if not arrays:
        raise ValueError(f'{pack.name}: no usable glyphs')
    mode = pack.options.get('layout', 'auto')
    info, place = lay.plan(boxes, mode)
    chars = sorted(arrays, key=lambda c: (not c.isalpha(), not c.isdigit(), c))
    os.makedirs(outdir, exist_ok=True)
    family = pack.name
    tt, cf, adv = make_glyphs(arrays, place, pack.options)
    out = {}
    for kind in ('ttf', 'otf'):
        font = _assemble(kind, family, 'Regular', chars, (tt, cf), adv, lower=lower)
        path = os.path.join(outdir, f'{pack.slug}-Regular.{kind}')
        font.save(path); out[kind] = path
    colored = is_color_pack(arrays)
    if color == 'all' or (color == 'auto' and colored):
        font = TTFont(out['otf'])                          # same outlines as fallback + SVG colour glyphs
        fam, ps = family + ' Color', pack.slug + '-Color'
        for nid, val in ((1, fam), (3, ps + ';1.000'), (4, fam + ' Regular'), (6, ps)):
            font['name'].setName(val, nid, 3, 1, 0x409)
            font['name'].setName(val, nid, 1, 0, 0)
        t = newTable('SVG ')
        order = font.getGlyphOrder()
        t.docList = [SVGDocument(doc, gid, gid, False) for gid, doc in sorted(svg_documents(arrays, place, svg_px)(order).items())]
        font['SVG '] = t
        path = os.path.join(outdir, f'{pack.slug}-Color.otf')
        font.save(path); out['color'] = path
    return {'family': family, 'chars': ''.join(chars), 'layout': info, 'is_color': colored, 'files': out,
            'glyph_report': {c: r for c, r in rep.items() if r.get('removed_border') or r.get('removed_groups') or r.get('clipped') or r.get('error')},
            'notes': pack.notes, 'skipped': pack.skipped, 'arrays': arrays, 'place': place, 'boxes': boxes}
