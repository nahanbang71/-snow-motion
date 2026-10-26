// End-to-end test of the built web app. usage: node tests/e2e.mjs   (needs: npm run build in webapp/, python3 + Pillow, playwright)
import { createRequire } from 'node:module';
import { spawn, execFileSync } from 'node:child_process';
import { mkdtempSync, existsSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');   // npm i -D playwright (webapp/) or a global install
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const out = mkdtempSync(join(tmpdir(), 'nb-e2e-'));
let failed = 0;
const ok = (c, m) => { console.log(`${c ? 'PASS' : 'FAIL'}  ${m}`); if (!c) failed++; };
const py = (code, ...args) => execFileSync('python3', ['-I', '-c', code, ...args]).toString().trim();

for (const f of ['samples/TestMono.zip', 'samples/TestNeon.zip']) if (!existsSync(join(ROOT, f))) execFileSync('python3', [join(ROOT, 'samples/make_samples.py')]);
if (!existsSync(join(ROOT, 'webapp/dist/index.html'))) throw new Error('run `npm run build` in webapp/ first');

const srv = spawn('npx', ['vite', 'preview', '--host', '127.0.0.1', '--port', '4173', '--strictPort'], { cwd: join(ROOT, 'webapp'), stdio: 'ignore' });
const browser = await chromium.launch();
try {
  for (let i = 0; i < 50; i++) { try { if ((await fetch('http://127.0.0.1:4173/')).ok) break; } catch {} await new Promise((r) => setTimeout(r, 200)); }
  const ctx = await browser.newContext({ acceptDownloads: true, viewport: { width: 1500, height: 900 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
  await page.goto('http://127.0.0.1:4173/');

  // ---- built-in library
  await page.waitForFunction(() => document.querySelectorAll('[data-testid=pack-item]').length >= 1, null, { timeout: 60000 });
  await page.waitForFunction(() => /준비 완료/.test(document.querySelector('[data-testid=status]').textContent), null, { timeout: 120000 });
  const builtin = await page.locator('[data-testid=pack-item]').count();
  ok(builtin >= 7, `built-in library loaded (${builtin} fonts)`);

  // ---- drag&drop style loading of raw zips (the same input the drop zone uses)
  await page.setInputFiles('[data-testid=zip-input]', [join(ROOT, 'samples/TestMono.zip'), join(ROOT, 'samples/TestNeon.zip')]);
  await page.waitForFunction((n) => document.querySelectorAll('[data-testid=pack-item]').length >= n + 2, builtin, { timeout: 60000 });
  ok(true, 'raw .zip packs added');
  await page.locator('[data-testid=pack-item]').filter({ has: page.locator('b', { hasText: /^TestNeon$/ }) }).click();

  // ---- typing
  await page.locator('[data-testid=text]').fill('');
  await page.keyboard.type("HELLO, WORLD!\n2026 & @ it's?");
  const inkPixels = () => page.evaluate(() => {
    const c = document.querySelector('[data-testid=preview]');
    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
    let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 20) n++;
    return { n, w: c.width, h: c.height };
  });
  const flat = await inkPixels();
  ok(flat.n > 2000, `preview shows typed text (${flat.n} ink px, ${flat.w}x${flat.h})`);
  await page.screenshot({ path: join(out, 'studio_flat.png') });

  // ---- spacing / arc / alignment
  const setRange = (id, v) => page.locator(`[data-testid=${id}]`).evaluate((el, val) => { const s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; s.call(el, val); el.dispatchEvent(new Event('input', { bubbles: true })); }, String(v));
  await setRange('tracking', 120);
  const wide = await inkPixels();
  ok(wide.h < flat.h, `tracking widens the text (preview height shrinks to fit: ${flat.h} -> ${wide.h})`);
  await setRange('arc', 70);
  const arched = await inkPixels();
  ok(arched.h > wide.h, `arc bends the line (height ${wide.h} -> ${arched.h})`);
  await page.screenshot({ path: join(out, 'studio_arc.png') });
  await setRange('arc', -70);
  const smile = await inkPixels();
  ok(smile.h > wide.h, `negative arc works (height ${smile.h})`);
  await setRange('arc', 0); await setRange('tracking', 0);
  await page.locator('[data-testid=align-right]').click();

  // ---- every built-in pack renders text
  const names = await page.locator('[data-testid=pack-item] b').allTextContents();
  for (const n of names.filter((x) => !/^Test/.test(x))) {
    await page.locator('[data-testid=pack-item]').filter({ has: page.locator('b', { hasText: new RegExp(`^${n}$`) }) }).click();
    const r = await inkPixels();
    ok(r.n > 500, `pack "${n}" renders (${r.n} ink px)`);
  }
  await page.locator('[data-testid=pack-item]').filter({ has: page.locator('b', { hasText: /^Bold Calligraphy Alphabet White$/ }) }).click();
  await page.locator('[data-testid=text]').fill('NeonBrush\nStudio');

  // ---- transparent, cropped, hi-res PNG download
  await page.selectOption('[data-testid=scale]', '3');
  const [dl] = await Promise.all([page.waitForEvent('download'), page.locator('[data-testid=download]').click()]);
  const png = join(out, dl.suggestedFilename());
  await dl.saveAs(png);
  const info = JSON.parse(py(`
import sys, json
from PIL import Image
import numpy as np
im = Image.open(sys.argv[1]); a = np.array(im.convert('RGBA'))[..., 3]
ys, xs = np.where(a > 0)
print(json.dumps({'mode': im.mode, 'w': im.width, 'h': im.height, 'corner': int(a[0, 0]), 'pad': [int(xs.min()), int(ys.min()), int(im.width - 1 - xs.max()), int(im.height - 1 - ys.max())], 'ink': int((a > 0).sum())}))`, png));
  ok(info.mode === 'RGBA' && info.corner === 0, `PNG is RGBA with transparent corner (${info.w}x${info.h})`);
  ok(info.w > 1500, `PNG is high-res at 3x (${info.w}px wide)`);
  ok(Math.max(...info.pad) < 24 * 3 + 6, `PNG is tightly cropped (margins ${info.pad.join('/')} px)`);
  await page.screenshot({ path: join(out, 'studio_final.png') });

  // ---- batch watermarker
  await page.locator('[data-testid=tab-watermark]').click();
  const imgs = ['photo_a', 'photo_b', 'photo_c'].map((n) => join(ROOT, `samples/images/${n}.png`));
  await page.setInputFiles('[data-testid=wm-images]', imgs);
  ok((await page.locator('[data-testid=wm-count]').textContent()).startsWith('3'), '3 images queued');
  ok((await page.locator('[data-testid=wm-opacity]').inputValue()) === '45', 'default watermark opacity is 45%');
  await page.locator('[data-testid=wm-run]').click();
  await page.waitForFunction(() => /완료: 3장/.test(document.querySelector('[data-testid=wm-status]').textContent), null, { timeout: 60000 });
  ok((await page.locator('[data-testid=wm-results] a').count()) === 3, 'batch produced 3 results');
  await page.screenshot({ path: join(out, 'watermark.png') });
  const [zdl] = await Promise.all([page.waitForEvent('download'), page.locator('[data-testid=wm-zip]').click()]);
  const zpath = join(out, 'wm.zip');
  await zdl.saveAs(zpath);
  const zres = JSON.parse(py(`
import sys, json, zipfile, io
from PIL import Image, ImageChops
z = zipfile.ZipFile(sys.argv[1]); res = []
for n in sorted(z.namelist()):
    im = Image.open(io.BytesIO(z.read(n))).convert('RGB')
    src = Image.open(sys.argv[2] + '/' + n.replace('_BRSh', '').rsplit('.', 1)[0] + '.png').convert('RGB')
    diff = ImageChops.difference(im, src).getbbox()
    res.append({'name': n, 'size': im.size == src.size, 'diff': diff, 'w': im.width, 'h': im.height})
print(json.dumps(res))`, zpath, join(ROOT, 'samples/images')));
  ok(zres.length === 3 && zres.every((r) => r.size), `zip holds 3 same-size images (${zres.map((r) => r.name).join(', ')})`);
  ok(zres.every((r) => r.diff && r.diff[0] > r.w * 0.5 && r.diff[1] > r.h * 0.5), 'watermark landed in the bottom-right area of every image');
  ok(errors.length === 0, `no browser errors${errors.length ? ': ' + errors.slice(0, 3).join(' | ') : ''}`);
  console.log('artifacts:', out);
} finally {
  await browser.close();
  srv.kill();
}
process.exit(failed ? 1 : 0);
