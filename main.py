# main.py

from fastapi import FastAPI
from core.api.kakao_api import get_nearby_cafes
from core.analysis.business_logic import analyze_business_area
from schemas.request import AnalysisRequest
from schemas.response import AnalysisResult, CompetitorAnalysis, ReasoningDetails
from core.db.database import get_nearby_stores, save_stores_data
from core.analysis import population_predictor

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Server is running"}

@app.post("/analyze_area/", response_model=AnalysisResult)
def analyze_area(request: AnalysisRequest):
    stores_from_db = get_nearby_stores(request.lat, request.lon)

    if not stores_from_db:
        print("데이터베이스에 데이터가 없습니다. 카카오맵 API를 호출합니다.")
        cafes_data_from_api = get_nearby_cafes(request.lat, request.lon)
        
        if cafes_data_from_api:
            save_stores_data(cafes_data_from_api)
        
        stores_to_analyze = cafes_data_from_api
    else:
        print("데이터베이스에 데이터가 있습니다. DB 데이터를 사용합니다.")
        stores_to_analyze = stores_from_db

    score, reasoning_details, competitor_info_dict = analyze_business_area(
        request.lat, request.lon, stores_to_analyze
    )

    competitor_analysis_model = CompetitorAnalysis(**competitor_info_dict)
    reasoning_details_model = ReasoningDetails(**reasoning_details)

    return AnalysisResult(
        suitability_score=int(score),
        reasoning=reasoning_details_model,
        competitor_analysis=competitor_analysis_model
    )