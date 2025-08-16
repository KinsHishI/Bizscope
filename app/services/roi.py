from app.schemas.simulate import ROISimRequest, ROISimResponse


def simulate_roi(req: ROISimRequest) -> ROISimResponse:
    cogs = int(req.monthly_sales * req.cogs_rate)
    opex = req.rent + req.labor + req.other_cost + cogs
    profit = req.monthly_sales - opex
    margin = (profit / req.monthly_sales) if req.monthly_sales else 0.0
    payback = max(1, int(req.capex / max(1, profit))) if profit > 0 else 999
    return ROISimResponse(
        monthly_profit=profit, payback_month=payback, margin_rate=round(margin, 3)
    )
