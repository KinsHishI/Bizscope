# core/api/kakao_api.py

import requests
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY") 

def get_nearby_cafes(lat: float, lng: float, radius_m=2000):
    """
    카카오 로컬 API를 사용하여 특정 좌표 주변의 카페 목록을 가져옵니다.

    Args:
        lat (float): 중심점의 위도.
        lng (float): 중심점의 경도.
        radius_m (int, optional): 검색 반경(미터). 기본값은 2000m.

    Returns:
        list: 검색된 카페 정보가 담긴 딕셔너리 리스트. API 호출 실패 시 빈 리스트 반환.
    """
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    
    all_cafes = []
    page = 1
    
    # 카카오 API는 한 번에 최대 15개의 결과만 반환하므로, 반복문을 통해 여러 페이지를 조회
    while True:
        params = {
            "category_group_code": "CE7",  # CE7은 '카페' 카테고리 코드
            "x": lng,
            "y": lat,
            "radius": radius_m,
            "sort": "distance",  # 거리순으로 정렬
            "page": page
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
            data = response.json()
            
            cafes_on_page = data.get('documents', [])
            # 현재 페이지에 결과가 없으면 반복 중단
            if not cafes_on_page:
                break
            
            all_cafes.extend(cafes_on_page)
            
            # 마지막 페이지이거나, 페이지가 3에 도달하면 중단 (API 호출 제한을 위해 최대 3페이지, 45개까지만 조회)
            if data['meta']['is_end'] or page >= 3:
                break

            page += 1

        except requests.exceptions.RequestException as e:
            print(f"API 호출 오류 (페이지 {page}): {e}")
            break
            
    return all_cafes