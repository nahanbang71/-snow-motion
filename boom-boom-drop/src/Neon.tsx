import React, { useLayoutEffect, useRef, useState } from "react";
import {
  AbsoluteFill,
  continueRender,
  delayRender,
  interpolate,
  random,
  spring,
  useCurrentFrame,
} from "remotion";
import "@fontsource/anton/400.css";
import "@fontsource/black-han-sans/400.css";
import { BEAT, ClipProps, FPS, WORD_STEP, timing } from "./neonTiming";

const FONT = "Anton, 'Black Han Sans', sans-serif";
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));

const COL = {
  en: { core: "#ffe3f1", glow: "#ff2f95" },
  ko: { core: "#e3fbff", glow: "#1fd0ff" },
};
const LASER = ["#ff4d6d", "#4d7cff", "#ff4d6d"];
const ICON_COL: Record<string, { core: string; glow: string }> = {
  star: { core: "#fff4b0", glow: "#ffd23f" },
  heart: { core: "#ffd1e6", glow: "#ff2f95" },
  sun: { core: "#fff4b0", glow: "#ffb703" },
  bolt: { core: "#fff4b0", glow: "#ffd23f" },
  crown: { core: "#fff4b0", glow: "#ffb703" },
};

const hexA = (hex: string, a: number) => {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
};

const isHangul = (s: string) => /[ㄱ-힝]/.test(s);
const isCaps = (s: string) => /[A-Z]/.test(s) && !/[a-z]/.test(s) && !isHangul(s);
const tokenScale = (w: string) => (isCaps(w) ? 1.2 : isHangul(w) ? 1 : 0.95);
const palette = (w: string) => (isHangul(w) ? COL.ko : COL.en);

/* ------------------------------------------------------------ 네온 글자 스타일 */

const litStyle = (c: { core: string; glow: string }, fs: number, k: number, hot: number): React.CSSProperties => {
  const core = hot > 0.35 ? "#ffffff" : c.core;
  const g = k * (1 + hot * 0.9);
  const r = (m: number) => fs * m * g;
  return {
    color: hexA(c.glow, 0.3 * Math.min(1, k)),
    WebkitTextStroke: `${Math.max(2.5, fs * 0.026)}px ${core}`,
    textShadow: [
      `0 0 ${r(0.03)}px ${core}`,
      `0 0 ${r(0.08)}px ${c.glow}`,
      `0 0 ${r(0.2)}px ${c.glow}`,
      `0 0 ${r(0.45)}px ${hexA(c.glow, 0.85)}`,
    ].join(","),
    opacity: Math.min(1, 0.25 + k),
  };
};
const unlitStyle = (c: { core: string; glow: string }, fs: number): React.CSSProperties => ({
  color: "transparent",
  WebkitTextStroke: `${Math.max(2, fs * 0.02)}px ${hexA(c.core, 0.16)}`,
});

/* ------------------------------------------------------------ 폰트 로딩 후 한 줄에 맞추기 */

const RowBase: React.FC<{ words: string[]; fs: number; children?: (w: string, i: number) => React.ReactNode }> = ({
  words,
  fs,
  children,
}) => (
  <div
    style={{
      display: "inline-flex",
      alignItems: "baseline",
      gap: fs * 0.3,
      fontFamily: FONT,
      fontSize: fs,
      letterSpacing: "0.02em",
      whiteSpace: "nowrap",
    }}
  >
    {words.map((w, i) => (
      <span key={i} style={{ display: "inline-flex", alignItems: "baseline", fontSize: `${tokenScale(w)}em` }}>
        {children ? children(w, i) : w}
      </span>
    ))}
  </div>
);

const useFit = (text: string, words: string[], maxFs: number, maxW: number) => {
  const ref = useRef<HTMLDivElement>(null);
  const [fs, setFs] = useState<number | null>(null);
  const [handle] = useState(() => delayRender("fit-text"));
  useLayoutEffect(() => {
    let alive = true;
    Promise.all([
      document.fonts.load("100px Anton", text),
      document.fonts.load("100px 'Black Han Sans'", text),
    ])
      .catch(() => undefined)
      .then(() => document.fonts.ready)
      .then(() => {
        if (!alive) return;
        const w = ref.current?.getBoundingClientRect().width ?? 1000;
        setFs(Math.min(maxFs, (100 * maxW) / w));
        continueRender(handle);
      });
    return () => {
      alive = false;
    };
  }, []);
  const measurer = (
    <div ref={ref} style={{ position: "absolute", visibility: "hidden", left: 0, top: 0 }}>
      <RowBase words={words} fs={100} />
    </div>
  );
  return { fs, measurer };
};

/* ------------------------------------------------------------ 레이저 선 + 아이콘 */

const Lasers: React.FC<{ seed: number; total: number; outAt: number }> = ({ seed, total, outAt }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const fade = 1 - clamp((t - outAt) / 0.3);
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, opacity: fade * 0.8 }}>
      {[0, 1, 2].map((i) => {
        const r = (k: string) => random(`${seed}-l${i}-${k}`);
        const fromLeft = i % 2 === 0;
        const pts = [
          [fromLeft ? -40 : 1960, 80 + r("a") * 900],
          [300 + r("b") * 1300, 100 + r("c") * 880],
          [fromLeft ? 1960 : -40, 80 + r("d") * 900],
        ];
        const d = `M${pts[0][0]},${pts[0][1]} L${pts[1][0]},${pts[1][1]} L${pts[2][0]},${pts[2][1]}`;
        const p = clamp((t - i * 0.08) / 0.55);
        const e = 1 - Math.pow(1 - p, 3);
        return (
          <g key={i} style={{ filter: `drop-shadow(0 0 6px ${LASER[i]}) drop-shadow(0 0 14px ${LASER[i]})` }}>
            <path d={d} pathLength={1} stroke={LASER[i]} strokeWidth={3} fill="none" strokeDasharray="1" strokeDashoffset={1 - e} />
            {p > 0 && p < 1 && (
              <circle
                r={7}
                fill="#fff"
                cx={0}
                cy={0}
                transform={`translate(${
                  e < 0.5 ? pts[0][0] + (pts[1][0] - pts[0][0]) * (e * 2) : pts[1][0] + (pts[2][0] - pts[1][0]) * ((e - 0.5) * 2)
                },${
                  e < 0.5 ? pts[0][1] + (pts[1][1] - pts[0][1]) * (e * 2) : pts[1][1] + (pts[2][1] - pts[1][1]) * ((e - 0.5) * 2)
                })`}
              />
            )}
          </g>
        );
      })}
    </svg>
  );
};

const ICON_PATH: Record<string, React.ReactNode> = {
  star: <polygon points="50,6 61,38 95,38 67,58 78,92 50,71 22,92 33,58 5,38 39,38" />,
  heart: <path d="M50 88 C10 58 6 30 26 18 C40 10 50 22 50 30 C50 22 60 10 74 18 C94 30 90 58 50 88Z" />,
  bolt: <polygon points="58,4 20,54 46,54 38,96 80,40 54,40" />,
  crown: <polygon points="8,78 8,30 30,52 50,16 70,52 92,30 92,78" />,
  sun: (
    <g>
      <circle cx="50" cy="50" r="18" />
      {[...Array(8)].map((_, i) => {
        const a = (i * Math.PI) / 4;
        return <line key={i} x1={50 + Math.cos(a) * 28} y1={50 + Math.sin(a) * 28} x2={50 + Math.cos(a) * 42} y2={50 + Math.sin(a) * 42} />;
      })}
    </g>
  ),
};

const Icon: React.FC<{ kind: string; seed: number; outAt: number }> = ({ kind, seed, outAt }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const c = ICON_COL[kind];
  const corner = Math.floor(random(`${seed}-corner`) * 4);
  const x = corner % 2 === 0 ? 150 : 1770;
  const y = corner < 2 ? 130 : 950;
  const s = spring({ frame: frame - 5, fps: FPS, config: { damping: 9, stiffness: 180, mass: 0.6 } });
  const flick = t < 0.5 ? (random(`${seed}-ic-${Math.floor(t * 30)}`) > 0.4 ? 1 : 0.3) : 1;
  const pulse = Math.exp(-((t % BEAT) / BEAT) * 5);
  const fade = 1 - clamp((t - outAt) / 0.3);
  const bob = Math.sin(t * 2.2 + seed) * 8;
  return (
    <svg
      width={120}
      height={120}
      viewBox="0 0 100 100"
      style={{
        position: "absolute",
        left: x - 60,
        top: y - 60 + bob,
        transform: `scale(${s * (1 + 0.08 * pulse)}) rotate(${Math.sin(t * 1.5 + seed) * 8}deg)`,
        opacity: fade * flick,
        overflow: "visible",
        filter: `drop-shadow(0 0 4px ${c.core}) drop-shadow(0 0 12px ${c.glow}) drop-shadow(0 0 26px ${c.glow})`,
      }}
      fill="none"
      stroke={c.core}
      strokeWidth={4}
      strokeLinejoin="round"
      strokeLinecap="round"
    >
      {ICON_PATH[kind]}
    </svg>
  );
};

/* ------------------------------------------------------------ 한 줄 렌더 (타이핑 / 슬램) */

const Line: React.FC<{ p: ClipProps; inDur: number; outAt: number }> = ({ p, inDur, outAt }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const words = p.text.split(" ");
  const { fs, measurer } = useFit(p.text, words, p.big ? 340 : p.mode === "slam" ? 210 : 132, 1600);
  if (fs === null) return <>{measurer}</>;

  const totalChars = words.join("").length;
  let g = 0;
  const pulse = Math.exp(-((t % BEAT) / BEAT) * 5);
  const fadeOut = clamp((t - outAt) / 0.3);
  const offFlick = fadeOut > 0 ? (random(`${p.seed}-off-${frame}`) > fadeOut * 0.7 ? 1 : 0.2) : 1;
  const lineScale = 1 + 0.022 * pulse;
  const tailStart = words.length - p.tailShake;

  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      {measurer}
      <div style={{ transform: `scale(${lineScale})`, opacity: p.tailShake && fadeOut ? 1 - fadeOut : offFlick * (1 - fadeOut * 0.5) }}>
        <RowBase words={words} fs={fs}>
          {(w, wi) => {
            const c = palette(w);
            const caps = isCaps(w);
            const shake = p.tailShake > 0 && wi >= tailStart;
            const wt = wi * WORD_STEP;
            return [...w].map((ch, ci) => {
              const my = g++;
              const tu = p.mode === "type" ? (my / totalChars) * inDur : wt;
              const f = t - tu;
              const on = f >= 0;
              if (!on && p.mode === "slam") return null;
              const sh = shake && on ? { x: (random(`${p.seed}-sx-${frame}-${my}`) - 0.5) * 12, y: (random(`${p.seed}-sy-${frame}-${my}`) - 0.5) * 12 } : { x: 0, y: 0 };
              if (!on) {
                return (
                  <span key={ci} style={{ ...unlitStyle(c, fs), display: "inline-block" }}>
                    {ch}
                  </span>
                );
              }
              const flick = f < 0.3 ? (random(`${p.seed}-f-${my}-${Math.floor(f * 30)}`) > 0.35 ? 1 : 0.25) : 1;
              const hot = clamp(1 - f / 0.18);
              const k = (0.85 + 0.3 * pulse + (caps ? 0.1 : 0)) * flick;
              const pop = p.mode === "slam" ? spring({ frame: Math.round(f * FPS), fps: FPS, config: { damping: 11, stiffness: 230, mass: 0.55 } }) : 1;
              const sc = p.mode === "slam" ? interpolate(pop, [0, 1], [1.7, 1]) : 1 + 0.18 * hot;
              return (
                <span
                  key={ci}
                  style={{
                    ...litStyle(c, fs, k, hot),
                    display: "inline-block",
                    transform: `translate(${sh.x}px, ${sh.y}px) scale(${sc})`,
                    transformOrigin: "50% 80%",
                  }}
                >
                  {ch}
                </span>
              );
            });
          }}
        </RowBase>
      </div>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------ 카운트다운 (3, 2, 1) */

const Countdown: React.FC<{ p: ClipProps; outAt: number }> = ({ p, outAt }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const step = BEAT * 2;
  const i = Math.min(2, Math.floor(t / step));
  const digit = ["3", "2", "1"][i];
  const f = t - i * step;
  const pop = spring({ frame: Math.round(f * FPS), fps: FPS, config: { damping: 10, stiffness: 240, mass: 0.55 } });
  const c = [COL.en, COL.ko, COL.en][i];
  const fadeOut = clamp((t - outAt) / 0.3);
  const fs = 620;
  const k = 0.9 + 0.4 * Math.exp(-((f % BEAT) / BEAT) * 5);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div
        style={{
          fontFamily: FONT,
          fontSize: fs,
          lineHeight: 1,
          transform: `scale(${interpolate(pop, [0, 1], [1.8, 1])})`,
          opacity: 1 - fadeOut,
          ...litStyle(c, fs, k, clamp(1 - f / 0.2)),
        }}
      >
        {digit}
      </div>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------ 합성 */

export const NeonClip: React.FC<ClipProps> = (p) => {
  const frame = useCurrentFrame();
  const { inDur, hold } = timing(p);
  const outAt = inDur + hold;
  const flash = p.big ? interpolate(frame, [0, 6], [0.45, 0], { extrapolateRight: "clamp" }) : 0;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Lasers seed={p.seed} total={inDur + hold} outAt={outAt} />
      <Icon kind={p.icon} seed={p.seed} outAt={outAt} />
      {p.mode === "countdown" ? <Countdown p={p} outAt={outAt} /> : <Line p={p} inDur={inDur} outAt={outAt} />}
      <AbsoluteFill style={{ background: "#fff", opacity: flash }} />
    </AbsoluteFill>
  );
};
