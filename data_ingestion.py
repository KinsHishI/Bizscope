# data_ingestion.py
import requests
import json
from datetime import datetime
import ssl
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

# ❗ 오래된 시스템 환경에서 최신 TLS 버전을 강제하기 위한 클래스
class TLSv12Adapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=ssl.PROTOCOL_TLSv1_2
        )

API_KEY = "99f35826b78e6d4ae93b2777b6dcd30bfc588f55374c8683f069e02b419d213d"
BASE_URL = "https://apis.data.go.kr/3460000/suseongfpa/viewdaypopudetail"

def fetch_and_save_population_data():
    """
    API를 호출하여 주간 유동인구 데이터를 가져오고 DB에 저장합니다.
    """
    params = {
        'serviceKey': API_KEY,
        'startYear': '2021',
        'startBungi': '4',
        'resultType': 'json',
        'page': '1',
        'size': '100'
    }

    # ❗ TLSv1.2 어댑터를 사용하는 세션을 생성
    session = requests.Session()
    session.mount('https://', TLSv12Adapter())
    
    try:
        # ❗ 기본 requests.get 대신 위에서 만든 session.get을 사용
        response = session.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'response' in data and 'body' in data['response'] and 'items' in data['response']['body']:
            body = data['response']['body']
            report_date = body.get('bungiNm1')
            
            population_records = []
            for item in body['items']:
                record = {
                    'region_id': item.get('cctvUid'),
                    'date': report_date,
                    'time_slot': 'daytime',
                    'population_count': item.get('cctvCount')
                }
                population_records.append(record)

            print(f"[{datetime.now()}] {len(population_records)}개의 주간 유동인구 데이터를 성공적으로 처리했습니다.")
        else:
            print(f"[{datetime.now()}] API 응답에서 유효한 데이터를 찾을 수 없습니다.")
            print("API 응답 내용:", data)
            
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] API 호출 중 오류 발생: {e}")
    except json.JSONDecodeError:
        print(f"[{datetime.now()}] JSON 디코딩 오류 발생")
        print("응답 내용:", response.text)

if __name__ == "__main__":
    fetch_and_save_population_data()