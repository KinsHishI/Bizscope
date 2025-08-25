# app/services/features.py

from typing import Sequence
from app.db.models import Place


def flow_score(
    num_poi: int, transit_nodes: int, avg_foot_traffic: float = 0.0
) -> float:
    """
    합성 유동 점수 (0~1): POI + 환승노드 + 유동인구(평균)
    스케일은 데이터 분포 보고 조정.
    """
    s_poi = min(1.0, num_poi / 50)
    s_transit = min(1.0, transit_nodes / 10)
    s_foot = min(1.0, (avg_foot_traffic or 0) / 20000)
    return round(0.4 * s_poi + 0.2 * s_transit + 0.4 * s_foot, 3)


def competition_density(places: Sequence[Place], target_cat: str) -> float:
    k = sum(1 for p in places if p.category == target_cat)
    return min(1.0, k / 10)
