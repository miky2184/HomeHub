from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.common import InventoryAlert, InventoryContainer, InventoryItem, InventoryQuantityDelta
from app.services.aggregator import adjust_item_quantity, get_inventory_alerts, get_inventory_by_container

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


@router.patch("/items/{item_id}/quantity", response_model=InventoryItem)
def adjust_quantity(item_id: int, payload: InventoryQuantityDelta, db: Session = Depends(get_db)) -> InventoryItem:
    """Unica scrittura consentita da Casa su home_inventory: +/- rapido sulla
    quantità (comprare un fardello d'acqua, bere un vino), senza dover aprire
    home_inventory_web. Non crea né elimina oggetti."""
    item = adjust_item_quantity(db, item_id, payload.delta)
    if item is None:
        raise HTTPException(status_code=404, detail="Oggetto non trovato")
    return item
