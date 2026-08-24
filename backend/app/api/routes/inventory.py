from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.common import InventoryAlert
from app.services.aggregator import get_inventory_alerts

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/alerts", response_model=list[InventoryAlert])
def list_alerts(db: Session = Depends(get_db)) -> list[InventoryAlert]:
    """Sola lettura: la gestione degli oggetti (creare/modificare/consumare)
    resta nella web app home_inventory_web dedicata, questa è solo la vista
    di sintesi per la Home/Casa di HomeHub."""
    return get_inventory_alerts(db, date.today())
