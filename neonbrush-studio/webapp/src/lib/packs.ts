import JSZip from 'jszip';

/** One drawable glyph; all metrics are font units (UPM 1000), y up, relative to pen position / baseline. */
export interface Glyph {
  ch: string;
  img: HTMLCanvasElement;
  left: number;
  top: number;
  w: number;
  h: number;
  adv: number;
}

export interface FontPack {
  id: string;
  name: string;
  source: string;
  isColor: boolean;
  upm: number;
  cap: number;
  space: number;
  glyphs: Map<string, Glyph>;
  /** how the metrics were obtained: 'webpack' (pipeline output) or 'raw' (guessed from the PNGs) */
  origin: 'webpack' | 'raw';
  notes: string[];
}

const KEYWORDS: Record<string, string> = {
  COMMA: ',', APOS: "'", APOSTROPHE: "'", EXCL: '!', EXCLAIM: '!', QUEST: '?', QUESTION: '?', AMP: '&', AMPERSAND: '&',
  AT: '@', PERIOD: '.', DOT: '.', HYPHEN: '-', DASH: '-', COLON: ':', SEMI: ';', SEMICOLON: ';', SLASH: '/',
  HASH: '#', PERCENT: '%', PLUS: '+', EQUALS: '=', STAR: '*', UNDERSCORE: '_', LPAREN: '(', RPAREN: ')', QUOTE: '"', DQUOTE: '"',
};

export function stemToChar(stem: string): string | null {
  const s = stem.trim();
  if ([...s].length === 1) return s;
  const k = KEYWORDS[s.toUpperCase()];
  if (k) return k;
  const m = /^(?:u\+?|uni)([0-9a-f]{4,6})$/i.exec(s);
  return m ? String.fromCodePoint(parseInt(m[1], 16)) : null;
}

export function cleanFamily(raw: string): string {
  const s = raw
    .replace(/[_-]+/g, ' ')
    .replace(/\b\d+\s*chars?\b|\b\d{3,4}x\d{3,4}\b|\bwhite\b/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return s
    .split(' ')
    .map((w) => (/^[A-Z]{3,}$/.test(w) ? w[0] + w.slice(1).toLowerCase() : /^[A-Z]{2}$|[A-Z]/.test(w.slice(1)) ? w : w.charAt(0).toUpperCase() + w.slice(1)))
    .join(' ');
}

async function pngBlob(f: JSZip.JSZipObject): Promise<Blob> {
  return new Blob([await f.async('arraybuffer')], { type: /\.webp$/i.test(f.name) ? 'image/webp' : 'image/png' });
}

async function toCanvas(blob: Blob): Promise<HTMLCanvasElement> {
  const bmp = await createImageBitmap(blob);
  const c = document.createElement('canvas');
  c.width = bmp.width;
  c.height = bmp.height;
  c.getContext('2d')!.drawImage(bmp, 0, 0);
  bmp.close();
  return c;
}

function inkBox(c: HTMLCanvasElement, thr = 60): [number, number, number, number] | null {
  const { width: w, height: h } = c;
  const d = c.getContext('2d')!.getImageData(0, 0, w, h).data;
  let x0 = w, y0 = h, x1 = -1, y1 = -1;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      if (d[(y * w + x) * 4 + 3] > thr) {
        if (x < x0) x0 = x;
        if (x > x1) x1 = x;
        if (y < y0) y0 = y;
        if (y > y1) y1 = y;
      }
    }
  }
  return x1 < 0 ? null : [x0, y0, x1 + 1, y1 + 1];
}

function crop(c: HTMLCanvasElement, box: [number, number, number, number], pad = 2): HTMLCanvasElement {
  const x0 = Math.max(box[0] - pad, 0), y0 = Math.max(box[1] - pad, 0);
  const x1 = Math.min(box[2] + pad, c.width), y1 = Math.min(box[3] + pad, c.height);
  const o = document.createElement('canvas');
  o.width = x1 - x0;
  o.height = y1 - y0;
  o.getContext('2d')!.drawImage(c, x0, y0, o.width, o.height, 0, 0, o.width, o.height);
  return o;
}

const median = (a: number[]) => {
  const s = [...a].sort((x, y) => x - y);
  return s.length ? (s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2) : 0;
};

let uid = 0;
const nextId = (name: string) => `${name}#${++uid}`;

function detectColor(glyphs: Map<string, Glyph>): boolean {
  let tot = 0, col = 0;
  for (const g of glyphs.values()) {
    const d = g.img.getContext('2d')!.getImageData(0, 0, g.img.width, g.img.height).data;
    for (let i = 0; i < d.length; i += 16) {
      if (d[i + 3] > 200) {
        tot++;
        if (Math.max(d[i], d[i + 1], d[i + 2]) - Math.min(d[i], d[i + 1], d[i + 2]) > 60) col++;
      }
    }
  }
  return tot > 0 && col / tot > 0.02;
}

/** pack.json + trimmed PNGs written by pipeline/build_fonts.py --webpacks */
async function fromWebpack(zip: JSZip, prefix: string, name: string, source: string): Promise<FontPack> {
  const meta = JSON.parse(await zip.file(prefix + 'pack.json')!.async('string'));
  const glyphs = new Map<string, Glyph>();
  for (const [ch, m] of Object.entries<any>(meta.glyphs)) {
    const f = zip.file(prefix + m.file);
    if (!f) continue;
    glyphs.set(ch, { ch, img: await toCanvas(await pngBlob(f)), left: m.left, top: m.top, w: m.w, h: m.h, adv: m.adv });
  }
  return {
    id: nextId(meta.name || name), name: meta.name || name, source, isColor: !!meta.isColor, upm: meta.upm, cap: meta.cap,
    space: meta.space, glyphs, origin: 'webpack', notes: [],
  };
}

/** plain folder of A.png / COMMA.png ...: guess scale + baseline like pipeline/nbfont/layout.py (canvas mode) */
async function fromRaw(zip: JSZip, files: string[], name: string, source: string): Promise<FontPack | null> {
  const items: { ch: string; c: HTMLCanvasElement; box: [number, number, number, number] }[] = [];
  const notes: string[] = [];
  for (const f of files) {
    const stem = f.split('/').pop()!.replace(/\.png$/i, '');
    const ch = stemToChar(stem);
    if (!ch) {
      notes.push(`skipped ${stem}.png`);
      continue;
    }
    const c = await toCanvas(await pngBlob(zip.file(f)!));
    const box = inkBox(c);
    if (box) items.push({ ch, c, box });
  }
  if (items.length < 5) return null;
  const letters = items.filter((i) => /^[A-Z]$/.test(i.ch));
  const ref = letters.length > 2 ? letters : items;
  const hs = ref.map((i) => i.box[3] - i.box[1]);
  const cys = ref.map((i) => (i.box[1] + i.box[3]) / 2);
  const mh = median(hs);
  const mcy = median(cys);
  const centered = Math.sqrt(median(cys.map((v) => (v - mcy) ** 2))) < 8;
  const base = centered ? mcy + mh / 2 : median(ref.map((i) => i.box[3]));
  const top = centered ? mcy - mh / 2 : median(ref.map((i) => i.box[1]));
  const UPM = 1000, CAP = 700, SB = 50;
  const k = CAP / (base - top);
  const glyphs = new Map<string, Glyph>();
  for (const { ch, c, box } of items) {
    const pad = 2;
    const x0 = Math.max(box[0] - pad, 0), y0 = Math.max(box[1] - pad, 0);
    const t = crop(c, box, pad);
    glyphs.set(ch, { ch, img: t, left: (x0 - box[0]) * k + SB, top: (base - y0) * k, w: t.width * k, h: t.height * k, adv: Math.round((box[2] - box[0]) * k + 2 * SB) });
  }
  notes.push('metrics guessed from the PNGs (no pack.json): run pipeline/build_fonts.py for cleaned / re-labelled packs');
  const pack: FontPack = { id: nextId(name), name, source, isColor: false, upm: UPM, cap: CAP, space: 300, glyphs, origin: 'raw', notes };
  pack.isColor = detectColor(glyphs);
  return pack;
}

/** Load every glyph pack inside a zip (a zip may hold several sub folders = several fonts). */
export async function loadPacksFromZip(data: Blob | ArrayBuffer | Uint8Array, fileName: string): Promise<FontPack[]> {
  const zip = await JSZip.loadAsync(data as any);
  const names = Object.keys(zip.files).filter((n) => !zip.files[n].dir && !n.startsWith('__MACOSX') && !/\/\._/.test(n));
  const folders = new Map<string, string[]>();
  for (const n of names) {
    const i = n.lastIndexOf('/');
    const folder = i < 0 ? '' : n.slice(0, i + 1);
    if (!folders.has(folder)) folders.set(folder, []);
    folders.get(folder)!.push(n);
  }
  const base = fileName.replace(/\.zip$/i, '').replace(/^[0-9a-f]{8}-/, '');
  const out: FontPack[] = [];
  const multi = folders.size > 1;
  for (const [folder, files] of [...folders.entries()].sort()) {
    const label = multi && folder ? cleanFamily(base) + ' ' + cleanFamily(folder.replace(/\/$/, '').split('/').pop()!) : cleanFamily(base);
    if (files.includes(folder + 'pack.json')) {
      out.push(await fromWebpack(zip, folder, label, fileName));
      continue;
    }
    const pngs = files.filter((f) => /\.png$/i.test(f));
    const glyphLike = pngs.filter((f) => stemToChar(f.split('/').pop()!.replace(/\.png$/i, '')));
    if (glyphLike.length >= Math.max(5, pngs.length / 2)) {
      const p = await fromRaw(zip, pngs, label, fileName);
      if (p) out.push(p);
    }
  }
  return out;
}

export const allImageFiles = (files: FileList | File[]) => [...files].filter((f) => /\.(png|jpe?g|webp|gif|bmp)$/i.test(f.name) || f.type.startsWith('image/'));
