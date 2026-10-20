"""4단계 face: 프레임별 얼굴/입 bbox 추출 + 크롭/합성 유틸(색 보정, 페더링 마스크).

검출 백엔드: mediapipe(권장, 입 랜드마크) | haar(OpenCV 내장, 입은 비율로 추정) | fixed(수동 bbox).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d

from .utils import (FrameWriter, PipelineError, Workspace, archive_existing, iter_frames, log,
                    read_json, video_stream_info, write_json)

Box = tuple[float, float, float, float]   # x, y, w, h


@dataclass
class FaceDet:
    box: Box
    mouth: Box
    score: float = 1.0
    yaw: Optional[float] = None       # 좌우 회전(도). 랜드마크 기반 근사치, haar 는 None
    pitch: Optional[float] = None     # 상하 각도(도) 근사치
    roll: Optional[float] = None      # 고개 기울임(도)
    eye_closed: Optional[bool] = None  # 눈 감김 (EAR 기반, mediapipe 만)
    occluded: bool = False            # 입이 마이크/손/머리카락 등에 가려졌는지
    occlusion_score: float = 0.0
    hand_overlap: bool = False


def mouth_occlusion_score(frame: np.ndarray, mouth: Box, face: Box) -> float:
    """입 주변 링(입 바로 바깥 피부 영역)에서 '피부색이 아닌' 픽셀 비율 (0~1).

    피부색 기준은 같은 얼굴의 양 볼 영역에서 스스로 보정한다(피부톤/조명에 적응).
    입 안쪽/입술은 일부러 제외하므로 입을 크게 벌려도 점수가 오르지 않는다.
    한계: 손은 피부색이라 이 지표로는 못 잡는다(mediapipe 손 검출 사용 시 hand_overlap 으로 보완, TODO 미검증).
    머리카락·마이크·마스크처럼 색이 다른 가림 위주로 탐지한다."""
    H, W = frame.shape[:2]
    fx, fy, fw, fh = face
    def roi(x0, y0, x1, y1):
        xa, ya, xb, yb = int(max(x0, 0)), int(max(y0, 0)), int(min(x1, W)), int(min(y1, H))
        return (xa, ya, xb, yb) if xb - xa > 2 and yb - ya > 2 else None
    ycc = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb).astype(np.float32)
    cheeks = [roi(fx + .12 * fw, fy + .45 * fh, fx + .32 * fw, fy + .62 * fh),
              roi(fx + .68 * fw, fy + .45 * fh, fx + .88 * fw, fy + .62 * fh)]
    samples = [ycc[b[1]:b[3], b[0]:b[2]].reshape(-1, 3) for b in cheeks if b]
    if not samples:
        return 0.0
    ref = np.median(np.concatenate(samples), axis=0)
    mx, my, mw, mh = mouth
    cx, cy = mx + mw / 2, my + mh / 2
    outer = roi(cx - 0.95 * mw, cy - 1.6 * mh, cx + 0.95 * mw, cy + 1.6 * mh)
    if outer is None:
        return 0.0
    ring = np.ones((outer[3] - outer[1], outer[2] - outer[0]), bool)
    ix0, iy0 = int(cx - 0.6 * mw) - outer[0], int(cy - 0.9 * mh) - outer[1]        # 입 본체(입술/입 안) 제외
    ix1, iy1 = int(cx + 0.6 * mw) - outer[0], int(cy + 0.9 * mh) - outer[1]
    ring[max(iy0, 0):max(iy1, 0), max(ix0, 0):max(ix1, 0)] = False
    px = ycc[outer[1]:outer[3], outer[0]:outer[2]]
    skin = (np.abs(px[..., 1] - ref[1]) < 16) & (np.abs(px[..., 2] - ref[2]) < 16) & (np.abs(px[..., 0] - ref[0]) < 70)
    return float((~skin)[ring].mean()) if ring.any() else 0.0


# ---------------------------------------------------------------- 검출기

def mouth_from_face(box: Box) -> Box:
    x, y, w, h = box
    return (x + 0.22 * w, y + 0.62 * h, 0.56 * w, 0.33 * h)


class HaarDetector:
    def __init__(self):
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.cascade = cv2.CascadeClassifier(path)
        if self.cascade.empty():
            raise PipelineError("OpenCV Haar 모델을 불러오지 못했습니다.")

    def __call__(self, frame: np.ndarray) -> Optional[FaceDet]:
        gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        faces = self.cascade.detectMultiScale(gray, 1.1, 5, minSize=(48, 48))
        if len(faces) == 0:
            return None
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        box = (float(x), float(y), float(w), float(h))
        return FaceDet(box, mouth_from_face(box))


class MediaPipeDetector:
    """TODO(검증 필요): mediapipe FaceMesh 로 얼굴 전체/입술 랜드마크 bbox 를 구한다."""

    def __init__(self):
        try:
            import mediapipe as mp
        except ImportError as e:
            raise PipelineError("mediapipe 가 설치되어 있지 않습니다. `pip install mediapipe` 또는 --backend haar 를 사용하세요.") from e
        self._mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True)
        self._lips = sorted({i for pair in mp.solutions.face_mesh.FACEMESH_LIPS for i in pair})
        try:
            self._hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=2)
        except Exception:
            self._hands = None

    def __call__(self, frame: np.ndarray) -> Optional[FaceDet]:
        h, w = frame.shape[:2]
        res = self._mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if not res.multi_face_landmarks:
            return None
        pts = np.array([(p.x * w, p.y * h) for p in res.multi_face_landmarks[0].landmark])
        def bb(a):
            x0, y0 = a.min(0); x1, y1 = a.max(0)
            return (float(x0), float(y0), float(x1 - x0), float(y1 - y0))
        face, mouth = bb(pts), bb(pts[self._lips])
        # TODO(검증 필요): 랜드마크 번호는 FaceMesh 표준(코끝 1, 얼굴 양끝 234/454, 눈 바깥쪽 33/263 ...)
        half = max((pts[454][0] - pts[234][0]) / 2, 1e-6)
        r = float(np.clip((pts[1][0] - (pts[234][0] + pts[454][0]) / 2) / half, -1, 1))
        yaw = float(np.degrees(np.arcsin(r)))
        roll = float(np.degrees(np.arctan2(pts[263][1] - pts[33][1], pts[263][0] - pts[33][0])))
        eye_y = (pts[33][1] + pts[263][1]) / 2
        span = max(pts[14][1] - eye_y, 1e-6)                        # 눈 중심 ~ 입 중심 거리
        pitch = float((((pts[1][1] - eye_y) / span) - 0.55) * 120.0)  # 정면일 때 코끝 비율 ~0.55 가정 (근사)
        def ear(i):
            p = pts[i]
            return (np.linalg.norm(p[1] - p[5]) + np.linalg.norm(p[2] - p[4])) / (2 * np.linalg.norm(p[0] - p[3]) + 1e-6)
        eye_closed = bool(min(ear([33, 160, 158, 133, 153, 144]), ear([362, 385, 387, 263, 373, 380])) < 0.15)
        return FaceDet(face, mouth, 1.0, yaw, pitch, roll, eye_closed, hand_overlap=self._hand_over(frame, mouth))

    def _hand_over(self, frame, mouth) -> bool:
        """TODO(미검증): mediapipe Hands 로 손이 입 bbox 와 겹치는지."""
        if self._hands is None:
            return False
        h, w = frame.shape[:2]
        res = self._hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        for hand in (res.multi_hand_landmarks or []):
            xs = [p.x * w for p in hand.landmark]; ys = [p.y * h for p in hand.landmark]
            hx0, hy0, hx1, hy1 = min(xs), min(ys), max(xs), max(ys)
            if hx0 < mouth[0] + mouth[2] and hx1 > mouth[0] and hy0 < mouth[1] + mouth[3] and hy1 > mouth[1]:
                return True
        return False


class FixedDetector:
    def __init__(self, box: Box):
        self.det = FaceDet(tuple(map(float, box)), mouth_from_face(tuple(map(float, box))))

    def __call__(self, frame):
        return self.det


def make_detector(backend: str, fixed_box: Optional[Box] = None) -> Callable:
    if backend == "auto":
        try:
            return MediaPipeDetector()
        except PipelineError:
            log("[face] mediapipe 가 없어 OpenCV Haar 로 대체합니다 (입 위치는 추정값).")
            return HaarDetector()
    if backend == "mediapipe":
        return MediaPipeDetector()
    if backend == "haar":
        return HaarDetector()
    if backend == "fixed":
        if fixed_box is None:
            raise PipelineError("--backend fixed 에는 --box x,y,w,h 가 필요합니다.")
        return FixedDetector(fixed_box)
    raise PipelineError(f"알 수 없는 얼굴 검출 backend: {backend}")


# ---------------------------------------------------------------- 트랙 생성 (보간/스무딩/크롭 박스)

def _fill(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    idx = np.arange(len(values))
    return np.stack([np.interp(idx, idx[valid], values[valid, c]) for c in range(values.shape[1])], axis=1)


def _smooth_range(face: np.ndarray, mouth: np.ndarray, valid: np.ndarray, sigma: float):
    face, mouth = _fill(face, valid), _fill(mouth, valid)
    return gaussian_filter1d(face, sigma, axis=0, mode="nearest"), gaussian_filter1d(mouth, sigma, axis=0, mode="nearest")


def build_track(dets: Sequence[Optional[FaceDet]], frame_w: int, frame_h: int, fps: float,
                crop_scale: float = 1.6, smooth_sec: float = 0.25, out_size: int = 512,
                ranges: Optional[Sequence[tuple[int, int]]] = None) -> dict:
    """프레임별 검출(없으면 None) -> 보간 + 스무딩된 정사각 크롭 박스와 입 bbox.

    보간/스무딩은 컷(ranges) 안에서만 한다 (장면 전환을 넘어 번지지 않도록).
    얼굴이 전혀 없는 컷은 detected=False, 크롭은 화면 중앙 정사각형(사용되지 않음)."""
    n = len(dets)
    ranges = list(ranges) if ranges else [(0, n)]
    face = np.zeros((n, 4)); mouth = np.zeros((n, 4)); has = np.zeros(n, bool)
    sigma = max(smooth_sec * fps / 2.0, 0.01)
    for s, e in ranges:
        valid = np.array([dets[i] is not None for i in range(s, e)])
        if not valid.any():
            continue
        f = np.zeros((e - s, 4)); m = np.zeros((e - s, 4))
        for k, i in enumerate(range(s, e)):
            if dets[i] is not None:
                f[k], m[k] = dets[i].box, dets[i].mouth
        face[s:e], mouth[s:e] = _smooth_range(f, m, valid, sigma)
        has[s:e] = True
    side_max = min(frame_w, frame_h)
    sides = np.clip(np.round(np.maximum(face[:, 2], face[:, 3]) * crop_scale), 16, side_max).astype(int)
    sides[~has] = side_max
    cx, cy = face[:, 0] + face[:, 2] / 2, face[:, 1] + face[:, 3] / 2
    cx[~has], cy[~has] = frame_w / 2, frame_h / 2
    x0 = np.clip(np.round(cx - sides / 2), 0, frame_w - sides).astype(int)
    y0 = np.clip(np.round(cy - sides / 2), 0, frame_h - sides).astype(int)
    frames = []
    for i in range(n):
        d = dets[i]
        frames.append({"crop": [int(x0[i]), int(y0[i]), int(sides[i])],
                       "face": [round(float(v), 1) for v in face[i]], "mouth": [round(float(v), 1) for v in mouth[i]],
                       "detected": d is not None,
                       "yaw": None if d is None or d.yaw is None else round(d.yaw, 1),
                       "pitch": None if d is None or d.pitch is None else round(d.pitch, 1),
                       "roll": None if d is None or d.roll is None else round(d.roll, 1),
                       "eye_closed": None if d is None else d.eye_closed,
                       "occluded": False if d is None else bool(d.occluded),
                       "occlusion_score": 0.0 if d is None else round(d.occlusion_score, 3)})
    detected = sum(1 for d in dets if d is not None)
    return {"frame_width": frame_w, "frame_height": frame_h, "fps": fps, "out_size": out_size,
            "crop_scale": crop_scale, "n_frames": n, "detected_ratio": round(detected / max(n, 1), 4),
            "frames": frames}


OCCLUSION_THR = 0.45


def detect_video(ws: Workspace, backend: str = "auto", fixed_box: Optional[Box] = None, stride: int = 1,
                 sample_frames: Optional[list] = None, n_samples: int = 40) -> list[Optional[FaceDet]]:
    v = video_stream_info(ws.video_noaudio)
    det = make_detector(backend, fixed_box)
    out: list[Optional[FaceDet]] = []
    every = max(v["frames"] // n_samples, 1)
    for i, frame in enumerate(iter_frames(ws.video_noaudio, v["width"], v["height"])):
        d = None
        if i % stride == 0:
            d = det(frame)
            if d is not None:
                d.occlusion_score = mouth_occlusion_score(frame, d.mouth, d.box)
                d.occluded = d.occlusion_score > OCCLUSION_THR or d.hand_overlap
        out.append(d)                  # 건너뛴 프레임은 None -> build_track 에서 보간
        if sample_frames is not None and i % every == 0:
            sample_frames.append(cv2.resize(frame, (v["width"] // 2, v["height"] // 2), interpolation=cv2.INTER_AREA))
        if i % 200 == 0:
            log(f"[scan] {i}/{v['frames']} 프레임")
    return out


# ---------------------------------------------------------------- 크롭 / 합성 유틸

def crop_square(frame: np.ndarray, x: int, y: int, s: int, out: int) -> np.ndarray:
    patch = frame[y:y + s, x:x + s]
    interp = cv2.INTER_AREA if s > out else cv2.INTER_CUBIC
    return cv2.resize(patch, (out, out), interpolation=interp)


def feather_mask(size: int, margin: float = 0.08, feather: float = 0.12, shape: str = "ellipse") -> np.ndarray:
    """(size, size, 1) float32 0~1. 가장자리를 가우시안으로 부드럽게 한 마스크."""
    m = np.zeros((size, size), np.float32)
    lo, hi = int(size * margin), int(size * (1 - margin))
    if shape == "ellipse":
        cv2.ellipse(m, (size // 2, size // 2), ((hi - lo) // 2, (hi - lo) // 2), 0, 0, 360, 1.0, -1)
    else:
        m[lo:hi, lo:hi] = 1.0
    k = int(size * feather) * 2 + 1
    m = cv2.GaussianBlur(m, (k, k), 0)
    return np.clip(m, 0, 1)[..., None]


def mouth_mask(size: int, mouth_rel: Box, expand: float = 1.8, feather: float = 0.08) -> np.ndarray:
    """입 bbox(크롭 좌표계 0~1 비율) 주변만 타원으로 합성하는 마스크."""
    mx, my, mw, mh = mouth_rel
    m = np.zeros((size, size), np.float32)
    c = (int((mx + mw / 2) * size), int((my + mh / 2) * size))
    ax = (max(int(mw * size * expand / 2), 2), max(int(mh * size * expand / 2), 2))
    cv2.ellipse(m, c, ax, 0, 0, 360, 1.0, -1)
    k = int(size * feather) * 2 + 1
    return np.clip(cv2.GaussianBlur(m, (k, k), 0), 0, 1)[..., None]


def match_color(src: np.ndarray, ref: np.ndarray, mask: Optional[np.ndarray] = None,
                strength: float = 1.0, std_clip: tuple[float, float] = (0.7, 1.4)) -> np.ndarray:
    """src 의 색 분포(LAB 평균/표준편차)를 ref 에 맞춘다. 마스크 안쪽 통계만 사용."""
    s = cv2.cvtColor(src, cv2.COLOR_BGR2LAB).astype(np.float32)
    r = cv2.cvtColor(ref, cv2.COLOR_BGR2LAB).astype(np.float32)
    w = np.ones(s.shape[:2], bool) if mask is None else (mask[..., 0] > 0.5)
    if w.sum() < 16:
        return src
    out = s.copy()
    for c in range(3):
        ms, ss = s[..., c][w].mean(), s[..., c][w].std() + 1e-6
        mr, sr = r[..., c][w].mean(), r[..., c][w].std() + 1e-6
        ratio = float(np.clip(sr / ss, *std_clip))
        out[..., c] = (s[..., c] - ms) * ratio + mr
    out = s + (out - s) * strength
    return cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)


def paste_back(frame: np.ndarray, patch: np.ndarray, x: int, y: int, s: int, mask: np.ndarray) -> np.ndarray:
    """patch(out x out) 를 s x s 로 되돌려 mask 로 블렌딩해 frame 에 합성 (frame 은 복사해서 반환)."""
    out = frame.copy()
    interp = cv2.INTER_AREA if patch.shape[0] > s else cv2.INTER_CUBIC
    p = cv2.resize(patch, (s, s), interpolation=interp).astype(np.float32)
    m = cv2.resize(mask[..., 0], (s, s), interpolation=cv2.INTER_LINEAR)[..., None]
    region = out[y:y + s, x:x + s].astype(np.float32)
    out[y:y + s, x:x + s] = np.clip(p * m + region * (1 - m), 0, 255).astype(np.uint8)
    return out


def mouth_relative(track_frame: dict) -> Box:
    """프레임의 입 bbox 를 크롭 좌표계(0~1 비율)로."""
    x0, y0, s = track_frame["crop"]
    mx, my, mw, mh = track_frame["mouth"]
    return ((mx - x0) / s, (my - y0) / s, mw / s, mh / s)


# ---------------------------------------------------------------- 단계 실행

def run_scan(ws: Workspace, backend: str = "auto", fixed_box: Optional[Box] = None, stride: int = 1,
             crop_scale: float = 1.6, size: int = 512, export_crop: bool = True,
             min_face_px: int = 96, apply_bad_cuts: bool = False) -> dict:
    """영상 사전 점검: 컷 감지 + 컷별 얼굴/각도/눈/입 가림 판정(cuts_report.csv) + 워터마크 경고 + 얼굴 트랙.

    기본 정책: 얼굴 없음/너무 작음/측면/입 가려짐 구간은 립싱크를 건너뛰고 원본을 유지한다 (apply_bad_cuts 로 해제)."""
    from . import cuts as cutmod
    from . import watermark as wm
    ws.require(ws.video_noaudio, hint="먼저 `prepare` 단계를 실행해 주세요.")
    v = video_stream_info(ws.video_noaudio)
    cut_info = cutmod.run_cuts(ws)
    ranges = [tuple(r) for r in cut_info["cuts"]]
    samples: list = []
    dets = detect_video(ws, backend, fixed_box, stride, samples)
    track = build_track(dets, v["width"], v["height"], v["fps"], crop_scale, out_size=size, ranges=ranges)
    if apply_bad_cuts:     # 얼굴만 있으면 측면/가림이어도 적용 (사용자가 명시한 경우)
        mask = cutmod.eligible_mask(track["frames"], ranges, v["fps"], min_face_px, 180.0, 180.0, False)
    else:
        mask = cutmod.eligible_mask(track["frames"], ranges, v["fps"], min_face_px)
    for f, ok in zip(track["frames"], mask):
        f["eligible"] = bool(ok)
    track["cuts"] = [list(r) for r in ranges]
    track["policy"] = {"min_face_px": min_face_px, "apply_bad_cuts": apply_bad_cuts}
    rows = cutmod.make_report(track["frames"], ranges, v["fps"], v["width"], v["height"], mask, min_face_px)

    overlays = wm.detect_static_overlays(samples)
    overlays = [{**o, "box": [c * 2 for c in o["box"]]} for o in overlays]          # 샘플은 1/2 크기였으므로 원래 좌표로
    wm_msgs = wm.watermark_warnings(overlays, [f["face"] for f in track["frames"] if f["detected"]])
    archive_existing(ws, ws.face_track, ws.face_crop, ws.p("cuts_report.csv"), ws.p("scan.json"))
    write_json(ws.face_track, track)
    cutmod.write_report_csv(ws.p("cuts_report.csv"), rows)
    write_json(ws.p("scan.json"), {"watermark_overlays": overlays, "watermark_warnings": wm_msgs,
                                   "cuts": len(rows), "lipsync_frame_ratio": float(mask.mean())})
    warned = [r for r in rows if r["warnings"]]
    log(f"[scan] 얼굴 검출률 {track['detected_ratio']:.0%}, 립싱크 적용 가능 프레임 {mask.mean():.0%}, "
        f"컷 {len(rows)}개 중 경고 {len(warned)}개 -> cuts_report.csv")
    for r in warned:
        log(f"  [경고] 컷 {r['cut']} ({r['start_s']}~{r['end_s']}초): {r['warnings']} -> {r['decision']}")
    for m in wm_msgs:
        log("  [경고] " + m)
    if not mask.any():
        log("[경고] 립싱크를 적용할 수 있는 구간이 없습니다. 최종 결과는 원본 영상이 그대로 사용됩니다.")
    if export_crop:
        with FrameWriter(ws.face_crop, size, size, v["fps_rational"], crf=8, preset="slow") as w:
            for fr, t in zip(iter_frames(ws.video_noaudio, v["width"], v["height"]), track["frames"]):
                x, y, c = t["crop"]
                w.write(crop_square(fr, x, y, c, size))
        log(f"[scan] 크롭 영상: {ws.face_crop.name} ({size}x{size})")
    return track


run_face = run_scan       # 이전 이름 호환
