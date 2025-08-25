# app/routers/analysis.py
from fastapi import APIRouter, HTTPException
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResult,
    CompetitorAnalysis,
    ReasoningDetails,
)
from app.services.analyzer import (
    get_nearby_stores,
    get_nearby_cafes,
    save_stores_data,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/area", response_model=AnalysisResult)
def analyze_area(request: AnalysisRequest):
    try:
        # 1) DB에서 반경 내 점포 조회
        stores_from_db = get_nearby_stores(
            request.lat, request.lon, radius_km=request.radius_m / 1000
        )

        # 2) 없으면 카카오맵에서 가져오고 DB에 저장
        if not stores_from_db:
            cafes = get_nearby_cafes(
                request.lat, request.lon, radius_m=request.radius_m
            )
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

        # 3) 간단한 요약
        competitor_cnt = len(stores_to_analyze) if stores_to_analyze else 0
        franchise_cnt = sum(
            1
            for s in stores_to_analyze or []
            if "스타벅스" in str(s.get("place_name", ""))
            or "이디야" in str(s.get("place_name", ""))
        )
        personal_cnt = max(0, competitor_cnt - franchise_cnt)

        reasoning = ReasoningDetails(
            competitor_count=competitor_cnt,
            franchise_count=franchise_cnt,
            personal_count=personal_cnt,
            floating_population=0,
            radius_km=request.radius_m // 1000,
        )
        competitor = CompetitorAnalysis(
            count=competitor_cnt,
            types={"franchise": franchise_cnt, "personal": personal_cnt},
            avg_rating=None,
        )

        score = max(0, 100 - int(competitor_cnt * 1.5))

        return AnalysisResult(
            suitability_score=score,
            reasoning=reasoning,
            competitor_analysis=competitor,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
