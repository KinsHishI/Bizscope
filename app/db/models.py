# app/db/models.py
# -----------------------------------------------------------------------------
# ORM 모델 정의
# - Place: 상권/공실/지점 등 '장소' 테이블
# - IngestLog: 데이터 적재/부트스트랩 이력
# -----------------------------------------------------------------------------
from sqlalchemy import Column, Integer, String, Float, Index
from app.db.session import Base


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)
    lat = Column(Float, index=True)
    lon = Column(Float, index=True)
    area_m2 = Column(Float, default=0.0)
    rent_month = Column(Integer, default=0)  # 월 임대료
    deposit = Column(Integer, default=0)

    # 최근 적재한 유동인구(요약)
    foot_traffic = Column(Integer, default=0)

    # 지오쿼리 최적화
    __table_args__ = (Index("ix_places_lat_lon", "lat", "lon"),)


class IngestLog(Base):
    __tablename__ = "ingest_logs"

    id = Column(Integer, primary_key=True)
    source = Column(String, index=True)  # 예: "suseong_2024Q2"
    status = Column(String)  # "done" | "error:..."


class FootTrafficQuarter(Base):
    """
    수성구 분기 유동인구 원천 테이블
    - year: 연도 (예: 2023)
    - quarter: 분기 (1~4)
    - lat/lon: 포인트 좌표 (상권 중심점 등)
    - pop: 해당 분기 유동인구(합계 또는 평균)
    """

    __tablename__ = "foot_traffic_quarter"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, index=True, nullable=False)
    quarter = Column(Integer, index=True, nullable=False)  # 1~4
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    pop = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_ftq_year_quarter", "year", "quarter"),
        Index("ix_ftq_lat_lon", "lat", "lon"),
    )
