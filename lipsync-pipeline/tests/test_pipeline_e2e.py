"""합성 샘플(testsrc+smptebars / sine) 로 전체 CLI 흐름을 CPU 에서 검증. 모델은 identity 어댑터."""
import csv
import http.client
import json
import threading
import zipfile

import pytest

from lipsync_pipeline import face as facemod
from lipsync_pipeline import review
from lipsync_pipeline.bundle import pack, unpack
from lipsync_pipeline.cli import main
from lipsync_pipeline.generate import existing_takes
from lipsync_pipeline.models import GenerationOptions
from lipsync_pipeline.utils import PipelineError, Workspace, video_stream_info

NAME = "내 영상 샘플"


class HalfFaceDetector:
    """앞 100프레임(첫 번째 컷)에서만 얼굴이 있는 것처럼 동작하는 가짜 검출기."""

    def __init__(self):
        self.i = -1

    def __call__(self, frame):
        self.i += 1
        if self.i < 100:
            return facemod.FaceDet((110, 60, 110, 110), (125, 135, 80, 30), yaw=0.0, roll=0.0)
        return None


@pytest.fixture()
def prepared(samples, work, monkeypatch):
    monkeypatch.setattr(facemod, "make_detector", lambda backend, box=None: HalfFaceDetector())
    monkeypatch.setattr(facemod, "mouth_occlusion_score", lambda *a: 0.0)      # 합성 영상엔 피부색이 없으므로 가림 판정은 별도 테스트
    w = ["--work-root", str(work)]
    assert main(["prepare", str(samples["video"]), str(samples["audio"]), *w]) == 0
    assert main(["separate", NAME, "--backend", "passthrough", *w]) == 0
    assert main(["analyze", NAME, *w]) == 0
    assert main(["scan", NAME, "--size", "128", *w]) == 0
    return Workspace.open(NAME, work), w


def test_cuts_report_and_skip_policy(prepared):
    ws, _ = prepared
    rows = list(csv.DictReader(open(ws.p("cuts_report.csv"), encoding="utf-8-sig")))
    assert [r["decision"] for r in rows] == ["apply", "skip"]
    assert "미검출" in rows[1]["warnings"] and float(rows[1]["lipsync_ratio"]) == 0
    track = json.loads(ws.face_track.read_text(encoding="utf-8"))
    assert sum(f["eligible"] for f in track["frames"]) == 100 and track["cuts"] == [[0, 100], [100, 200]]


def test_full_flow_keeps_resolution_fps_duration(prepared):
    ws, w = prepared
    assert main(["segments", NAME, "--min-len-sec", "1", "--max-len-sec", "3", *w]) == 0
    plan = json.loads(ws.p("segments.json").read_text(encoding="utf-8"))
    assert plan["segments"] and all(s["range"][1] <= 100 for s in plan["segments"])     # 얼굴 없는 컷에는 구간 없음
    assert main(["lipsync", NAME, "--model", "identity", "--takes", "2", *w]) == 0
    n = len(plan["segments"])
    for sg in plan["segments"]:
        assert existing_takes(ws.p(sg["dir"])) == [1, 2]
        meta = json.loads(ws.p(sg["dir"], ).joinpath("take_2.json").read_text(encoding="utf-8"))
        assert meta["seed"] != json.loads(ws.p(sg["dir"]).joinpath("take_1.json").read_text(encoding="utf-8"))["seed"]
        assert meta["scores"] and "stable_pct" in meta["scores"] and "sync_proxy" in meta["scores"]
    # 재생성: 기존 후보를 덮어쓰지 않고 번호가 이어진다
    before = ws.p(plan["segments"][0]["dir"], ).joinpath("take_1.mp4").read_bytes()
    assert main(["lipsync", NAME, "--model", "identity", "--takes", "1", "--segments", "1", *w]) == 0
    d1 = ws.p(plan["segments"][0]["dir"])
    assert existing_takes(d1) == [1, 2, 3] and (d1 / "take_1.mp4").read_bytes() == before

    # 선택 안 한 상태에서는 finalize 가 한국어 오류로 멈춘다
    assert main(["finalize", NAME, "--no-restore", "--no-upscale", "--no-interpolate", *w]) == 1
    for sg in plan["segments"]:
        assert main(["select", NAME, "--segment", str(sg["index"]), "--take", "2", *w]) == 0
    assert main(["compare", NAME, "--segment", "1", "--takes", "1,2", *w]) == 0
    assert list(ws.p("compare").glob("cmp_seg001_*.mp4"))

    assert main(["emotion", NAME, *w]) == 0
    assert main(["finalize", NAME, "--tag", "a", "--no-restore", "--no-upscale", "--no-interpolate", "--emotion", *w]) == 0
    assert main(["finalize", NAME, "--tag", "b", "--no-restore", "--no-upscale", "--no-interpolate", "--paste-mode", "mouth", *w]) == 0
    assert main(["finalize", NAME, "--tag", "a", "--no-restore", "--no-upscale", "--no-interpolate", *w]) == 1      # 덮어쓰기 금지
    src, out = video_stream_info(ws.video_noaudio), video_stream_info(ws.p("finalize/a/final.mp4"))
    assert (out["width"], out["height"], out["frames"]) == (320, 240, 200)
    assert abs(out["fps"] - src["fps"]) < 0.01 and abs(out["duration"] - src["duration"]) < 0.05
    run = json.loads(ws.p("finalize/a/render.json").read_text(encoding="utf-8"))
    assert run["lipsync_applied"] and run["verification"]["matches_expectation"]
    assert ws.p("finalize/a/01_assembled_crop.mp4").exists() and ws.p("finalize/b/03_composited.mp4").exists()
    assert len(list(ws.p("selection_history").glob("*.json"))) >= 1


def test_finalize_defaults_turn_everything_on_and_report_missing_tools(prepared, monkeypatch):
    ws, w = prepared
    for e in ("CODEFORMER_DIR", "REALESRGAN_DIR", "RIFE_DIR"):
        monkeypatch.delenv(e, raising=False)
    from lipsync_pipeline.cli import build_parser
    a = build_parser().parse_args(["finalize", NAME])
    assert a.restore is True and a.upscale is True and a.interpolate is True
    assert main(["segments", NAME, "--min-len-sec", "1", "--max-len-sec", "3", *w]) == 0
    assert main(["lipsync", NAME, "--model", "identity", "--takes", "1", *w]) == 0
    assert main(["finalize", NAME, "--fill-missing", "first", *w]) == 1        # CodeFormer 미설치 -> 한국어 오류


def test_no_face_anywhere_returns_original(samples, work, monkeypatch, capsys):
    monkeypatch.setattr(facemod, "make_detector", lambda b, box=None: (lambda f: None))
    w = ["--work-root", str(work)]
    for cmd in (["prepare", str(samples["video"]), str(samples["audio"])], ["separate", NAME, "--backend", "passthrough"],
                ["analyze", NAME], ["scan", NAME, "--size", "128"]):
        assert main([*cmd, *w]) == 0
    assert main(["finalize", NAME, "--tag", "orig", "--no-restore", "--no-upscale", "--no-interpolate", *w]) == 0                
    ws = Workspace.open(NAME, work)
    out = video_stream_info(ws.p("finalize/orig/final.mp4"))
    assert (out["width"], out["height"], out["frames"]) == (320, 240, 200)


def test_segments_refuse_replan_without_flag(prepared):
    ws, w = prepared
    assert main(["segments", NAME, "--min-len-sec", "1", "--max-len-sec", "3", *w]) == 0
    assert main(["segments", NAME, *w]) == 1
    assert main(["segments", NAME, "--replan", "--min-len-sec", "1", "--max-len-sec", "3", *w]) == 0
    assert any(ws.p("_archive").iterdir())


def test_pack_unpack_roundtrip_without_overwrite(prepared, tmp_path):
    ws, w = prepared
    assert main(["segments", NAME, "--min-len-sec", "1", "--max-len-sec", "3", *w]) == 0
    up = pack(ws, "upload")
    names = zipfile.ZipFile(up).namelist()
    assert "segments.json" in names and any(n.endswith("input.mp4") for n in names) and not any(n.endswith(".wav") and "/" not in n for n in names)
    assert main(["lipsync", NAME, "--model", "identity", "--takes", "2", "--no-score", *w]) == 0
    res = pack(ws, "result")
    assert not any("input.mp4" in n for n in zipfile.ZipFile(res).namelist())
    # 같은 결과를 다시 풀면 번호가 겹치므로 새 번호로 보존된다
    plan = json.loads(ws.p("segments.json").read_text(encoding="utf-8"))
    d = ws.p(plan["segments"][0]["dir"])
    unpack(ws, res)
    assert existing_takes(d) == [1, 2, 3, 4]
    assert json.loads((d / "take_3.json").read_text(encoding="utf-8"))["take"] == 3
    # 악의적 경로는 무시
    evil = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil, "w") as z:
        z.writestr("../evil.txt", "x"); z.writestr("segments/001/../../x.txt", "x")
    unpack(ws, evil)
    assert not (ws.root.parent / "evil.txt").exists() and not (ws.root / "x.txt").exists()


def test_review_server_select_regenerate_and_security(prepared):
    ws, w = prepared
    assert main(["segments", NAME, "--min-len-sec", "1", "--max-len-sec", "3", *w]) == 0
    assert main(["lipsync", NAME, "--model", "identity", "--takes", "2", *w]) == 0
    st = review.ReviewState(ws, "identity", GenerationOptions())
    from http.server import ThreadingHTTPServer
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), review.make_handler(st))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]

    def req(method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        c.request(method, path, json.dumps(body) if body is not None else None, headers or {})
        r = c.getresponse(); data = r.read(); c.close()
        return r.status, data, dict(r.getheaders())
    try:
        s, data, _ = req("GET", "/")
        assert s == 200 and st.token.encode() in data and "립싱크 후보 선택".encode() in data
        state = json.loads(req("GET", "/api/state")[1])
        assert state["segments"][0]["takes"][0]["scores"]["stable_pct"] > 0
        assert req("POST", "/api/select", {"segment": 1, "take": 2})[0] == 403          # 토큰 없음
        h = {"X-Token": st.token, "Content-Type": "application/json"}
        assert req("POST", "/api/select", {"segment": 1, "take": 2}, h)[0] == 200
        assert json.loads(ws.p("selection.json").read_text(encoding="utf-8"))["segments"]["1"] == 2
        assert req("POST", "/api/select", {"segment": 1, "take": 99}, h)[0] == 400
        s, data, hd = req("GET", "/file/segments/001/take_1.mp4", headers={"Range": "bytes=0-99"})
        assert s == 206 and len(data) == 100 and hd["Content-Range"].startswith("bytes 0-99/")
        assert req("GET", "/file/info.json")[0] == 404 and req("GET", "/file/../../etc/passwd")[0] == 404
        assert req("POST", "/api/regenerate", {"segment": 1, "takes": 1, "model": "identity"}, h)[0] == 200
        import time
        for _ in range(100):
            if not json.loads(req("GET", "/api/status")[1])["running"]:
                break
            time.sleep(0.2)
        assert existing_takes(ws.p("segments/001"))[-1] == 3
    finally:
        httpd.shutdown(); httpd.server_close()
