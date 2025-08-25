# app/services/ingest.py
# -----------------------------------------------------------------------------
# (1) 데모용 MOCK 적재
# (2) 수성구 공공데이터 유동인구 적재
# (3) 서버 기동 시 분기별 부트스트랩
# -----------------------------------------------------------------------------
from __future__ import annotations

import asyncio
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Place, IngestLog
from app.db import crud


# ── (1) MOCK DEMO DATA ────────────────────────────────────────────────────────
MOCK = [
    {
        "name": "북문코너",
        "category": "카페",
        "lat": 35.888,
        "lon": 128.611,
        "area_m2": 50,
        "rent_month": 1_500_000,
    },
    {
        "name": "분식나라",
        "category": "분식",
        "lat": 35.889,
        "lon": 128.612,
        "area_m2": 33,
        "rent_month": 1_100_000,
    },
    {
        "name": "미니편의",
        "category": "편의점",
        "lat": 35.887,
        "lon": 128.610,
        "area_m2": 45,
        "rent_month": 1_200_000,
    },
]


async def load_mock(session: AsyncSession) -> None:
    for m in MOCK:
        session.add(Place(**m))
    await session.commit()


# ── (2) 수성구 유동인구 적재 ───────────────────────────────────────────────────
async def ingest_suseong_foot_traffic(
    db: AsyncSession, *, year: int, quarter: int, pages: int = 5, page_size: int = 100
) -> dict:
    """
    수성구 유동인구 API 호출 → items 파싱 → Place & FTQ에 upsert
    """
    if not settings.SUSEONG_API_KEY:
        raise RuntimeError("SUSEONG_API_KEY가 설정되어 있지 않습니다")

    total_ingested = 0
    async with httpx.AsyncClient(timeout=20) as client:
        for page in range(1, pages + 1):
            params = {
                "serviceKey": settings.SUSEONG_API_KEY,
                "startYear": str(year),
                "startBungi": str(quarter),
                "resultType": "json",
                "size": str(page_size),
                "page": str(page),
            }
            r = await client.get(settings.SUSEONG_API_URL, params=params)
            r.raise_for_status()
            data = r.json()

            # 응답 구조 방어적 파싱
            items_node = data.get("response", {}).get("body", {}).get("items")
            if isinstance(items_node, dict):
                items = items_node.get("item", [])
            elif isinstance(items_node, list):
                items = items_node
            else:
                items = []

            if not items:
                break

            for it in items:
                # 이름
                name = str(it.get("marketNm") or it.get("name") or "상권").strip()

                # 좌표
                lat_raw = it.get("lat") or it.get("latitude") or it.get("위도")
                lon_raw = it.get("lon") or it.get("longitude") or it.get("경도")
                try:
                    lat = float(lat_raw)
                    lon = float(lon_raw)
                except (TypeError, ValueError):
                    continue
                if not lat or not lon:
                    continue

                # 유동인구
                pop_raw = it.get("popuCnt") or it.get("flowCnt") or it.get("total")
                try:
                    pop = int(float(pop_raw))
                except (TypeError, ValueError):
                    pop = 0

                # upsert
                await crud.upsert_place_with_foot_traffic(
                    db, name=name, lat=lat, lon=lon, foot_traffic=pop
                )
                await crud.upsert_ftq(
                    db, year=year, quarter=quarter, lat=lat, lon=lon, pop=pop
                )

                total_ingested += 1

            # 배치 커밋
            await db.commit()

    return {
        "status": "ok",
        "ingested": total_ingested,
        "year": year,
        "quarter": quarter,
    }


# ── (3) 부트스트랩 유틸 ────────────────────────────────────────────────────────
async def _is_done(db: AsyncSession, key: str) -> bool:
    res = await db.execute(
        select(IngestLog).where(IngestLog.source == key, IngestLog.status == "done")
    )
    return res.scalar_one_or_none() is not None


async def _mark(db: AsyncSession, key: str, status: str) -> None:
    db.add(IngestLog(source=key, status=status))
    await db.commit()


async def bootstrap_suseong(db: AsyncSession) -> dict:
    """
    설정된 범위(연/분기) 전체를 자동 적재.
    - 이미 성공한 키는 패스
    - 실패는 error:* 로 남겨 재시도 판별
    """
    y_from = settings.SUSEONG_BOOTSTRAP_YEAR_FROM
    y_to = settings.SUSEONG_BOOTSTRAP_YEAR_TO
    q_to = settings.SUSEONG_BOOTSTRAP_QUARTER_TO
    page_size = settings.SUSEONG_PAGE_SIZE
    pages = settings.SUSEONG_PAGES

    total = 0
    for y in range(y_from, y_to + 1):
        qmax = q_to if y == y_to else 4
        for q in range(1, qmax + 1):
            key = f"suseong_{y}Q{q}"
            try:
                if await _is_done(db, key):
                    continue
                res = await ingest_suseong_foot_traffic(
                    db, year=y, quarter=q, pages=pages, page_size=page_size
                )
                total += res.get("ingested", 0)
                await _mark(db, key, "done")
                await asyncio.sleep(0.2)
            except Exception as e:  # 실패도 로그 남김
                await _mark(db, key, f"error:{e}")
                await asyncio.sleep(0.5)

    return {"status": "ok", "bootstrapped": total}
