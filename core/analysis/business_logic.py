# core/analysis/business_logic.py

from typing import List, Dict

def flow_score(num_poi: int, transit_nodes: int) -> float:
    """유동인구와 POI 기반 점수를 계산합니다. (0.0 ~ 1.0)"""
    return min(1.0, 0.2 + 0.6 * (num_poi / 50) + 0.2 * (transit_nodes / 10))

def competition_density(competitor_count: int) -> float:
    """경쟁업체 수 기반 경쟁 밀도를 계산합니다. (0.0 ~ 1.0)"""
    return min(1.0, competitor_count / 10)

# ❗️ 이 부분이 3개의 인자(lat, lon, nearby_cafes)를 받도록 수정되어야 합니다.
def analyze_business_area(lat: float, lon: float, nearby_cafes: List[Dict]):
    # 1. 경쟁업체 데이터는 인자로 직접 받습니다.
    competitor_count = len(nearby_cafes)

    # 2. 유동인구 데이터는 임시값으로 설정합니다. (TODO: 실제 데이터 수집 로직 구현 필요)
    floating_population = 50000  # 임시 값

    # 3. 유동인구와 POI 기반 유동 점수 계산
    num_poi_approx = int(floating_population / 2000)
    transit_nodes_approx = int(floating_population / 10000)
    
    flow_score_result = flow_score(num_poi_approx, transit_nodes_approx)
    
    # 4. 경쟁 밀도 점수 계산
    competition_score_result = competition_density(competitor_count)

    # 5. 최종 적합도 점수 계산
    suitability_score = (flow_score_result * 0.7 - competition_score_result * 0.3) * 100
    
    suitability_score = max(0, min(100, suitability_score)) # 점수를 0과 100 사이로 고정
    
    # 6. 분석 상세 정보 생성
    franchise_count = sum(1 for cafe in nearby_cafes if "스타벅스" in cafe.get('place_name', '') or "투썸플레이스" in cafe.get('place_name', ''))
    personal_count = competitor_count - franchise_count

    reasoning_details = {
        "competitor_count": competitor_count,
        "franchise_count": franchise_count,
        "personal_count": personal_count,
        "floating_population": floating_population,
        "radius_km": 2
    }
    
    competitor_details = {
        "count": competitor_count,
        "types": {"franchise": franchise_count, "personal": personal_count},
        "avg_rating": 4.0
    }

    return suitability_score, reasoning_details, competitor_details