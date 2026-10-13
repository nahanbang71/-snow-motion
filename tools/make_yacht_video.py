#!/usr/bin/env python3
"""Yacht round-the-world film: map voyage (parallel chunks) + 4 sea cutaways cut into open-water legs -> 세계지도비행/요트_세계일주.mp4 (300 s)"""
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '세계지도비행')
WORK = os.path.join(ROOT, 'yacht', 'parts')
os.makedirs(WORK, exist_ok=True)
JOBS = int(os.environ.get('JOBS', 4))
CUTS = [(2, 'yacht', 6), (9, 'dolphin', 7), (12, 'whale', 6), (20, 'gull', 6)]     # (leg index, scene, seconds)
MAP_SEC = 300 - sum(s for _, _, s in CUTS)
FPS = 30


def sh(*a):
    subprocess.run(list(map(str, a)), check=True)


info = subprocess.run(['node', os.path.join(HERE, 'render_yacht_map.js'), 'info', '-', str(MAP_SEC)], capture_output=True, text=True, check=True).stdout
legs = json.loads(re.search(r'LEGS (.*)', info).group(1))
N = round(MAP_SEC * FPS)
size = -(-N // (JOBS * 2))
chunks = [(i, a, min(N, a + size)) for i, a in enumerate(range(0, N, size))]


def chunk(c):
    i, a, b = c
    out = os.path.join(WORK, f'map_{i:02d}.mp4')
    if not os.path.exists(out):
        sh('node', os.path.join(HERE, 'render_yacht_map.js'), 'video', out + '.tmp.mp4', MAP_SEC, a, b)
        os.rename(out + '.tmp.mp4', out)
    print('done', out, flush=True)


def cutaway(c):
    _, name, sec = c
    out = os.path.join(WORK, f'cut_{name}.mp4')
    if not os.path.exists(out):
        sh('node', os.path.join(HERE, 'render_airport.js'), 'video', os.path.join(ROOT, f'{name}_sample.svg'), out + '.tmp.mp4', sec)
        os.rename(out + '.tmp.mp4', out)
    print('done', out, flush=True)


with ThreadPoolExecutor(JOBS) as ex:
    list(ex.map(cutaway, CUTS))
    list(ex.map(chunk, chunks))
lst = os.path.join(WORK, 'list.txt')
open(lst, 'w').write(''.join(f"file '{os.path.abspath(os.path.join(WORK, f'map_{i:02d}.mp4')}'\n" for i, _, _ in chunks))
mapmp4 = os.path.join(WORK, 'map_full.mp4')
sh('ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', mapmp4)

# cut points: middle of the chosen legs
pts = [legs[i][0] + legs[i][1] * 0.5 for i, _, _ in CUTS]
FADE = 0.35
inputs, filt, labels = [], [], []
t0 = 0.0
def seg(a, b, fin, fout):
    k = len(inputs)
    inputs.extend(['-ss', f'{a:.3f}', '-t', f'{b - a:.3f}', '-i', mapmp4])
    f = f'[{k}:v]setpts=PTS-STARTPTS'
    if fin: f += f',fade=t=in:st=0:d={FADE}'
    if fout: f += f',fade=t=out:st={b - a - FADE:.3f}:d={FADE}'
    filt.append(f + f'[v{k}]'); labels.append(f'[v{k}]')
for n, ((_, name, sec), cp) in enumerate(zip(CUTS, pts)):
    seg(t0, cp, n > 0, True)
    k = len(inputs)
    inputs.extend(['-i', os.path.join(WORK, f'cut_{name}.mp4')])
    filt.append(f'[{k}:v]setpts=PTS-STARTPTS,fade=t=in:st=0:d={FADE},fade=t=out:st={sec - FADE:.3f}:d={FADE}[v{k}]'); labels.append(f'[v{k}]')
    t0 = cp
seg(t0, MAP_SEC, True, False)
final = os.path.join(ROOT, '요트_세계일주.mp4')
sh('ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(filt) + ';' + ''.join(labels) + f'concat=n={len(labels)}:v=1:a=0[v]',
   '-map', '[v]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', final)
print('joined', final)
