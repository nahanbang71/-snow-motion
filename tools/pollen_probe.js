// Measures where each butterfly is (in the coordinates of the #world group) at given times of an animated SVG.
// usage: node pollen_probe.js <svg> <meta.json> <out.json>
//   meta: { K, container, samples: [{id, t}] }   t = story seconds, real time = t*K
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [svgPath, metaPath, outPath] = process.argv.slice(2);
  const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
  const b = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 960, height: 540 } });
  await p.goto('file://' + svgPath);
  await p.waitForTimeout(300);
  await p.evaluate(() => document.getAnimations().forEach(a => a.pause()));
  const byT = new Map();
  for (const s of meta.samples) { const k = s.t.toFixed(3); if (!byT.has(k)) byT.set(k, []); byT.get(k).push(s.id); }
  const out = [];
  const read = ({ ids, container }) => {
    const inv = document.getElementById(container).getScreenCTM().inverse();
    return ids.map(id => {
      const r = document.getElementById(id).getBoundingClientRect();
      const pt = new DOMPoint(r.x + r.width / 2, r.y + r.height / 2).matrixTransform(inv);
      return { id, x: pt.x, y: pt.y, w: Math.max(r.width, r.height) };
    });
  };
  for (const [k, ids] of byT) {
    const t = parseFloat(k);
    const at = async tt => { await p.evaluate(v => document.getAnimations().forEach(a => { a.currentTime = v; }), tt * meta.K * 1000); };
    await at(t);
    const a = await p.evaluate(read, { ids, container: meta.container });
    await at(t + 0.15);
    const c = await p.evaluate(read, { ids, container: meta.container });
    ids.forEach((id, i) => out.push({ id, t, x: a[i].x, y: a[i].y, w: a[i].w, hx: c[i].x - a[i].x, hy: c[i].y - a[i].y }));
  }
  fs.writeFileSync(outPath, JSON.stringify(out));
  await b.close();
})();
