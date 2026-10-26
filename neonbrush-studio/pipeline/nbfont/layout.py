"""Typographic layout: one shared scale + baseline for the whole pack (all values in font units, UPM 1000).

modes
  canvas  keep the glyph position inside the PNG canvas, one scale for all (packs that were typeset on a shared baseline)
  fit     every glyph scaled to the same cap height, bottoms on the baseline (packs whose glyphs were fitted to the canvas)
  align   one scale for all, but every glyph bottom sits on the baseline (tiles whose vertical position is arbitrary)
  auto    fit when glyphs are vertically centred with equal heights, else canvas
"""
import statistics

from .naming import LETTERS, DIGITS

UPM = 1000
CAP = 700
SB = 50            # side bearing
SPACE = 300


def plan(boxes, mode='auto', cap=CAP):
    """boxes: {char: (x0, y0, x1, y1)} in px (bbox of ink). Returns (info, {char: placement}).
    placement: scale (units/px), x0 (px), ybase (px that maps to y=0), adv (units)."""
    letters = [c for c in LETTERS if c in boxes] or [c for c in boxes if c.isalnum()] or list(boxes)
    hs = [boxes[c][3] - boxes[c][1] for c in letters]
    cys = [(boxes[c][1] + boxes[c][3]) / 2 for c in letters]
    med_h = statistics.median(hs)
    centered = (statistics.pstdev(cys) < 8) if len(cys) > 2 else False
    cv = (statistics.pstdev(hs) / statistics.mean(hs)) if len(hs) > 2 else 0
    if mode == 'auto':
        mode = 'fit' if (centered and cv < 0.055) else 'canvas'
    if centered:
        mid = statistics.median(cys)
        base, top = mid + med_h / 2, mid - med_h / 2
    else:
        base = statistics.median(boxes[c][3] for c in letters)
        top = statistics.median(boxes[c][1] for c in letters)
    k = cap / (base - top)
    place = {}
    fit_scales = []
    if mode == 'fit':
        for c in letters + [d for d in DIGITS if d in boxes]:
            h = boxes[c][3] - boxes[c][1]
            fit_scales.append(min(max(cap / h, .8 * k), 1.45 * k))
    kp = statistics.median(fit_scales) if fit_scales else k        # punctuation scale (k in align mode)
    for c, (x0, y0, x1, y1) in boxes.items():
        if mode in ('fit', 'align') and (c in LETTERS or c in DIGITS):
            ks = min(max(cap / (y1 - y0), .8 * k), 1.45 * k) if mode == 'fit' else k
            yb = y1                                       # bottom sits on the baseline
        elif mode in ('fit', 'align'):
            ks = kp
            if c in '!?':
                yb = y1
            elif c == ',':
                yb = y1 - 0.12 * cap / ks               # comma hangs below the baseline
            elif c in '\'"':
                yb = y0 + cap / ks                       # apostrophe hangs from cap height
            else:
                yb = base
        else:
            ks, yb = k, base
        place[c] = {'scale': ks, 'x0': x0, 'ybase': yb, 'adv': round((x1 - x0) * ks + 2 * SB)}
    return {'mode': mode, 'scale': k, 'base_px': base, 'top_px': top, 'centered': centered, 'cv': round(cv, 3)}, place
