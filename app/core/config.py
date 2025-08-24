# app/core/config.py
# -----------------------------------------------------------------------------
# 전역 설정 관리 (pydantic-settings v2)
# - .env 파일과 OS 환경변수를 읽어 Settings 객체로 제공
# - 타입 세이프티/기본값/도움말을 함께 정의
# -----------------------------------------------------------------------------
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 앱 메타
    APP_NAME: str = "CarryOn"
    ENV: str = "dev"

    # DB
    DATABASE_URL: str = "sqlite+aiosqlite:///./space.db"

    # 모델/파일 저장 디렉터리
    MODEL_DIR: str = "./models"

    # 외부 API 키 (옵션)
    MAP_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    # 수성구 공공데이터 (유동인구)
    SUSEONG_API_KEY: str | None = None
    SUSEONG_API_URL: str = (
        "https://apis.data.go.kr/3460000/suseongfpa/viewmarketpopudetail"
    )

    # 서버 기동 시 자동 적재 옵션
    AUTO_INGEST_SUSEONG: bool = False
    SUSEONG_BOOTSTRAP_YEAR_FROM: int = 2020
    SUSEONG_BOOTSTRAP_YEAR_TO: int = 2025
    SUSEONG_BOOTSTRAP_QUARTER_TO: int = 3
    SUSEONG_PAGE_SIZE: int = 200
    SUSEONG_PAGES: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # .env 의 소문자 키도 허용
        extra="ignore",  # 알 수 없는 키 무시
    )


settings = Settings()
