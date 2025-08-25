# core/analysis/business_logic.py

from typing import List, Dict
from core.analysis.population_predictor import predict_population
from datetime import datetime

# 분석에 사용할 주요 프랜차이즈 카페 목록
FRANCHISE_LIST = [
    "스타벅스", "투썸플레이스", "이디야", "메가엠지씨커피", "컴포즈커피",
    "빽다방", "폴바셋", "할리스", "커피빈", "탐앤탐스", "파스쿠찌", "엔제리너스"
]

def flow_score(num_poi: int, transit_nodes: int) -> float:
    """
    주요 시설(POI) 수와 대중교통 노드 수를 기반으로 유동인구 점수를 계산합니다.
    점수는 0.0에서 1.0 사이의 값으로 정규화됩니다.

    Args:
        num_poi (int): 주변의 주요 시설(Point of Interest) 수.
        transit_nodes (int): 주변의 대중교통 정류장/역 수.

    Returns:
        float: 계산된 유동인구 점수 (0.0 ~ 1.0).
    """
    # 기본 점수 0.2에 POI와 대중교통 수를 가중치 적용하여 합산.
    # POI는 30개, 대중교통은 5개일 때 최대치에 가깝게 설계되었습니다.
    # min() 함수를 사용하여 점수가 1.0을 넘지 않도록 합니다.
    return min(1.0, 0.2 + 0.6 * (num_poi / 30) + 0.2 * (transit_nodes / 5))

def competition_density(competitor_count: int) -> float:
    """
    경쟁업체 수를 기반으로 경쟁 밀도 점수를 계산합니다.
    점수는 0.0에서 1.0 사이의 값으로 정규화됩니다.

    Args:
        competitor_count (int): 주변 경쟁업체(카페)의 총 수.

    Returns:
        float: 계산된 경쟁 밀도 점수 (0.0 ~ 1.0).
    """
    # 경쟁업체가 40개일 때 경쟁 밀도가 최대(1.0)가 되도록 설계되었습니다.
    return min(1.0, competitor_count / 40)

def analyze_business_area(lat: float, lng: float, nearby_cafes: List[Dict]):
    """
    주어진 좌표와 주변 카페 목록을 바탕으로 상권의 적합도를 종합적으로 분석합니다.

    Args:
        lat (float): 분석할 위치의 위도.
        lng (float): 분석할 위치의 경도.
        nearby_cafes (List[Dict]): 주변 카페 목록. 각 카페는 딕셔너리 형태입니다.

    Returns:
        tuple: (적합도 점수, 분석 근거 상세, 경쟁업체 분석 상세)
    """
    competitor_count = len(nearby_cafes)

    # 현재 날짜를 기준으로 연도와 분기를 계산
    now = datetime.now()
    current_year = now.year
    current_quarter = (now.month - 1) // 3 + 1
    
    # AI 모델을 사용하여 해당 분기의 유동인구를 예측
    floating_population = predict_population(current_year, current_quarter)

    # 예측 실패 시 기본값(50,000명)을 사용하고 경고 메시지 출력
    if not floating_population or floating_population == 0:
        floating_population = 50000 
        print("WARN: AI 예측에 실패하여 기본값(50000)을 사용합니다.")

    # 유동인구 데이터를 기반으로 POI와 대중교통 노드 수를 추정
    # 이 값들은 실제 데이터가 아닌, 유동인구를 통한 간접적인 추정치입니다.
    num_poi_approx = int(floating_population / 2000)
    transit_nodes_approx = int(floating_population / 10000)
    
    # 유동인구 점수와 경쟁 밀도 점수를 각각 계산
    flow_score_result = flow_score(num_poi_approx, transit_nodes_approx)
    competition_score_result = competition_density(competitor_count)

    # 최종 적합도 점수 계산: 유동인구 점수에 가중치 0.7, 경쟁 밀도 점수에 -0.3을 부여
    suitability_score = (flow_score_result * 0.7 - competition_score_result * 0.3) * 100
    # 점수가 0 미만이거나 100을 초과하지 않도록 조정
    suitability_score = max(0, min(100, suitability_score))
    
    # 주변 카페를 프랜차이즈와 개인 카페로 분류
    franchise_count = sum(1 for cafe in nearby_cafes if any(cafe.get('place_name', '').strip().startswith(f) for f in FRANCHISE_LIST))
    personal_count = competitor_count - franchise_count

    # 분석 결과에 대한 근거 데이터를 딕셔너리로 정리
    reasoning_details = {
        "competitor_count": competitor_count,
        "franchise_count": franchise_count,
        "personal_count": personal_count,
        "floating_population": int(floating_population),
        "radius_km": 2
    }
    
    # 경쟁업체 관련 정보를 딕셔너리로 정리 (평점은 예시로 4.0 고정)
    competitor_details = {
        "count": competitor_count,
        "types": {"franchise": franchise_count, "personal": personal_count},
        "avg_rating": 4.0
    }

    return suitability_score, reasoning_details, competitor_details