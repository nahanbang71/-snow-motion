"""Alpha clean-up: drop neighbour fragments that touch the image border (bad slicing) and tiny specks."""
import io

import numpy as np
from PIL import Image
from scipy import ndimage

STRUCT8 = np.ones((3, 3), int)


def load_rgba(data):
    return np.array(Image.open(io.BytesIO(data)).convert('RGBA'))


def clean(rgba, border=True, min_area=6, margin=1):
    """Return (rgba, info). Components touching the border (within margin px) are removed; so are specks < min_area px
    unless that would remove everything."""
    a = rgba[..., 3]
    mask = a > 8
    lab, n = ndimage.label(mask, structure=STRUCT8)
    info = {'removed_border': 0, 'removed_specks': 0, 'clipped': False}
    if n == 0:
        return rgba, info
    sizes = ndimage.sum(mask, lab, index=np.arange(1, n + 1))
    h, w = a.shape
    touch = np.zeros(n + 1, bool)
    for sl in (lab[:margin + 1, :], lab[-margin - 1:, :], lab[:, :margin + 1], lab[:, -margin - 1:]):
        touch[np.unique(sl)] = True
    touch[0] = False
    drop = np.zeros(n + 1, bool)
    if border:
        biggest = 1 + int(np.argmax(sizes))
        for i in range(1, n + 1):
            if touch[i] and i != biggest:
                drop[i] = True
        info['removed_border'] = int(drop.sum())
        info['clipped'] = bool(touch[biggest])         # the main glyph itself is cut by the image edge
    for i in range(1, n + 1):
        if sizes[i - 1] < min_area and not drop[i]:
            drop[i] = True
            info['removed_specks'] += 1
    if drop[1:].all():
        return rgba, info
    out = rgba.copy()
    out[drop[lab] & (lab > 0)] = 0
    return out, info


def bbox(rgba, thr=100):
    ys, xs = np.where(rgba[..., 3] > thr)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def keep_center_groups(rgba, gap=3, band=48, speck=1500, near=40):
    """Remove fragments of neighbouring glyphs that were cut into the tile (straight cut edges inside the canvas).
    Ink is grouped after dilating by `gap` px. Kept: groups touching the central vertical band (the glyph itself) plus
    small groups (< `speck` px) lying within `near` px of the glyph's bounding box (splatter, dots). Big groups
    outside the band are neighbour fragments. Fallback: the group closest to the centre."""
    a = rgba[..., 3] > 8
    if not a.any():
        return rgba, {'removed_groups': 0}
    grown = ndimage.binary_dilation(a, structure=STRUCT8, iterations=gap) if gap > 0 else a
    lab, n = ndimage.label(grown, structure=STRUCT8)
    h, w = a.shape
    cx = w // 2
    inband = a[:, max(0, cx - band):cx + band]
    keep = set(int(i) for i in np.unique(lab[:, max(0, cx - band):cx + band][inband]) if i)
    ys, xs = np.where(a)
    if not keep:
        d = {i: abs(xs[lab[ys, xs] == i].mean() - cx) for i in range(1, n + 1) if (lab[ys, xs] == i).any()}
        keep = {min(d, key=d.get)}
    km = np.isin(lab, list(keep)) & a
    ky, kx = np.where(km)
    bx0, bx1, by0, by1 = kx.min() - near, kx.max() + near, ky.min() - near, ky.max() + near
    sizes = ndimage.sum(a, lab, index=np.arange(1, n + 1))
    objs = ndimage.find_objects(lab)
    for i in range(1, n + 1):
        if i in keep:
            continue
        sl = objs[i - 1]
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if sizes[i - 1] < speck and x0 >= bx0 and x1 <= bx1 and y0 >= by0 and y1 <= by1:
            keep.add(i)
    out = rgba.copy()
    out[~np.isin(lab, list(keep))] = 0
    return out, {'removed_groups': n - len(keep)}
