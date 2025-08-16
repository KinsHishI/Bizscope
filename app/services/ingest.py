# TODO: 실제 외부 API 연동 전, 목업 데이터 로더
from app.db.models import Place

MOCK = [
    {
        "name": "북문코너",
        "category": "카페",
        "lat": 35.888,
        "lon": 128.611,
        "area_m2": 50,
        "rent_month": 1500000,
    },
    {
        "name": "분식나라",
        "category": "분식",
        "lat": 35.889,
        "lon": 128.612,
        "area_m2": 33,
        "rent_month": 1100000,
    },
    {
        "name": "미니편의",
        "category": "편의점",
        "lat": 35.887,
        "lon": 128.610,
        "area_m2": 45,
        "rent_month": 1200000,
    },
]


async def load_mock(session):
    for m in MOCK:
        session.add(Place(**m))
    await session.commit()
