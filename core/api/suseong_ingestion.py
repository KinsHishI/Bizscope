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

load_dotenv()
RAW_KEY = os.getenv("SUSEONG_API_KEY", "")
API_KEY = RAW_KEY

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

def _ensure_env():
    if not API_KEY:
        raise RuntimeError("SUSEONG_API_KEY가 비어있습니다(.env 확인).")

def _pick_num(*candidates) -> int:
    for c in candidates:
        if c is None:
            continue
        try:
            return int(float(c))
        except Exception:
            pass
    return 0

def _pick_float(*candidates) -> float:
    for c in candidates:
        if c is None:
            continue
        try:
            return float(c)
        except Exception:
            pass
    return 0.0

def _normalize_item(it: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    name = (it.get("marketNm") or it.get("cctvNm") or it.get("name") or it.get("상권명") or "상권")
    lat = _pick_float(it.get("lat"), it.get("latitude"), it.get("위도"))
    lon = _pick_float(it.get("lon"), it.get("longitude"), it.get("경도"))
    pop = _pick_num(it.get("popuCnt"), it.get("cctvCount"), it.get("flowCnt"), it.get("total"))
    if not lat or not lon:
        return None
    return {"name": str(name).strip(), "lat": lat, "lon": lon, "pop_quarter": pop}

def _fetch_page(base_url: str, year: int, quarter: int, page: int, size: int, timeout: int = 10):
    _ensure_env()
    params = {
        "serviceKey": API_KEY,
        "startYear": str(year),     
        "startBungi": str(quarter),  
        "resultType": "json",
        "page": str(page),           
        "size": str(size),           
    }
    s = requests.Session()
    s.mount("https://", TLSv12Adapter())
    r = s.get(base_url, params=params, timeout=timeout)
    r.raise_for_status()
    try:
        data = r.json()
    except json.JSONDecodeError:
        raise RuntimeError(f"JSON 디코딩 실패: {r.text[:200]}…")
    
    items_path = data.get("response", {}).get("body", {}).get("items", {})
    items = items_path.get("item") if isinstance(items_path, dict) else items_path
    
    if not isinstance(items, list):
        return []
    return items

def fetch_quarter_all(base_url: str, year: int, quarter: int, max_pages: int = 10, size: int = 100):
    acc: List[Dict[str, Any]] = []
    for p in range(1, max_pages + 1):
        chunk = _fetch_page(base_url, year, quarter, p, size)
        if not chunk:
            break
        acc.extend(chunk)
        if len(chunk) < size:
            break
        time.sleep(0.2)
    return acc

def fetch_and_save_population_data(api_url: str, data_type: str, year: int, quarter: int):
    raw = fetch_quarter_all(api_url, year, quarter, max_pages=10, size=100)
    normed = [x for x in (_normalize_item(it) for it in raw) if x]
    saved = upsert_flow_items(year, quarter, normed, data_type) if normed else 0
    print(f"[{datetime.now()}] type={data_type}, year={year}, q={quarter}, items={len(normed)}, saved={saved}")
    return {"type": data_type, "year": year, "quarter": quarter, "items": len(normed), "saved": int(saved)}