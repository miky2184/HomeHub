from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.common import InventoryAlert, InventoryContainer
from app.services.aggregator import get_inventory_alerts, get_inventory_by_container

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/alerts", response_model=list[InventoryAlert])
def list_alerts(db: Session = Depends(get_db)) -> list[InventoryAlert]:
    """Sola lettura: la gestione degli oggetti (creare/modificare/consumare)
    resta nella web app home_inventory_web dedicata, questa è solo la vista
    di sintesi per la Home/Casa di HomeHub."""
    return get_inventory_alerts(db, date.today())


@router.get("/containers", response_model=list[InventoryContainer])
def list_containers(db: Session = Depends(get_db)) -> list[InventoryContainer]:
    """"Sfoglia per contenitore": tutto il contenuto di home_inventory,
    non solo ciò che scade a breve — per sapere cosa c'è in un cassetto
    del freezer senza doverlo aprire (sostituisce il foglio di carta sul
    frigo)."""
    return get_inventory_by_container(db)
