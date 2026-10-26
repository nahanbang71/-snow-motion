export type Pos = 'tl' | 'tc' | 'tr' | 'ml' | 'mc' | 'mr' | 'bl' | 'bc' | 'br';

export interface WmOptions {
  /** 0..100 */
  opacity: number;
  /** watermark width in % of the image width */
  sizePct: number;
  pos: Pos;
  /** margin in % of the image width */
  marginPct: number;
  tile: boolean;
  /** degrees, used for tiles */
  tileAngle: number;
  format: 'png' | 'jpeg' | 'webp';
  quality: number;
}

export const defaultWm: WmOptions = { opacity: 45, sizePct: 22, pos: 'br', marginPct: 3, tile: false, tileAngle: -25, format: 'png', quality: 0.92 };

export async function loadBitmap(src: Blob): Promise<ImageBitmap> {
  return createImageBitmap(src);
}

export function compose(base: ImageBitmap | HTMLImageElement, wm: ImageBitmap, o: WmOptions): HTMLCanvasElement {
  const W = (base as ImageBitmap).width, H = (base as ImageBitmap).height;
  const c = document.createElement('canvas');
  c.width = W;
  c.height = H;
  const ctx = c.getContext('2d')!;
  ctx.imageSmoothingQuality = 'high';
  if (o.format === 'jpeg') {
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, W, H);
  }
  ctx.drawImage(base as CanvasImageSource, 0, 0);
  const w = Math.max(1, (W * o.sizePct) / 100);
  const h = w * (wm.height / wm.width);
  const m = (W * o.marginPct) / 100;
  ctx.globalAlpha = o.opacity / 100;
  if (o.tile) {
    ctx.save();
    ctx.translate(W / 2, H / 2);
    ctx.rotate((o.tileAngle * Math.PI) / 180);
    const gx = w * 1.5, gy = h * 2.4;
    const R = Math.hypot(W, H) / 2 + w;
    for (let y = -R, row = 0; y < R; y += gy, row++) {
      for (let x = -R + (row % 2 ? gx / 2 : 0); x < R; x += gx) ctx.drawImage(wm, x, y, w, h);
    }
    ctx.restore();
  } else {
    const col = o.pos[1], row = o.pos[0];
    const x = col === 'l' ? m : col === 'r' ? W - w - m : (W - w) / 2;
    const y = row === 't' ? m : row === 'b' ? H - h - m : (H - h) / 2;
    ctx.drawImage(wm, x, y, w, h);
  }
  ctx.globalAlpha = 1;
  return c;
}

export function toBlob(c: HTMLCanvasElement, o: WmOptions): Promise<Blob> {
  const type = o.format === 'jpeg' ? 'image/jpeg' : o.format === 'webp' ? 'image/webp' : 'image/png';
  return new Promise((res, rej) => c.toBlob((b) => (b ? res(b) : rej(new Error('toBlob failed'))), type, o.quality));
}
