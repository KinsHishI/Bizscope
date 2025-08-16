from fastapi import FastAPI
from app.core.config import settings
from app.db.session import Base, engine
from app.routers import analysis, simulate, admin

app = FastAPI(title=settings.APP_NAME)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(analysis.router)
app.include_router(simulate.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
