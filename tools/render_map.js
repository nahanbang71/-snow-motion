// Render the world flight map (세계지도비행/map.html) by stepping time.
//   video: node tools/render_map.js video <out.mp4> <fromStop> <toStop>
//   still: node tools/render_map.js still <out.png> <fromStop> <toStop> <t1,t2,...>
//   chunk: node tools/render_map.js video <out.mp4> <fromStop> <toStop> - <frame0> <frame1>   (frames [f0,f1) of the full timeline)
//   info:  node tools/render_map.js info - <fromStop> <toStop>   (prints duration only)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const [mode, out, from, to, times, f0a, f1a] = process.argv.slice(2);
const FPS = 30;
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto('file://' + path.resolve(__dirname, '..', '세계지도비행', 'map.html'));
  const dur = await page.evaluate(([a, b]) => setup(+a, +b, { total: (+a === 0 && +b === 30) ? 300 : 0 }), [from, to]);
  console.log('duration', dur.toFixed(2));
  if (mode === 'info') { await browser.close(); return; }
  if (mode === 'still') {
    for (const t of times.split(',').map(Number)) {
      await page.evaluate(t => frame(t), t);
      await page.screenshot({ path: out.replace('.png', `_${t}.png`) });
    }
  } else {
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const done = new Promise(r => ff.on('close', r));
    const N = Math.round(dur * FPS), a = f0a ? +f0a : 0, b = f1a ? Math.min(N, +f1a) : N;
    for (let n = a; n < b; n++) {
      await page.evaluate(t => frame(t), n / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end(); await done;
  }
  await browser.close();
})();
