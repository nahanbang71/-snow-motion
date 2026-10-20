import csv
import json

import cv2
import numpy as np
import pytest

from lipsync_pipeline import cuts, emotion, face, scoring, segments
from lipsync_pipeline.models import (GenerationOptions, LipSyncRequest, available_models, get_lipsync_model,
                                     get_post_processor)
from lipsync_pipeline.utils import PipelineError


# ------------------------------------------------------------ cuts
def test_cut_detection_on_concat_video(samples, work):
    from lipsync_pipeline.prepare import prepare
    from lipsync_pipeline.utils import Workspace
    prepare(samples["video"], samples["audio"], work)
    ws = Workspace.open("내 영상 샘플", work)
    res = cuts.run_cuts(ws)
    assert res["cut_starts"] == [100]                      # testsrc 4초 | smptebars 4초
    assert res["cuts"] == [[0, 100], [100, 200]]


def test_cut_detection_ignores_fast_motion():
    rng = np.random.default_rng(0)
    d = np.abs(rng.normal(0.08, 0.02, 100)); d[0] = 0
    assert cuts.cuts_from_distances(d, 25) == []
    d[50] = 0.6
    assert cuts.cuts_from_distances(d, 25) == [50]


def _frames(n, detected=True, size=150, yaw=0.0, roll=0.0, pitch=0.0, occluded=False, eye_closed=False):
    return [{"detected": detected, "face": [100, 50, size, size], "yaw": yaw, "roll": roll, "pitch": pitch,
             "occluded": occluded, "eye_closed": eye_closed,
             "crop": [0, 0, 200], "mouth": [120, 130, 60, 30]} for _ in range(n)]


def test_eligibility_skips_missing_small_and_profile_faces():
    fps = 25
    frames = (_frames(50) + _frames(50, detected=False) + _frames(50, size=40) + _frames(50, yaw=70)
              + _frames(50, occluded=True) + _frames(50, pitch=60))
    ranges = [(i, i + 50) for i in range(0, 300, 50)]
    m = cuts.eligible_mask(frames, ranges, fps)
    assert m[:50].all() and not m[50:].any()
    assert cuts.eligible_mask(frames, ranges, fps, skip_occluded=False)[200:250].all()      # 해제 옵션


def test_eligibility_fills_short_gaps_and_drops_short_runs():
    fps = 25
    frames = _frames(100)
    for i in range(40, 44):
        frames[i] = {**frames[i], "detected": False}          # 0.16초 끊김 -> 메움
    for i in range(60, 100):
        frames[i] = {**frames[i], "detected": i == 70}         # 1프레임짜리 -> 버림
    m = cuts.eligible_mask(frames, [(0, 100)], fps)
    assert m[:60].all() and not m[60:].any()


def test_eligibility_does_not_cross_cuts():
    m = cuts.eligible_mask(_frames(100), [(0, 50), (50, 100)], 25)
    assert cuts.eligible_spans(m) == [(0, 50), (50, 100)] or cuts.eligible_spans(m) == [(0, 100)]
    # 서로 다른 컷의 연속 구간이 이어져도 span 이 컷에서 끊기도록: 컷 경계로 쪼갠 마스크 사용
    assert cuts.eligible_spans(np.array([True] * 50 + [False] + [True] * 49)) == [(0, 50), (51, 100)]


def test_report_warnings_and_csv(tmp_path):
    fps = 25
    frames = (_frames(50) + _frames(50, yaw=35, roll=25, eye_closed=True) + _frames(50, detected=False)
              + _frames(50, size=60) + _frames(50, occluded=True))
    ranges = [(0, 50), (50, 100), (100, 150), (150, 200), (200, 250)]
    mask = cuts.eligible_mask(frames, ranges, fps)
    rows = cuts.make_report(frames, ranges, fps, 320, 240, mask)
    assert rows[0]["decision"] == "apply" and rows[0]["warnings"] == ""
    assert rows[1]["decision"] == "apply_with_warning"
    assert "정면 아님" in rows[1]["warnings"] and "눈 감김" in rows[1]["warnings"] and "기울어짐" in rows[1]["warnings"]
    assert rows[4]["decision"] == "skip" and "입 가려짐" in rows[4]["warnings"] and rows[4]["mouth_occluded_ratio"] == 1.0
    assert rows[2]["decision"] == "skip" and "미검출" in rows[2]["warnings"]
    assert rows[3]["decision"] == "skip" and "너무 작음" in rows[3]["warnings"]
    p = tmp_path / "cuts_report.csv"
    cuts.write_report_csv(p, rows)
    got = list(csv.DictReader(open(p, encoding="utf-8-sig")))
    assert len(got) == 5 and got[2]["decision"] == "skip" and "pitch_deg_median" in got[0]


# ------------------------------------------------------------ face
def test_build_track_interpolates_and_smooths_within_cuts():
    W, H, fps = 320, 240, 25
    dets = [face.FaceDet((100, 60, 100, 100), (120, 130, 60, 30)) if i % 4 else None for i in range(100)]
    for i in range(50, 100):                                   # 두 번째 컷은 얼굴 위치가 완전히 다름
        dets[i] = None if i % 4 == 0 else face.FaceDet((20, 20, 80, 80), (35, 70, 50, 20))
    tr = face.build_track(dets, W, H, fps, ranges=[(0, 50), (50, 100)])
    f = tr["frames"]
    assert all(t["crop"][0] >= 0 and t["crop"][0] + t["crop"][2] <= W for t in f)
    assert f[48]["face"][0] == pytest.approx(100, abs=1) and f[52]["face"][0] == pytest.approx(20, abs=1)   # 컷 사이 번짐 없음
    assert f[0]["detected"] is False and f[1]["detected"] is True


def test_build_track_no_face_cut_is_not_error():
    tr = face.build_track([None] * 10, 320, 240, 25, ranges=[(0, 10)])
    assert tr["detected_ratio"] == 0 and not any(t["detected"] for t in tr["frames"])


def test_feather_mask_and_paste_and_color():
    m = face.feather_mask(128)
    assert m.shape == (128, 128, 1) and m[64, 64, 0] > 0.99 and m[0, 0, 0] < 0.01
    frame = np.full((200, 200, 3), 50, np.uint8)
    patch = np.full((128, 128, 3), 200, np.uint8)
    out = face.paste_back(frame, patch, 20, 20, 100, m)
    assert out[70, 70, 0] > 190 and out[5, 5, 0] == 50 and (frame == 50).all()      # 원본 불변
    dark, ref = np.full((64, 64, 3), 60, np.uint8), np.full((64, 64, 3), 150, np.uint8)
    matched = face.match_color(dark, ref)
    assert abs(int(matched.mean()) - int(ref.mean())) < 10
    mm = face.mouth_mask(128, (0.3, 0.6, 0.4, 0.2))
    assert mm[int(0.7 * 128), 64, 0] > 0.9 and mm[5, 5, 0] == 0


# ------------------------------------------------------------ emotion
def _pf(n=250, fps=25.0):
    beat = [1 if i % 12 == 0 else 0 for i in range(n)]
    return {"fps": fps, "n": n, "rms_db": [-20.0] * n, "f0": [220.0] * n, "voiced": [1] * n, "beat": beat}


def test_emotion_nods_follow_beats_and_are_bounded():
    pf = _pf()
    p = emotion.generate_params(pf)
    dy = np.array(p["dy"])
    assert len(dy) == 250 and np.abs(dy).max() < 0.05 and np.abs(p["rot"]).max() < 5
    beats = [i for i, b in enumerate(pf["beat"]) if b]
    peaks = [i for i in range(2, 248) if dy[i] > dy[i - 1] and dy[i] >= dy[i + 1] and dy[i] > 0.5 * dy.max()]
    assert all(min(abs(pk - b) for b in beats) <= 4 for pk in peaks)
    assert emotion.generate_params(pf) == p                    # 같은 seed -> 같은 결과
    assert emotion.generate_params(pf, emotion.EmotionConfig(seed=3)) != p


def test_emotion_silence_is_calm():
    pf = _pf(); pf["voiced"] = [0] * 250; pf["f0"] = [0.0] * 250; pf["beat"] = [0] * 250
    assert np.abs(emotion.generate_params(pf)["dy"]).max() < 0.005


def test_apply_motion_identity_and_shift():
    img = (np.random.default_rng(1).random((64, 64, 3)) * 255).astype(np.uint8)
    assert emotion.apply_motion(img, 0, 0, 0, 0) is img
    shifted = emotion.apply_motion(img, 0.1, 0, 0, 0)
    assert shifted.shape == img.shape and not np.array_equal(shifted, img)


# ------------------------------------------------------------ segments
def _analysis(duration_s, silences, fps=25):
    segs, cur = [], 0.0
    for a, b in silences:
        segs += [{"start": cur, "end": a, "type": "voiced"}, {"start": a, "end": b, "type": "silence"}]
        cur = b
    segs.append({"start": cur, "end": duration_s, "type": "voiced"})
    n = int(duration_s * fps)
    rms = [-60.0 if any(a * fps <= i < b * fps for a, b in silences) else -20.0 for i in range(n)]
    return {"segments": segs, "per_frame": {"rms_db": rms}}


def test_plan_segments_overlap_and_boundaries_in_silence():
    fps = 25
    an = _analysis(30, [(8, 9), (17, 18.5)])
    segs = segments.plan_segments([(0, 750)], an, fps, overlap_s=0.5, min_len_s=2, max_len_s=13)
    cores = [s["core"] for s in segs]
    assert len(cores) == 3 and cores[0][0] == 0 and cores[-1][1] == 750
    assert abs(cores[0][1] - 212) <= 1 and abs(cores[1][1] - 444) <= 1       # 무음(8~9초, 17~18.5초) 중앙
    a, b = segs[0], segs[1]
    assert a["range"][1] - b["range"][0] == 2 * round(0.5 * fps / 2)               # 0.5초(=12~13프레임) 겹침
    assert segs[0]["range"][0] == 0 and segs[-1]["range"][1] == 750               # span 바깥으로 확장 안 함
    for s in segs[:-1]:
        c = s["core"][1]; assert an["per_frame"]["rms_db"][c] == -60.0              # 경계는 무음 한가운데


def test_long_phrase_is_split_and_short_ones_merged():
    fps = 25
    an = _analysis(40, [(5, 5.5), (6, 6.5)])       # 짧은 조각이 생기는 무음
    segs = segments.plan_segments([(0, 1000)], an, fps, min_len_s=3, max_len_s=12)
    lens = [(s["core"][1] - s["core"][0]) / fps for s in segs]
    assert all(l <= 12.5 for l in lens) and all(l >= 2.5 for l in lens)


def test_segments_do_not_cross_span_edges():
    an = _analysis(20, [(8, 9)])
    segs = segments.plan_segments([(0, 200), (300, 500)], an, 25)
    assert all(s["range"][1] <= 200 or s["range"][0] >= 300 for s in segs)


def test_crossfade_weights_sum_to_one():
    plan = segments.plan_segments([(0, 750)], _analysis(30, [(8, 9), (17, 18.5)]), 25)
    half = round(0.5 * 25 / 2)
    for i in range(750):
        tot = sum(segments.segment_weights(s, i, half) for s in plan if s["range"][0] <= i < s["range"][1])
        assert tot == pytest.approx(1.0)


# ------------------------------------------------------------ models / adapters
def test_registry_and_defaults_are_max_quality():
    m = available_models()
    assert {"identity", "latentsync", "musetalk", "infinitetalk", "wan_s2v"} <= set(m["lipsync"]) and "codeformer" in m["restore"]
    ls = get_lipsync_model("latentsync")
    o = ls.resolve(GenerationOptions())
    assert o.steps == ls.MAX_STEPS == 50 and o.precision == "fp16" and o.offload == "none"
    with pytest.raises(PipelineError, match="알 수 없는"):
        get_lipsync_model("없는모델")
    with pytest.raises(PipelineError):
        GenerationOptions(offload="weird").validate()


def test_new_adapter_needs_only_one_class():
    from lipsync_pipeline.models.base import BaseLipSyncModel, register

    @register("dummy_test_model")
    class Dummy(BaseLipSyncModel):
        def generate(self, req):
            return req.output
    assert "dummy_test_model" in available_models()["lipsync"]


def test_adapter_commands_handle_spaces_and_korean(tmp_path):
    req = LipSyncRequest(tmp_path / "내 입력.mp4", tmp_path / "음원 a.wav", tmp_path / "out 1.mp4", 25.0,
                         get_lipsync_model("latentsync").resolve(GenerationOptions(seed=7)))
    cmd = get_lipsync_model("latentsync").build_command(req, tmp_path)
    assert str(tmp_path / "내 입력.mp4") in cmd and "50" in cmd and "7" in cmd
    mt = get_lipsync_model("musetalk")
    yml = mt.build_config(req)
    assert json.dumps(str(tmp_path / "내 입력.mp4"), ensure_ascii=False) in yml


def test_gpu_adapters_fail_with_korean_message_when_not_installed(tmp_path, monkeypatch):
    for env in ("LATENTSYNC_DIR", "MUSETALK_DIR", "CODEFORMER_DIR", "REALESRGAN_DIR", "RIFE_DIR", "INFINITETALK_DIR", "WAN22_DIR"):
        monkeypatch.delenv(env, raising=False)
    with pytest.raises(PipelineError, match="LATENTSYNC_DIR"):
        get_lipsync_model("latentsync").check_environment(GenerationOptions())
    for kind, name, env in (("restore", "codeformer", "CODEFORMER_DIR"), ("upscale", "realesrgan", "REALESRGAN_DIR"),
                            ("interpolate", "rife", "RIFE_DIR")):
        with pytest.raises(PipelineError, match=env):
            get_post_processor(kind, name).process(tmp_path / "a.mp4", tmp_path / "b.mp4", {})


# ------------------------------------------------------------ scoring
def test_sync_proxy_detects_audio_motion_correlation(tmp_path):
    from lipsync_pipeline.utils import write_wav
    fps, n = 25, 100
    rng = np.random.default_rng(0)
    env = np.abs(np.sin(np.arange(n) / 4.0)) + 0.05
    sr = 16000
    audio = np.concatenate([rng.standard_normal(sr // fps) * e * 0.2 for e in env]).astype(np.float32)
    write_wav(tmp_path / "a.wav", sr, audio)
    good = np.zeros((n, 64, 64), np.float32)
    good[:, 40:56, 20:44] = np.cumsum(env * 20)[:, None, None]    # 입 영역 밝기 변화 ~ 오디오 에너지
    flat = np.zeros((n, 64, 64), np.float32)
    flat[:, 40:56, 20:44] = rng.random((n, 1, 1)) * 255
    g = scoring.sync_proxy(good, tmp_path / "a.wav", fps)
    r = scoring.sync_proxy(flat, tmp_path / "a.wav", fps)
    assert g["corr"] > r["corr"] and g["corr"] > 0.5


def test_flicker_scores_noise_lower_than_clean():
    rng = np.random.default_rng(0)
    ref = np.tile(rng.random((1, 64, 64)) * 255, (20, 1, 1)).astype(np.float32)
    clean = ref.copy()
    noisy = ref + rng.normal(0, 12, ref.shape).astype(np.float32)
    assert scoring.flicker(clean, ref)["stable_pct"] > 99
    assert scoring.flicker(noisy, ref)["stable_pct"] < scoring.flicker(clean, ref)["stable_pct"] - 20


def test_face_generation_adapters_declare_mode_and_check_env(monkeypatch):
    monkeypatch.delenv("INFINITETALK_DIR", raising=False); monkeypatch.delenv("WAN22_DIR", raising=False)
    for name, env in (("infinitetalk", "INFINITETALK_DIR"), ("wan_s2v", "WAN22_DIR")):
        m = get_lipsync_model(name)
        assert m.MODE == "face_generation"
        with pytest.raises(PipelineError, match=env):
            m.check_environment(GenerationOptions())
    assert get_lipsync_model("musetalk").MODE == "inpaint_mouth"


# ------------------------------------------------------------ 입 가림 / 워터마크
def _skin_frame():
    img = np.full((240, 320, 3), (140, 170, 215), np.uint8)             # BGR 피부색
    cv2.ellipse(img, (160, 170), (28, 10), 0, 0, 360, (90, 90, 190), -1)   # 입술
    return img


def test_mouth_occlusion_score_distinguishes_covered_mouth():
    face_box, mouth = (100.0, 60.0, 120.0, 140.0), (130.0, 150.0, 60.0, 25.0)
    clean = _skin_frame()
    covered = clean.copy()
    cv2.rectangle(covered, (110, 135), (210, 205), (20, 20, 20), -1)      # 검은 마이크/머리카락
    hair = clean.copy()
    cv2.rectangle(hair, (100, 150), (135, 205), (30, 40, 60), -1)         # 볼 아래~입 옆을 덮은 머리카락
    s_clean = face.mouth_occlusion_score(clean, mouth, face_box)
    assert s_clean < 0.1
    assert face.mouth_occlusion_score(covered, mouth, face_box) > face.OCCLUSION_THR
    assert face.mouth_occlusion_score(hair, mouth, face_box) > s_clean + 0.1
    open_mouth = clean.copy()
    cv2.ellipse(open_mouth, (160, 170), (20, 14), 0, 0, 360, (10, 10, 40), -1)   # 입을 크게 벌려도 오탐 없음
    assert face.mouth_occlusion_score(open_mouth, mouth, face_box) < 0.1


def test_mouth_metal_ratio_flags_gray_mic_but_not_open_mouth():
    mouth = (130.0, 150.0, 60.0, 25.0)
    clean = _skin_frame()
    mic = clean.copy()
    cv2.rectangle(mic, (120, 140), (200, 200), (95, 95, 95), -1)             # 회색 마이크(무채색)
    open_mouth = clean.copy()
    cv2.ellipse(open_mouth, (160, 170), (20, 14), 0, 0, 360, (20, 20, 90), -1)   # 붉은 입 안
    assert face.mouth_metal_ratio(clean, mouth) < face.METAL_OCC_THR
    assert face.mouth_metal_ratio(open_mouth, mouth) < face.METAL_OCC_THR
    assert face.mouth_metal_ratio(mic, mouth) > face.METAL_OCC_THR


def _moving_frames(n=30, overlay=True):
    rng = np.random.default_rng(0)
    out = []
    for i in range(n):
        f = (rng.random((120, 160, 3)) * 255).astype(np.uint8)
        f = cv2.GaussianBlur(f, (9, 9), 0)
        f = np.roll(f, i * 3, axis=1)
        if overlay:
            cv2.putText(f, "WM", (110, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.rectangle(f, (108, 85), (155, 112), (255, 255, 255), 1)
        out.append(f)
    return out


def test_watermark_overlay_warning_only():
    from lipsync_pipeline import watermark as wm
    found = wm.detect_static_overlays(_moving_frames())
    assert found and found[0]["box"][0] >= 100 and found[0]["box"][1] >= 75
    assert wm.detect_static_overlays(_moving_frames(overlay=False)) == []
    msgs = wm.watermark_warnings(found, [[90, 60, 30, 30]])
    assert any("얼굴 근처" in m for m in msgs)
    assert not any("얼굴 근처" in m for m in wm.watermark_warnings(found, [[0, 0, 20, 20]]))
    assert not hasattr(wm, "remove_watermark")        # 제거 기능은 만들지 않는다


def test_workspace_root_is_absolute(tmp_path, monkeypatch):
    """외부 모델은 자기 저장소를 cwd 로 실행되므로, 작업 폴더가 상대경로로 남으면 입력 파일을 못 찾는다."""
    from lipsync_pipeline.utils import Workspace
    monkeypatch.chdir(tmp_path)
    ws = Workspace.open("abs_test", "work", must_exist=False)
    assert ws.root.is_absolute()
    assert ws.p("segments/001/input.mp4").is_absolute()
