// Render any animated SVG (CSS animations) to mp4 by seeking.  usage: node tools/render_svg_video.js <in.svg> <out.mp4> <seconds> <width> <height>
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const [inp, out, SEC, W, H] = [process.argv[2], process.argv[3], +process.argv[4], +process.argv[5], +process.argv[6]];
const FPS = 30;
(async () => {
  const svg = fs.readFileSync(path.resolve(inp), 'utf8');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  await page.setContent(`<body style="margin:0;background:#000;overflow:hidden">${svg}</body>`);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise(r => ff.on('close', r));
  for (let n = 0; n < SEC * FPS; n++) {
    await page.evaluate(t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; }), n / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await done; await browser.close();
})();
