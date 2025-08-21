# app/schemas/finance.py
# -----------------------------------------------------------------------------
# 재무 예측용 스키마
# -----------------------------------------------------------------------------
from pydantic import BaseModel, Field
from typing import List, Optional


class FinancePoint(BaseModel):
    month: str  # "YYYY-MM"
    sales: int


class FinanceAssumption(BaseModel):
    cogs_rate: float = 0.35
    labor_base: int = 3_200_000
    rent: int = 1_500_000
    utilities: int = 500_000
    marketing: int = 200_000


class FinanceForecastRequest(BaseModel):
    series: List[FinancePoint] = Field(min_length=3)  # 최소 3개월 권장
    capex: int
    horizon_months: int = 12
    assumptions: Optional[FinanceAssumption] = None


class ForecastItem(BaseModel):
    month: str
    sales: int
    sales_pi: List[int]  # [low, high] 자리만 유지(간단 버전)
    cogs: int
    labor: int
    rent: int
    utilities: int
    marketing: int
    profit: int


class FinanceForecastResponse(BaseModel):
    forecast: List[ForecastItem]
    payback_month: int
    payback_prob_12m: float
    model: str
    top_features: Optional[List[str]] = None
    explain: List[str]


# AUTO (lat/lon 옵션)
class FinanceForecastAutoRequest(BaseModel):
    series: List[FinancePoint] = Field(min_length=3)
    capex: int
    horizon_months: int = 12
    assumptions: Optional[FinanceAssumption] = None


class FinanceForecastAutoResponse(FinanceForecastResponse):
    pass
