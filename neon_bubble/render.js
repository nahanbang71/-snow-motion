const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const { spawn } = require('child_process');
const path = require('path');
const [IN, OUT] = process.argv.slice(2), FPS = 24, N = 240;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await p.goto('file://' + path.resolve(__dirname, 'overlay.html'));
  const ff = spawn('ffmpeg', ['-v','error','-y','-i',IN,'-f','image2pipe','-framerate',String(FPS),'-c:v','png','-i','-',
    '-filter_complex','[0][1]overlay=0:0:format=auto,format=yuv420p','-c:v','libx264','-crf','20','-r',String(FPS),'-an','-t','10',OUT],{stdio:['pipe','inherit','inherit']});
  const done = new Promise(r => ff.on('close', r));
  for (let n = 0; n < N; n++) {
    await p.evaluate(t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t*1000; }), n/FPS*1);
    const buf = await p.screenshot({ type:'png', omitBackground:true });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await done; await b.close();
})();
