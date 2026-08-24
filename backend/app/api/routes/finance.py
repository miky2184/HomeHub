from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.common import FinanceSummary
from app.services.aggregator import get_finance_summary

router = APIRouter(prefix="/api/finance", tags=["finance"])


@router.get("/summary", response_model=FinanceSummary | None)
async def finance_summary(db: Session = Depends(get_db)) -> FinanceSummary | None:
    """None se la modalità ospiti è attiva o l'integrazione non è
    configurata — il frontend nasconde la sezione in quel caso, non mostra
    un errore. Sola lettura, mai importi assoluti (vedi
    app/adapters/finance.py)."""
    return await get_finance_summary(db, date.today())
