# app/db/crud.py
# -----------------------------------------------------------------------------
# 읽기/쓰기 유틸 함수 모음
# - bbox 조회
# - 좌표 근접 조회(+ 업서트 예시)
# -----------------------------------------------------------------------------
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Place
from typing import Sequence


async def get_places_bbox(
    db: AsyncSession, min_lat: float, min_lon: float, max_lat: float, max_lon: float
) -> Sequence[Place]:
    stmt = select(Place).where(
        Place.lat.between(min_lat, max_lat),
        Place.lon.between(min_lon, max_lon),
    )
    res = await db.execute(stmt)
    return res.scalars().all()


async def get_nearby_place(
    db: AsyncSession, lat: float, lon: float, eps: float = 0.0005
) -> Place | None:
    """대략 수십 m 박스 내 근접 장소 1건"""
    stmt = (
        select(Place)
        .where(
            Place.lat.between(lat - eps, lat + eps),
            Place.lon.between(lon - eps, lon + eps),
        )
        .limit(1)
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def upsert_place_with_foot_traffic(
    db: AsyncSession, *, name: str, lat: float, lon: float, foot_traffic: int
) -> Place:
    """
    좌표 근접 기준으로 존재하면 업데이트, 없으면 신규 생성
    """
    p = await get_nearby_place(db, lat, lon)
    if p:
        p.foot_traffic = max(
            p.foot_traffic or 0, foot_traffic
        )  # 최근치/최댓값 등 정책 가능
    else:
        p = Place(
            name=name, category="상권", lat=lat, lon=lon, foot_traffic=foot_traffic
        )
        db.add(p)
    await db.commit()
    await db.refresh(p)
    return p
