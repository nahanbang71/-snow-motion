import type { FontPack, Glyph } from './packs';

export type Align = 'left' | 'center' | 'right';

export interface TypeOptions {
  text: string;
  /** em size in px at export scale 1 */
  size: number;
  /** extra letter spacing in font units (kerning / tracking), may be negative */
  tracking: number;
  /** space width in % of the pack's default */
  spacePct: number;
  /** line height in em */
  lineHeight: number;
  /** -100 (smile) .. 100 (rainbow); 0 = straight */
  arc: number;
  align: Align;
  /** tint colour for monochrome packs; null = original colours */
  tint: string | null;
  padding: number;
}

export const defaultOptions: TypeOptions = {
  text: 'NEON BRUSH', size: 200, tracking: 0, spacePct: 100, lineHeight: 1.05, arc: 0, align: 'center', tint: null, padding: 24,
};

interface Placed {
  g: Glyph;
  /** transform: translate(tx,ty) rotate(rot) then draw rect at (dx,dy,w,h); all in font units, y down */
  tx: number;
  ty: number;
  rot: number;
  dx: number;
  dy: number;
}

export interface Layout {
  placed: Placed[];
  missing: string[];
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

export function glyphFor(pack: FontPack, ch: string): Glyph | undefined {
  return pack.glyphs.get(ch) ?? pack.glyphs.get(ch.toUpperCase());
}

export function layout(pack: FontPack, o: TypeOptions): Layout {
  const lines = o.text.split('\n');
  const missing = new Set<string>();
  const spaceW = pack.space * (o.spacePct / 100);
  // 1) flat layout per line
  const flat = lines.map((line) => {
    let pen = 0;
    const items: { g: Glyph; x: number }[] = [];
    let first = true;
    for (const ch of line) {
      if (ch === ' ') {
        pen += spaceW + o.tracking;
        continue;
      }
      const g = glyphFor(pack, ch);
      if (!g) {
        if (ch.trim()) missing.add(ch);
        continue;
      }
      if (!first) pen += o.tracking;
      items.push({ g, x: pen });
      pen += g.adv;
      first = false;
    }
    return { items, width: Math.max(pen, 0) };
  });
  const maxW = Math.max(1, ...flat.map((l) => l.width));
  const lh = o.lineHeight * pack.upm;
  const placed: Placed[] = [];
  const arc = Math.max(-100, Math.min(100, o.arc));
  const R0 = arc === 0 ? 0 : Math.max(pack.upm * 0.3, (maxW / Math.PI) * (100 / Math.abs(arc)));
  flat.forEach((line, i) => {
    const off = o.align === 'left' ? 0 : o.align === 'right' ? maxW - line.width : (maxW - line.width) / 2;
    const yBase = i * lh;
    for (const { g, x } of line.items) {
      if (arc === 0) {
        placed.push({ g, tx: off + x + g.left, ty: yBase - g.top, rot: 0, dx: 0, dy: 0 });
      } else {
        const s = off + x + g.adv / 2 - maxW / 2;                 // arc length from the centre
        const up = arc > 0;
        const R = Math.max(pack.upm * 0.15, up ? R0 - i * lh : R0 + i * lh);
        const phi = s / R;
        const px = R * Math.sin(phi);
        const py = up ? yBase + (R0 - i * lh) - R * Math.cos(phi) : yBase - (R0 + i * lh) + R * Math.cos(phi);
        placed.push({ g, tx: px + maxW / 2, ty: py, rot: up ? phi : -phi, dx: g.left - g.adv / 2, dy: -g.top });
      }
    }
  });
  // 2) bounds
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const p of placed) {
    const corners: [number, number][] = [[0, 0], [p.g.w, 0], [0, p.g.h], [p.g.w, p.g.h]];
    for (const [cx, cy] of corners) {
      const lx = cx + p.dx, ly = cy + p.dy;
      const x = p.tx + lx * Math.cos(p.rot) - ly * Math.sin(p.rot);
      const y = p.ty + lx * Math.sin(p.rot) + ly * Math.cos(p.rot);
      minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y);
    }
  }
  if (!placed.length) {
    minX = minY = 0;
    maxX = pack.upm;
    maxY = pack.upm * 0.5;
  }
  return { placed, missing: [...missing], minX, minY, maxX, maxY };
}

const tintCache = new WeakMap<HTMLCanvasElement, Map<string, HTMLCanvasElement>>();
function tinted(img: HTMLCanvasElement, color: string): HTMLCanvasElement {
  let m = tintCache.get(img);
  if (!m) tintCache.set(img, (m = new Map()));
  let t = m.get(color);
  if (!t) {
    t = document.createElement('canvas');
    t.width = img.width;
    t.height = img.height;
    const c = t.getContext('2d')!;
    c.drawImage(img, 0, 0);
    c.globalCompositeOperation = 'source-in';
    c.fillStyle = color;
    c.fillRect(0, 0, t.width, t.height);
    m.set(color, t);
  }
  return t;
}

/** px size of the (tightly cropped) result at the given pixels-per-unit scale */
export function measure(l: Layout, pxPerUnit: number, padding: number) {
  return { w: Math.ceil((l.maxX - l.minX) * pxPerUnit + padding * 2), h: Math.ceil((l.maxY - l.minY) * pxPerUnit + padding * 2) };
}

export function draw(ctx: CanvasRenderingContext2D, pack: FontPack, l: Layout, o: TypeOptions, pxPerUnit: number) {
  const useTint = !!o.tint && !pack.isColor;
  ctx.save();
  ctx.imageSmoothingQuality = 'high';
  ctx.translate(o.padding - l.minX * pxPerUnit, o.padding - l.minY * pxPerUnit);
  for (const p of l.placed) {
    ctx.save();
    ctx.translate(p.tx * pxPerUnit, p.ty * pxPerUnit);
    ctx.rotate(p.rot);
    ctx.drawImage(useTint ? tinted(p.g.img, o.tint!) : p.g.img, p.dx * pxPerUnit, p.dy * pxPerUnit, p.g.w * pxPerUnit, p.g.h * pxPerUnit);
    ctx.restore();
  }
  ctx.restore();
}

export const MAX_EXPORT_PX = 12000;

/** Render the text to a transparent, tightly cropped canvas. scale multiplies o.size. */
export function renderToCanvas(pack: FontPack, o: TypeOptions, scale = 1): { canvas: HTMLCanvasElement; missing: string[]; clamped: boolean } {
  const l = layout(pack, o);
  let ppu = (o.size * scale) / pack.upm;
  let m = measure(l, ppu, o.padding * scale);
  let clamped = false;
  const big = Math.max(m.w, m.h);
  if (big > MAX_EXPORT_PX) {
    ppu *= MAX_EXPORT_PX / big;
    clamped = true;
    m = measure(l, ppu, o.padding * scale);
  }
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, m.w);
  canvas.height = Math.max(1, m.h);
  draw(canvas.getContext('2d')!, pack, l, { ...o, padding: o.padding * scale }, ppu);
  return { canvas, missing: l.missing, clamped };
}

export function canvasToPngBlob(c: HTMLCanvasElement): Promise<Blob> {
  return new Promise((res, rej) => c.toBlob((b) => (b ? res(b) : rej(new Error('toBlob failed'))), 'image/png'));
}
