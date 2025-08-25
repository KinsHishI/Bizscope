# app/db/crud.py
# -----------------------------------------------------------------------------
# 읽기/쓰기 유틸 함수 모음
# - bbox 조회
# - 좌표 근접 조회(+ 업서트 예시)
# -----------------------------------------------------------------------------
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Place, FootTrafficQuarter
from typing import Sequence, Optional


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


async def upsert_place_with_foot_traffic(db, name, lat, lon, foot_traffic):
    stmt = select(Place).where(Place.lat == lat, Place.lon == lon)
    result = await db.execute(stmt)
    place = result.scalar_one_or_none()
    if place:
        place.foot_traffic = foot_traffic
    else:
        place = Place(name=name, lat=lat, lon=lon, foot_traffic=foot_traffic)
        db.add(place)
    await db.commit()


async def save_kakao_places(db: AsyncSession, places: list[dict]) -> int:
    inserted = 0
    for p in places:
        stmt = select(Place).where(
            and_(Place.name == p["name"], Place.lat == p["lat"], Place.lon == p["lon"])
        )
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            db.add(
                Place(
                    name=p["name"],
                    category=p.get("category") or "카페",
                    lat=p["lat"],
                    lon=p["lon"],
                )
            )
            inserted += 1
    await db.commit()
    return inserted


async def widen_bbox_places(
    db: AsyncSession, lat: float, lon: float, radii=(0.001, 0.002, 0.005)
) -> Sequence[Place]:
    """점차 반경을 키워가며 Place 검색"""
    for d in radii:
        stmt = select(Place).where(
            Place.lat.between(lat - d, lat + d),
            Place.lon.between(lon - d, lon + d),
        )
        res = await db.execute(stmt)
        rows = res.scalars().all()
        if rows:
            return rows
    return []


async def upsert_ftq(
    db: AsyncSession, *, year: int, quarter: int, lat: float, lon: float, pop: int
) -> None:
    stmt = select(FootTrafficQuarter).where(
        FootTrafficQuarter.year == year,
        FootTrafficQuarter.quarter == quarter,
        FootTrafficQuarter.lat == lat,
        FootTrafficQuarter.lon == lon,
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row:
        row.pop = pop
    else:
        db.add(
            FootTrafficQuarter(year=year, quarter=quarter, lat=lat, lon=lon, pop=pop)
        )
    await db.commit()


async def get_ftq_recent_near(
    db: AsyncSession, lat: float, lon: float, deg: float = 0.03
) -> Optional[int]:
    max_year = (
        await db.execute(select(func.max(FootTrafficQuarter.year)))
    ).scalar_one_or_none()
    if not max_year:
        return None
    max_quarter = (
        await db.execute(
            select(func.max(FootTrafficQuarter.quarter)).where(
                FootTrafficQuarter.year == max_year
            )
        )
    ).scalar_one_or_none()
    if not max_quarter:
        return None

    mx = (
        await db.execute(
            select(func.max(FootTrafficQuarter.pop)).where(
                FootTrafficQuarter.year == max_year,
                FootTrafficQuarter.quarter == max_quarter,
                FootTrafficQuarter.lat.between(lat - deg, lat + deg),
                FootTrafficQuarter.lon.between(lon - deg, lon + deg),
            )
        )
    ).scalar_one_or_none()
    return int(mx) if mx and mx > 0 else None
