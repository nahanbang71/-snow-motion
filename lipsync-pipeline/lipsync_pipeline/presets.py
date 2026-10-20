"""프리셋: presets/*.yaml. 알 수 없는 키는 오류로 막아 오타를 조기에 발견한다."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Optional

from .utils import PipelineError


@dataclass
class Preset:
    name: str = "quality"
    # 5. lipsync
    model: str = "latentsync"
    takes: int = 3
    seed: int = 1234
    steps: Optional[int] = None          # None = 모델 최대값
    guidance: Optional[float] = None
    precision: str = "fp16"
    offload: str = "none"
    lipsync_device: str = "cuda"
    # 합성
    paste_mode: str = "face"             # face(얼굴 전체) | mouth(입 영역만)
    emotion: bool = True
    # 7. finalize
    restore: bool = True
    upscale: bool = True
    interpolate: bool = True
    upscale_scale: float = 2.0
    interp_multi: int = 2
    restore_weight: float = 0.7
    fill_missing: str = "score"          # 배치에서는 사람이 고르지 않으므로 점수 기준 임시 선택 (review 후 재-finalize 가능)
    # 앞 단계
    separate_device: str = "cpu"
    separate_model: str = "htdemucs"
    separate_backend: str = "demucs"     # demucs | passthrough(테스트용)
    face_backend: str = "auto"           # auto | mediapipe | haar
    face_size: int = 512
    min_face_px: int = 96
    apply_bad_cuts: bool = False
    overlap_sec: float = 0.5
    min_len_sec: float = 2.0
    max_len_sec: float = 12.0
    tool_dirs: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def preset_dirs() -> list[Path]:
    return [Path("presets"), Path(__file__).resolve().parent.parent / "presets"]


def load_preset(name_or_path: str, extra_dirs: Optional[list[Path]] = None) -> Preset:
    try:
        import yaml
    except ImportError as e:
        raise PipelineError("PyYAML 이 필요합니다: pip install pyyaml") from e
    cand = [Path(name_or_path)] if name_or_path.endswith((".yaml", ".yml")) else []
    for d in [*(extra_dirs or []), *preset_dirs()]:
        cand += [Path(d) / f"{name_or_path}.yaml", Path(d) / f"{name_or_path}.yml"]
    path = next((c for c in cand if c.is_file()), None)
    if path is None:
        raise PipelineError(f"프리셋 '{name_or_path}' 를 찾을 수 없습니다 (찾은 위치: {', '.join(str(d) for d in preset_dirs())}).")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise PipelineError(f"프리셋 YAML 형식 오류 ({path}): {e}") from e
    if not isinstance(data, dict):
        raise PipelineError(f"프리셋은 키: 값 형태여야 합니다: {path}")
    known = {f.name for f in fields(Preset)}
    unknown = sorted(set(data) - known)
    if unknown:
        raise PipelineError(f"프리셋 {path.name} 에 알 수 없는 키가 있습니다: {', '.join(unknown)} (사용 가능: {', '.join(sorted(known))})")
    p = Preset(name=path.stem, **data)
    if p.paste_mode not in ("face", "mouth"):
        raise PipelineError(f"프리셋 paste_mode 는 face 또는 mouth 여야 합니다: {p.paste_mode}")
    if p.fill_missing not in ("error", "first", "score"):
        raise PipelineError(f"프리셋 fill_missing 은 error|first|score 중 하나입니다: {p.fill_missing}")
    return p
