"""LatentSync 어댑터.

검증 상태: Colab(GPU)에서 실제로 실행해 본 유일한 어댑터다(README 의 "검증 범위", Colab 실측 커밋 기록 기준).
설치 절차는 README 의 Colab 실측 교훈(Python 3.10 가상환경, 체크포인트 다운로드 인자, fps 맞춤)을 따른다.
TODO(미검증): 설치한 버전에 따라 `--unet_config_path` 의 설정 파일 이름이 다를 수 있으므로 README/inference.sh 와
대조할 것. 얼굴이 화면을 꽉 채우는 크롭은 블러 여백을 붙여 넣고 결과에서 잘라 되돌린다(아래 pad_video/crop_back, Colab 실측).
precision / offload 를 넘기는 공식 인자가 있는지는 확인하지 못했다.

사용법
  1) git clone https://github.com/bytedance/LatentSync  && cd LatentSync && pip install -r requirements.txt
  2) 체크포인트(latentsync_unet.pt, whisper/tiny.pt)를 LatentSync/checkpoints/ 에 내려받기
  3) export LATENTSYNC_DIR=/path/to/LatentSync   (또는 --tool-dir)
  4) python -m lipsync_pipeline lipsync <이름> --model latentsync

입출력 규격은 base.py 상단 참고. LatentSync 는 자체 얼굴 검출/정렬을 하고 256px(v1.5) 또는 512px(v1.6) 모델이므로
출력 해상도가 입력 크롭과 다르면 TODO 부분에서 리사이즈해야 한다.
offload: 미확인 — 공식 코드에 offload 옵션이 없으면 diffusers 파이프라인에
  `pipeline.enable_model_cpu_offload()` / `enable_sequential_cpu_offload()` 를 넣는 패치가 필요하다.
"""
import dataclasses
from pathlib import Path

from ..utils import find_binary, run, video_stream_info
from .base import BaseLipSyncModel, LipSyncRequest, py, register, resolve_tool_dir, run_tool

# LatentSync(main) 의 얼굴 검출기(InsightFace, det_size 512)는 얼굴이 화면을 꽉 채우면 찾지 못한다.
# 실측(Colab, 얼굴 크롭 512x512, 240프레임): 원본 240/240 실패, 80% 축소 192/240 실패, 65% 축소 0/240, 50% 축소 0/240.
# 그래서 크롭을 줄이지 않고(화질 손실 없음) 바깥에 블러 여백을 붙여 캔버스를 키워서 얼굴이 캔버스의 이 비율이 되게 한다.
FACE_FRACTION = 0.6


def padded_canvas_side(width: int, height: int, fraction: float = FACE_FRACTION) -> int:
    side = int(round(max(width, height) / fraction))
    return side + (side % 2)                      # yuv420p/x264 는 짝수 크기를 요구한다


def _offsets(width: int, height: int, side: int) -> tuple[int, int]:
    return (side - width) // 2, (side - height) // 2


def pad_video(src: Path, dst: Path, fraction: float = FACE_FRACTION) -> int:
    """src 를 가운데에 그대로 두고(축소 없음) 바깥을 블러한 자기 자신으로 채운 정사각 캔버스 영상을 dst 에 쓴다. 캔버스 한 변을 돌려준다."""
    info = video_stream_info(src)
    w, h = info["width"], info["height"]
    side = padded_canvas_side(w, h, fraction)
    ox, oy = _offsets(w, h, side)
    blur = max(1, min(40, side // 8))               # ffmpeg boxblur 는 반경이 (색차 평면 크기)/2 미만이어야 한다
    run([find_binary("ffmpeg"), "-y", "-v", "error", "-i", src, "-an",
         "-filter_complex", f"[0:v]split[a][b];[a]scale={side}:{side},boxblur={blur}:3[bg];[bg][b]overlay={ox}:{oy}",
         "-c:v", "libx264", "-crf", "8", "-preset", "slow", "-pix_fmt", "yuv420p", dst], "LatentSync 입력 여백 추가")
    return side


def crop_back(padded_out: Path, dst: Path, width: int, height: int, side: int) -> None:
    """모델이 돌려준 캔버스 영상에서 원래 크롭 영역만 잘라 width x height 로 되돌린다 (소리가 있으면 보존)."""
    info = video_stream_info(padded_out)
    k = info["width"] / side                      # 모델이 해상도를 바꿨다면 비율만큼 보정
    ox, oy = _offsets(width, height, side)
    vf = f"crop={round(width * k)}:{round(height * k)}:{round(ox * k)}:{round(oy * k)}"
    if abs(k - 1.0) > 1e-6:
        vf += f",scale={width}:{height}:flags=lanczos"
    run([find_binary("ffmpeg"), "-y", "-v", "error", "-i", padded_out, "-vf", vf, "-map", "0:v:0", "-map", "0:a?",
         "-c:v", "libx264", "-crf", "8", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "copy", dst], "LatentSync 출력 크롭 복원")


@register("latentsync")
class LatentSyncModel(BaseLipSyncModel):
    MAX_STEPS = 50
    DEFAULT_GUIDANCE = 2.0
    NATIVE_RESOLUTION = 256
    TOOL_ENV = "LATENTSYNC_DIR"

    def build_command(self, req: LipSyncRequest, repo: Path) -> list:
        o = req.options
        cmd = [py(), "-m", "scripts.inference",
               "--unet_config_path", "configs/unet/stage2.yaml",       # 버전에 맞는 설정 파일인지 확인
               "--inference_ckpt_path", "checkpoints/latentsync_unet.pt",
               "--inference_steps", o.steps, "--guidance_scale", o.guidance,
               "--seed", o.seed,
               "--video_path", req.video, "--audio_path", req.audio, "--video_out_path", req.output]
        # precision / offload: 공식 인자가 없다면 환경변수나 패치로 전달 (미확인)
        return [str(c) for c in cmd]

    def check_environment(self, opts):
        resolve_tool_dir(self.TOOL_ENV, opts.tool_dir, "LatentSync")

    def generate(self, req: LipSyncRequest) -> Path:
        repo = resolve_tool_dir(self.TOOL_ENV, req.options.tool_dir, "LatentSync")
        info = video_stream_info(req.video)
        padded_in = req.output.with_name(req.output.stem + ".pad_in.mp4")
        padded_out = req.output.with_name(req.output.stem + ".pad_out.mp4")
        try:
            side = pad_video(req.video, padded_in)
            run_tool(self.build_command(dataclasses.replace(req, video=padded_in, output=padded_out), repo), repo, "LatentSync 추론")
            crop_back(padded_out, req.output, info["width"], info["height"], side)
        finally:
            padded_in.unlink(missing_ok=True)
            padded_out.unlink(missing_ok=True)
        return req.output
