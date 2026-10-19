export const FPS = 30;
export const BPM = 143.5; // 곡 템포: 클립 시작을 박자에 맞추면 클립 안의 깜빡임도 박자에 맞음
export const BEAT = 60 / BPM;

export type ClipProps = {
  n: number;
  sec: string;
  text: string;
  mode: "type" | "slam" | "countdown";
  icon: "star" | "heart" | "sun" | "bolt" | "crown";
  seed: number;
  tailShake: number;
  big: boolean;
};

const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));

export const WORD_STEP = BEAT / 2; // 슬램 줄: 단어가 8분음표 간격으로 켜짐
export const OUT = 0.3;

export const timing = (p: ClipProps) => {
  const words = p.text.split(" ").length;
  const chars = p.text.replace(/\s/g, "").length;
  if (p.mode === "countdown") {
    const inDur = BEAT * 2 * 3;
    return { inDur, hold: 0.5, out: OUT };
  }
  if (p.mode === "slam") {
    const inDur = WORD_STEP * (words - 1) + 0.35;
    return { inDur, hold: 1.3, out: OUT };
  }
  return { inDur: clamp(chars * 0.06, 0.8, 1.8), hold: 1.0, out: OUT };
};

export const clipFrames = (p: ClipProps) => {
  const t = timing(p);
  return Math.round((t.inDur + t.hold + t.out) * FPS);
};
