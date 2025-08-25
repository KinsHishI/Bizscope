import sqlite3
import requests
from typing import List, Dict
from datetime import datetime
from app.core.config import settings
from app.services.population_predictor import predict_population

DATABASE_NAME = "space.db"
KAKAO_API_KEY = settings.KAKAO_API_KEY


FRANCHISE_LIST = [
    "스타벅스",
    "투썸플레이스",
    "이디야",
    "메가엠지씨커피",
    "컴포즈커피",
    "빽다방",
    "폴바셋",
    "할리스",
    "커피빈",
    "탐앤탐스",
    "파스쿠찌",
    "엔제리너스",
]


def flow_score(num_poi: int, transit_nodes: int) -> float:
    return min(1.0, 0.2 + 0.6 * (num_poi / 30) + 0.2 * (transit_nodes / 5))


def competition_density(competitor_count: int) -> float:
    return min(1.0, competitor_count / 40)


def analyze_business_area(lat: float, lon: float, nearby_cafes: List[Dict]):
    competitor_count = len(nearby_cafes)

    now = datetime.now()
    pop = predict_population(now.year, (now.month - 1) // 3 + 1) or 0.0
    if pop <= 0:
        pop = 50_000

    num_poi_approx = int(pop / 2000)
    transit_nodes_approx = int(pop / 10000)

    flow = flow_score(num_poi_approx, transit_nodes_approx)
    comp = competition_density(competitor_count)

    suitability = (flow * 0.7 - comp * 0.3) * 100
    suitability = max(0, min(100, suitability))

    franchise_count = sum(
        1
        for c in nearby_cafes
        if any((c.get("name") or "").startswith(f) for f in FRANCHISE_LIST)
    )
    personal_count = competitor_count - franchise_count

    reasoning = {
        "competitor_count": competitor_count,
        "franchise_count": franchise_count,
        "personal_count": personal_count,
        "floating_population": int(pop),
        "radius_km": 2,
    }
    competitor = {
        "count": competitor_count,
        "types": {"franchise": franchise_count, "personal": personal_count},
        "avg_rating": 4.0,
    }
    return int(suitability), reasoning, competitor


def get_nearby_stores(lat, lng, radius_km=2):
    """
    특정 위치(lat, lng) 반경 내에 있는 상점 데이터를 가져옵니다.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *,
            (
                6371 * acos(
                    cos(radians(?)) * cos(radians(y)) * cos(radians(x) - radians(?)) +
                    sin(radians(?)) * sin(radians(y))
                )
            ) AS distance_km
            FROM stores
            HAVING distance_km <= ?
            ORDER BY distance_km
        """,
            (lat, lng, lat, radius_km),
        )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def save_stores_data(records):
    """
    상점 데이터를 DB에 저장합니다.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO stores (place_name, category_name, y, x)
            VALUES (:place_name, :category_name, :y, :x)
        """,
            records,
        )
        conn.commit()
    print(f"✅ Saved {len(records)} store records.")


def get_nearby_cafes(lat: float, lng: float, radius_m=2000):
    """
    카카오맵 API로 반경 내 카페를 가져옵니다.
    """
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}

    all_cafes = []
    page = 1

    while True:
        params = {
            "category_group_code": "CE7",
            "x": lng,
            "y": lat,
            "radius": radius_m,
            "sort": "distance",
            "page": page,
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            cafes_on_page = data.get("documents", [])
            if not cafes_on_page:
                break

            all_cafes.extend(cafes_on_page)

            if data["meta"]["is_end"] or page >= 3:
                break

            page += 1

        except requests.exceptions.RequestException as e:
            print(f"❌ Kakao API error (page {page}): {e}")
            break

    return all_cafes
