# app/services/analyzer.py
from __future__ import annotations
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db import crud

KAKAO_API_KEY = settings.KAKAO_API_KEY


async def fetch_kakao_cafes(lat: float, lon: float, radius_m: int = 2000) -> list[dict]:
    """
    카카오 카테고리 검색(카페: CE7) 호출. 원본 문서 리스트 반환.
    """
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    out: list[dict] = []
    page = 1
    while True:
        params = {
            "category_group_code": "CE7",
            "x": lon,
            "y": lat,
            "radius": radius_m,
            "sort": "distance",
            "page": page,
        }
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        docs = data.get("documents", []) or []
        if not docs:
            break
        out.extend(docs)
        meta = data.get("meta", {}) or {}
        if meta.get("is_end") or page >= 3:
            break
        page += 1
    return out


def _kakao_docs_to_places(docs: list[dict]) -> list[dict]:
    """
    Kakao 문서를 Place insert용 dict로 매핑.
    - name, category, lat(y), lon(x)
    """
    places = []
    for d in docs:
        try:
            places.append(
                {
                    "name": d.get("place_name") or "상호",
                    "category": d.get("category_name") or "카페",
                    "lat": float(d.get("y")),
                    "lon": float(d.get("x")),
                }
            )
        except Exception:
            continue
    return places


async def upsert_kakao_places(db: AsyncSession, docs: list[dict]) -> int:
    """
    Kakao 문서를 Place로 저장(중복 방지). crud.save_kakao_places 사용.
    """
    to_save = _kakao_docs_to_places(docs)
    if not to_save:
        return 0
    return await crud.save_kakao_places(db, to_save)


from typing import Sequence
from app.db.models import Place


async def find_places_nearby(
    db: AsyncSession, *, lat: float, lon: float, radius_km: float = 2.0
) -> Sequence[Place]:
    """
    반경 rkm ≈ 위도/경도 상자 검색으로 근사. (1도 ≈ ~111km 가정)
    """
    deg = radius_km / 111.0
    rows = await crud.get_places_bbox(db, lat - deg, lon - deg, lat + deg, lon + deg)
    if rows:
        return rows

    # DB에 없으면 Kakao 호출 → 저장 → 재조회
    docs = await fetch_kakao_cafes(lat, lon, int(radius_km * 1000))
    if docs:
        await upsert_kakao_places(db, docs)
        rows = await crud.get_places_bbox(
            db, lat - deg, lon - deg, lat + deg, lon + deg
        )
        if rows:
            return rows

    # 그래도 없으면 반경을 조금씩 키워서 시도 (선택)
    rows = await crud.widen_bbox_places(db, lat, lon, radii=(0.01, 0.02, 0.03))
    return rows
