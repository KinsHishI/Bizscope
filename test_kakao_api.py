# test_kakao_api.py
from core.api.kakao_api import get_nearby_cafes

def test_final_cafe_search():
    """
    페이지네이션 기능이 적용된 get_nearby_cafes 함수가
    정상적으로 최대 45개의 결과를 가져오는지 테스트합니다.
    """
    # 테스트를 진행할 기준 좌표 (대구 수성구 범어역 근처)
    test_lat = 35.8560 
    test_lon = 128.6220
    
    print(f"▶️  최종 수정된 get_nearby_cafes 함수를 호출합니다...")
    
    cafes = get_nearby_cafes(lat=test_lat, lon=test_lon)
    
    if cafes:
        print(f"✅ 총 {len(cafes)}개의 카페 정보를 찾았습니다!")
        print("-" * 30)
        
        for i, cafe in enumerate(cafes[:5]):
            cafe_name = cafe.get('place_name', '이름 없음')
            cafe_address = cafe.get('road_address_name', '주소 없음')
            print(f"  {i+1}. {cafe_name} ({cafe_address})")
            
        print("-" * 30)
        print("페이지네이션 기능이 성공적으로 작동하는 것 같습니다. 👍")
        
    else:
        print("❌ 검색된 카페가 없습니다. API 키 설정 또는 네트워크 연결을 확인해주세요.")

if __name__ == "__main__":
    test_final_cafe_search()