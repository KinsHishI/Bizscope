#카카오맵 API를 호출해 주변 카페 데이터를 가져오는 함수
# core/api/kakao_api.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")

def get_nearby_cafes(lat: float, lon: float, radius_m=2000):
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    params = {
        "category_group_code": "CE7",
        "x": lon,
        "y": lat,
        "radius": radius_m
    }
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json().get('documents', [])
    except requests.exceptions.RequestException as e:
        print(f"API 호출 오류: {e}")
        return []