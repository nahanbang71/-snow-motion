#!/usr/bin/env python3
"""Natural Earth 50m countries (public domain) -> 세계지도비행/data.js (one SVG path in degree coords: x=lon, y=-lat)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '세계지도비행')
gj = json.load(open(os.path.join(ROOT, 'data', 'ne_50m_admin_0_countries.geojson'), encoding='utf-8'))


def ring(r):
    pts, last = [], None
    for lon, lat in r:
        p = (round(lon, 2), round(-lat, 2))
        if p != last:
            pts.append(p)
        last = p
    if len(pts) < 4:
        return ''
    return 'M' + ' '.join(f'{x:g} {y:g}' for x, y in pts) + 'Z'


parts = []
for ft in gj['features']:
    if ft['properties'].get('NAME') == 'Antarctica':
        continue
    g = ft['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for poly in polys:
        for r in poly[:1]:
            parts.append(ring(r))
land = ''.join(p for p in parts if p)

# route stops: code, city, country, lat, lon, chapter
STOPS = [
    ('ICN', 'SEOUL', 'SOUTH KOREA', 37.46, 126.44, 1), ('HND', 'TOKYO', 'JAPAN', 35.55, 139.78, 1),
    ('KIX', 'OSAKA', 'JAPAN', 34.43, 135.23, 1), ('PKX', 'BEIJING', 'CHINA', 39.51, 116.41, 1),
    ('HKG', 'HONG KONG', 'HONG KONG SAR', 22.31, 113.91, 1), ('BKK', 'BANGKOK', 'THAILAND', 13.69, 100.75, 1),
    ('SIN', 'SINGAPORE', 'SINGAPORE', 1.36, 103.99, 1),
    ('DXB', 'DUBAI', 'UNITED ARAB EMIRATES', 25.25, 55.36, 2), ('DOH', 'DOHA', 'QATAR', 25.27, 51.61, 2),
    ('IST', 'ISTANBUL', 'TURKIYE', 41.26, 28.74, 2), ('CAI', 'CAIRO', 'EGYPT', 30.12, 31.41, 2),
    ('CPT', 'CAPE TOWN', 'SOUTH AFRICA', -33.97, 18.6, 2),
    ('LHR', 'LONDON', 'UNITED KINGDOM', 51.47, -0.45, 3), ('CDG', 'PARIS', 'FRANCE', 49.01, 2.55, 3),
    ('AMS', 'AMSTERDAM', 'NETHERLANDS', 52.31, 4.76, 3), ('MAD', 'MADRID', 'SPAIN', 40.49, -3.57, 3),
    ('FCO', 'ROME', 'ITALY', 41.8, 12.25, 3), ('ZRH', 'ZURICH', 'SWITZERLAND', 47.46, 8.55, 3),
    ('JFK', 'NEW YORK', 'UNITED STATES', 40.64, -73.78, 4), ('DEN', 'DENVER', 'UNITED STATES', 39.86, -104.67, 4),
    ('YVR', 'VANCOUVER', 'CANADA', 49.2, -123.18, 4), ('SFO', 'SAN FRANCISCO', 'UNITED STATES', 37.62, -122.38, 4),
    ('LAX', 'LOS ANGELES', 'UNITED STATES', 33.94, -118.41, 4), ('MIA', 'MIAMI', 'UNITED STATES', 25.79, -80.29, 4),
    ('GIG', 'RIO DE JANEIRO', 'BRAZIL', -22.81, -43.25, 5), ('EZE', 'BUENOS AIRES', 'ARGENTINA', -34.82, -58.54, 5),
    ('SCL', 'SANTIAGO', 'CHILE', -33.39, -70.79, 5), ('SYD', 'SYDNEY', 'AUSTRALIA', -33.95, 151.18, 5),
    ('AKL', 'AUCKLAND', 'NEW ZEALAND', -37.01, 174.79, 5), ('HNL', 'HONOLULU', 'UNITED STATES', 21.32, -157.92, 5),
    ('ICN', 'SEOUL', 'SOUTH KOREA', 37.46, 126.44, 5),
]
js = 'const LAND=' + json.dumps(land) + ';\nconst STOPS=' + json.dumps(
    [dict(code=c, city=n, country=k, lat=la, lon=lo, ch=ch) for c, n, k, la, lo, ch in STOPS], ensure_ascii=False) + ';\n'
open(os.path.join(ROOT, 'data.js'), 'w', encoding='utf-8').write(js)
print(len(parts), 'rings,', len(js) // 1024, 'KB')
