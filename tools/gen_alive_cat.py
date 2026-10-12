#!/usr/bin/env python3
"""Dynamic ('alive') versions for categories 03-07 -> 한국전통문양/<cat>/<slug>_alive.svg   usage: python3 tools/gen_alive_cat.py [slug ...]"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'kp'))
ROOT = os.path.join(HERE, '..', '한국전통문양')
only = set(sys.argv[1:])

mods = []
import alive_nature
mods.append(('03_자연문', alive_nature.NATURE))
for name, cat, attr in (('alive_geo', '04_기하문', 'GEO'), ('alive_text', '05_문자_길상문', 'TEXT'),
                        ('alive_special', '06_특별묶음', 'SPECIAL'), ('alive_dancheong', '07_단청문양', 'DANCHEONG')):
    try:
        m = __import__(name)
        mods.append((cat, getattr(m, attr)))
    except ModuleNotFoundError as e:
        if name not in str(e):
            raise
for cat, table in mods:
    for slug, fn in table.items():
        if only and slug not in only:
            continue
        open(os.path.join(ROOT, cat, f'{slug}_alive.svg'), 'w', encoding='utf-8').write(fn())
print('done')
