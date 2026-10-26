import { useEffect, useRef, useState } from 'react';
import JSZip from 'jszip';
import { Pos, WmOptions, compose, defaultWm, loadBitmap, toBlob } from '../lib/watermark';
import { allImageFiles } from '../lib/packs';
import { saveBlob } from '../lib/download';

const base = import.meta.env.BASE_URL;
interface Result { name: string; blob: Blob; url: string; w: number; h: number }
const POS: Pos[] = ['tl', 'tc', 'tr', 'ml', 'mc', 'mr', 'bl', 'bc', 'br'];

export default function Watermarker() {
  const [images, setImages] = useState<File[]>([]);
  const [builtin, setBuiltin] = useState<string[]>([]);
  const [wmName, setWmName] = useState('');
  const [wmFile, setWmFile] = useState<Blob | null>(null);
  const [wm, setWm] = useState<ImageBitmap | null>(null);
  const [o, setO] = useState<WmOptions>(defaultWm);
  const [results, setResults] = useState<Result[]>([]);
  const [busy, setBusy] = useState('');
  const [drag, setDrag] = useState(false);
  const prevRef = useRef<HTMLCanvasElement>(null);
  const set = <K extends keyof WmOptions>(k: K, v: WmOptions[K]) => setO((x) => ({ ...x, [k]: v }));

  // built-in BRSh watermarks (solid white 100 % versions; opacity is applied here)
  useEffect(() => {
    fetch(`${base}watermarks/index.json`)
      .then((r) => r.json())
      .then((l: string[]) => {
        const list = l.filter((n) => !/45pct/i.test(n));
        setBuiltin(list);
        if (list.length) setWmName(list[0]);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    let dead = false;
    (async () => {
      let blob: Blob | null = wmFile;
      if (!blob && wmName) blob = await (await fetch(`${base}watermarks/${wmName}`)).blob();
      if (blob) {
        const b = await loadBitmap(blob);
        if (!dead) setWm(b);
      }
    })().catch(() => undefined);
    return () => {
      dead = true;
    };
  }, [wmName, wmFile]);

  // live preview on the first image
  useEffect(() => {
    const c = prevRef.current;
    if (!c || !wm) return;
    let dead = false;
    (async () => {
      const src = images[0];
      let bmp: ImageBitmap;
      if (src) bmp = await loadBitmap(src);
      else {
        const s = document.createElement('canvas');
        s.width = 1200;
        s.height = 800;
        const g = s.getContext('2d')!;
        const gr = g.createLinearGradient(0, 0, 1200, 800);
        gr.addColorStop(0, '#2b5876');
        gr.addColorStop(1, '#4e4376');
        g.fillStyle = gr;
        g.fillRect(0, 0, 1200, 800);
        bmp = await createImageBitmap(s);
      }
      if (dead) return;
      const out = compose(bmp, wm, { ...o, format: 'png' });
      const k = Math.min(1, 720 / out.width);
      c.width = Math.round(out.width * k);
      c.height = Math.round(out.height * k);
      c.getContext('2d')!.drawImage(out, 0, 0, c.width, c.height);
    })().catch(() => undefined);
    return () => {
      dead = true;
    };
  }, [images, wm, o]);

  const addImages = (fs: FileList | File[]) => {
    const f = allImageFiles(fs);
    if (f.length) setImages((p) => [...p, ...f]);
  };

  const run = async () => {
    if (!wm || !images.length) return;
    results.forEach((r) => URL.revokeObjectURL(r.url));
    const out: Result[] = [];
    for (let i = 0; i < images.length; i++) {
      setBusy(`${i + 1} / ${images.length} 처리 중…`);
      const f = images[i];
      const bmp = await loadBitmap(f);
      const c = compose(bmp, wm, o);
      const blob = await toBlob(c, o);
      const ext = o.format === 'jpeg' ? 'jpg' : o.format;
      out.push({ name: f.name.replace(/\.[^.]+$/, '') + `_BRSh.${ext}`, blob, url: URL.createObjectURL(blob), w: c.width, h: c.height });
      bmp.close();
    }
    setResults(out);
    setBusy(`완료: ${out.length}장`);
  };

  const zipAll = async () => {
    const z = new JSZip();
    const used = new Set<string>();
    for (const r of results) {
      let n = r.name;
      for (let k = 2; used.has(n); k++) n = r.name.replace(/(\.[^.]+)$/, `_${k}$1`);
      used.add(n);
      z.file(n, r.blob);
    }
    saveBlob(await z.generateAsync({ type: 'blob', compression: 'STORE' }), 'BRSh_watermarked.zip');
  };

  return (
    <div className="wmk" onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={(e) => { e.preventDefault(); setDrag(false); addImages(e.dataTransfer.files); }}>
      <aside className="side">
        <h2>1. 이미지</h2>
        <label className={`drop ${drag ? 'over' : ''}`}>
          <input type="file" accept="image/*" multiple hidden data-testid="wm-images" onChange={(e) => e.target.files && addImages(e.target.files)} />
          <span>+ 이미지 여러 장을 끌어다 놓거나 클릭</span>
        </label>
        <p className="note" data-testid="wm-count">{images.length}장 선택됨</p>
        {images.length > 0 && <button onClick={() => { setImages([]); setResults([]); }}>목록 비우기</button>}
        <h2>2. 워터마크</h2>
        <div className="wmlist">
          {builtin.map((n) => (
            <button key={n} className={!wmFile && wmName === n ? 'on' : ''} onClick={() => { setWmFile(null); setWmName(n); }} title={n}>
              <img src={`${base}watermarks/${n}`} alt={n} />
            </button>
          ))}
        </div>
        <label className="drop small">
          <input type="file" accept="image/*" hidden data-testid="wm-file" onChange={(e) => e.target.files?.[0] && setWmFile(e.target.files[0])} />
          <span>내 워터마크 PNG 올리기</span>
        </label>
      </aside>

      <main className="main">
        <div className="stage checker wmstage">
          <canvas ref={prevRef} data-testid="wm-preview" />
        </div>
        <div className="bar">
          <span className="status" data-testid="wm-status">{busy || '옵션을 맞추고 "일괄 합성"을 누르세요 (미리보기는 첫 번째 이미지)'}</span>
          <button className="primary" onClick={run} disabled={!wm || !images.length} data-testid="wm-run">일괄 합성</button>
          <button onClick={zipAll} disabled={!results.length} data-testid="wm-zip">ZIP으로 저장</button>
        </div>
        {results.length > 0 && (
          <div className="results" data-testid="wm-results">
            {results.map((r) => (
              <a key={r.name + r.url} href={r.url} download={r.name} title={`${r.name} ${r.w}×${r.h}`}>
                <img src={r.url} alt={r.name} />
                <small>{r.name}</small>
              </a>
            ))}
          </div>
        )}
      </main>

      <aside className="ctrls">
        <h2>워터마크 옵션</h2>
        <label className="ctl"><span>투명도 <b>{o.opacity}%</b></span><input data-testid="wm-opacity" type="range" min={5} max={100} value={o.opacity} onChange={(e) => set('opacity', +e.target.value)} /></label>
        <label className="ctl"><span>크기 (이미지 너비 대비) <b>{o.sizePct}%</b></span><input data-testid="wm-size" type="range" min={4} max={90} value={o.sizePct} onChange={(e) => set('sizePct', +e.target.value)} /></label>
        <label className="ctl"><span>여백 <b>{o.marginPct}%</b></span><input type="range" min={0} max={15} step={0.5} value={o.marginPct} onChange={(e) => set('marginPct', +e.target.value)} /></label>
        <div className="ctl">
          <span>위치</span>
          <div className="grid9">
            {POS.map((p) => (
              <button key={p} className={o.pos === p && !o.tile ? 'on' : ''} onClick={() => setO((x) => ({ ...x, pos: p, tile: false }))} data-testid={`pos-${p}`} aria-label={p} />
            ))}
          </div>
        </div>
        <label className="ctl row"><input type="checkbox" checked={o.tile} onChange={(e) => set('tile', e.target.checked)} data-testid="wm-tile" /> 전체에 반복(타일)</label>
        {o.tile && <label className="ctl"><span>타일 각도 <b>{o.tileAngle}°</b></span><input type="range" min={-90} max={90} value={o.tileAngle} onChange={(e) => set('tileAngle', +e.target.value)} /></label>}
        <label className="ctl">
          <span>저장 형식</span>
          <select value={o.format} onChange={(e) => set('format', e.target.value as WmOptions['format'])} data-testid="wm-format">
            <option value="png">PNG (투명 유지)</option>
            <option value="jpeg">JPEG</option>
            <option value="webp">WebP</option>
          </select>
        </label>
        {o.format !== 'png' && <label className="ctl"><span>품질 <b>{Math.round(o.quality * 100)}</b></span><input type="range" min={0.5} max={1} step={0.01} value={o.quality} onChange={(e) => set('quality', +e.target.value)} /></label>}
        <button onClick={() => setO(defaultWm)}>기본값(투명도 45%)</button>
      </aside>
    </div>
  );
}
