# main.py

from fastapi import FastAPI
from core.api.kakao_api import get_nearby_cafes
from core.analysis.business_logic import analyze_business_area
from schemas.request import AnalysisRequest
from schemas.response import AnalysisResult, CompetitorAnalysis, ReasoningDetails
from core.db.database import get_nearby_stores, save_stores_data
# population_predictor 모듈은 명시적으로 사용되지는 않지만,
# analyze_business_area 내부에서 호출되므로 임포트가 필요합니다.
from core.analysis import population_predictor

app = FastAPI()

@app.get("/")
def read_root():
    """서버가 정상적으로 실행 중인지 확인하는 루트 엔드포인트입니다."""
    return {"message": "Server is running"}

@app.post("/analyze_area/", response_model=AnalysisResult)
def analyze_area(request: AnalysisRequest):
    """
    요청된 위치의 상권 분석을 수행하고 결과를 반환하는 API 엔드포인트입니다.
    """
    # 1. 데이터베이스에서 먼저 주변 상점(카페) 정보를 조회 (캐시처럼 활용)
    stores_from_db = get_nearby_stores(request.lat, request.lng)

    # 2. DB에 데이터가 없는 경우
    if not stores_from_db:
        print("데이터베이스에 데이터가 없습니다. 카카오맵 API를 호출합니다.")
        # 카카오맵 API를 호출하여 실시간으로 데이터를 가져옴
        cafes_data_from_api = get_nearby_cafes(request.lat, request.lng)
        
        # API에서 가져온 데이터가 있다면, 다음 요청을 위해 DB에 저장
        if cafes_data_from_api:
            # save_stores_data는 딕셔너리 리스트를 받으므로 포맷 변환이 필요할 수 있습니다.
            # 현재 get_nearby_cafes의 반환 형식과 save_stores_data의 입력 형식이 호환됩니다.
            stores_to_save = [
                {'place_name': c.get('place_name'), 'category_name': c.get('category_name'), 'y': float(c.get('y')), 'x': float(c.get('x'))} 
                for c in cafes_data_from_api
            ]
            save_stores_data(stores_to_save)
        
        stores_to_analyze = cafes_data_from_api
    # 3. DB에 데이터가 있는 경우
    else:
        print("데이터베이스에 데이터가 있습니다. DB 데이터를 사용합니다.")
        stores_to_analyze = stores_from_db

    # 4. 확보된 데이터를 바탕으로 상권 분석 로직 실행
    score, reasoning_details, competitor_info_dict = analyze_business_area(
        request.lat, request.lng, stores_to_analyze
    )

    # 5. 분석 결과를 Pydantic 모델에 맞춰 구조화
    competitor_analysis_model = CompetitorAnalysis(**competitor_info_dict)
    reasoning_details_model = ReasoningDetails(**reasoning_details)

    # 6. 최종 분석 결과를 클라이언트에 반환
    return AnalysisResult(
        suitability_score=int(score),
        reasoning=reasoning_details_model,
        competitor_analysis=competitor_analysis_model,
        lat=request.lat,
        lng=request.lng
    )