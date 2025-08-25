# app/main.py
# -----------------------------------------------------------------------------
# FastAPI 엔트리포인트
# - 서버 기동 시 테이블 생성
# -----------------------------------------------------------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import Base, engine, get_session
from app.routers import analysis, simulate, admin, finance
from app.services.ingest import bootstrap_suseong

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if settings.AUTO_INGEST_SUSEONG:
        import asyncio

        async def _bg():
            async for db in get_session():
                await bootstrap_suseong(db)
                break

        asyncio.create_task(_bg())


app.include_router(finance.router)
app.include_router(admin.router)
app.include_router(analysis.router)
app.include_router(simulate.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
