# data_ingestion.py

import os
from datetime import datetime
from dotenv import load_dotenv
from core.api.suseong_ingestion import fetch_and_save_population_data

load_dotenv()

def run_data_ingestion():
    """
    주간, 상권 유동인구 데이터를 과거부터 현재까지 모두 가져와 DB에 저장하는 전체 프로세스를 실행합니다.
    """
    print("공공데이터 API에서 모든 종류의 유동인구 데이터 수집을 시작합니다...")
    
    # 수집할 데이터의 종류와 API URL을 정의
    data_sources = {
        "daytime": "https://apis.data.go.kr/3460000/suseongfpa/viewdaypopudetail",
        "commercial": "https://apis.data.go.kr/3460000/suseongfpa/viewmarketpopudetail"
    }
    
    # 데이터 수집 시작 시점 정의
    start_year = 2021
    start_quarter = 4
    
    # 현재 시점의 연도와 분기 계산
    now = datetime.now()
    current_year = now.year
    current_quarter = (now.month - 1) // 3 + 1
    
    year, quarter = start_year, start_quarter
    
    # 시작 시점부터 현재 시점까지 반복
    while year < current_year or (year == current_year and quarter <= current_quarter):
        # 정의된 모든 데이터 소스(주간, 상권)에 대해 데이터 수집 실행
        for data_type, api_url in data_sources.items():
            print(f"--> {year}년 {quarter}분기 [{data_type}] 데이터 수집 중...")
            fetch_and_save_population_data(api_url, data_type, year=year, quarter=quarter)
        
        # 다음 분기로 이동
        quarter += 1
        if quarter > 4:
            quarter = 1
            year += 1
            
    print("모든 기간의 데이터 수집 완료.")

if __name__ == "__main__":
    # 이 스크립트를 직접 실행하면 데이터 수집 프로세스 시작
    run_data_ingestion()