from pydantic import BaseModel


class ROISimRequest(BaseModel):
    monthly_sales: int
    rent: int
    cogs_rate: float = 0.35
    labor: int = 3000000
    other_cost: int = 500000
    capex: int = 30000000  # 인테리어 + 권리금


class ROISimResponse(BaseModel):
    monthly_profit: int
    payback_month: int
    margin_rate: float
