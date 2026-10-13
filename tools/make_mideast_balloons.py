#!/usr/bin/env python3
"""Middle East film: overview intro (16 s) + 20 balloon-over-landscape scenes (13.6 s) + credits (12 s) = 300 s
-> 열기구풍경/중동_열기구_풍경_5분.mp4"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_europe_video as MV  # noqa: E402

ORDER = ['marrakech', 'eljem', 'meteora', 'ephesus', 'pamukkale', 'cappadocia', 'nemrut', 'baalbek', 'palmyra', 'jerusalem',
         'petra', 'giza', 'karnak', 'abusimbel', 'hegra', 'ur', 'isfahan', 'persepolis', 'abudhabi', 'burj']
ROOT = os.path.join(HERE, '..', '열기구풍경')
SVG, PARTS = os.path.join(ROOT, 'mideast'), os.path.join(ROOT, 'parts_mideast')
os.makedirs(PARTS, exist_ok=True)
seq = [(os.path.join(ROOT, 'overview_mideast.svg'), 'overview', 16)] + [(os.path.join(SVG, f'{i}.svg'), i, 13.6) for i in ORDER]
seq.append((os.path.join(SVG, 'credits.svg'), 'credits', 12))
open(os.path.join(SVG, 'credits.svg'), 'w', encoding='utf-8').write(
    MV.credits_svg().replace('EUROPE FROM ABOVE', 'MIDDLE EAST FROM ABOVE').replace('Europe from above', 'Middle East from above'))
assert abs(sum(s for _, _, s in seq) - 300) < 1e-6, sum(s for _, _, s in seq)


def run(job):
    i, (svg, name, sec) = job
    out = os.path.join(PARTS, f'{i:02d}_{name}.mp4')
    if not os.path.exists(out):
        subprocess.run(['node', os.path.join(HERE, 'render_airport.js'), 'video', svg, out + '.tmp.mp4', str(sec)], check=True)
        os.rename(out + '.tmp.mp4', out)
    print('done', out, flush=True)


with ThreadPoolExecutor(int(os.environ.get('JOBS', 4))) as ex:
    list(ex.map(run, list(enumerate(seq))))
lst = os.path.join(PARTS, 'list.txt')
open(lst, 'w').write(''.join("file '%s'\n" % os.path.abspath(os.path.join(PARTS, f'{i:02d}_{n}.mp4')) for i, (_, n, _) in enumerate(seq)))
final = os.path.join(ROOT, '중동_열기구_풍경_5분.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-movflags', '+faststart', final], check=True)
print('joined', final)
