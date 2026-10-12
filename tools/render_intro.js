// usage: node tools/render_intro.js <out.mp4> [seconds=6]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const out = process.argv[2], SEC = +(process.argv[3] || 6), FPS = 30;
(async () => {
  const svg = fs.readFileSync(path.join(__dirname, '..', 'flowers', 'intro.svg'), 'utf8');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.setContent(`<body style="margin:0;background:#080a1a;overflow:hidden">${svg}</body>`);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '24', '-pix_fmt', 'yuv420p', '-g', String(SEC * FPS), '-keyint_min', String(SEC * FPS),
    '-sc_threshold', '0', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise(r => ff.on('close', r));
  for (let n = 0; n < SEC * FPS; n++) {
    const t = n / FPS, op = Math.max(0, Math.min(1, t / .2, (SEC - t) / .3));
    await page.evaluate(([t, op]) => {
      document.querySelector('svg').style.opacity = op;
      document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; });
    }, [t, op]);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (n % 30 === 0) console.log('frame', n);
  }
  ff.stdin.end(); await done; await browser.close();
})();
