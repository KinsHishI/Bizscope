# app/routers/admin.py
# -----------------------------------------------------------------------------
# 부트스트랩/수동 적재/로그 조회
# -----------------------------------------------------------------------------
import traceback
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.db.models import IngestLog
from app.services.ingest import load_mock, ingest_suseong_foot_traffic

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/ingest/mock")
async def ingest_mock(db: AsyncSession = Depends(get_session)):
    try:
        await load_mock(db)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(500, detail=f"{e}\n{traceback.format_exc()}")


@router.post("/ingest/suseong")
async def ingest_suseong(
    year: int = Query(..., ge=2018, le=2100),
    quarter: int = Query(..., ge=1, le=4),
    pages: int = Query(5, ge=1, le=100),
    page_size: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_session),
):
    try:
        return await ingest_suseong_foot_traffic(
            db, year=year, quarter=quarter, pages=pages, page_size=page_size
        )
    except Exception as e:
        raise HTTPException(500, detail=f"{e}\n{traceback.format_exc()}")


@router.get("/logs")
async def get_ingest_logs(db: AsyncSession = Depends(get_session)):
    res = await db.execute(select(IngestLog))
    logs = res.scalars().all()
    return [{"id": x.id, "source": x.source, "status": x.status} for x in logs]
