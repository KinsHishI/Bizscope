# data_kakao.py

from datetime import datetime
from core.db.database import save_stores_data
from core.api.kakao_api import get_nearby_cafes

def fetch_and_save_all_cafe_data(lat, lng):
    """
    주어진 위도/경도 기준 주변 모든 카페(최대 45개)를 카카오 API에서 가져와 DB에 저장합니다.
    """
    print(f"[{datetime.now()}] 주변 카페 데이터 수집을 시작합니다 (최대 45개)...")

    # 카카오 API를 통해 주변 카페 데이터 가져오기
    cafes_data = get_nearby_cafes(lat, lng)
    
    if cafes_data:
        stores_to_save = []
        # API 응답 데이터를 DB 스키마에 맞는 형식으로 변환
        for doc in cafes_data:
            stores_to_save.append({
                'place_name': doc.get('place_name'),
                'category_name': doc.get('category_name'),
                'y': float(doc.get('y')), # 위도
                'x': float(doc.get('x'))  # 경도
            })

        # 변환된 데이터를 DB에 저장
        save_stores_data(stores_to_save)
        print(f"[{datetime.now()}] {len(stores_to_save)}개의 카페 데이터를 성공적으로 저장했습니다.")
    else:
        print(f"[{datetime.now()}] 카카오 API에서 유효한 데이터를 찾을 수 없습니다.")

if __name__ == "__main__":
    # 이 스크립트를 직접 실행할 때 사용할 테스트용 좌표 (대구 수성구)
    suseong_gu_lat = 35.8361
    suseong_gu_lng = 128.6148
    
    fetch_and_save_all_cafe_data(suseong_gu_lat, suseong_gu_lng)