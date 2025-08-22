# core/api/kakao_api.py

import requests
import os
from dotenv import load_dotenv

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY") 

def get_nearby_cafes(lat: float, lon: float, radius_m=2000):
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    
    all_cafes = []
    page = 1
    
    while True:
        params = {
            "category_group_code": "CE7",
            "x": lon,
            "y": lat,
            "radius": radius_m,
            "sort": "distance",
            "page": page
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            cafes_on_page = data.get('documents', [])
            if not cafes_on_page:
                break
            
            all_cafes.extend(cafes_on_page)
            
            if data['meta']['is_end'] or page >= 3:
                break

            page += 1

        except requests.exceptions.RequestException as e:
            print(f"API 호출 오류 (페이지 {page}): {e}")
            break
            
    return all_cafes