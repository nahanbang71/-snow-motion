// Render one constellation clip (16 s, 30 fps) of 별자리영상/constellations.html.  usage: node tools/render_constellation.js <0-39>
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const idx = +process.argv[2], FPS = 30, SEC = 16;
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto('file://' + path.resolve(__dirname, '..', '별자리영상', 'constellations.html'));
  const m = await page.evaluate(i => window.meta(i), idx);
  const dir = path.resolve(__dirname, '..', '별자리영상', '장소별', String(m.placeIdx + 1).padStart(2, '0') + '_' + m.place);
  fs.mkdirSync(dir, { recursive: true });
  const out = path.join(dir, `${m.nth}_${m.ko}.mp4`);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise(r => ff.on('close', r));
  for (let n = 0; n < FPS * SEC; n++) {
    await page.evaluate(([i, t]) => window.drawFrame(i, t), [idx, n / FPS]);
    const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await done; await browser.close();
  console.log(out);
})();
