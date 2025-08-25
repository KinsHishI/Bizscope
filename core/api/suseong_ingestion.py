# core/api/suseong_ingestion.py

import os
import ssl
import time
import json
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from dotenv import load_dotenv

from core.db.database import upsert_flow_items

# .env 파일에서 환경 변수 로드
load_dotenv()
RAW_KEY = os.getenv("SUSEONG_API_KEY", "")
API_KEY = RAW_KEY

# 일부 공공데이터 API 서버는 구형 TLS 버전을 사용하므로, TLSv1.2를 강제하는 어댑터 클래스
class TLSv12Adapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        context.minimum_protocol_version = ssl.TLSVersion.TLSv1_2
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=context
        )

# API 키가 설정되었는지 확인하는 헬퍼 함수
def _ensure_env():
    if not API_KEY:
        raise RuntimeError("SUSEONG_API_KEY가 비어있습니다(.env 확인).")

# 여러 후보 값 중에서 유효한 정수 값을 찾아 반환하는 헬퍼 함수
def _pick_num(*candidates) -> int:
    for c in candidates:
        if c is None:
            continue
        try:
            return int(float(c))
        except (ValueError, TypeError):
            pass
    return 0

# 여러 후보 값 중에서 유효한 실수 값을 찾아 반환하는 헬퍼 함수
def _pick_float(*candidates) -> float:
    for c in candidates:
        if c is None:
            continue
        try:
            return float(c)
        except (ValueError, TypeError):
            pass
    return 0.0

# API에서 받은 원본 데이터를 표준화된 형식으로 변환하는 함수
def _normalize_item(it: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # API마다 다른 필드 이름을 공통 필드 이름으로 매핑
    name = (it.get("marketNm") or it.get("cctvNm") or it.get("name") or it.get("상권명") or "상권")
    lat = _pick_float(it.get("lat"), it.get("latitude"), it.get("위도"))
    lng = _pick_float(it.get("lng"), it.get("lnggitude"), it.get("경도"))
    pop = _pick_num(it.get("popuCnt"), it.get("cctvCount"), it.get("flowCnt"), it.get("total"))
    
    # 위도 또는 경도 값이 없으면 유효하지 않은 데이터로 간주
    if not lat or not lng:
        return None
        
    return {"name": str(name).strip(), "lat": lat, "lng": lng, "pop_quarter": pop}

# 특정 페이지의 유동인구 데이터를 API에서 가져오는 함수
def _fetch_page(base_url: str, year: int, quarter: int, page: int, size: int, timeout: int = 10):
    _ensure_env()
    params = {
        "serviceKey": API_KEY,
        "startYear": str(year),      # 조회 연도
        "startBungi": str(quarter),  # 조회 분기
        "resultType": "json",
        "page": str(page),           # 페이지 번호
        "size": str(size),           # 페이지 당 항목 수
    }
    s = requests.Session()
    s.mount("https://", TLSv12Adapter()) # TLSv1.2 어댑터 사용
    r = s.get(base_url, params=params, timeout=timeout)
    r.raise_for_status() # 오류 발생 시 예외 발생
    
    try:
        data = r.json()
    except json.JSONDecodeError:
        raise RuntimeError(f"JSON 디코딩 실패: {r.text[:200]}…")
    
    # API 응답 구조가 복잡하여 안전하게 데이터 아이템에 접근
    items_path = data.get("response", {}).get("body", {}).get("items", {})
    items = items_path.get("item") if isinstance(items_path, dict) else items_path
    
    if not isinstance(items, list):
        return []
    return items

# 특정 분기의 모든 유동인구 데이터를 가져오는 함수 (여러 페이지에 걸쳐)
def fetch_quarter_all(base_url: str, year: int, quarter: int, max_pages: int = 10, size: int = 100):
    acc: List[Dict[str, Any]] = []
    for p in range(1, max_pages + 1):
        chunk = _fetch_page(base_url, year, quarter, p, size)
        if not chunk: # 더 이상 데이터가 없으면 중단
            break
        acc.extend(chunk)
        if len(chunk) < size: # 마지막 페이지이면 중단
            break
        time.sleep(0.2) # API 서버 부하를 줄이기 위해 0.2초 대기
    return acc

# 유동인구 데이터를 가져와 정제 후 DB에 저장하는 메인 함수
def fetch_and_save_population_data(api_url: str, data_type: str, year: int, quarter: int):
    raw = fetch_quarter_all(api_url, year, quarter, max_pages=10, size=100)
    normed = [x for x in (_normalize_item(it) for it in raw) if x] # 정규화 및 유효성 검사
    
    # 정규화된 데이터가 있을 경우에만 DB에 저장(upsert)
    saved = upsert_flow_items(year, quarter, normed, data_type) if normed else 0
    print(f"[{datetime.now()}] type={data_type}, year={year}, q={quarter}, items={len(normed)}, saved={saved}")
    return {"type": data_type, "year": year, "quarter": quarter, "items": len(normed), "saved": int(saved)}