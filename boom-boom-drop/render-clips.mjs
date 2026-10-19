// 사용법: node render-clips.mjs [시작번호] [끝번호]
import path from "node:path";
import fs from "node:fs";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";

const clips = JSON.parse(fs.readFileSync("src/clips.json", "utf8"));
const from = Number(process.argv[2] ?? 1);
const to = Number(process.argv[3] ?? clips.length);
const browserExecutable = process.env.BROWSER || undefined;
const outDir = "out/clips";
fs.mkdirSync(outDir, { recursive: true });

const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
for (const c of clips.filter((x) => x.n >= from && x.n <= to)) {
  const comp = await selectComposition({ serveUrl, id: "Line", inputProps: c, browserExecutable });
  const slug = c.text.replace(/[\\/:*?"<>|,!.']/g, "").replace(/\s+/g, "_").slice(0, 28);
  const file = path.join(outDir, `${String(c.n).padStart(2, "0")}_${c.sec}_${slug}.mp4`);
  await renderMedia({
    composition: comp,
    serveUrl,
    codec: "h264",
    pixelFormat: "yuv420p",
    crf: 18,
    imageFormat: "png",
    outputLocation: file,
    inputProps: c,
    browserExecutable,
  });
  console.log("done", file);
}
