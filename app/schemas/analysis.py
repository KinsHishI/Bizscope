# app/schemas/analysis.py

from pydantic import BaseModel, Field
from typing import Dict, Optional


class AnalysisRequest(BaseModel):
    lat: float
    lon: float
    radius_m: int = Field(2000, ge=100, le=5000)


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
    lon: float
