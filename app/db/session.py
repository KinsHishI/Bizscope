# app/db/session.py
# -----------------------------------------------------------------------------
# SQLAlchemy Async 엔진/세션/베이스
# - FastAPI Depends(get_session)로 주입
# - SQLite 기본, 추후 PostgreSQL로 교체 시 URL만 변경
# -----------------------------------------------------------------------------
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """요청 스코프 세션 제공"""
    async with AsyncSessionLocal() as session:
        yield session
