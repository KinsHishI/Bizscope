# app/services/exog.py
from __future__ import annotations
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models import Place


def quarter_to_monthly(q_value: int) -> list[int]:
    """
    분기 유동인구를 3개월로 균등 분할.
    예: 30000 -> [10000, 10000, 10000]
    """
    per = round((q_value or 0) / 3)
    return [per, per, per]


async def get_latest_quarter_foot_traffic(
    db: AsyncSession,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_m: float = 200.0,
    agg: str = "avg",  # 'avg' or 'sum'
) -> Optional[int]:
    """
    최신 분기의 foot_traffic을 하나의 스칼라로 반환.
    - lat/lon이 주어지면 근방(대략 bbox) 장소들의 집계(평균/합계)를 사용
    - 없으면 테이블 전체의 최신 레코드들 중 평균 사용
    """
    if lat is not None and lon is not None:
        d = radius_m / 111_000  # degree per meter 근사
        stmt = select(
            func.avg(Place.foot_traffic)
            if agg == "avg"
            else func.sum(Place.foot_traffic)
        ).where(
            Place.lat.between(lat - d, lat + d),
            Place.lon.between(lon - d, lon + d),
        )
    else:
        # 전체 평균(또는 합계). 간단히 전체 평균으로.
        stmt = select(func.avg(Place.foot_traffic))

    res = await db.execute(stmt)
    val = res.scalar()
    return int(val) if val is not None else None


def build_future_months(last_ym: str, horizon: int) -> list[str]:
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    last = datetime.strptime(last_ym, "%Y-%m")
    months: list[str] = []
    for i in range(1, horizon + 1):
        months.append((last + relativedelta(months=i)).strftime("%Y-%m"))
    return months


def build_future_exog(months: list[str], ft_monthly: list[int]) -> list[dict]:
    """
    미래 exog 시퀀스(foot_traffic) 생성. 3개월 패턴 반복.
    """
    out = []
    for i, m in enumerate(months):
        out.append({"month": m, "foot_traffic": ft_monthly[i % 3]})
    return out
