#!/usr/bin/env python3
"""Render every SVG in 공항영상/svg to a clip (parallel) and join them in play order -> 공항영상/공항_5분.mp4"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_airports as G  # noqa: E402

ROOT = os.path.join(HERE, '..', '공항영상')
SVG, CLIPS = os.path.join(ROOT, 'svg'), os.path.join(ROOT, 'clips')
os.makedirs(CLIPS, exist_ok=True)
seq = G.order()
jobs = [(i, svg, sec) for i, (svg, sec) in enumerate(seq)]


def clip_name(i, svg):
    return os.path.join(CLIPS, f'{i:02d}_{svg[:-4]}.mp4')


def run(j):
    i, svg, sec = j
    out = clip_name(i, svg)
    if not os.path.exists(out):
        subprocess.run(['node', os.path.join(HERE, 'render_airport.js'), 'video', os.path.join(SVG, svg), out + '.part.mp4', str(sec)], check=True)
        os.rename(out + '.part.mp4', out)
    print('done', out, flush=True)


with ThreadPoolExecutor(int(os.environ.get('JOBS', 4))) as ex:
    list(ex.map(run, jobs))
lst = os.path.join(CLIPS, 'list.txt')
with open(lst, 'w') as fh:
    for i, svg, sec in jobs:
        fh.write(f"file '{os.path.abspath(clip_name(i, svg))}'\n")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-movflags', '+faststart',
                os.path.join(ROOT, '공항_5분.mp4')], check=True)
print('joined')
