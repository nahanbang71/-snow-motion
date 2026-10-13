#!/usr/bin/env python3
"""Round-the-world YACHT route: ports -> sea-only legs found with A* on a 0.5 deg ocean grid (wraps at the date line)
-> 세계지도비행/yacht_data.js  (PORTS, LEGS[[lon,lat]...], WAVES[[lon,lat]...]).
Land comes from Natural Earth (세계지도비행/data/ne_50m_admin_0_countries.geojson); straits/canals that are narrower than
a grid cell are carved open by hand (CARVE)."""
import heapq
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '세계지도비행')
RES = 0.5
W, H = int(360 / RES), int(180 / RES)           # 720 x 360

# (code, city, country, lon, lat)  - sea side of each port; the voyage ends where it began
PORTS = [
    ('PUS', 'BUSAN', 'SOUTH KOREA', 129.1, 35.0), ('HKG', 'HONG KONG', 'HONG KONG SAR', 114.2, 22.2),
    ('SIN', 'SINGAPORE', 'SINGAPORE', 104.0, 1.2), ('BOM', 'MUMBAI', 'INDIA', 72.8, 18.9),
    ('DXB', 'DUBAI', 'UNITED ARAB EMIRATES', 55.0, 25.4), ('PSD', 'PORT SAID', 'EGYPT', 32.35, 31.35),
    ('IST', 'ISTANBUL', 'TURKIYE', 29.0, 41.0), ('CVV', 'ROME', 'ITALY', 11.7, 42.0),
    ('BCN', 'BARCELONA', 'SPAIN', 2.3, 41.3), ('LIS', 'LISBON', 'PORTUGAL', -9.4, 38.6),
    ('CPT', 'CAPE TOWN', 'SOUTH AFRICA', 18.3, -33.9), ('GIG', 'RIO DE JANEIRO', 'BRAZIL', -43.1, -23.1),
    ('JFK', 'NEW YORK', 'UNITED STATES', -73.9, 40.5), ('MIA', 'MIAMI', 'UNITED STATES', -80.0, 25.7),
    ('PTY', 'PANAMA', 'PANAMA', -79.6, 8.8), ('LAX', 'LOS ANGELES', 'UNITED STATES', -118.4, 33.7),
    ('SFO', 'SAN FRANCISCO', 'UNITED STATES', -122.6, 37.7), ('HNL', 'HONOLULU', 'UNITED STATES', -157.9, 21.2),
    ('AKL', 'AUCKLAND', 'NEW ZEALAND', 174.8, -36.8), ('SYD', 'SYDNEY', 'AUSTRALIA', 151.4, -33.9),
    ('TYO', 'TOKYO', 'JAPAN', 139.9, 35.3), ('PUS', 'BUSAN', 'SOUTH KOREA', 129.1, 35.0),
]
# open water that a half-degree grid would otherwise see as land: (lon0, lat0, lon1, lat1) segments, carved with a 0.5 deg brush
CARVE = [
    (32.4, 29.9, 32.35, 31.3),       # Suez Canal
    (-79.95, 9.4, -79.55, 8.9),      # Panama Canal
    (-5.7, 35.95, -5.3, 36.05),      # Gibraltar
    (29.05, 41.3, 28.9, 40.9), (28.9, 40.9, 27.5, 40.7), (27.5, 40.7, 26.3, 40.15), (26.3, 40.15, 25.8, 40.0),   # Bosphorus, Marmara, Dardanelles
    (43.7, 12.9, 43.3, 12.4),        # Bab-el-Mandeb
    (56.2, 26.5, 56.9, 26.8),        # Hormuz
    (104.4, 1.25, 103.7, 1.2), (103.7, 1.2, 102.6, 1.8), (102.6, 1.8, 101.5, 2.7), (101.5, 2.7, 100.6, 3.9),   # Singapore + Malacca strait
    (100.6, 3.9, 99.4, 5.0), (99.4, 5.0, 97.6, 5.9), (97.6, 5.9, 95.6, 6.4),
    (43.3, 12.4, 42.5, 13.5), (42.5, 13.5, 41.0, 15.5), (41.0, 15.5, 39.5, 18.5), (39.5, 18.5, 37.6, 21.5),     # Red Sea
    (37.6, 21.5, 36.0, 25.0), (36.0, 25.0, 34.6, 27.2), (34.6, 27.2, 33.6, 27.9), (33.6, 27.9, 32.75, 29.7),      # Red Sea -> Gulf of Suez
    (9.0, 41.3, 9.4, 41.3),          # Bonifacio
    (23.6, 37.6, 23.2, 36.9), (10.1, 55.4, 10.9, 55.5),
]


def rasterize():
    gj = json.load(open(os.path.join(ROOT, 'data', 'ne_50m_admin_0_countries.geojson'), encoding='utf-8'))
    sc = 10
    im = Image.new('L', (360 * sc, 180 * sc), 0)
    d = ImageDraw.Draw(im)
    for ft in gj['features']:
        if ft['properties'].get('NAME') == 'Antarctica':
            continue
        g = ft['geometry']
        for poly in (g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]):
            d.polygon([((lo + 180) * sc, (90 - la) * sc) for lo, la in poly[0]], fill=255)
    a = np.asarray(im, dtype=np.float32) / 255
    k = int(RES * sc)
    frac = a.reshape(H, k, W, k).mean(axis=(1, 3))
    return frac > 0.35


def cell(lon, lat):
    return int(min(H - 1, max(0, (90 - lat) / RES))), int(((lon + 180) / RES) % W)


def carve(land):
    for lo0, la0, lo1, la1 in CARVE:
        n = int(max(abs(lo1 - lo0), abs(la1 - la0)) / (RES / 3)) + 2
        for i in range(n + 1):
            r, c = cell(lo0 + (lo1 - lo0) * i / n, la0 + (la1 - la0) * i / n)
            land[r, c] = False
            land[r, (c + 1) % W] = False       # 4-connected, so the A* diagonal rule cannot pinch the canal
            land[min(H - 1, r + 1), c] = False
    return land


def near_land(land, steps=2):
    out = np.zeros_like(land, dtype=np.int8)
    cur = land.copy()
    for s in range(1, steps + 1):
        nxt = cur | np.roll(cur, 1, 0) | np.roll(cur, -1, 0) | np.roll(cur, 1, 1) | np.roll(cur, -1, 1)
        out[nxt & ~cur & (out == 0)] = s
        cur = nxt
    return out


def snap(land, lon, lat):
    r, c = cell(lon, lat)
    if not land[r, c]:
        return r, c
    for rad in range(1, 8):
        best = None
        for dr in range(-rad, rad + 1):
            for dc in range(-rad, rad + 1):
                rr, cc = r + dr, (c + dc) % W
                if 0 <= rr < H and not land[rr, cc]:
                    d = dr * dr + dc * dc
                    if best is None or d < best[0]:
                        best = (d, rr, cc)
        if best:
            return best[1], best[2]
    raise SystemExit(f'cannot snap port at {lon},{lat}')


def astar(land, pen, a, b):
    lat_of = lambda r: 90 - (r + .5) * RES
    def h(r, c):
        dc = abs(c - b[1]); dc = min(dc, W - dc)
        return math.hypot(dc * RES * math.cos(math.radians(lat_of(r))), (r - b[0]) * RES)
    pq = [(h(*a), 0.0, a)]
    best = {a: 0.0}
    prev = {}
    while pq:
        _, g, cur = heapq.heappop(pq)
        if cur == b:
            break
        if g > best.get(cur, 1e18):
            continue
        r, c = cur
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if not dr and not dc:
                    continue
                rr, cc = r + dr, (c + dc) % W
                if not (0 <= rr < H) or land[rr, cc]:
                    continue
                if dr and dc and (land[r, cc] or land[rr, c]):      # no squeezing diagonally between two land corners
                    continue
                step = math.hypot(dc * RES * math.cos(math.radians(lat_of(r))), dr * RES) * (1 + pen[rr, cc])
                ng = g + step
                if ng < best.get((rr, cc), 1e18):
                    best[(rr, cc)] = ng
                    prev[(rr, cc)] = cur
                    heapq.heappush(pq, (ng + h(rr, cc), ng, (rr, cc)))
    path = [b]
    while path[-1] != a:
        path.append(prev[path[-1]])
    return path[::-1]


def to_ll(rc):
    return [(rc[1] + .5) * RES - 180, 90 - (rc[0] + .5) * RES]


def clear_line(land, p, q):
    n = int(max(abs(q[0] - p[0]), abs(((q[1] - p[1]) + W / 2) % W - W / 2)) * 2) + 2
    for i in range(n + 1):
        t = i / n
        dc = ((q[1] - p[1]) + W / 2) % W - W / 2
        r, c = int(round(p[0] + (q[0] - p[0]) * t)), int(round(p[1] + dc * t)) % W
        if land[r, c]:
            return False
    return True


def pull(land, path):
    """string pulling: drop waypoints while the straight segment stays over water"""
    out = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1 and not clear_line(land, path[i], path[j]):
            j -= 1
        out.append(path[j]); i = j
    return out


def unwrap(pts):
    res = [pts[0][:]]
    for lo, la in pts[1:]:
        while lo - res[-1][0] > 180: lo -= 360
        while res[-1][0] - lo > 180: lo += 360
        res.append([lo, la])
    return res


def chaikin(pts, n=3):
    for _ in range(n):
        q = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            q += [[.75 * a[0] + .25 * b[0], .75 * a[1] + .25 * b[1]], [.25 * a[0] + .75 * b[0], .25 * a[1] + .75 * b[1]]]
        q.append(pts[-1]); pts = q
    return pts


def main():
    land = carve(rasterize())
    pen = near_land(land).astype(np.float32)
    pen = np.where(pen == 1, 2.5, np.where(pen == 2, 0.8, 0.0))
    legs = []
    for i in range(len(PORTS) - 1):
        A, B = PORTS[i], PORTS[i + 1]
        a, b = snap(land, A[3], A[4]), snap(land, B[3], B[4])
        raw = astar(land, pen, a, b)
        sm = pull(land, raw)
        pts = unwrap([[A[3], A[4]]] + [to_ll(p) for p in sm[1:-1]] + [[B[3], B[4]]])
        pts = chaikin(pts, 3)
        legs.append([[round(x, 2), round(y, 2)] for x, y in pts])
        print(f'{A[0]}->{B[0]}: {len(raw)} cells, {len(sm)} waypoints', flush=True)
    # ocean sparkles: sea cells reachable from the Pacific only (no lakes)
    seen = np.zeros_like(land)
    start = snap(land, -150, 0)
    stack = [start]
    seen[start] = True
    while stack:
        r, c = stack.pop()
        for rr, cc in ((r + 1, c), (r - 1, c), (r, (c + 1) % W), (r, (c - 1) % W)):
            if 0 <= rr < H and not land[rr, cc] and not seen[rr, cc]:
                seen[rr, cc] = True; stack.append((rr, cc))
    rng = np.random.default_rng(3)
    coast = near_land(land, 3)
    ok = np.argwhere(seen & (coast == 0) & (np.abs(90 - (np.arange(H)[:, None] + .5) * RES) < 72))
    pick = ok[rng.choice(len(ok), size=1400, replace=False)]
    waves = [[round((c + rng.random()) * RES - 180, 2), round(90 - (r + rng.random()) * RES, 2)] for r, c in pick]
    ports = [dict(code=p[0], city=p[1], country=p[2], lon=p[3], lat=p[4]) for p in PORTS]
    open(os.path.join(ROOT, 'yacht_data.js'), 'w', encoding='utf-8').write(
        'const PORTS=' + json.dumps(ports, ensure_ascii=False) + ';\nconst LEGS=' + json.dumps(legs) + ';\nconst WAVES=' + json.dumps(waves) + ';\n')
    # check image: land mask + routes, to see at a glance whether anything crosses land
    sc = 4
    im = Image.fromarray(np.where(land, 40, 8).astype(np.uint8)).resize((W * sc, H * sc), Image.NEAREST).convert('RGB')
    d = ImageDraw.Draw(im)
    for lg in legs:
        pts = [(((x + 180) % 360) / RES * sc, (90 - y) / RES * sc) for x, y in lg]
        for p, q in zip(pts, pts[1:]):
            if abs(p[0] - q[0]) < W * sc / 2:
                d.line([p, q], fill=(255, 200, 60), width=2)
    for p in PORTS:
        x, y = ((p[3] + 180) % 360) / RES * sc, (90 - p[4]) / RES * sc
        d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(255, 80, 200), width=2)
    im.save(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'route_check.png'))


if __name__ == '__main__':
    main()
