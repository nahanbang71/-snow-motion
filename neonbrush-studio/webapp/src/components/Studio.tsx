import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { FontPack, loadPacksFromZip } from '../lib/packs';
import { Align, TypeOptions, canvasToPngBlob, defaultOptions, draw, layout, measure, renderToCanvas } from '../lib/typeset';
import { safeName, saveBlob } from '../lib/download';

type Bg = 'checker' | 'dark' | 'light' | 'custom';

/** a font in the list; built-in packs are only downloaded when they are selected */
interface Item {
  key: string;
  name: string;
  isColor: boolean;
  glyphs: number;
  origin: 'builtin' | 'webpack' | 'raw';
  file?: string;
  pack?: FontPack;
  loading?: boolean;
}
const base = import.meta.env.BASE_URL;

function Slider(p: { label: string; value: number; min: number; max: number; step?: number; onChange: (v: number) => void; suffix?: string; id: string }) {
  return (
    <label className="ctl">
      <span>
        {p.label} <b>{p.value}{p.suffix ?? ''}</b>
      </span>
      <input data-testid={p.id} type="range" min={p.min} max={p.max} step={p.step ?? 1} value={p.value} onChange={(e) => p.onChange(+e.target.value)} />
    </label>
  );
}

export default function Studio() {
  const [items, setItems] = useState<Item[]>([]);
  const [sel, setSel] = useState<string>('');
  const [opt, setOpt] = useState<TypeOptions>(defaultOptions);
  const [bg, setBg] = useState<Bg>('checker');
  const [bgColor, setBgColor] = useState('#3b82f6');
  const [exportScale, setExportScale] = useState(2);
  const [status, setStatus] = useState('내장 글꼴을 불러오는 중…');
  const [drag, setDrag] = useState(false);
  const [missing, setMissing] = useState<string[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);
  const [stageSize, setStageSize] = useState({ w: 800, h: 400 });

  const pack = useMemo(() => items.find((i) => i.key === sel)?.pack ?? null, [items, sel]);
  const current = items.find((i) => i.key === sel);
  const set = <K extends keyof TypeOptions>(k: K, v: TypeOptions[K]) => setOpt((o) => ({ ...o, [k]: v }));

  const addZips = useCallback(async (files: File[] | { name: string; data: Blob }[]) => {
    const added: FontPack[] = [];
    for (const f of files) {
      const name = f.name;
      try {
        const data = 'data' in f ? f.data : f;
        added.push(...(await loadPacksFromZip(data, name)));
      } catch (e) {
        setStatus(`${name}: 읽을 수 없는 파일 (${(e as Error).message})`);
      }
    }
    if (added.length) {
      setItems((it) => [...it, ...added.map((p): Item => ({ key: p.id, name: p.name, isColor: p.isColor, glyphs: p.glyphs.size, origin: p.origin, pack: p }))]);
      setSel((s) => s || added[0].id);
      setStatus(`${added.length}개 글꼴 추가됨`);
    }
    return added;
  }, []);

  /** select a font, downloading a built-in pack on first use */
  const choose = useCallback(async (key: string, list?: Item[]) => {
    setSel(key);
    const it = (list ?? items).find((i) => i.key === key);
    if (!it || it.pack || it.loading || !it.file) return;
    setItems((cur) => cur.map((i) => (i.key === key ? { ...i, loading: true } : i)));
    setStatus(`${it.name} 불러오는 중…`);
    try {
      const blob = await (await fetch(`${base}packs/${it.file}`)).blob();
      const [p] = await loadPacksFromZip(blob, it.file);
      setItems((cur) => cur.map((i) => (i.key === key ? { ...i, pack: p, loading: false } : i)));
      setStatus(`${it.name} 준비 완료 — 키보드로 바로 입력하세요`);
    } catch (e) {
      setItems((cur) => cur.map((i) => (i.key === key ? { ...i, loading: false } : i)));
      setStatus(`${it.name}: 불러오기 실패 (${(e as Error).message})`);
    }
  }, [items]);

  // built-in library: only the list (index.json) is fetched up front; each pack downloads when selected
  useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const list: { file: string; name: string; isColor: boolean; glyphs: number }[] = await (await fetch(`${base}packs/index.json`)).json();
        if (dead) return;
        const its: Item[] = list.map((e) => ({ key: 'builtin:' + e.file, name: e.name, isColor: e.isColor, glyphs: e.glyphs, origin: 'builtin', file: e.file }));
        setItems((cur) => [...its, ...cur]);
        if (its.length) await choose(its[0].key, its);
        else setStatus('내장 글꼴이 없습니다. .zip 팩을 끌어다 놓으세요');
      } catch {
        if (!dead) setStatus('.zip 글자 팩을 화면에 끌어다 놓으세요');
      }
    })();
    return () => {
      dead = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // keep the preview stage size
  useEffect(() => {
    const el = stageRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setStageSize({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // typing anywhere goes into the text box
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (t && /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.key.length === 1 || e.key === 'Enter' || e.key === 'Backspace') taRef.current?.focus();
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  // live preview
  useEffect(() => {
    const c = canvasRef.current;
    if (!c || !pack) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const l = layout(pack, opt);
    setMissing(l.missing);
    const natural = measure(l, opt.size / pack.upm, opt.padding);
    const fit = Math.min(1, (stageSize.w - 24) / natural.w, (stageSize.h - 24) / natural.h);
    const ppu = (opt.size / pack.upm) * fit * dpr;
    const m = measure(l, ppu, opt.padding * fit * dpr);
    c.width = Math.max(1, m.w);
    c.height = Math.max(1, m.h);
    c.style.width = `${c.width / dpr}px`;
    c.style.height = `${c.height / dpr}px`;
    const ctx = c.getContext('2d')!;
    ctx.clearRect(0, 0, c.width, c.height);
    draw(ctx, pack, l, { ...opt, padding: opt.padding * fit * dpr }, ppu);
  }, [pack, opt, stageSize]);

  const download = async () => {
    if (!pack) return;
    const r = renderToCanvas(pack, opt, exportScale);
    const blob = await canvasToPngBlob(r.canvas);
    saveBlob(blob, `neonbrush_${safeName(pack.name)}_${safeName(opt.text.split('\n')[0])}_${r.canvas.width}x${r.canvas.height}.png`);
    setStatus(`PNG 저장: ${r.canvas.width}×${r.canvas.height}px (투명 배경, 여백 크롭)${r.clamped ? ' — 너무 커서 축소됨' : ''}`);
  };

  const stageBg = bg === 'checker' ? 'checker' : bg === 'dark' ? 'dark' : bg === 'light' ? 'light' : '';
  const onDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setDrag(false);
    const zips = [...e.dataTransfer.files].filter((f) => /\.zip$/i.test(f.name));
    if (zips.length) await addZips(zips);
    else setStatus('.zip 파일만 글꼴 팩으로 불러올 수 있어요');
  };

  return (
    <div className="studio" onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={onDrop}>
      <aside className="side">
        <h2>글꼴 목록</h2>
        <ul className="packs" data-testid="pack-list">
          {items.map((p) => (
            <li key={p.key} className={p.key === sel ? 'on' : ''} onClick={() => choose(p.key)} data-testid="pack-item">
              <b>{p.name}</b>
              <small>
                {p.glyphs}자 {p.isColor ? '· 컬러' : '· 단색'} {p.origin === 'raw' ? '· 원본' : ''} {p.loading ? '· 불러오는 중…' : ''}
              </small>
            </li>
          ))}
        </ul>
        <label className={`drop ${drag ? 'over' : ''}`}>
          <input type="file" accept=".zip" multiple hidden data-testid="zip-input" onChange={(e) => e.target.files && addZips([...e.target.files])} />
          <span>+ .zip 글꼴 팩을 끌어다 놓거나 클릭</span>
        </label>
        {current?.pack?.notes.map((n, i) => (
          <p className="note" key={i}>{n}</p>
        ))}
      </aside>

      <main className="main">
        <textarea
          ref={taRef}
          autoFocus
          spellCheck={false}
          data-testid="text"
          value={opt.text}
          onChange={(e) => set('text', e.target.value)}
          placeholder="여기에 입력하세요 (Enter = 줄바꿈)"
          rows={3}
        />
        {missing.length > 0 && <div className="warn">이 글꼴에 없는 글자: {missing.join(' ')}</div>}
        <div ref={stageRef} className={`stage ${stageBg}`} style={bg === 'custom' ? { background: bgColor } : undefined} onClick={() => taRef.current?.focus()}>
          {pack ? <canvas ref={canvasRef} data-testid="preview" /> : <p className="hint">글꼴을 불러오는 중이거나 선택된 글꼴이 없어요</p>}
        </div>
        <div className="bar">
          <span className="status" data-testid="status">{status}</span>
          <label>
            해상도
            <select value={exportScale} onChange={(e) => setExportScale(+e.target.value)} data-testid="scale">
              {[1, 2, 3, 4, 6].map((s) => (
                <option key={s} value={s}>{s}× </option>
              ))}
            </select>
          </label>
          <button className="primary" onClick={download} disabled={!pack} data-testid="download">투명 PNG 다운로드 (여백 크롭)</button>
        </div>
      </main>

      <aside className="ctrls">
        <h2>조판 설정</h2>
        <Slider id="size" label="글자 크기" value={opt.size} min={40} max={600} onChange={(v) => set('size', v)} suffix="px" />
        <Slider id="tracking" label="자간 (Kerning)" value={opt.tracking} min={-250} max={500} onChange={(v) => set('tracking', v)} />
        <Slider id="space" label="띄어쓰기 폭" value={opt.spacePct} min={20} max={400} onChange={(v) => set('spacePct', v)} suffix="%" />
        <Slider id="lineheight" label="줄 간격" value={opt.lineHeight} min={0.4} max={2.2} step={0.01} onChange={(v) => set('lineHeight', v)} suffix="em" />
        <Slider id="arc" label="아치 곡선" value={opt.arc} min={-100} max={100} onChange={(v) => set('arc', v)} />
        <div className="ctl">
          <span>줄 정렬</span>
          <div className="seg">
            {(['left', 'center', 'right'] as Align[]).map((a) => (
              <button key={a} className={opt.align === a ? 'on' : ''} onClick={() => set('align', a)} data-testid={`align-${a}`}>
                {a === 'left' ? '왼쪽' : a === 'center' ? '가운데' : '오른쪽'}
              </button>
            ))}
          </div>
        </div>
        <Slider id="padding" label="PNG 여백" value={opt.padding} min={0} max={200} onChange={(v) => set('padding', v)} suffix="px" />
        <div className="ctl">
          <span>글자 색 {pack?.isColor && <small>(컬러 팩은 원본 색 유지)</small>}</span>
          <div className="row">
            <input type="checkbox" checked={!!opt.tint} disabled={!pack || pack.isColor} onChange={(e) => set('tint', e.target.checked ? '#ffffff' : null)} data-testid="tint-on" />
            <input type="color" value={opt.tint ?? '#ffffff'} disabled={!opt.tint || !!pack?.isColor} onChange={(e) => set('tint', e.target.value)} data-testid="tint" />
          </div>
        </div>
        <div className="ctl">
          <span>미리보기 배경</span>
          <div className="seg">
            {(['checker', 'dark', 'light', 'custom'] as Bg[]).map((b) => (
              <button key={b} className={bg === b ? 'on' : ''} onClick={() => setBg(b)}>
                {b === 'checker' ? '체크' : b === 'dark' ? '어둡게' : b === 'light' ? '밝게' : '색'}
              </button>
            ))}
          </div>
          {bg === 'custom' && <input type="color" value={bgColor} onChange={(e) => setBgColor(e.target.value)} />}
        </div>
        <button onClick={() => setOpt(defaultOptions)}>설정 초기화</button>
      </aside>
    </div>
  );
}
