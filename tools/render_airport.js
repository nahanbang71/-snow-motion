// Render a laser-line SVG (CSS animations + SMIL) by seeking.
//   video: node tools/render_airport.js video <in.svg> <out.mp4> <seconds>
//   still: node tools/render_airport.js still <in.svg> <out.png> <t1[,t2,...]>   (several times -> several files out_t1.png ...)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const [mode, inp, out, arg] = process.argv.slice(2);
const FPS = 30;

async function seek(page, t) {
  await page.evaluate(t => {
    document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; });
    const s = document.querySelector('svg');
    s.pauseAnimations(); s.setCurrentTime(t);
  }, t);
}

(async () => {
  const svg = fs.readFileSync(path.resolve(inp), 'utf8');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.log('ERR', e.message));
  await page.setContent(`<body style="margin:0;background:#05060d;overflow:hidden">${svg}</body>`);
  if (mode === 'still') {
    for (const t of arg.split(',').map(Number)) {
      await seek(page, t);
      await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));   // let the glow filter repaint before a single still
      await page.screenshot({ path: arg.includes(',') ? out.replace('.png', `_${t}.png`) : out });
    }
  } else {
    const SEC = +arg;
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const done = new Promise(r => ff.on('close', r));
    for (let n = 0; n < SEC * FPS; n++) {
      await seek(page, n / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end(); await done;
  }
  await browser.close();
})();
