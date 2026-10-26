// lists public/packs/*.zip and public/watermarks/* so the app can show them as built-in libraries
import { readdirSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = join(dirname(fileURLToPath(import.meta.url)), '..', 'public');
for (const [dir, re] of [['packs', /\.zip$/i], ['watermarks', /\.(png|webp|jpg|jpeg)$/i]]) {
  const d = join(root, dir);
  if (!existsSync(d)) mkdirSync(d, { recursive: true });
  const files = readdirSync(d).filter((f) => re.test(f)).sort();
  writeFileSync(join(d, 'index.json'), JSON.stringify(files, null, 1));
  console.log(`${dir}/index.json: ${files.length} files`);
}
