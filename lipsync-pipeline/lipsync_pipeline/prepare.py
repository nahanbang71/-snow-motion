"""1단계 prepare: 메타데이터 확인 + 오디오 제거 영상 / 44.1kHz 스테레오 WAV / 16kHz 모노 WAV 생성."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .utils import (PipelineError, Workspace, archive_existing, ffprobe, find_binary, log, run,
                    sanitize_name, video_stream_info, write_json)


def _summarize(probe: dict) -> dict:
    streams = probe.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    return {
        "duration": float(probe.get("format", {}).get("duration") or 0.0),
        "format": probe.get("format", {}).get("format_name"),
        "video": None if v is None else {k: v.get(k) for k in
                 ("codec_name", "width", "height", "avg_frame_rate", "r_frame_rate", "nb_frames", "pix_fmt")},
        "audio": None if a is None else {k: a.get(k) for k in
                 ("codec_name", "sample_rate", "channels", "duration")},
    }


def prepare(video: Path, audio: Path, work_root: Path | str = "work", name: Optional[str] = None,
            audio_start: float = 0.0, crf: int = 14) -> dict:
    video, audio = Path(video), Path(audio)
    for label, p in (("영상", video), ("음원", audio)):
        if not p.is_file():
            raise PipelineError(f"{label} 파일을 찾을 수 없습니다: {p}")
    if audio_start < 0:
        raise PipelineError("--audio-start 는 0 이상이어야 합니다.")

    vprobe, aprobe = ffprobe(video), ffprobe(audio)
    vsum, asum = _summarize(vprobe), _summarize(aprobe)
    if vsum["video"] is None:
        raise PipelineError(f"영상 파일에 비디오 스트림이 없습니다: {video}")
    if asum["audio"] is None:
        raise PipelineError(f"음원 파일에 오디오 스트림이 없습니다: {audio}")

    ws = Workspace.open(name or sanitize_name(video.stem), work_root, must_exist=False)
    archive_existing(ws, ws.info, ws.video_noaudio, ws.audio_44k, ws.audio_16k)
    ffmpeg = find_binary("ffmpeg")
    src_fps = video_stream_info(video)["fps_rational"]

    # 오디오 제거 + 고정 프레임레이트(CFR) + 짝수 해상도로 정규화. 회전 메타데이터는 ffmpeg 가 자동 적용.
    log("[prepare] 영상 정규화 (오디오 제거)...")
    run([ffmpeg, "-y", "-v", "error", "-i", video, "-an",
         "-vf", f"fps={src_fps},scale=trunc(iw/2)*2:trunc(ih/2)*2",
         "-c:v", "libx264", "-crf", str(crf), "-preset", "fast", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", ws.video_noaudio], "영상 정규화")
    vinfo = video_stream_info(ws.video_noaudio)
    dur = vinfo["duration"]
    if dur <= 0:
        raise PipelineError("정규화된 영상의 길이를 확인할 수 없습니다.")

    # 영상 길이에 맞춰 자르거나(길면) 무음으로 채운다(짧으면)
    log("[prepare] 오디오 변환 (44.1kHz 스테레오 / 16kHz 모노)...")
    common = [ffmpeg, "-y", "-v", "error", "-ss", f"{audio_start}", "-i", audio, "-vn",
              "-af", "apad", "-t", f"{dur:.6f}"]
    run(common + ["-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", ws.audio_44k], "44.1kHz 변환")
    run(common + ["-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", ws.audio_16k], "16kHz 변환")

    warnings = []
    avail = asum["duration"] - audio_start
    if abs(avail - dur) > 0.5:
        warnings.append(
            f"음원 길이({avail:.1f}초, 시작 {audio_start}초 이후)와 영상 길이({dur:.1f}초)가 다릅니다. "
            "영상 길이에 맞춰 자르거나 무음으로 채웠습니다. 필요하면 --audio-start 로 시작 위치를 맞추세요."
        )
    for w in warnings:
        log("[경고] " + w)

    info = {
        "name": ws.name,
        "source": {"video": str(video), "audio": str(audio), "audio_start": audio_start,
                   "video_meta": vsum, "audio_meta": asum},
        "video": {**vinfo, "file": ws.video_noaudio.name},
        "audio": {"file_44k": ws.audio_44k.name, "file_16k": ws.audio_16k.name,
                  "duration": dur},
        "warnings": warnings,
    }
    write_json(ws.info, info)
    log(f"[prepare] 완료: {ws.root}  ({vinfo['width']}x{vinfo['height']}, {vinfo['fps']:.3f}fps, "
        f"{vinfo['frames']}프레임, {dur:.2f}초)")
    return info
