import math
from typing import Sequence
from app.db.models import Place

# 단순 합성 유동/경쟁 지표 (MVP)


def flow_score(num_poi: int, transit_nodes: int) -> float:
    return min(1.0, 0.2 + 0.6 * (num_poi / 50) + 0.2 * (transit_nodes / 10))


def competition_density(places: Sequence[Place], target_cat: str) -> float:
    k = sum(1 for p in places if p.category == target_cat)
    return min(1.0, k / 10)
