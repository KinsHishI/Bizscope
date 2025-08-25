# app/routers/finance.py
# -----------------------------------------------------------------------------
# /finance/forecast   : 유동인구(exog) 자동 결합 예측
# -----------------------------------------------------------------------------
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.schemas.finance import FinanceForecastAutoRequest, FinanceForecastAutoResponse
from app.services.forecast import forecast_finance_auto

router = APIRouter(prefix="/finance", tags=["finance"])


@router.post("/forecast_auto", response_model=FinanceForecastAutoResponse)
async def forecast_auto(
    req: FinanceForecastAutoRequest, db: AsyncSession = Depends(get_session)
):

    try:
        lat = getattr(req, "lat", None)
        lon = getattr(req, "lon", None)
        return await forecast_finance_auto(db, req, lat=lat, lon=lon)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
