from pydantic import BaseModel, Field
from typing import List, Literal


class AnalysisRequest(BaseModel):
    lat: float
    lon: float
    radius_m: int = Field(500, ge=100, le=2000)  # 분석 반경
    budget_month_rent: int | None = None
    candidate_categories: List[str] = ["카페", "분식", "편의점"]


class FitItem(BaseModel):
    category: str
    score: int  # 0~100


class SalesPred(BaseModel):
    monthly: int
    ci: tuple[int, int]


class ROI(BaseModel):
    payback_month: int
    margin_rate: float


class AnalysisResponse(BaseModel):
    area_features: dict
    fit: List[FitItem]
    sales_pred: SalesPred
    costs: dict
    roi: ROI
    explain: List[str]
