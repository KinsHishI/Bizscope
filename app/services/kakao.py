# app/services/kakao.py
import os
import httpx
from typing import List, Dict, Optional
from app.core.config import settings
from loguru import logger

KAKAO_REST_URL = "https://dapi.kakao.com/v2/local/search/category.json"


def _auth_headers() -> Dict[str, str]:
    key = settings.KAKAO_API_KEY or settings.MAP_API_KEY
    if not key:
        raise RuntimeError("KAKAO_API_KEY/MAP_API_KEY가 설정되어 있지 않습니다.")
    return {"Authorization": f"KakaoAK {key}"}


async def get_nearby_cafes(lat: float, lon: float, radius_m: int = 2000) -> List[Dict]:
    """
    카카오 장소 검색(카페 CE7). 타임아웃/재시도 내장.
    실패 시 [] 반환(서버는 폴백으로 DB 데이터만 사용).
    """
    headers = _auth_headers()
    all_docs: List[Dict] = []
    max_pages = 3

    # 연결/읽기 타임아웃을 넉넉히, 전체 요청 타임아웃도 설정
    timeout = httpx.Timeout(connect=6.0, read=10.0, write=10.0, pool=6.0)
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)

    # 최대 3회 재시도 (지수 백오프)
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
                for page in range(1, max_pages + 1):
                    params = {
                        "category_group_code": "CE7",
                        "y": str(lat),
                        "x": str(lon),
                        "radius": str(radius_m),
                        "sort": "distance",
                        "page": str(page),
                    }
                    r = await client.get(KAKAO_REST_URL, params=params, headers=headers)
                    r.raise_for_status()
                    data = r.json()
                    docs = data.get("documents", []) or []
                    if not docs:
                        break
                    all_docs.extend(docs)
                    # meta.is_end가 True면 종료
                    meta = data.get("meta", {}) or {}
                    if meta.get("is_end") or page >= max_pages:
                        break
            return all_docs

        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            wait = 1.5 * (attempt + 1)
            logger.warning(
                f"[Kakao] timeout 재시도 {attempt+1}/3 … {e}. {wait:.1f}s 대기"
            )
            import asyncio

            await asyncio.sleep(wait)
        except httpx.HTTPError as e:
            logger.error(f"[Kakao] HTTPError: {e}")
            break
        except Exception as e:
            logger.error(f"[Kakao] 기타 오류: {e}")
            break

    # 모든 시도 실패 -> 폴백: 빈 리스트(상위 라우터가 DB데이터만 사용)
    return []
