# app/main.py
# -----------------------------------------------------------------------------
# FastAPI 엔트리포인트
# - 서버 기동 시 테이블 생성
# - 옵션: 자동 부트스트랩(AUTO_INGEST_SUSEONG)
# -----------------------------------------------------------------------------
from fastapi import FastAPI
from app.core.config import settings
from app.db.session import Base, engine, get_session
from app.routers import analysis, simulate, admin, finance
from app.services.ingest import bootstrap_suseong

app = FastAPI(title=settings.APP_NAME)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if settings.AUTO_INGEST_SUSEONG:
        # 서버 초기화 이후 첫 이벤트 루프에서 백그라운드 태스크로
        import asyncio

        async def _bg_bootstrap():
            from sqlalchemy.ext.asyncio import AsyncSession

            async for db in get_session():  # 간단히 세션 하나 빌려서
                await bootstrap_suseong(db)
                break

        asyncio.create_task(_bg_bootstrap())


# 필요한 라우터만 include (미사용시 주석처리 가능)
app.include_router(finance.router)
app.include_router(admin.router)
app.include_router(analysis.router)
app.include_router(simulate.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
