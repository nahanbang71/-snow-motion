"""Pollen puffs for flying butterflies: a little cloud of golden dust is shaken off the wings, drifts and vanishes,
then (after a pause) another puff - on repeat while the butterfly flies.

How: the film script registers every flying butterfly (an element id + the story-second window it is airborne).
We pick puff times, ask a headless browser where each butterfly really is at those moments (so eased flights, orbits
and spirals are all exact), and drop short-lived dots at those world positions.
"""
import json
import math
import os
import random
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
COLORS = ['#ffe9a0', '#fff4c8', '#ffd27a', '#fff0b0']


class Pollen:
    def __init__(self, T, K, seed=3, container='world'):
        self.T, self.K, self.container = T, K, container
        self.rng = random.Random(seed)
        self.em = []
        self.n = 0

    def new_id(self):
        self.n += 1
        return f'pe{self.n}'

    def add(self, eid, a, b):
        """butterfly element `eid` is airborne from story second a to b"""
        self.em.append((eid, a, b))

    def schedule(self):
        out = []
        for eid, a, b in self.em:
            t = a + self.rng.uniform(.5, 1.1)
            while t < b - .6:
                out.append((eid, t))
                t += self.rng.uniform(1.9, 2.9)      # puff ... gone ... pause ... puff
        return out

    def probe(self, svg_text):
        samples = [{'id': e, 't': t} for e, t in self.schedule()]
        with tempfile.TemporaryDirectory() as d:
            svg, meta, out = (os.path.join(d, n) for n in ('a.svg', 'meta.json', 'out.json'))
            open(svg, 'w', encoding='utf-8').write(svg_text)
            json.dump({'K': self.K, 'container': self.container, 'samples': samples}, open(meta, 'w'))
            env = dict(os.environ)
            env.setdefault('NODE_PATH', subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip())
            subprocess.run(['node', os.path.join(HERE, 'pollen_probe.js'), svg, meta, out], check=True, env=env)
            return json.load(open(out))

    def render(self, positions):
        """-> (svg markup, css keyframes)"""
        rng, T = self.rng, self.T
        kf, els = [], []
        for i, p in enumerate(positions):
            t, life = p['t'], rng.uniform(1.9, 2.8)
            fade_in, peak = .18, rng.uniform(.8, 1.0)
            hl = math.hypot(p['hx'], p['hy']) or 1.0
            ux, uy = p['hx'] / hl, p['hy'] / hl                     # heading
            kf.append(f'@keyframes pb{i}{{0%,{t/T*100:.3f}%{{opacity:0;transform:translate(0px,0px)}}'
                      f'{(t+fade_in)/T*100:.3f}%{{opacity:{peak:.2f}}}'
                      f'{(t+life)/T*100:.3f}%,100%{{opacity:0;transform:translate(var(--dx),var(--dy))}}}}')
            spread = max(9.0, p['w'] * .24)
            for _ in range(rng.randint(13, 18)):
                ox, oy = rng.gauss(0, spread), rng.gauss(0, spread)
                bx, by = p['x'] - ux * spread * .8 + ox, p['y'] - uy * spread * .8 + oy      # born slightly behind the wings
                ang = rng.uniform(0, 2 * math.pi)
                mag = rng.uniform(16, 52)
                dx, dy = math.cos(ang) * mag - ux * 10, math.sin(ang) * mag * .8 + rng.uniform(8, 22)   # floats outward and settles
                els.append(f'<circle class="k pol" cx="{bx:.1f}" cy="{by:.1f}" r="{rng.uniform(1.5, 3.4):.1f}" '
                           f'style="animation-name:pb{i};--dx:{dx:.0f}px;--dy:{dy:.0f}px;fill:{rng.choice(COLORS)}"/>')
        css = '\n'.join(kf) + '\n.pol{opacity:0;animation-timing-function:cubic-bezier(.15,.7,.3,1) !important}'
        return ''.join(els), css
