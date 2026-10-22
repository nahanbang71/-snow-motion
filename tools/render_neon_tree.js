// Render tools/neon_tree.html (25.6 s, 30 fps) to an mp4.  usage: node tools/render_neon_tree.js <out.mp4> [onlyTimeSeconds -> png]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const out = process.argv[2], FPS = 30, SEC = 25.6;
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto('file://' + path.resolve(__dirname, 'neon_tree.html'));
  if (process.argv[3]) { await page.evaluate(t => window.drawFrame(t), +process.argv[3]); await page.screenshot({ path: out }); await browser.close(); return; }
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise(r => ff.on('close', r));
  for (let n = 0; n < Math.round(FPS * SEC); n++) {
    await page.evaluate(t => window.drawFrame(t), n / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await done; await browser.close();
})();
