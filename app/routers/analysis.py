from fastapi import APIRouter, Depends
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.db.session import get_session
from app.db import crud
from app.services.analyzer import analyze

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/district", response_model=AnalysisResponse)
async def analyze_district(req: AnalysisRequest, db=Depends(get_session)):
    # 단순 bbox 검색 (실서비스는 반경쿼리/지오인덱스 권장)
    d = req.radius_m / 111_000  # approx degree per meter
    places = await crud.get_places_bbox(
        db, req.lat - d, req.lon - d, req.lat + d, req.lon + d
    )
    return await analyze(req, places, transit_nodes=2)
