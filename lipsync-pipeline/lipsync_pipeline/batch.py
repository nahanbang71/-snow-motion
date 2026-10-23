"""batch: 작업목록.csv (영상경로, 음원경로, 이름, 프리셋) 를 순서대로 처리. 한 작업이 실패해도 다음 작업은 계속한다."""
from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Optional, Sequence

from .pipeline import Job, run_job
from .presets import load_preset
from .utils import PipelineError, log, read_json, sanitize_name

COL_VIDEO, COL_AUDIO, COL_NAME, COL_PRESET = "영상경로", "음원경로", "이름", "프리셋"


def read_jobs(csv_path: Path, default_preset: str = "quality") -> list[tuple[int, Optional[Job], str]]:
    """[(행 번호, Job 또는 None, 오류 메시지)]. 잘못된 행도 목록에 남겨 마지막 리포트에 표시한다."""
    raw = Path(csv_path).read_bytes()
    for enc in ("utf-8-sig", "cp949"):                      # 한국어 엑셀이 저장한 CSV 는 cp949 인 경우가 많다
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise PipelineError("CSV 인코딩을 읽을 수 없습니다. UTF-8 로 저장해 주세요.")
    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        raise PipelineError("작업목록이 비어 있습니다.")
    missing = [c for c in (COL_VIDEO, COL_AUDIO) if c not in (rows[0].keys())]
    if missing:
        raise PipelineError(f"CSV 에 필요한 열이 없습니다: {', '.join(missing)} (열: 영상경로, 음원경로, 이름, 프리셋)")
    base = Path(csv_path).resolve().parent
    out, seen = [], set()
    for i, r in enumerate(rows, start=2):                   # 1행은 헤더
        v, a = (r.get(COL_VIDEO) or "").strip(), (r.get(COL_AUDIO) or "").strip()
        if not v and not a:
            continue
        try:
            if not v or not a:
                raise PipelineError("영상경로/음원경로 중 비어 있는 값이 있습니다.")
            vp, ap = (Path(x) if Path(x).is_absolute() else base / x for x in (v, a))
            name = sanitize_name((r.get(COL_NAME) or "").strip() or vp.stem)
            if name in seen:
                raise PipelineError(f"이름 '{name}' 이(가) 중복됩니다. 이름 열을 구분해 주세요.")
            seen.add(name)
            out.append((i, Job(name, vp, ap, (r.get(COL_PRESET) or "").strip() or default_preset), ""))
        except PipelineError as e:
            out.append((i, None, str(e)))
    return out


def run_batch(csv_path: Path, work_root: Path | str = "work", stages: Optional[Sequence[str]] = None,
              start: Optional[str] = None, until: Optional[str] = None, force: bool = False,
              default_preset: str = "quality", preset_dir: Optional[Path] = None, overrides: Optional[dict] = None) -> list[dict]:
    jobs = read_jobs(csv_path, default_preset)
    results: list[dict] = []
    t_all = time.time()
    for row_no, job, err in jobs:
        if job is None:
            log(f"[건너뜀] {row_no}행: {err}")
            results.append({"row": row_no, "name": "", "status": "failed", "stage": "csv", "error": err})
            continue
        log(f"\n######## [{len(results) + 1}/{len(jobs)}] {job.name} (프리셋: {job.preset}) ########")
        try:
            pr = load_preset(job.preset, [preset_dir] if preset_dir else None)
            for k, v in (overrides or {}).items():
                if v is not None:
                    setattr(pr, k, v)
            r = run_job(job, pr, work_root, stages, start, until, force)
            results.append({"row": row_no, "name": job.name, "status": "done", "stage": ",".join(r["ran"]) or "(모두 완료됨)", "error": ""})
        except KeyboardInterrupt:
            raise
        except BaseException as e:                       # 실패해도 다음 작업은 계속
            st = read_json(Path(work_root) / job.name / "state.json") if (Path(work_root) / job.name / "state.json").exists() else {"stages": {}}
            failed = next((s for s, v in st["stages"].items() if v.get("status") == "failed"), "")
            msg = str(e) if isinstance(e, PipelineError) else f"{type(e).__name__}: {e}"
            log(f"[실패] {job.name} / {failed or '?'}: {msg}")
            results.append({"row": row_no, "name": job.name, "status": "failed", "stage": failed, "error": msg})
    write_summary(Path(work_root), results, time.time() - t_all)
    return results


def write_summary(work_root: Path, results: list[dict], seconds: float) -> Path:
    work_root.mkdir(parents=True, exist_ok=True)
    p = work_root / f"batch_summary_{time.strftime('%Y%m%d-%H%M%S')}.csv"          # 매번 새 파일
    with open(p, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["row", "name", "status", "stage", "error"])
        w.writeheader(); w.writerows(results)
    bad = [r for r in results if r["status"] != "done"]
    log(f"\n==== 배치 결과: 성공 {len(results) - len(bad)} / 실패 {len(bad)} / 전체 {len(results)}  ({seconds / 60:.1f}분) ====")
    for r in bad:
        log(f"  실패: {r['name'] or ('행 ' + str(r['row']))} [{r['stage']}] {r['error'].splitlines()[0] if r['error'] else ''}")
    log(f"  요약 파일: {p}")
    return p
