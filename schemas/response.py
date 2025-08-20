# schemas/response.py
from pydantic import BaseModel
from typing import Dict, Optional

class CompetitorAnalysis(BaseModel):
    count: int
    types: Dict[str, int]
    avg_rating: Optional[float] = None

# 새롭게 추가할 모델
class ReasoningDetails(BaseModel):
    competitor_count: int
    franchise_count: int
    personal_count: int
    floating_population: int
    radius_km: int = 2 # 기본값 추가

class AnalysisResult(BaseModel):
    suitability_score: int
    # reasoning 필드 타입을 str에서 ReasoningDetails로 변경
    reasoning: ReasoningDetails 
    competitor_analysis: CompetitorAnalysis