#!/usr/bin/env python3
"""Render the full world flight (all stops) in parallel chunks and join -> 세계지도비행/세계지도_비행.mp4"""
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '세계지도비행')
PARTS = os.path.join(ROOT, 'clips', 'parts')
os.makedirs(PARTS, exist_ok=True)
FROM, TO, JOBS = 0, 30, int(os.environ.get('JOBS', 4))
info = subprocess.run(['node', os.path.join(HERE, 'render_map.js'), 'info', '-', str(FROM), str(TO)], capture_output=True, text=True, check=True).stdout
dur = float(re.search(r'duration ([\d.]+)', info).group(1))
N = round(dur * 30)
size = -(-N // (JOBS * 2))          # 2 chunks per worker keeps the load even
chunks = [(i, a, min(N, a + size)) for i, a in enumerate(range(0, N, size))]


def run(c):
    i, a, b = c
    out = os.path.join(PARTS, f'part_{i:02d}.mp4')
    if not os.path.exists(out):
        subprocess.run(['node', os.path.join(HERE, 'render_map.js'), 'video', out + '.tmp.mp4', str(FROM), str(TO), '-', str(a), str(b)], check=True)
        os.rename(out + '.tmp.mp4', out)
    print('done', out, flush=True)


with ThreadPoolExecutor(JOBS) as ex:
    list(ex.map(run, chunks))
lst = os.path.join(PARTS, 'list.txt')
with open(lst, 'w') as fh:
    for i, _, _ in chunks:
        fh.write(f"file '{os.path.abspath(os.path.join(PARTS, f'part_{i:02d}.mp4'))}'\n")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-movflags', '+faststart',
                os.path.join(ROOT, '세계지도_비행.mp4')], check=True)
print('joined', N, 'frames')
