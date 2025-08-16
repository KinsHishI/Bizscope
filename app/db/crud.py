from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Place


async def get_places_bbox(
    db: AsyncSession, min_lat: float, min_lon: float, max_lat: float, max_lon: float
):
    stmt = select(Place).where(
        Place.lat.between(min_lat, max_lat), Place.lon.between(min_lon, max_lon)
    )
    res = await db.execute(stmt)
    return res.scalars().all()
