// 타이밍은 임시 추정치입니다. Whisper 단어 타임스탬프로 교체하면 정확해집니다.
export const FPS = 30;
export const DROP_T = 13.68; // 인트로 끝, 비트가 터지는 지점(초)

export type RapLine = { text: string };

// 최종 완성본 가사 기준 (Verse 1)
export const VERSE1: RapLine[] = [
  { text: "땅이 울려대" },
  { text: "heavy feet on the floor," },
  { text: "가짜들의 왕관, 손끝으로 깨" },
  { text: "DROP THAT BEAT, 밑바닥에서 IGNITE" },
  { text: "i don't play no game, I RULE THE NIGHT" },
  { text: "단단히 벼린 블레이드, 절대로 안 부러져" },
  { text: "무대 위 터진 에너지, 사방으로 번져" },
  { text: "HEAR THAT ROAR, 멈출 생각 없어" },
  { text: "더 세게 때려라, 비트 위를 덮어!" },
];

export const VERSE1_START = 13.9;
export const VERSE1_END = 40.4;

const isHangul = (s: string) => /[ㄱ-힝]/.test(s);
const isCaps = (s: string) => /[A-Z]/.test(s) && !/[a-z]/.test(s) && !isHangul(s);

export const syllables = (w: string) => {
  const h = (w.match(/[ㄱ-힝]/g) || []).length;
  if (h) return h;
  const v = (w.toLowerCase().match(/[aeiouy]+/g) || []).length;
  return Math.max(1, v);
};

export type Unit = { ch: string; t: number };
export type Token = {
  text: string;
  kind: "hangul" | "caps" | "lower";
  units: Unit[]; // 한글은 글자 단위, 영어는 단어 단위
  t0: number;
};
export type TimedLine = { start: number; end: number; tokens: Token[] };

// 음절 수에 비례해서 시간을 나눕니다 (일정한 랩 속도 가정)
export const buildVerse1 = (): TimedLine[] => {
  const weights = VERSE1.map((l) =>
    l.text.split(" ").reduce((a, w) => a + syllables(w) + (w.endsWith(",") ? 0.5 : 0), 0)
  );
  const gap = 0.12;
  const total = weights.reduce((a, b) => a + b, 0);
  const perSyl = (VERSE1_END - VERSE1_START - gap * VERSE1.length) / total;
  let cursor = VERSE1_START;
  return VERSE1.map((l, i) => {
    const start = cursor;
    const end = start + weights[i] * perSyl;
    cursor = end + gap;
    let tc = start;
    const tokens: Token[] = l.text.split(" ").map((w) => {
      const dur = syllables(w) * perSyl;
      const t0 = tc;
      tc += dur + (w.endsWith(",") ? 0.5 * perSyl : 0);
      const kind = isHangul(w) ? "hangul" : isCaps(w) ? "caps" : "lower";
      const chars = [...w];
      const units: Unit[] =
        kind === "hangul"
          ? chars.map((ch, k) => ({ ch, t: t0 + (k / chars.length) * dur }))
          : [{ ch: w, t: t0 }];
      return { text: w, kind, units, t0 };
    });
    return { start, end, tokens };
  });
};
