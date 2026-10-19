import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
} from "remotion";
import "@fontsource/anton/400.css";
import "@fontsource/black-han-sans/400.css";
import analysis from "../public/analysis.json";
import { DROP_T, FPS, buildVerse1, Token } from "./lyrics";

export const SAMPLE_FRAMES = Math.round(30.4 * FPS);

const f = (t: number) => Math.round(t * FPS);
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const easeOut = (x: number) => 1 - Math.pow(1 - clamp(x), 3);
const easeInOut = (x: number) => {
  const c = clamp(x);
  return c < 0.5 ? 4 * c * c * c : 1 - Math.pow(-2 * c + 2, 3) / 2;
};

const FONT = "Anton, 'Black Han Sans', sans-serif";
const SHADOW = "#2a0a5e";
const DROP_F = f(DROP_T);

const useBeat = () => {
  const frame = useCurrentFrame();
  const i = Math.min(frame, analysis.kick.length - 1);
  return { kick: analysis.kick[i] ?? 0, energy: analysis.energy[i] ?? 0 };
};

/* ---------------------------------------------------------------- 배경 */

type Blob = { c: string; cx: number; cy: number; ax: number; ay: number; w: number; ph: number; r: number };

const INTRO = {
  base: "#00e5ff",
  blobs: [
    { c: "#9b3df0", cx: 0.28, cy: 0.18, ax: 0.1, ay: 0.08, w: 0.9, ph: 0.0, r: 470 },
    { c: "#ffd60a", cx: 0.66, cy: 0.3, ax: 0.12, ay: 0.1, w: 0.7, ph: 1.7, r: 430 },
    { c: "#ff2e88", cx: 0.14, cy: 0.74, ax: 0.08, ay: 0.1, w: 1.1, ph: 3.1, r: 400 },
    { c: "#1cf58b", cx: 0.88, cy: 0.82, ax: 0.1, ay: 0.08, w: 0.8, ph: 4.4, r: 420 },
  ] as Blob[],
};
const VERSE = {
  base: "#ff5e0e",
  blobs: [
    { c: "#00e5ff", cx: 0.12, cy: 0.12, ax: 0.1, ay: 0.1, w: 1.3, ph: 0.4, r: 520 },
    { c: "#9b3df0", cx: 0.64, cy: 0.1, ax: 0.14, ay: 0.08, w: 1.0, ph: 2.0, r: 480 },
    { c: "#ff2e88", cx: 0.7, cy: 0.62, ax: 0.12, ay: 0.14, w: 1.2, ph: 3.3, r: 520 },
    { c: "#ffd60a", cx: 0.24, cy: 0.9, ax: 0.14, ay: 0.08, w: 0.9, ph: 5.0, r: 560 },
  ] as Blob[],
};

const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const { kick, energy } = useBeat();
  const set = frame < DROP_F ? INTRO : VERSE;
  const time = frame / FPS;
  const speed = frame < DROP_F ? 0.7 : 1.0 + energy * 0.8;

  // 인트로: "turn the lights off" → 어두워졌다가 진짜들이에서 켜짐
  const dark =
    frame < f(2.3)
      ? 0
      : frame < f(2.75)
      ? interpolate(frame, [f(2.3), f(2.75)], [0, 0.62])
      : frame < f(6.4)
      ? 0.62
      : 0;
  const flash = frame >= DROP_F ? interpolate(frame, [DROP_F, DROP_F + 9], [0.95, 0], { extrapolateRight: "clamp" }) : 0;
  const kickBoost = frame < DROP_F ? 0 : kick;

  return (
    <AbsoluteFill style={{ background: set.base }}>
      {set.blobs.map((b, i) => {
        const x = (b.cx + b.ax * Math.sin(time * b.w * speed + b.ph)) * 1920;
        const y = (b.cy + b.ay * Math.cos(time * b.w * 0.8 * speed + b.ph * 1.3)) * 1080;
        const r = b.r * (1 + 0.28 * kickBoost + 0.1 * energy);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - r,
              top: y - r,
              width: r * 2,
              height: r * 2,
              borderRadius: "50%",
              background: `radial-gradient(circle, ${b.c} 0%, ${b.c} 22%, ${b.c}00 70%)`,
              opacity: 0.95,
            }}
          />
        );
      })}
      <AbsoluteFill style={{ background: `rgba(14,0,46,${dark})` }} />
      <AbsoluteFill style={{ background: "#fff", opacity: flash }} />
    </AbsoluteFill>
  );
};

/* ---------------------------------------------------------------- 인트로: 슬램 */

type SlamProps = {
  text: string;
  at: number; // 등장(초)
  size: number;
  rot?: number;
  end?: number; // 퇴장(초)
  shake?: [number, number]; // [시작초, 끝초] 떨림+확대
};

const Slam: React.FC<SlamProps> = ({ text, at, size, rot = 0, end, shake }) => {
  const frame = useCurrentFrame();
  const t = frame - f(at);
  if (t < 0) return <div style={{ height: size * 1.02 }} />;
  const s = spring({ frame: t, fps: FPS, config: { damping: 10, stiffness: 240, mass: 0.55 } });
  let scale = interpolate(s, [0, 1], [2.3, 1]);
  let opacity = clamp(t / 2);
  let dx = 0;
  let dy = 0;
  if (end !== undefined && frame > f(end)) {
    const k = clamp((frame - f(end)) / 5);
    opacity *= 1 - k;
    scale *= 1 + 0.12 * k;
  }
  if (shake) {
    const k = clamp((frame - f(shake[0])) / (f(shake[1]) - f(shake[0])));
    scale *= 1 + 0.22 * k;
    dx = Math.sin(frame * 2.9) * 10 * k;
    dy = Math.cos(frame * 3.7) * 10 * k;
  }
  return (
    <div
      style={{
        fontFamily: FONT,
        fontSize: size,
        lineHeight: 1.02,
        color: "#fff",
        letterSpacing: "0.01em",
        whiteSpace: "nowrap",
        opacity,
        transform: `translate(${dx}px, ${dy}px) rotate(${rot}deg) scale(${scale})`,
        textShadow: `${size * 0.045}px ${size * 0.045}px 0 ${SHADOW}`,
      }}
    >
      {text}
    </div>
  );
};

const Group: React.FC<{ from: number; to: number; children: React.ReactNode }> = ({ from, to, children }) => {
  const frame = useCurrentFrame();
  if (frame < f(from) || frame >= f(to)) return null;
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
      {children}
    </AbsoluteFill>
  );
};

const Intro: React.FC = () => {
  const { kick } = useBeat();
  return (
    <AbsoluteFill style={{ transform: `scale(${1 + 0.02 * kick})` }}>
      {/* 0.44 YEAH, turn the lights off */}
      <Group from={0.4} to={3.5}>
        <Slam text="YEAH," at={0.44} size={400} rot={-3} end={3.35} />
        <div style={{ display: "flex", gap: 34, marginTop: 10 }}>
          {[
            ["turn", 1.3],
            ["the", 1.72],
            ["lights", 2.16],
            ["off", 2.6],
          ].map(([w, t]) => (
            <Slam key={w as string} text={w as string} at={t as number} size={150} rot={1.5} end={3.35} />
          ))}
        </div>
      </Group>

      {/* 6.43 진짜들이 판을 쓸어 */}
      <Group from={6.4} to={10.2}>
        <Slam text="진짜들이" at={6.43} size={250} rot={-2} end={10.0} />
        <Slam text="판을" at={7.08} size={250} rot={2} end={10.0} />
        <Slam text="쓸어" at={7.73} size={250} rot={-1.5} end={10.0} />
      </Group>

      {/* 10.31 LET IT, LET IT DROP! */}
      <Group from={10.3} to={DROP_T}>
        <Slam text="LET IT," at={10.31} size={210} rot={-2} />
        <Slam text="LET IT" at={11.59} size={210} rot={2} />
        <Slam text="DROP!" at={12.45} size={430} shake={[12.45, DROP_T]} />
      </Group>
    </AbsoluteFill>
  );
};

/* ---------------------------------------------------------------- 랩 구간: 이어 쓰기 */

const LINES = buildVerse1();

const tokenScale = (t: Token) => (t.kind === "caps" ? 1.2 : t.kind === "lower" ? 0.95 : 1);
const tokenWidth = (t: Token) =>
  tokenScale(t) *
  [...t.text].reduce((a, c) => a + (/[ㄱ-힝]/.test(c) ? 1.0 : /[A-Z]/.test(c) ? 0.52 : 0.46), 0);

const RapLine: React.FC<{ index: number; offset: number; activeFloat: number }> = ({ index, offset }) => {
  const frame = useCurrentFrame();
  const { kick } = useBeat();
  const line = LINES[index];
  const widthEm = line.tokens.reduce((a, t) => a + tokenWidth(t), 0) + (line.tokens.length - 1) * 0.3;
  const fs = Math.min(150, 1700 / widthEm);

  const scale = interpolate(Math.abs(offset), [0, 1, 2], [1, 0.58, 0.4], { extrapolateRight: "clamp" });
  const opacity = interpolate(offset, [-2, -1, 0, 1, 2], [0, 0.42, 1, 0.3, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const y = 540 + offset * 235;
  const isCurrent = Math.abs(offset) < 0.5;
  const bump = isCurrent ? 1 + 0.03 * kick : 1;
  const shadow = fs * 0.05;

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        width: 1920,
        top: y,
        transform: `translateY(-50%) scale(${scale * bump})`,
        opacity,
        display: "flex",
        justifyContent: "center",
        alignItems: "baseline",
        gap: fs * 0.3,
        fontFamily: FONT,
        fontSize: fs,
        lineHeight: 1.1,
        whiteSpace: "nowrap",
      }}
    >
      {line.tokens.map((tok, ti) => (
        <span key={ti} style={{ display: "inline-flex", alignItems: "baseline" }}>
          {tok.units.map((u, ui) => {
            const t = frame - f(u.t);
            const on = t >= 0;
            const pop = tok.kind === "caps" || tok.kind === "lower" ? 1 - easeOut(t / 7) : 1 - easeOut(t / 4) * 0.85;
            const sc = on ? 1 + (tok.kind === "caps" ? 0.35 : 0.18) * pop : 1;
            return (
              <span
                key={ui}
                style={{
                  display: "inline-block",
                  fontSize: `${tokenScale(tok)}em`,
                  color: on ? "#fff" : "rgba(255,255,255,0.38)",
                  textShadow: on
                    ? `${shadow}px ${shadow}px 0 ${SHADOW}`
                    : `${shadow * 0.6}px ${shadow * 0.6}px 0 rgba(42,10,94,0.2)`,
                  transform: `scale(${sc})`,
                  transformOrigin: "50% 85%",
                }}
              >
                {u.ch}
              </span>
            );
          })}
        </span>
      ))}
    </div>
  );
};

const Rap: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame < DROP_F - 2) return null;
  // 각 줄이 "현재 줄"이 되는 진행도의 합 → 연속 스크롤 위치
  let active = -1;
  LINES.forEach((l) => {
    active += easeInOut((frame - (f(l.start) - 6)) / 11);
  });
  return (
    <AbsoluteFill>
      {LINES.map((_, i) => {
        const offset = i - active;
        if (Math.abs(offset) > 2.2) return null;
        return <RapLine key={i} index={i} offset={offset} activeFloat={active} />;
      })}
    </AbsoluteFill>
  );
};

/* ---------------------------------------------------------------- 합성 */

export const Sample: React.FC = () => (
  <AbsoluteFill>
    <Audio src={staticFile("audio.mp3")} />
    <Background />
    <Intro />
    <Rap />
  </AbsoluteFill>
);
