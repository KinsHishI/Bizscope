import sqlite3

DATABASE_NAME = "business_data.db"

def init_db():
    """
    데이터베이스를 초기화하고 필요한 테이블을 생성합니다.
    stores: 경쟁업체(카페) 정보
    floating_population: 유동인구 정보
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        
      
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                place_name TEXT NOT NULL,
                category_name TEXT,
                y REAL,
                x REAL
            )
        """)
        
      
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS floating_population (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region_id TEXT NOT NULL,
                date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                population_count INTEGER NOT NULL,
                data_type TEXT NOT NULL,
                UNIQUE(region_id, date, data_type)
            )
        """)
        conn.commit()
    print("Database initialized successfully.")

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

def get_nearby_stores(lat, lon, radius_km=2):
    """
    특정 위치(lat, lon) 반경 내에 있는 상점 데이터를 가져옵니다.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
       
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Haversine 공식을 사용해 거리 계산 (SQLite는 WHERE절에서 별칭 사용 가능)
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
        """, (lat, lon, lat, radius_km))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def save_stores_data(records):
    """
    상점(카페) 데이터를 데이터베이스에 저장합니다.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO stores (place_name, category_name, y, x)
            VALUES (:place_name, :category_name, :y, :x)
        """, records)
        conn.commit()
    print(f"Successfully saved {len(records)} store records.")
    
def get_nearest_population(lat: float, lon: float):
    """
    주어진 위치에서 가장 가까운 유동인구를 찾습니다.
    1순위로 '상권(commercial)' 데이터를, 없을 경우 2순위로 '주간(daytime)' 데이터를 조회합니다.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT population_count
            FROM floating_population
            WHERE data_type = 'commercial'
            ORDER BY (
                6371 * acos(
                    cos(radians(?)) * cos(radians(lat)) * cos(radians(lon) - radians(?)) + 
                    sin(radians(?)) * sin(radians(lat))
                )
            )
            LIMIT 1
        """, (lat, lon, lat))
        
        result = cursor.fetchone()
        
        if result:
            return result[0]
            
        print("WARN: 주변 상권 유동인구 데이터가 없어, 주간 유동인구 데이터로 대체합니다.")
        cursor.execute("""
            SELECT population_count
            FROM floating_population
            WHERE data_type = 'daytime'
            ORDER BY (
                6371 * acos(
                    cos(radians(?)) * cos(radians(lat)) * cos(radians(lon) - radians(?)) + 
                    sin(radians(?)) * sin(radians(lat))
                )
            )
            LIMIT 1
        """, (lat, lon, lat))
        
        result = cursor.fetchone()
        
        if result:
            return result[0]
            
    return 0

def get_nearest_population(lat: float, lon: float):
    """
    주어진 위치에서 가장 가까운 '상권' 유동인구를 찾고, 없으면 '주간' 유동인구를 찾습니다.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        
        # Haversine 공식을 사용해 가장 가까운 1개의 데이터 선택
        cursor.execute("""
            SELECT population_count
            FROM floating_population
            ORDER BY (
                6371 * acos(
                    cos(radians(?)) * cos(radians(lat)) * cos(radians(lon) - radians(?)) + 
                    sin(radians(?)) * sin(radians(lat))
                )
            )
            LIMIT 1
        """, (lat, lon, lat))
        
        result = cursor.fetchone()
        
        if result:
            return result[0]
        return 0

def upsert_flow_items(year, quarter, items, data_type): 
    """
    주어진 데이터를 'floating_population' 테이블에 upsert합니다.
    (ON CONFLICT 구문을 사용해 중복된 데이터는 업데이트합니다)
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        for item in items:
            cursor.execute("""
                INSERT INTO floating_population (region_id, date, time_slot, population_count, data_type)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(region_id, date, data_type) DO UPDATE SET
                population_count=excluded.population_count
            """, (
                item.get('name'), 
                f'{year}-{quarter}', 
                'quarter_total', 
                item.get('pop_quarter'), 
                data_type  
            ))
        conn.commit()
        return len(items)

if __name__ == '__main__':
    init_db()
