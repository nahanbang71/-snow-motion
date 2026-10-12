#!/usr/bin/env python3
"""Generate the 'alive' animal SVGs -> 한국전통문양/02_동물문/<slug>_alive.svg   (usage: python3 tools/gen_alive.py [slug ...])"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'kp'))
import alive  # noqa: E402

OUT = os.path.join(HERE, '..', '한국전통문양', '02_동물문')
only = set(sys.argv[1:])
for slug, fn in alive.ALIVE.items():
    if only and slug not in only:
        continue
    open(os.path.join(OUT, f'{slug}_alive.svg'), 'w', encoding='utf-8').write(fn())
if not only or 'bonghwang' in only:
    open(os.path.join(OUT, 'bonghwang_alive.svg'), 'w', encoding='utf-8').write(alive.bonghwang(os.path.join(OUT, 'bonghwang_laser.svg')))
print('done')
