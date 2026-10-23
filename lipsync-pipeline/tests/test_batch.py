"""프리셋 / state.json 이어하기 / report.csv / batch (실패 격리) — 전부 CPU, identity 모델."""
import csv
import json
from pathlib import Path

import pytest

from lipsync_pipeline import face as facemod
from lipsync_pipeline.batch import read_jobs
from lipsync_pipeline.cli import main
from lipsync_pipeline.pipeline import STAGES, Job, State, run_job, select_stages
from lipsync_pipeline.presets import Preset, load_preset
from lipsync_pipeline.utils import PipelineError, Workspace, video_stream_info


@pytest.fixture()
def cpu_preset(tmp_path):
    d = tmp_path / "presets"; d.mkdir()
    (d / "cpu.yaml").write_text(
        "model: identity\ntakes: 2\nseparate_backend: passthrough\nface_size: 128\nmin_len_sec: 1\nmax_len_sec: 3\n"
        "restore: false\nupscale: false\ninterpolate: false\nemotion: true\n", encoding="utf-8")
    return d


@pytest.fixture(autouse=True)
def fake_face(monkeypatch):
    class Det:
        def __init__(self): self.i = -1
        def __call__(self, frame):
            self.i += 1
            return facemod.FaceDet((110, 60, 110, 110), (125, 135, 80, 30), yaw=0.0, pitch=0.0, roll=0.0, eye_closed=False)
    monkeypatch.setattr(facemod, "make_detector", lambda b, box=None: Det())
    monkeypatch.setattr(facemod, "mouth_occlusion_score", lambda *a: 0.0)


def test_shipped_presets_load_and_match_spec():
    fast, quality = load_preset("fast"), load_preset("quality")
    assert fast.paste_mode == "mouth" and quality.paste_mode == "face"
    assert quality.emotion is True and fast.emotion is False and quality.takes == 3
    for p in (fast, quality):                                   # 속도 최적화 금지: 스텝/정밀도는 프리셋이 낮추지 않는다
        assert p.steps is None and p.precision in ("fp16", "bf16", "fp32")
        assert p.restore and p.upscale and p.interpolate


def test_preset_unknown_key_and_missing(tmp_path):
    (tmp_path / "bad.yaml").write_text("modle: x\n", encoding="utf-8")
    with pytest.raises(PipelineError, match="알 수 없는 키"):
        load_preset("bad", [tmp_path])
    with pytest.raises(PipelineError, match="찾을 수 없습니다"):
        load_preset("없는프리셋")


def test_select_stages():
    assert select_stages() == STAGES
    assert select_stages(["lipsync", "emotion"]) == ["emotion", "lipsync"]
    assert select_stages(start="scan", until="segments") == ["scan", "emotion", "segments"]
    with pytest.raises(PipelineError, match="알 수 없는 단계"):
        select_stages(["nope"])


def test_run_job_state_resume_and_report(samples, work, cpu_preset, capsys):
    pr = load_preset("cpu", [cpu_preset])
    job = Job("잡 1", samples["video"], samples["audio"], "cpu")
    # 1) 앞 단계까지만 실행 (PC 에서 하는 부분)
    run_job(job, pr, work, until="segments")
    ws = Workspace.open("잡 1", work)
    st = json.loads(ws.p("state.json").read_text(encoding="utf-8"))["stages"]
    assert all(st[s]["status"] == "done" for s in ("prepare", "separate", "analyze", "scan", "emotion", "segments"))
    assert "lipsync" not in st
    # 2) 이어서 전체 실행 -> 끝난 단계는 건너뛴다
    capsys.readouterr()
    r = run_job(job, pr, work)
    assert r["ran"] == ["lipsync", "finalize"] and r["skipped"][:2] == ["prepare", "separate"]
    assert "이미 완료되어 건너뜁니다" in capsys.readouterr().err
    out = list(ws.p("finalize").glob("auto_*/final.mp4"))
    assert len(out) == 1 and video_stream_info(out[0])["frames"] == 200
    # 3) 다시 실행해도 아무것도 하지 않음
    assert run_job(job, pr, work)["ran"] == []
    # 4) report.csv: 단계별 시간 기록
    rows = list(csv.DictReader(open(ws.p("report.csv"), encoding="utf-8-sig")))
    assert {r["stage"] for r in rows} == set(STAGES) and all(float(r["seconds"]) >= 0 for r in rows)
    assert rows[0]["video_seconds"] or rows[1]["video_seconds"]
    # 5) --force 는 기존 결과를 지우지 않고 새 결과를 추가
    run_job(job, pr, work, stages=["lipsync", "finalize"], force=True)
    assert len(list(ws.p("finalize").glob("auto_*/final.mp4"))) == 2
    assert all(len(list(ws.p(s["dir"]).glob("take_*.mp4"))) == 4 for s in json.loads(ws.p("segments.json").read_text(encoding="utf-8"))["segments"])


def test_failure_is_recorded_and_resumable(samples, work, cpu_preset):
    pr = load_preset("cpu", [cpu_preset])
    pr.model = "latentsync"                                   # 설치 안 됨 -> lipsync 에서 실패
    job = Job("실패잡", samples["video"], samples["audio"], "cpu")
    with pytest.raises(PipelineError, match="LATENTSYNC_DIR"):
        run_job(job, pr, work)
    ws = Workspace.open("실패잡", work)
    st = json.loads(ws.p("state.json").read_text(encoding="utf-8"))["stages"]
    assert st["lipsync"]["status"] == "failed" and "LATENTSYNC_DIR" in st["lipsync"]["error"] and st["segments"]["status"] == "done"
    pr.model = "identity"                                     # 고친 뒤 이어서 -> 앞 단계는 재실행하지 않음
    r = run_job(job, pr, work)
    assert r["ran"] == ["lipsync", "finalize"]


def test_rerunning_upstream_marks_downstream_stale(samples, work, cpu_preset):
    pr = load_preset("cpu", [cpu_preset])
    job = Job("스테일", samples["video"], samples["audio"], "cpu")
    run_job(job, pr, work, until="analyze")
    run_job(job, pr, work, stages=["separate"], force=True)
    st = State(Workspace.open("스테일", work))
    assert st.get("separate")["status"] == "done" and st.get("analyze")["status"] == "stale"


def _write_csv(path, rows, enc="utf-8-sig"):
    with open(path, "w", newline="", encoding=enc) as f:
        w = csv.writer(f); w.writerow(["영상경로", "음원경로", "이름", "프리셋"]); w.writerows(rows)


def test_read_jobs_handles_relative_paths_cp949_and_bad_rows(samples, tmp_path):
    v, a = samples["video"], samples["audio"]
    _write_csv(tmp_path / "작업 목록.csv", [[str(v), str(a), "", "cpu"], [str(v), "", "x", ""], [str(v), str(a), "내이름", ""],
                                         [str(v), str(a), "내이름", ""]], enc="cp949")
    jobs = read_jobs(tmp_path / "작업 목록.csv")
    assert [j[1].name if j[1] else None for j in jobs] == ["내 영상 샘플", None, "내이름", None]
    assert jobs[0][1].preset == "cpu" and jobs[2][1].preset == "quality"
    assert "비어 있는" in jobs[1][2] and "중복" in jobs[3][2]
    (tmp_path / "bad.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(PipelineError, match="필요한 열"):
        read_jobs(tmp_path / "bad.csv")


def test_batch_continues_after_failure_and_reports(samples, work, cpu_preset, tmp_path, capsys):
    v, a = samples["video"], samples["audio"]
    csv_path = tmp_path / "jobs.csv"
    _write_csv(csv_path, [[str(v), str(a), "잡A", "cpu"], [str(tmp_path / "없는영상.mp4"), str(a), "잡B", "cpu"],
                          [str(v), str(a), "잡C", "cpu"]])
    w = ["--work-root", str(work), "--preset-dir", str(cpu_preset)]
    assert main(["batch", str(csv_path), *w]) == 1            # 실패가 있으면 종료 코드 1, 그래도 끝까지 진행
    err = capsys.readouterr().err
    assert "배치 결과: 성공 2 / 실패 1" in err and "잡B" in err
    for ok in ("잡A", "잡C"):
        assert list((work / ok / "finalize").glob("auto_*/final.mp4"))
    summary = next(work.glob("batch_summary_*.csv"))
    rows = {r["name"]: r for r in csv.DictReader(open(summary, encoding="utf-8-sig"))}
    assert rows["잡B"]["status"] == "failed" and rows["잡A"]["status"] == "done"
    # 다시 실행하면 성공한 작업은 건너뛰고 실패한 작업만 시도
    capsys.readouterr()
    assert main(["batch", str(csv_path), *w]) == 1
    assert capsys.readouterr().err.count("이미 완료되어 건너뜁니다") >= 8
