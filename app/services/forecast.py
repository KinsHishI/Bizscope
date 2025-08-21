# app/services/forecast.py
# -----------------------------------------------------------------------------
# 재무 예측/ROI 계산(SARIMAX 기반) + 외생변수(foot_traffic) 결합
# - forecast_finance: 수동 입력된 시리즈로 예측
# - forecast_finance_auto: lat/lon 근처 분기 유동인구를 월로 분할해 외생변수로 결합
# -----------------------------------------------------------------------------
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from app.schemas.finance import (
    FinancePoint,
    FinanceForecastRequest,
    FinanceForecastResponse,
    FinanceForecastAutoRequest,
    FinanceForecastAutoResponse,
    ForecastItem,
)
from app.db.crud import get_places_bbox
from app.db.session import AsyncSession


# ── 유틸 ──────────────────────────────────────────────────────────────────────
@dataclass(slots=True)
class CostAssumptions:
    cogs_rate: float = 0.35
    labor_base: int = 3_200_000
    rent: int = 1_500_000
    utilities: int = 500_000
    marketing: int = 200_000


def _assumptions_to_cost(a_like) -> CostAssumptions:
    """
    Pydantic v2 모델/딕셔너리/네임스페이스 어떤 형태로 와도 CostAssumptions로 안전 변환.
    """
    if a_like is None:
        return CostAssumptions()
    # pydantic v2
    if hasattr(a_like, "model_dump"):
        data = a_like.model_dump()
    # 이미 dict
    elif isinstance(a_like, dict):
        data = a_like
    else:
        # 마지막 안전망: 필요한 필드만 뽑아서 dict화
        fields = ("cogs_rate", "labor_base", "rent", "utilities", "marketing")
        data = {k: getattr(a_like, k) for k in fields if hasattr(a_like, k)}
    return CostAssumptions(**data)


def _to_month_index(series: Sequence[FinancePoint]) -> pd.Series:
    """FinancePoint[] → pandas Series(index=Period[M], value=sales)"""
    idx = pd.PeriodIndex([p.month for p in series], freq="M")
    vals = [p.sales for p in series]
    return pd.Series(vals, index=idx)


def _calc_costs(sales: int, a: CostAssumptions) -> dict:
    cogs = int(sales * a.cogs_rate)
    return {
        "cogs": cogs,
        "labor": a.labor_base,
        "rent": a.rent,
        "utilities": a.utilities,
        "marketing": a.marketing,
        "profit": sales - (cogs + a.labor_base + a.rent + a.utilities + a.marketing),
    }


def _make_items(
    months: pd.PeriodIndex, sales: Iterable[int], a: CostAssumptions
) -> list[ForecastItem]:
    out: list[ForecastItem] = []
    for m, s in zip(months, sales):
        costs = _calc_costs(int(s), a)
        out.append(
            ForecastItem(
                month=str(m),
                sales=int(s),
                sales_pi=[int(s), int(s)],
                **costs,
            )
        )
    return out


# ── 기본 예측(SARIMAX) ────────────────────────────────────────────────────────
def forecast_finance(req: FinanceForecastRequest) -> FinanceForecastResponse:
    """
    입력 series(월 매출)만으로 12개월 예측 + 비용/이익 계산
    """
    a = _assumptions_to_cost(req.assumptions)
    y = _to_month_index(req.series)
    y = y.asfreq("M")  # 결측은 NaN

    model = SARIMAX(
        y,
        order=(1, 1, 1),
        seasonal_order=(1, 1, 1, 12),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    fit = model.fit(disp=False)
    h = req.horizon_months
    fcast = fit.get_forecast(steps=h)
    mean = fcast.predicted_mean
    months = pd.period_range(start=y.index[-1] + 1, periods=h, freq="M")

    items = _make_items(months, mean, a)

    # 단순 payback 계산
    profits = np.array([it.profit for it in items], dtype=int)
    payback = (
        int(np.argmax(np.cumsum(profits) >= req.capex) + 1)
        if profits.sum() > 0
        else 999
    )

    return FinanceForecastResponse(
        forecast=items,
        payback_month=payback,
        payback_prob_12m=min(0.998, float((profits[:12] > 0).mean())),  # 간단 지표
        model="SARIMAX(1,1,1)(1,1,1,12)",
        top_features=None,
        explain=[f"원가율 {a.cogs_rate:.2f}, 인건비 base {a.labor_base:,}"],
    )


# ── AUTO: 수성구 유동인구 → 월 분할 → 외생변수로 결합 ─────────────────────────
async def forecast_finance_auto(
    db: AsyncSession,
    req: FinanceForecastAutoRequest,
    *,
    lat: float | None,
    lon: float | None,
) -> FinanceForecastAutoResponse:
    """
    사용자가 보낸 최근 n개월 매출 + (선택) lat/lon 근처의 '분기 유동인구'를 월로 분할해 exog 구성
    """
    a = _assumptions_to_cost(req.assumptions)
    y = _to_month_index(req.series).asfreq("M")
    h = req.horizon_months

    # 1) 외생변수(exog) 준비
    exog_hist: pd.Series | None = None
    if lat is not None and lon is not None:
        d = 0.0005  # 약 100m bbox
        places = await get_places_bbox(db, lat - d, lon - d, lat + d, lon + d)
        if places:
            base_pop = max(getattr(p, "foot_traffic", 0) or 0 for p in places)
            months_pop = pd.Series([base_pop / 3] * len(y), index=y.index)
            exog_hist = months_pop

    # 2) 모델 적합
    if exog_hist is not None:
        model = SARIMAX(
            y,
            exog=exog_hist,
            order=(1, 1, 1),
            seasonal_order=(1, 1, 1, 12),
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fit = model.fit(disp=False)
        future_exog = pd.Series(
            [exog_hist.iloc[-1]] * h,
            index=pd.period_range(y.index[-1] + 1, periods=h, freq="M"),
        )
        fcast = fit.get_forecast(steps=h, exog=future_exog)
        model_name = "SARIMAX+exog(foot_traffic)"
    else:
        model = SARIMAX(
            y,
            order=(1, 1, 1),
            seasonal_order=(1, 1, 1, 12),
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fit = model.fit(disp=False)
        fcast = fit.get_forecast(steps=h)
        model_name = "SARIMAX"

    mean = fcast.predicted_mean
    months = pd.period_range(start=y.index[-1] + 1, periods=h, freq="M")
    items = _make_items(months, mean, a)

    profits = np.array([it.profit for it in items], dtype=int)
    payback = (
        int(np.argmax(np.cumsum(profits) >= req.capex) + 1)
        if profits.sum() > 0
        else 999
    )

    return FinanceForecastAutoResponse(
        forecast=items,
        payback_month=payback,
        payback_prob_12m=min(0.998, float((profits[:12] > 0).mean())),
        model=model_name,
        top_features=None,
        explain=[
            f"원가율 {a.cogs_rate:.2f}, 인건비 base {a.labor_base:,}",
            "유동인구는 분기→월 균등 분할 가정",
        ],
    )
