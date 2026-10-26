// Render the 3D Character Builder demo timeline to mp4 (frame-exact, via window.__seek).
// usage: node tools/render_character3d.js <out.mp4> [seconds=20] [width=1280] [height=720] [model.glb]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');
const [out, SEC = 20, W = 1280, H = 720, MODEL] = [process.argv[2], +process.argv[3] || 20, +process.argv[4] || 1280, +process.argv[5] || 720, process.argv[6]];
const FPS = 30;
const ROOT = path.resolve(__dirname, '..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json' };
(async () => {
  const srv = http.createServer((q, r) => {
    const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0]));
    if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
    r.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r);
  }).listen(0);
  const port = srv.address().port;
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: +W, height: +H } });
  page.on('pageerror', e => console.error('page error:', e.message));
  const q = MODEL ? `&model=${encodeURIComponent('/' + path.relative(ROOT, path.resolve(MODEL)))}` : '';
  await page.goto(`http://localhost:${port}/character3d/index.html?x=1${q}`);
  await page.waitForFunction(() => window.__seek, null, { timeout: 30000 });
  await page.waitForTimeout(1500);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise(r => ff.on('close', r));
  for (let n = 0; n < SEC * FPS; n++) {
    await page.evaluate(t => window.__seek(t), n / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await done; await browser.close(); srv.close();
})();
