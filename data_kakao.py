# data_kakao.py

from datetime import datetime
from core.db.database import save_stores_data
from core.api.kakao_api import get_nearby_cafes

def fetch_and_save_all_cafe_data(lat, lon):
    """
    주어진 위도/경도 기준 주변 모든 카페(최대 45개)를 가져와 DB에 저장합니다.
    """
    print(f"[{datetime.now()}] 주변 카페 데이터 수집을 시작합니다 (최대 45개)...")

    cafes_data = get_nearby_cafes(lat, lon)
    
    if cafes_data:
        stores_to_save = []
        for doc in cafes_data:
            stores_to_save.append({
                'place_name': doc.get('place_name'),
                'category_name': doc.get('category_name'),
                'y': float(doc.get('y')),
                'x': float(doc.get('x'))
            })

        save_stores_data(stores_to_save)
        print(f"[{datetime.now()}] {len(stores_to_save)}개의 카페 데이터를 성공적으로 저장했습니다.")
    else:
        print(f"[{datetime.now()}] 카카오 API에서 유효한 데이터를 찾을 수 없습니다.")

if __name__ == "__main__":
    # 테스트를 위한 예시: 대구 수성구의 위도와 경도
    suseong_gu_lat = 35.8361
    suseong_gu_lon = 128.6148
    
    fetch_and_save_all_cafe_data(suseong_gu_lat, suseong_gu_lon)