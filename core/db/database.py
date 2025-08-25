# core/db/database.py

import sqlite3

DATABASE_NAME = "business_data.db"

def init_db():
    """
    데이터베이스를 초기화하고 필요한 테이블을 생성합니다.
    - stores: 경쟁업체(카페) 정보 저장
    - floating_population: 유동인구 정보 저장
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        
        # 경쟁업체 정보 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                place_name TEXT NOT NULL,
                category_name TEXT,
                y REAL, -- 위도 (latitude)
                x REAL  -- 경도 (longitude)
            )
        """)
        
        # 유동인구 데이터 테이블
        # floating_population 테이블에 위도(lat), 경도(lng) 컬럼 추가가 필요해 보입니다.
        # 현재 get_nearest_population 함수에서 lat, lng를 사용하려고 하지만 스키마에 없습니다.
        # (아래 upsert_flow_items를 보니 region_id에 상권 이름이 들어가고, lat/lng는 저장되지 않음)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS floating_population (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region_id TEXT NOT NULL,  -- 지역/상권 이름
                date TEXT NOT NULL,       -- 연도-분기 (예: '2023-4')
                time_slot TEXT NOT NULL,  -- 시간대 (여기서는 'quarter_total'로 고정)
                population_count INTEGER NOT NULL, -- 분기별 유동인구 수
                data_type TEXT NOT NULL,  -- 데이터 종류 ('daytime', 'commercial')
                lat REAL,                 -- 위도 (추가됨)
                lng REAL,                 -- 경도 (추가됨)
                UNIQUE(region_id, date, data_type) -- 중복 데이터 방지
            )
        """)
        conn.commit()
    print("Database initialized successfully.")


# 참고: 이 함수는 현재 코드에서 사용되지 않지만, 일반적인 INSERT 용도로 구현되어 있습니다.
def save_population_data(records):
    """
    유동인구 데이터를 데이터베이스에 저장합니다.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO floating_population (region_id, date, time_slot, population_count)
            VALUES (:region_id, :date, :time_slot, :population_count)
        """, records)
        conn.commit()
    print(f"Successfully saved {len(records)} population records.")


def get_nearby_stores(lat, lng, radius_km=2):
    """
    특정 위치(lat, lng) 반경 내에 있는 상점 데이터를 DB에서 가져옵니다.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.row_factory = sqlite3.Row  # 결과를 딕셔너리처럼 접근 가능하게 설정
        cursor = conn.cursor()
        
        # Haversine 공식을 사용하여 두 지점 간의 거리를 킬로미터 단위로 계산
        # 이 공식은 지구의 곡률을 고려하여 위도/경도 간의 거리를 정확하게 계산합니다.
        cursor.execute("""
            SELECT *,
            (
                6371 * acos(
                    cos(radians(?)) * cos(radians(y)) * cos(radians(x) - radians(?)) + 
                    sin(radians(?)) * sin(radians(y))
                )
            ) AS distance_km
            FROM stores
            WHERE distance_km <= ?
            ORDER BY distance_km
        """, (lat, lng, lat, radius_km))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def save_stores_data(records):
    """
    상점(카페) 데이터를 데이터베이스에 저장합니다.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        # API 응답 필드명('y', 'x')에 맞춰서 데이터를 저장합니다.
        cursor.executemany("""
            INSERT INTO stores (place_name, category_name, y, x)
            VALUES (:place_name, :category_name, :y, :x)
        """, records)
        conn.commit()
    print(f"Successfully saved {len(records)} store records.")

# 참고: 아래 함수는 중복으로 정의되어 있습니다. 하나는 삭제하는 것이 좋습니다.
# 이 버전은 'commercial' 데이터를 우선 조회하고, 없으면 'daytime' 데이터를 조회하는 로직을 가집니다.
def get_nearest_population_with_fallback(lat: float, lng: float):
    """
    주어진 위치에서 가장 가까운 유동인구를 찾습니다.
    1순위로 '상권(commercial)' 데이터를, 없을 경우 2순위로 '주간(daytime)' 데이터를 조회합니다.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        
        # 1. 'commercial' 데이터 타입에서 가장 가까운 데이터 조회
        cursor.execute("""
            SELECT population_count
            FROM floating_population
            WHERE data_type = 'commercial'
            ORDER BY (
                6371 * acos( cos(radians(?)) * cos(radians(lat)) * cos(radians(lng) - radians(?)) + sin(radians(?)) * sin(radians(lat)) )
            )
            LIMIT 1
        """, (lat, lng, lat))
        
        result = cursor.fetchone()
        if result:
            return result[0]
            
        # 2. 'commercial' 데이터가 없을 경우, 'daytime' 데이터로 대체 조회
        print("WARN: 주변 상권 유동인구 데이터가 없어, 주간 유동인구 데이터로 대체합니다.")
        cursor.execute("""
            SELECT population_count
            FROM floating_population
            WHERE data_type = 'daytime'
            ORDER BY (
                6371 * acos( cos(radians(?)) * cos(radians(lat)) * cos(radians(lng) - radians(?)) + sin(radians(?)) * sin(radians(lat)) )
            )
            LIMIT 1
        """, (lat, lng, lat))
        
        result = cursor.fetchone()
        if result:
            return result[0]
            
        return 0

# 이 함수는 데이터 타입('commercial', 'daytime')을 구분하지 않고 가장 가까운 데이터를 조회합니다.
def get_nearest_population(lat: float, lng: float):
    """
    주어진 위치에서 가장 가까운 유동인구 데이터를 찾습니다. (데이터 타입 무관)
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        
        # Haversine 공식을 사용하여 가장 가까운 1개의 데이터 선택
        cursor.execute("""
            SELECT population_count
            FROM floating_population
            ORDER BY (
                6371 * acos(
                    cos(radians(?)) * cos(radians(lat)) * cos(radians(lng) - radians(?)) + 
                    sin(radians(?)) * sin(radians(lat))
                )
            )
            LIMIT 1
        """, (lat, lng, lat))
        
        result = cursor.fetchone()
        
        if result:
            return result[0]
        return 0

def upsert_flow_items(year, quarter, items, data_type): 
    """
    주어진 데이터를 'floating_population' 테이블에 삽입하거나 업데이트(upsert)합니다.
    UNIQUE 제약 조건(region_id, date, data_type)에 따라 동작합니다.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        for item in items:
            # ON CONFLICT: region_id, date, data_type이 동일한 데이터가 이미 존재할 경우,
            # 새로 삽입하는 대신 population_count 값을 업데이트합니다.
            cursor.execute("""
                INSERT INTO floating_population (region_id, date, time_slot, population_count, data_type, lat, lng)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(region_id, date, data_type) DO UPDATE SET
                population_count=excluded.population_count
            """, (
                item.get('name'), 
                f'{year}-{quarter}', 
                'quarter_total', 
                item.get('pop_quarter'), 
                data_type,
                item.get('lat'), # 위도 추가
                item.get('lng')  # 경도 추가
            ))
        conn.commit()
        return len(items)

if __name__ == '__main__':
    # 이 파일을 직접 실행하면 DB 초기화 수행
    init_db()