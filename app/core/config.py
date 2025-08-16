from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "CarryOn"
    ENV: str = "dev"
    DATABASE_URL: str = "sqlite+aiosqlite:///./space.db"
    MODEL_DIR: str = "./models"
    MAP_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None


settings = Settings()
