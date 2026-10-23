"""CPU 검증용 어댑터: 입력 영상을 그대로 복사한다 (모델 없이 전체 파이프라인 연결을 시험할 때)."""
import shutil
from pathlib import Path

from .base import BaseLipSyncModel, LipSyncRequest, register


@register("identity")
class IdentityModel(BaseLipSyncModel):
    MAX_STEPS = 1

    def generate(self, req: LipSyncRequest) -> Path:
        shutil.copyfile(req.video, req.output)
        return req.output
