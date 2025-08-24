# app/core/logging.py
# -----------------------------------------------------------------------------
# Loguru 기반 로깅 설정
# - 회전/백트레이스/레벨 지정
# - Uvicorn/SQLAlchemy 로그도 캡처하려면 intercept 추가 가능
# -----------------------------------------------------------------------------
from loguru import logger
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True, parents=True)

logger.remove()  # 기본 핸들러 제거
logger.add(
    LOG_DIR / "app.log",
    rotation="10 MB",
    retention="10 files",
    enqueue=True,  # 멀티프로세스 안전
    backtrace=True,
    diagnose=True,
    level="INFO",
)
