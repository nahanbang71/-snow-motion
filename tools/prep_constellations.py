#!/usr/bin/env python3
"""Build 별자리영상/data.js from d3-celestial (BSD-3, Olaf Frohn): stars (Hipparcos), constellation lines, Korean names.
usage: python3 tools/prep_constellations.py <path to node_modules/d3-celestial/data>"""
import json
import math
import os
import sys

import numpy as np

D = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '별자리영상', 'data.js')
CODES = ['Sco', 'Leo', 'Cru', 'Cnc', 'UMa', 'UMi', 'Cas', 'Cep', 'Del', 'Psc', 'Aqr', 'PsA', 'Lyr', 'Cyg', 'Aql', 'Sge',
         'Ori', 'Gem', 'CMa', 'CMi', 'Boo', 'Vir', 'Lib', 'CrB', 'Peg', 'And', 'Per', 'Ari', 'Tau', 'Aur', 'Lep', 'Cet',
         'Sgr', 'Cap', 'Oph', 'Crv', 'Dra', 'Her', 'Cen', 'Lac']
stars = json.load(open(os.path.join(D, 'stars.8.json')))['features']
names = json.load(open(os.path.join(D, 'starnames.json')))
cons = {f['id']: f for f in json.load(open(os.path.join(D, 'constellations.json')))['features']}
lines = {f['id']: f for f in json.load(open(os.path.join(D, 'constellations.lines.json')))['features']}
S = np.array([[s['geometry']['coordinates'][0] % 360, s['geometry']['coordinates'][1], float(s['properties']['mag'])] for s in stars])
IDS = [s['id'] for s in stars]
BV = [float(s['properties'].get('bv') or 0.6) if str(s['properties'].get('bv', '')).replace('.', '', 1).replace('-', '', 1).isdigit() else 0.6 for s in stars]


def unit(ra, dec):
    r, d = math.radians(ra), math.radians(dec)
    return np.array([math.cos(d) * math.cos(r), math.cos(d) * math.sin(r), math.sin(d)])


SU = np.array([unit(a, b) for a, b, _ in S])
out_cons = []
for code in CODES:
    geom = lines[code]['geometry']['coordinates']
    verts, idx, polys = [], {}, []
    for poly in geom:
        p = []
        for lon, lat in poly:
            key = (round(lon, 3), round(lat, 3))
            if key not in idx:
                u = unit(lon % 360, lat)
                dots = SU @ u
                j = int(np.argmax(dots))
                ang = math.degrees(math.acos(min(1, dots[j])))
                v = {'ra': lon % 360, 'dec': lat, 'mag': 4.0, 'name': '', 'en': ''}
                if ang < 0.45:
                    v['ra'], v['dec'], v['mag'] = float(S[j][0]), float(S[j][1]), float(S[j][2])
                    nm = names.get(str(IDS[j]))
                    if nm and nm.get('name'):
                        v['en'] = nm['name']
                        v['name'] = nm.get('ko') or ''
                idx[key] = len(verts)
                verts.append(v)
            p.append(idx[key])
        polys.append(p)
    cs = np.array([unit(v['ra'], v['dec']) for v in verts])
    c = cs.mean(axis=0)
    c /= np.linalg.norm(c)
    rad = max(math.acos(min(1, float(u @ c))) for u in cs)
    ra0 = math.degrees(math.atan2(c[1], c[0])) % 360
    dec0 = math.degrees(math.asin(c[2]))
    pr = cons[code]['properties']
    out_cons.append({'code': code, 'ko': pr['ko'], 'la': pr['name'], 'en': pr['en'], 'ra': ra0, 'dec': dec0, 'rad': rad, 'verts': verts, 'polys': polys})
data = {'stars': [[round(float(a), 3), round(float(b), 3), round(float(m), 2), round(bv, 2)] for (a, b, m), bv in zip(S, BV)], 'cons': out_cons}
with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write('window.SKY=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';')
print(len(S), 'stars', len(out_cons), 'constellations', os.path.getsize(OUT) // 1024, 'KB')
for c in out_cons[:6]:
    print(c['code'], c['ko'], round(math.degrees(c['rad']), 1), 'deg', sum(1 for v in c['verts'] if v['name']), 'named')
