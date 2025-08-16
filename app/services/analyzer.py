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

# MVP용 휴리스틱 분석기
CATEGORIES = ["카페", "분식", "편의점"]


async def analyze(
    req: AnalysisRequest, nearby_places: list, transit_nodes: int = 2
) -> AnalysisResponse:
    flow = flow_score(num_poi=len(nearby_places), transit_nodes=transit_nodes)

    fit_list: List[FitItem] = []
    for c in req.candidate_categories:
        comp = competition_density(nearby_places, c)
        score = int(100 * (0.6 * flow + 0.4 * (1 - comp)))
        fit_list.append(FitItem(category=c, score=score))

    fit_list.sort(key=lambda x: x.score, reverse=True)

    # 간이 매출 추정(벤치마크: 기준매출 1500만원)
    top = fit_list[0]
    base = 15000000
    monthly_sales = int(base * (0.8 + 0.4 * flow) * (0.9 + 0.2 * (top.score / 100)))
    ci = (int(monthly_sales * 0.85), int(monthly_sales * 1.15))

    # ROI 시뮬 (월세 추정: 입력 or 150만원)
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

    area_features = {"flow_score": round(flow, 2), "poi_count": len(nearby_places)}

    explain = [
        f"유동 합성점수 {area_features['flow_score']}",
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
