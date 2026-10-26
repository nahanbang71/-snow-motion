#!/usr/bin/env python3
"""Glyph PNGs (alpha = ink) -> TTF + OTF.   pip install fonttools potracer pillow numpy
usage: python3 tools/png_to_font.py <png_dir> <out_dir> <FamilyName> [--no-lower]

File names: single character (A.png, 7.png) or a keyword: COMMA APOS EXCL QUEST PERIOD HYPHEN COLON SEMI.
Glyph placement inside the PNG canvas is kept (all glyphs share one scale and baseline); the baseline is the
bottom of the flat-bottomed capitals (median of the undecorated K/L/N/P/U), cap height is the median of their tops.
"""
import os
import sys
import glob
import numpy as np
from PIL import Image
import potrace
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen

NAMES = {'COMMA': ',', 'APOS': "'", 'EXCL': '!', 'QUEST': '?', 'PERIOD': '.', 'HYPHEN': '-', 'COLON': ':', 'SEMI': ';'}
GLYPH_NAMES = {',': 'comma', "'": 'quotesingle', '!': 'exclam', '?': 'question', '.': 'period', '-': 'hyphen', ':': 'colon', ';': 'semicolon'}
UPM, CAP = 1000, 700
SB = 50          # side bearing
SS = 2           # supersample for smoother outlines


def trace_glyph(path):
    a = np.array(Image.open(path).convert('RGBA'))[..., 3]
    im = Image.fromarray(a).resize((a.shape[1] * SS, a.shape[0] * SS), Image.LANCZOS)
    bm = potrace.Bitmap(np.array(im) <= 127)  # potracer treats dark (low) pixels as ink
    return bm.trace(turdsize=12 * SS * SS, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY, alphamax=1.0, opticurve=True, opttolerance=0.4)


def draw(plist, tf, pen):
    """tf: (x_px, y_px) in supersampled px -> font units"""
    P = lambda pt: tf(pt.x, pt.y)
    for curve in plist:
        pen.moveTo(P(curve.start_point))
        for seg in curve.segments:
            if seg.is_corner:
                pen.lineTo(P(seg.c)); pen.lineTo(P(seg.end_point))
            else:
                pen.curveTo(P(seg.c1), P(seg.c2), P(seg.end_point))
        pen.closePath()


def signed_area(rec):
    """sum of signed polygon areas over on-curve + control points (good enough for orientation)"""
    total, pts = 0.0, []
    for op, args in rec.value:
        if op in ('moveTo', 'lineTo', 'curveTo', 'qCurveTo'):
            pts.extend(a for a in args if a is not None)
        elif op == 'closePath':
            n = len(pts)
            total += sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) / 2
            pts = []
    return total


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 3:
        sys.exit(__doc__)
    src, out, family = args[:3]
    lower = '--no-lower' not in sys.argv
    os.makedirs(out, exist_ok=True)

    files = {}
    for f in sorted(glob.glob(os.path.join(src, '*.png'))):
        stem = os.path.splitext(os.path.basename(f))[0]
        ch = NAMES.get(stem.upper(), stem if len(stem) == 1 else None)
        if ch is None:
            print('skip (not a single character):', os.path.basename(f))
            continue
        files[ch] = f

    # common scale / baseline from capitals
    bbox = {}
    for ch, f in files.items():
        al = np.array(Image.open(f).convert('RGBA'))[..., 3] > 127
        ys, xs = np.where(al)
        bbox[ch] = (xs.min(), xs.max(), ys.min(), ys.max())
    flat = [c for c in 'KLNPU' if c in bbox] or [c for c in bbox if c.isalpha()]
    base_y = float(np.median([bbox[c][3] for c in flat]))
    top_y = float(np.median([bbox[c][2] for c in flat]))
    k = CAP / (base_y - top_y)
    print(f'baseline y={base_y:.0f}px  cap top y={top_y:.0f}px  scale={k:.4f} units/px')

    glyphs_tt, glyphs_cff, adv, cmap, order = {}, {}, {}, {}, ['.notdef', 'space']
    notdef_tt = TTGlyphPen(None); notdef_cff = T2CharStringPen(UPM // 2, None)
    for p in (notdef_tt, notdef_cff):
        p.moveTo((50, 0)); p.lineTo((50, 700)); p.lineTo((450, 700)); p.lineTo((450, 0)); p.closePath()
        p.moveTo((100, 50)); p.lineTo((400, 50)); p.lineTo((400, 650)); p.lineTo((100, 650)); p.closePath()
    glyphs_tt['.notdef'] = notdef_tt.glyph(); glyphs_cff['.notdef'] = notdef_cff.getCharString(); adv['.notdef'] = UPM // 2
    sp_tt = TTGlyphPen(None); glyphs_tt['space'] = sp_tt.glyph()
    sp_cff = T2CharStringPen(300, None); glyphs_cff['space'] = sp_cff.getCharString(); adv['space'] = 300
    cmap[0x20] = 'space'

    for ch, f in sorted(files.items()):
        x0, x1 = bbox[ch][0], bbox[ch][1]
        name = GLYPH_NAMES.get(ch, ch if ch.isalnum() and not ch.isdigit() else {'0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'}.get(ch, 'uni%04X' % ord(ch)))
        if ch.isalpha():
            name = ch
        tf = lambda x, y: (round((x / SS - x0) * k + SB), round((base_y - y / SS) * k))
        plist = trace_glyph(f)
        rec = RecordingPen(); draw(plist, tf, rec)
        flip = signed_area(rec) > 0   # TrueType wants clockwise outers; CFF counter-clockwise
        width = round((x1 - x0) * k + 2 * SB)
        # TrueType (quadratic)
        tt = TTGlyphPen(None); pen = Cu2QuPen(ReverseContourPen(tt) if flip else tt, max_err=1.0, reverse_direction=False)
        rec.replay(pen); glyphs_tt[name] = tt.glyph()
        # CFF (cubic): outer counter-clockwise
        cf = T2CharStringPen(width, None); pen = cf if flip else ReverseContourPen(cf)
        rec.replay(pen); glyphs_cff[name] = cf.getCharString()
        adv[name] = width
        order.append(name)
        cps = [ord(ch)]
        if ch.isalpha() and lower:
            cps.append(ord(ch.lower()))
        if ch == "'":
            cps.append(0x2019)
        for cp in cps:
            cmap[cp] = name
        print(f'  {ch!r:5} -> {name:12} width {width}')

    order = list(dict.fromkeys(order))
    names = {'familyName': family, 'styleName': 'Regular', 'uniqueFontIdentifier': f'{family}-Regular', 'fullName': family,
             'psName': family.replace(' ', '') + '-Regular', 'version': 'Version 1.000'}
    metrics = {g: (adv[g], 0) for g in order}

    def build(kind):
        fb = FontBuilder(UPM, isTTF=(kind == 'ttf'))
        fb.setupGlyphOrder(order); fb.setupCharacterMap(cmap)
        if kind == 'ttf':
            fb.setupGlyf({g: glyphs_tt[g] for g in order})
        else:
            fb.setupCFF(names['psName'], {'FullName': family}, {g: glyphs_cff[g] for g in order}, {})
        fb.setupHorizontalMetrics({g: (adv[g], 0) for g in order})
        fb.setupHorizontalHeader(ascent=900, descent=-250)
        fb.setupNameTable(names)
        fb.setupOS2(sTypoAscender=900, sTypoDescender=-250, sTypoLineGap=0, usWinAscent=1000, usWinDescent=300,
                    sCapHeight=CAP, sxHeight=CAP, achVendID='NONE', fsType=0)
        fb.setupPost()
        if kind == 'ttf':
            fb.setupDummyDSIG() if hasattr(fb, 'setupDummyDSIG') else None
        path = os.path.join(out, f'{family.replace(" ", "")}-Regular.{kind if kind == "ttf" else "otf"}')
        fb.save(path)
        # recalc bounds / lsb from outlines
        from fontTools.ttLib import TTFont
        t = TTFont(path)
        if kind == 'ttf':
            for g in order:
                gl = t['glyf'][g]; gl.recalcBounds(t['glyf'])
                t['hmtx'][g] = (adv[g], getattr(gl, 'xMin', 0))
        else:
            t['hmtx'].metrics = {g: (adv[g], 0) for g in order}
        t.save(path); print('wrote', path)

    build('ttf'); build('otf')


main()
