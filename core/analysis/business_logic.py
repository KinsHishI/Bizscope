# core/analysis/business_logic.py

from typing import List, Dict
from core.analysis.population_predictor import predict_population
from datetime import datetime

FRANCHISE_LIST = [
    "스타벅스", "투썸플레이스", "이디야", "메가엠지씨커피", "컴포즈커피",
    "빽다방", "폴바셋", "할리스", "커피빈", "탐앤탐스", "파스쿠찌", "엔제리너스"
]

def flow_score(num_poi: int, transit_nodes: int) -> float:
    """유동인구와 POI 기반 점수를 계산합니다. (0.0 ~ 1.0)"""
    return min(1.0, 0.2 + 0.6 * (num_poi / 30) + 0.2 * (transit_nodes / 5))

def competition_density(competitor_count: int) -> float:
    """경쟁업체 수 기반 경쟁 밀도를 계산합니다. (0.0 ~ 1.0)"""
    return min(1.0, competitor_count / 40)

def analyze_business_area(lat: float, lon: float, nearby_cafes: List[Dict]):
    competitor_count = len(nearby_cafes)

    now = datetime.now()
    current_year = now.year
    current_quarter = (now.month - 1) // 3 + 1
    
    floating_population = predict_population(current_year, current_quarter)

    if not floating_population or floating_population == 0:
        floating_population = 50000 
        print("WARN: AI 예측에 실패하여 기본값(50000)을 사용합니다.")

    num_poi_approx = int(floating_population / 2000)
    transit_nodes_approx = int(floating_population / 10000)
    
    flow_score_result = flow_score(num_poi_approx, transit_nodes_approx)
    
    competition_score_result = competition_density(competitor_count)

    suitability_score = (flow_score_result * 0.7 - competition_score_result * 0.3) * 100
    suitability_score = max(0, min(100, suitability_score))
    

    franchise_count = sum(1 for cafe in nearby_cafes if any(cafe.get('place_name', '').strip().startswith(f) for f in FRANCHISE_LIST))
    personal_count = competitor_count - franchise_count

    reasoning_details = {
        "competitor_count": competitor_count,
        "franchise_count": franchise_count,
        "personal_count": personal_count,
        "floating_population": int(floating_population),
        "radius_km": 2
    }
    
    competitor_details = {
        "count": competitor_count,
        "types": {"franchise": franchise_count, "personal": personal_count},
        "avg_rating": 4.0
    }

    return suitability_score, reasoning_details, competitor_details