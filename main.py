# main.py

from fastapi import FastAPI
from core.api.kakao_api import get_nearby_cafes
from core.analysis.business_logic import analyze_business_area
from schemas.request import AnalysisRequest
from schemas.response import AnalysisResult, CompetitorAnalysis, ReasoningDetails
from core.db.database import get_nearby_stores, save_stores_data

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Server is running"}

@app.post("/analyze_area/", response_model=AnalysisResult)
def analyze_area(request: AnalysisRequest):
    # 1. 데이터베이스에서 주변 상점 데이터를 조회합니다.
    stores_from_db = get_nearby_stores(request.lat, request.lon)

    # 2. 만약 DB에 데이터가 없으면, 카카오맵 API를 호출합니다.
    if not stores_from_db:
        print("데이터베이스에 데이터가 없습니다. 카카오맵 API를 호출합니다.")
        cafes_data_from_api = get_nearby_cafes(request.lat, request.lon)
        
        # 3. API에서 받은 데이터를 DB에 저장합니다.
        if cafes_data_from_api:
            save_stores_data(cafes_data_from_api)
        
        # 4. 분석을 위해 API 데이터를 사용합니다.
        stores_to_analyze = cafes_data_from_api
    else:
        print("데이터베이스에 데이터가 있습니다. DB 데이터를 사용합니다.")
        stores_to_analyze = stores_from_db

    # 5. 수집된 데이터(stores_to_analyze)를 비즈니스 로직 함수에 전달합니다. (수정된 부분)
    score, reasoning_details, competitor_info_dict = analyze_business_area(
        request.lat, request.lon, stores_to_analyze
    )

    # 6. 딕셔너리를 Pydantic 모델로 변환
    competitor_analysis_model = CompetitorAnalysis(**competitor_info_dict)
    reasoning_details_model = ReasoningDetails(**reasoning_details)

    # 7. 최종 결과 반환 (점수를 int로 변환)
    return AnalysisResult(
        suitability_score=int(score),
        reasoning=reasoning_details_model,
        competitor_analysis=competitor_analysis_model
    )