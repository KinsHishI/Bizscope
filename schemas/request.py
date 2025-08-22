# schemas/request.py
from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    budget: int
    lat: float
    lon: float