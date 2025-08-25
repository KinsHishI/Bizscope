from typing import List, Dict
from datetime import datetime
from app.services.population_predictor import predict_population

FRANCHISE_LIST = [
    "스타벅스",
    "투썸플레이스",
    "이디야",
    "메가엠지씨커피",
    "컴포즈커피",
    "빽다방",
    "폴바셋",
    "할리스",
    "커피빈",
    "탐앤탐스",
    "파스쿠찌",
    "엔제리너스",
]


def flow_score(num_poi: int, transit_nodes: int) -> float:
    return min(1.0, 0.2 + 0.6 * (num_poi / 30) + 0.2 * (transit_nodes / 5))


def competition_density(competitor_count: int) -> float:
    return min(1.0, competitor_count / 40)


def analyze_business_area(lat: float, lon: float, nearby_cafes: List[Dict]):
    competitor_count = len(nearby_cafes)

    now = datetime.now()
    pop = predict_population(now.year, (now.month - 1) // 3 + 1) or 0.0
    if pop <= 0:
        pop = 50_000  # fallback

    num_poi_approx = int(pop / 2000)
    transit_nodes_approx = int(pop / 10000)

    flow = flow_score(num_poi_approx, transit_nodes_approx)
    comp = competition_density(competitor_count)

    suitability = (flow * 0.7 - comp * 0.3) * 100
    suitability = max(0, min(100, suitability))

    franchise_count = sum(
        1
        for c in nearby_cafes
        if any((c.get("name") or "").startswith(f) for f in FRANCHISE_LIST)
    )
    personal_count = competitor_count - franchise_count

    reasoning = {
        "competitor_count": competitor_count,
        "franchise_count": franchise_count,
        "personal_count": personal_count,
        "floating_population": int(pop),
        "radius_km": 2,
    }
    competitor = {
        "count": competitor_count,
        "types": {"franchise": franchise_count, "personal": personal_count},
        "avg_rating": 4.0,
    }
    return int(suitability), reasoning, competitor
