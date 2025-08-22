import os
from datetime import datetime
from dotenv import load_dotenv
from core.api.suseong_ingestion import fetch_and_save_population_data

load_dotenv()

def run_data_ingestion():
    """
    주간, 상권 유동인구 데이터를 과거부터 현재까지 모두 가져와 DB에 저장합니다.
    """
    print("공공데이터 API에서 모든 종류의 유동인구 데이터 수집을 시작합니다...")
    
    data_sources = {
        "daytime": "https://apis.data.go.kr/3460000/suseongfpa/viewdaypopudetail",
        "commercial": "https://apis.data.go.kr/3460000/suseongfpa/viewmarketpopudetail"
    }
    
   
    start_year = 2021
    start_quarter = 4
    
   
    now = datetime.now()
    current_year = now.year
    current_quarter = (now.month - 1) // 3 + 1
    
    year, quarter = start_year, start_quarter
    
   
    while year < current_year or (year == current_year and quarter <= current_quarter):
     
        for data_type, api_url in data_sources.items():
            print(f"--> {year}년 {quarter}분기 [{data_type}] 데이터 수집 중...")
            fetch_and_save_population_data(api_url, data_type, year=year, quarter=quarter)
        
       
        quarter += 1
        if quarter > 4:
            quarter = 1
            year += 1
            
    print("모든 기간의 데이터 수집 완료.")

if __name__ == "__main__":
    run_data_ingestion()