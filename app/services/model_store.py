# 모델 파일 경로/버전 관리 (향후 XGBoost 추가)
from pathlib import Path
from app.core.config import settings

MODELDIR = Path(settings.MODEL_DIR)
MODELDIR.mkdir(parents=True, exist_ok=True)


def path(name: str) -> Path:
    return MODELDIR / name
