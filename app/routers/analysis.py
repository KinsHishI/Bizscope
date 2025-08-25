from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResult,
    CompetitorAnalysis,
    ReasoningDetails,
)
from app.services.analyzer import find_places_nearby
import traceback

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/area", response_model=AnalysisResult)
async def analyze_area(req: AnalysisRequest, db: AsyncSession = Depends(get_session)):
    try:
        radius_km = req.radius_m / 1000
        places = await find_places_nearby(
            db, lat=req.lat, lon=req.lon, radius_km=radius_km
        )

        competitor_count = len(places)
        franchise = sum(1 for p in places if (p.category or "").find("프랜차이즈") >= 0)
        personal = competitor_count - franchise
        floating_population = 0

        score = max(0, min(100, 80 - competitor_count + (floating_population // 10000)))

        return AnalysisResult(
            suitability_score=int(score),
            reasoning=ReasoningDetails(
                competitor_count=competitor_count,
                franchise_count=franchise,
                personal_count=personal,
                floating_population=floating_population,
                radius_km=int(radius_km),
            ),
            competitor_analysis=CompetitorAnalysis(
                count=competitor_count,
                types={"franchise": franchise, "personal": personal},
                avg_rating=None,
            ),
            lat=req.lat,
            lon=req.lon,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}\n{traceback.format_exc()}")
