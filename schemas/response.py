# schemas/response.py
from pydantic import BaseModel
from typing import Dict, Optional

class CompetitorAnalysis(BaseModel):
    count: int
    types: Dict[str, int]
    avg_rating: Optional[float] = None

class ReasoningDetails(BaseModel):
    competitor_count: int
    franchise_count: int
    personal_count: int
    floating_population: int
    radius_km: int = 2 

class AnalysisResult(BaseModel):
    suitability_score: int
    reasoning: ReasoningDetails 
    competitor_analysis: CompetitorAnalysis
    lat: float 
    lng: float