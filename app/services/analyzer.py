# app/services/analyzer.py (핵심만)
from typing import List
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    FitItem,
    SalesPred,
    ROI,
)
from app.services.features import flow_score, competition_density
from app.services.roi import simulate_roi, ROISimRequest

CATEGORIES = ["카페", "분식", "편의점"]


async def analyze(
    req: AnalysisRequest, nearby_places: list, transit_nodes: int = 2
) -> AnalysisResponse:
    # 반경 내 평균 유동인구
    ft_vals = [p.foot_traffic for p in nearby_places if getattr(p, "foot_traffic", 0)]
    avg_ft = sum(ft_vals) / len(ft_vals) if ft_vals else 0.0

    flow = flow_score(
        num_poi=len(nearby_places), transit_nodes=transit_nodes, avg_foot_traffic=avg_ft
    )

    fit_list: List[FitItem] = []
    for c in req.candidate_categories:
        comp = competition_density(nearby_places, c)
        score = int(100 * (0.6 * flow + 0.4 * (1 - comp)))
        fit_list.append(FitItem(category=c, score=score))
    fit_list.sort(key=lambda x: x.score, reverse=True)
    top = fit_list[0]

    # 간이 매출 추정 (유동인구 보정치 포함)
    base = 15000000
    ft_boost = 0.9 + min(0.2, (avg_ft / 20000) * 0.2)  # avg_ft가 2만이면 +0.2
    monthly_sales = int(
        base * (0.8 + 0.4 * flow) * (0.9 + 0.2 * (top.score / 100)) * ft_boost
    )
    ci = (int(monthly_sales * 0.85), int(monthly_sales * 1.15))

    rent = req.budget_month_rent or 1500000
    roi_res = simulate_roi(
        ROISimRequest(
            monthly_sales=monthly_sales,
            rent=rent,
            cogs_rate=0.35,
            labor=3200000,
            other_cost=600000,
            capex=30000000,
        )
    )

    area_features = {
        "flow_score": round(flow, 2),
        "poi_count": len(nearby_places),
        "avg_foot_traffic": int(avg_ft),
    }
    explain = [
        f"유동 합성점수 {area_features['flow_score']}",
        f"평균 유동인구 {area_features['avg_foot_traffic']:,}명/분기",
        f"POI {area_features['poi_count']}개",
        f"최상위 업종 {top.category}",
    ]

    return AnalysisResponse(
        area_features=area_features,
        fit=fit_list[:3],
        sales_pred=SalesPred(monthly=monthly_sales, ci=ci),
        costs={"rent": rent, "cogs": 0.35, "labor": 3200000},
        roi=ROI(payback_month=roi_res.payback_month, margin_rate=roi_res.margin_rate),
        explain=explain,
    )
