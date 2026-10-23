"""pack / unpack: PC <-> 외부 GPU 사이로 주고받는 zip.

  pack --kind upload : (PC) segments/*/input.mp4, audio.wav, segments.json, info.json, analysis.json -> gpu_upload.zip
  pack --kind result : (GPU) segments/*/take_*.mp4|json, generation_log -> gpu_result.zip
  unpack             : (PC) 결과 zip 을 work/<이름>/ 에 병합. 기존 파일은 덮어쓰지 않고, 번호가 겹치는 take 는 새 번호로 보존.
"""
from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

from .generate import next_take_number
from .utils import PipelineError, Workspace, log, timestamp

_UPLOAD_TOP = {"segments.json", "info.json", "analysis.json", "face_track.json", "emotion.json", "cuts.json", "cuts_report.csv", "scan.json"}
_SEG_INPUT = re.compile(r"^segments/\d{3}/(input\.mp4|audio\.wav)$")
_SEG_TAKE = re.compile(r"^segments/(\d{3})/take_(\d+)\.(mp4|json)$")


def pack(ws: Workspace, kind: str, out: Path | None = None) -> Path:
    if kind not in ("upload", "result", "full"):
        raise PipelineError("--kind 는 upload, result, full 중 하나입니다.")
    out = out or ws.p(f"gpu_{kind}.zip")
    if out.exists():
        out = out.with_name(f"{out.stem}_{timestamp()}{out.suffix}")      # 덮어쓰기 금지
    files = []
    for f in sorted(ws.root.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(ws.root).as_posix()
        if kind == "upload" and (rel in _UPLOAD_TOP or _SEG_INPUT.match(rel)):
            files.append((f, rel))
        elif kind == "full" and not rel.startswith(("_archive/", "finalize/", "compare/", "gpu_")):
            files.append((f, rel))
        elif kind == "result" and (_SEG_TAKE.match(rel) or rel == "segments/generation_log.jsonl"):
            files.append((f, rel))
    if not files:
        raise PipelineError("묶을 파일이 없습니다. " + ("`segments` 단계를 먼저 실행했나요?" if kind == "upload" else "`lipsync` 로 후보를 먼저 만드세요."))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:        # mp4 는 이미 압축됨
        for f, rel in files:
            z.write(f, rel)
    log(f"[pack] {len(files)}개 파일 -> {out} ({out.stat().st_size / 1e6:.1f}MB)")
    return out


def unpack(ws: Workspace, zip_path: Path) -> list[str]:
    if not Path(zip_path).is_file():
        raise PipelineError(f"zip 파일이 없습니다: {zip_path}")
    added, skipped = [], []
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        allowed = lambda n: n in _UPLOAD_TOP or n == "segments/generation_log.jsonl" or _SEG_INPUT.match(n) or _SEG_TAKE.match(n)
        takes = {}
        for n in names:
            if not allowed(n):
                skipped.append(n)         # 허용 목록 밖의 경로는 무시 (zip-slip 방지)
                continue
            m = _SEG_TAKE.match(n)
            if m:
                takes.setdefault((m.group(1), m.group(2)), []).append(n)
                continue
            dest = ws.p(n)
            if n == "segments/generation_log.jsonl":
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "ab") as f:
                    f.write(z.read(n))
                continue
            if dest.exists():
                skipped.append(n)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(n))
            added.append(n)
        for (seg, k), members in sorted(takes.items()):
            d = ws.p(f"segments/{seg}"); d.mkdir(parents=True, exist_ok=True)
            newk = int(k)
            if (d / f"take_{k}.mp4").exists() or (d / f"take_{k}.json").exists():
                newk = next_take_number(d)          # 번호 충돌 -> 새 번호로 보존
            for n in members:
                ext = n.rsplit(".", 1)[1]
                data = z.read(n)
                if ext == "json":
                    import json
                    meta = json.loads(data.decode("utf-8"))
                    meta["take"] = newk
                    data = json.dumps(meta, ensure_ascii=False, indent=1).encode("utf-8")
                (d / f"take_{newk}.{ext}").write_bytes(data)
                added.append(f"segments/{seg}/take_{newk}.{ext}")
    log(f"[unpack] 추가 {len(added)}개, 건너뜀 {len(skipped)}개")
    return added
