from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResult,
    CompetitorAnalysis,
    ReasoningDetails,
)
from app.services.kakao import get_nearby_cafes
from app.services.analyzer import analyze_business_area
from app.db import crud
import traceback

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _normalize_places(rows):
    """
    Kakao 문서/DB Row를 analyzer가 기대하는 공통 스키마로 통일.
    반환: dict(place_name, category_name, y(lat), x(lon))
    """
    norm = []
    for r in rows or []:
        place_name = (
            r.get("place_name")
            or r.get("name")
            or r.get("cctvNm")
            or r.get("marketNm")
            or ""
        )
        category_name = r.get("category_name") or r.get("category") or ""
        lat = r.get("y") or r.get("lat") or r.get("latitude")
        lon = r.get("x") or r.get("lon") or r.get("longitude")
        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            continue
        if not place_name:
            continue
        norm.append(
            {
                "place_name": str(place_name).strip(),
                "category_name": str(category_name or "").strip(),
                "y": lat,
                "x": lon,
            }
        )
    return norm


def _normalize_kakao_docs_for_db(docs: list[dict]) -> list[dict]:
    """
    DB 저장용 내부 스키마로 변환.
    crud.save_kakao_places()가 기대하는 키셋: name, category, lat, lon
    """
    out = []
    for d in docs or []:
        try:
            lon = float(d.get("x"))
            lat = float(d.get("y"))
        except (TypeError, ValueError):
            continue
        name = (d.get("place_name") or "").strip()
        category = (d.get("category_name") or "").strip()
        if not name:
            continue
        out.append({"name": name, "category": category, "lat": lat, "lon": lon})
    return out


@router.post("/area", response_model=AnalysisResult)
async def analyze_area(req: AnalysisRequest, db: AsyncSession = Depends(get_session)):
    try:
        radius_m = req.radius_m or 2000
        d = radius_m / 111_000  # 대략 위경도 -> 미터

        # 1) DB에서 기존 장소 조회
        existing = await crud.get_places_bbox(
            db, req.lat - d, req.lon - d, req.lat + d, req.lon + d
        )
        cafes_from_db = _normalize_places(
            [
                {"name": p.name, "category": p.category, "lat": p.lat, "lon": p.lon}
                for p in existing
                if (p.category or "").startswith("카페")
            ]
        )

        # 2) 없으면 Kakao 호출 -> 정규화하여 DB 저장 -> 분석 입력 생성
        if not cafes_from_db:
            kakao_docs = await get_nearby_cafes(req.lat, req.lon, radius_m)
            to_save = _normalize_kakao_docs_for_db(kakao_docs)
            if to_save:
                await crud.save_kakao_places(db, to_save)
            nearby = _normalize_places(kakao_docs)
        else:
            nearby = cafes_from_db

        # 3) 분석 실행
        score, reasoning, comp = analyze_business_area(req.lat, req.lon, nearby)

        return AnalysisResult(
            suitability_score=int(round(score)),
            reasoning=ReasoningDetails(**reasoning),
            competitor_analysis=CompetitorAnalysis(**comp),
        )
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())
