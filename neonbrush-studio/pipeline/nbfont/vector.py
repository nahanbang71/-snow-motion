"""Alpha channel -> cubic Bezier outlines with potrace (potracer)."""
import numpy as np
from PIL import Image
import potrace

SS = 2   # supersample before tracing (smoother outlines)


def trace(rgba, threshold=96, turd=12, mono_source='alpha'):
    """Return potrace path list in *supersampled* pixel coordinates (divide by SS)."""
    a = rgba[..., 3].astype(np.uint8)
    if mono_source == 'white':        # strokes only: opaque AND near-white, drops coloured decoration
        rgb = rgba[..., :3].astype(int)
        white = (rgb.min(axis=2) > 170) & ((rgb.max(axis=2) - rgb.min(axis=2)) < 60)
        a = np.where(white, a, 0).astype(np.uint8)
    im = Image.fromarray(a).resize((a.shape[1] * SS, a.shape[0] * SS), Image.LANCZOS)
    bm = potrace.Bitmap(np.array(im) <= threshold)      # potracer treats dark pixels as ink
    kw = dict(turdsize=turd * SS * SS, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY, alphamax=1.0)
    for opticurve, tol in ((True, 0.4), (True, 0.2), (False, 0.4)):   # potracer can hit a math domain error in opticurve
        try:
            return bm.trace(opticurve=opticurve, opttolerance=tol, **kw)
        except ValueError:
            continue
    raise RuntimeError('potrace failed for this glyph')


def replay(plist, tf, pen):
    """tf maps supersampled px -> font units."""
    P = lambda pt: tf(pt.x, pt.y)
    for curve in plist:
        pen.moveTo(P(curve.start_point))
        for seg in curve.segments:
            if seg.is_corner:
                pen.lineTo(P(seg.c)); pen.lineTo(P(seg.end_point))
            else:
                pen.curveTo(P(seg.c1), P(seg.c2), P(seg.end_point))
        pen.closePath()
