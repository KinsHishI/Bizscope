from fastapi import APIRouter, Depends
from app.db.session import get_session
from app.services.ingest import load_mock

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/ingest/mock")
async def ingest_mock(db=Depends(get_session)):
    await load_mock(db)
    return {"status": "ok"}
