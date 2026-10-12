// Render one scene of 밤하늘영상/nightsky.html (25 s, 30 fps) to an mp4.  usage: node tools/render_nightsky.js <scene 0-11> <out.mp4>
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const idx = +process.argv[2], out = process.argv[3], FPS = 30, SEC = 25;
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto('file://' + path.resolve(__dirname, '..', '밤하늘영상', 'nightsky.html'));
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise(r => ff.on('close', r));
  for (let n = 0; n < FPS * SEC; n++) {
    await page.evaluate(([i, t]) => window.drawFrame(i, t), [idx, n / FPS]);
    const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await done; await browser.close();
})();
