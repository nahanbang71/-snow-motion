// Render flower SVG animations to mp4 (1920x1080, 30fps) by seeking CSS animations frame by frame.
// usage: node tools/render_video.js <first-index> <count> <out.mp4> [seconds-per-flower=7.5]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const [first, count, out, secArg] = [+process.argv[2], +process.argv[3], process.argv[4], +(process.argv[5] || 7.5)];
const FPS = 30, FADE = 0.3;
const root = path.join(__dirname, '..', 'flowers');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8')).slice(first, first + count);

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '24', '-pix_fmt', 'yuv420p',
    '-g', String(Math.round(secArg * FPS)), '-keyint_min', String(Math.round(secArg * FPS)), '-sc_threshold', '0',
    '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise(r => ff.on('close', r));
  const frames = Math.round(secArg * FPS);
  for (const [i, f] of manifest.entries()) {
    let svg = fs.readFileSync(path.join(root, 'svg', f.slug + '.svg'), 'utf8');
    svg = svg.replace('viewBox="0 0 800 600" width="800" height="600"', 'viewBox="-133.33 0 1066.67 600" width="1920" height="1080"')
             .replace('<rect width="800" height="600" fill="url(#bg)"/>', '<rect x="-200" width="1200" height="600" fill="url(#bg)"/>');
    await page.setContent(`<body style="margin:0;background:#080a1a;overflow:hidden">${svg}</body>`);
    for (let n = 0; n < frames; n++) {
      const t = n / FPS;
      const op = Math.max(0, Math.min(1, t / FADE, (secArg - t) / FADE));
      await page.evaluate(([t, op]) => {
        document.querySelector('svg').style.opacity = op;
        document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; });
      }, [t, op]);
      const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    console.log(`${out}: ${i + 1}/${manifest.length} ${f.slug}`);
  }
  ff.stdin.end();
  await done;
  await browser.close();
})();
