# app/routers/finance.py
# -----------------------------------------------------------------------------
# /finance/forecast        : 수동 시계열 기반 예측
# /finance/forecast_auto   : 유동인구(exog) 자동 결합 예측 (lat/lon 옵션)
# -----------------------------------------------------------------------------
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.finance import (
    FinanceForecastRequest,
    FinanceForecastResponse,
    FinanceForecastAutoRequest,
    FinanceForecastAutoResponse,
)
from app.services.forecast import forecast_finance, forecast_finance_auto
from app.db.session import get_session

router = APIRouter(prefix="/finance", tags=["finance"])


@router.post("/forecast", response_model=FinanceForecastResponse)
async def forecast(req: FinanceForecastRequest) -> FinanceForecastResponse:
    try:
        return forecast_finance(req)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.post("/forecast_auto", response_model=FinanceForecastAutoResponse)
async def forecast_auto(
    req: FinanceForecastAutoRequest,
    lat: float | None = Query(None, description="옵션: 중심 위도"),
    lon: float | None = Query(None, description="옵션: 중심 경도"),
    db: AsyncSession = Depends(get_session),
) -> FinanceForecastAutoResponse:
    try:
        return await forecast_finance_auto(db, req, lat=lat, lon=lon)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
