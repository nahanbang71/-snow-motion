// public/packs/index.json  -> [{file,name,isColor,glyphs,bytes}]  (names are read from each pack.json, so the app can list
// fonts without downloading them);  public/watermarks/index.json -> [file]
import { readdirSync, readFileSync, writeFileSync, existsSync, mkdirSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import JSZip from 'jszip';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', 'public');
const packs = join(root, 'packs');
if (!existsSync(packs)) mkdirSync(packs, { recursive: true });
const entries = [];
for (const f of readdirSync(packs).filter((n) => /\.zip$/i.test(n)).sort()) {
  const zip = await JSZip.loadAsync(readFileSync(join(packs, f)));
  const pj = zip.file('pack.json');
  const meta = pj ? JSON.parse(await pj.async('string')) : {};
  entries.push({ file: f, name: meta.name || f.replace(/\.zip$/i, ''), isColor: !!meta.isColor, glyphs: meta.glyphs ? Object.keys(meta.glyphs).length : 0, bytes: statSync(join(packs, f)).size });
}
writeFileSync(join(packs, 'index.json'), JSON.stringify(entries, null, 1));
console.log(`packs/index.json: ${entries.length} packs`);
const wm = join(root, 'watermarks');
if (!existsSync(wm)) mkdirSync(wm, { recursive: true });
const files = readdirSync(wm).filter((f) => /\.(png|webp|jpg|jpeg)$/i.test(f)).sort();
writeFileSync(join(wm, 'index.json'), JSON.stringify(files, null, 1));
console.log(`watermarks/index.json: ${files.length} files`);
