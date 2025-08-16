from sqlalchemy import Column, Integer, String, Float
from app.db.session import Base


class Place(Base):
    __tablename__ = "places"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)  # 업종
    lat = Column(Float)
    lon = Column(Float)
    area_m2 = Column(Float, default=0.0)
    rent_month = Column(Integer, default=0)  # 월 임대료
    deposit = Column(Integer, default=0)


class IngestLog(Base):
    __tablename__ = "ingest_logs"
    id = Column(Integer, primary_key=True)
    source = Column(String)
    status = Column(String)
