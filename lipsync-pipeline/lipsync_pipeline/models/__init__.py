"""어댑터 자동 등록: 이 폴더의 모든 모듈을 import 하면 @register 가 실행된다."""
import importlib
import pkgutil

from .base import (BaseLipSyncModel, BasePostProcessor, GenerationOptions, LipSyncRequest,  # noqa: F401
                   available_models, get_lipsync_model, get_post_processor, register)

for _m in pkgutil.iter_modules(__path__):
    if _m.name != "base":
        importlib.import_module(f"{__name__}.{_m.name}")
