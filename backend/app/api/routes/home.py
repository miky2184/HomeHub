from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.common import HomeSummary
from app.services.aggregator import build_home_summary

router = APIRouter(prefix="/api/home", tags=["home"])


@router.get("/summary", response_model=HomeSummary)
async def get_home_summary(db: Session = Depends(get_db)) -> HomeSummary:
    """Riepilogo per la Home: quello che finisce nelle card mostrate nel wireframe
    (ARCHITECTURE.md §4.1.1)."""
    return await build_home_summary(db)
