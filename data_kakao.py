# data_kakao.py
import requests
from datetime import datetime
from core.db.database import save_stores_data

KAKAO_API_KEY = "9a8a22a79fb31b29da45a14246b913b3"
KAKAO_API_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

def fetch_and_save_cafe_data(lat, lon):
    """
    주어진 위도와 경도를 기준으로 카카오맵 API를 호출하여 카페 데이터를 가져오고 DB에 저장합니다.
    """
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {
        'query': '카페',
        'x': lon,
        'y': lat,
        'radius': 2000,
        'category_group_code': 'CE7',
        'sort': 'distance'
    }

    try:
        response = requests.get(KAKAO_API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'documents' in data:
            stores = []
            for doc in data['documents']:
                stores.append({
                    'place_name': doc['place_name'],
                    'category_name': doc['category_name'],
                    'y': float(doc['y']),
                    'x': float(doc['x'])
                })
            
            save_stores_data(stores)
            print(f"[{datetime.now()}] {len(stores)}개의 카페 데이터를 성공적으로 저장했습니다.")
        else:
            print(f"[{datetime.now()}] 카카오 API 응답에서 유효한 데이터를 찾을 수 없습니다.")

    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] API 호출 중 오류 발생: {e}")

if __name__ == "__main__":
    # 테스트를 위한 예시: 대구 수성구의 위도와 경도
    suseong_gu_lat = 35.8361
    suseong_gu_lon = 128.6148
    
    fetch_and_save_cafe_data(suseong_gu_lat, suseong_gu_lon)
