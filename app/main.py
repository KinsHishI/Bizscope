# app/main.py
# -----------------------------------------------------------------------------
# FastAPI 엔트리포인트
# - 서버 기동 시 테이블 생성
# -----------------------------------------------------------------------------
from fastapi import FastAPI, HTTPException
from app.core.config import settings
from app.db.session import Base, engine, get_session
from app.routers import analysis, simulate, admin, finance
from app.services.ingest import bootstrap_suseong
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResult,
    CompetitorAnalysis,
    ReasoningDetails,
)

import traceback

app = FastAPI(title=settings.APP_NAME)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if settings.AUTO_INGEST_SUSEONG:
        import asyncio

        async def _bg_bootstrap():
            from sqlalchemy.ext.asyncio import AsyncSession

            async for db in get_session():
                await bootstrap_suseong(db)
                break

        asyncio.create_task(_bg_bootstrap())


# 필요한 라우터만 include
app.include_router(finance.router)
app.include_router(admin.router)
app.include_router(analysis.router)
app.include_router(simulate.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analysis/area", response_model=AnalysisResult)
def analyze_area(request: AnalysisRequest):
    try:
        stores_from_db = get_nearby_stores(request.lat, request.lon)

        if not stores_from_db:
            cafes = get_nearby_cafes(request.lat, request.lon)
            if cafes:
                save_stores_data(
                    [
                        {
                            "place_name": c.get("place_name"),
                            "category_name": c.get("category_name"),
                            "y": float(c.get("y")),
                            "x": float(c.get("x")),
                        }
                        for c in cafes
                    ]
                )
            stores_to_analyze = cafes
        else:
            stores_to_analyze = stores_from_db

        score, reasoning_details, competitor_info_dict = analyze_business_area(
            request.lat, request.lon, stores_to_analyze
        )

        competitor_analysis_model = CompetitorAnalysis(**competitor_info_dict)
        reasoning_details_model = ReasoningDetails(**reasoning_details)

        return AnalysisResult(
            suitability_score=int(score),
            reasoning=reasoning_details_model,
            competitor_analysis=competitor_analysis_model,
        )

    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{tb}")
