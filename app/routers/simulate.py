from fastapi import APIRouter
from app.schemas.simulate import ROISimRequest, ROISimResponse
from app.services.roi import simulate_roi

router = APIRouter(prefix="/simulate", tags=["simulate"])


@router.post("/roi", response_model=ROISimResponse)
async def roi(req: ROISimRequest):
    return simulate_roi(req)
