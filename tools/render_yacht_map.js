// Render the yacht voyage map (세계지도비행/yacht_map.html) by stepping time.
//   video: node tools/render_yacht_map.js video <out.mp4> <totalSeconds> [frame0 frame1]
//   still: node tools/render_yacht_map.js still <out.png> <totalSeconds> <t1,t2,...>
//   info:  node tools/render_yacht_map.js info - <totalSeconds>
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const [mode, out, total, a1, a2] = process.argv.slice(2);
const FPS = 30;
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto('file://' + path.resolve(__dirname, '..', '세계지도비행', 'yacht_map.html'));
  const dur = await page.evaluate(t => setup(+t), total);
  console.log('duration', dur.toFixed(2));
  if (mode === 'info') { console.log('LEGS ' + JSON.stringify(await page.evaluate(() => TL.filter(e => e.f !== undefined).map(e => [e.td, e.f])))); await browser.close(); return; }
  if (mode === 'still') {
    for (const t of a1.split(',').map(Number)) {
      await page.evaluate(t => frame(t), t);
      await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
      await page.screenshot({ path: out.replace('.png', `_${t}.png`) });
    }
  } else {
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const done = new Promise(r => ff.on('close', r));
    const N = Math.round(dur * FPS), f0 = a1 ? +a1 : 0, f1 = a2 ? Math.min(N, +a2) : N;
    for (let n = f0; n < f1; n++) {
      await page.evaluate(t => frame(t), n / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end(); await done;
  }
  await browser.close();
})();
