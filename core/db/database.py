# core/db/database.py
import sqlite3
import os
import math

DB_FILE = os.path.join(os.path.dirname(__file__), 'business_data.db')

def create_connection():
    """데이터베이스 연결 객체를 생성하고 반환합니다."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except sqlite3.Error as e:
        print(f"데이터베이스 연결 오류: {e}")
        return None

def create_table():
    """상점 데이터를 저장할 테이블을 생성합니다."""
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        sql_create_table = """
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL
        );
        """
        try:
            cursor.execute(sql_create_table)
            conn.commit()
            print("stores 테이블 생성 완료!")
        except sqlite3.Error as e:
            print(f"테이블 생성 오류: {e}")
        finally:
            conn.close()

def insert_dummy_data():
    """테스트를 위한 더미 데이터를 삽입합니다."""
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        dummy_data = [
            ('스타벅스 강남점', '카페', 37.4981, 127.0276),
            ('투썸플레이스 강남점', '카페', 37.4985, 127.0280),
            ('탐앤탐스 강남점', '카페', 37.4975, 127.0285),
            ('빽다방 강남점', '카페', 37.4979, 127.0271),
            ('개인 카페 A', '카페', 37.4980, 127.0275),
            ('개인 카페 B', '카페', 37.4988, 127.0282)
        ]
        
        sql_insert = "INSERT INTO stores (name, category, latitude, longitude) VALUES (?, ?, ?, ?);"
        
        try:
            cursor.executemany(sql_insert, dummy_data)
            conn.commit()
            print("더미 데이터 삽입 완료!")
        except sqlite3.Error as e:
            print(f"데이터 삽입 오류: {e}")
        finally:
            conn.close()

def get_nearby_stores(user_lat, user_lon, radius_m=2000):
    """지정된 반경 내의 상점 데이터를 조회합니다."""
    conn = create_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        
        # 간단한 위경도 기반 반경 계산
        lat_degree_distance = radius_m / 111000.0
        lon_degree_distance = radius_m / (111000.0 * math.cos(math.radians(user_lat)))

        min_lat = user_lat - lat_degree_distance
        max_lat = user_lat + lat_degree_distance
        min_lon = user_lon - lon_degree_distance
        max_lon = user_lon + lon_degree_distance

        sql_query = """
        SELECT name, category, latitude, longitude
        FROM stores
        WHERE
            latitude BETWEEN ? AND ?
            AND longitude BETWEEN ? AND ?;
        """
        
        cursor.execute(sql_query, (min_lat, max_lat, min_lon, max_lon))
        rows = cursor.fetchall()
        
        stores_data = []
        for row in rows:
            stores_data.append({
                "place_name": row[0],
                "category_name": row[1],
                "y": row[2],  # 위도
                "x": row[3]   # 경도
            })
        
        return stores_data
    except sqlite3.Error as e:
        print(f"데이터베이스 조회 오류: {e}")
        return []
    finally:
        conn.close()

def save_stores_data(stores_list):
    """카카오맵 API에서 받은 데이터를 데이터베이스에 저장합니다."""
    conn = create_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    # 중복 삽입을 막기 위해 ON CONFLICT 절을 사용합니다.
    sql_insert = """
    INSERT INTO stores (name, category, latitude, longitude) 
    VALUES (?, ?, ?, ?)
    ON CONFLICT(name) DO NOTHING;
    """
    
    data_to_insert = []
    for store in stores_list:
        data_to_insert.append((
            store.get('place_name'),
            store.get('category_name'),
            store.get('y'),  # 'y'는 위도
            store.get('x')   # 'x'는 경도
        ))
        
    try:
        cursor.executemany(sql_insert, data_to_insert)
        conn.commit()
        print(f"{len(stores_list)}개의 데이터가 데이터베이스에 성공적으로 저장되었습니다.")
    except sqlite3.Error as e:
        print(f"데이터 저장 오류: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    create_table()
    insert_dummy_data()