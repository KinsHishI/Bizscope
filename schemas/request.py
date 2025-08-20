# schemas/request.py
# 사용자 입력을 받을 모델을 만들기
from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    budget: int
    lat: float
    lon: float