from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import Shipment
from app.schemas.common import ShipmentCreate, ShipmentOut, ShipmentUpdate
from app.services.aggregator import refresh_shipment, refresh_stale_shipments, shipment_item_out, sort_shipments

router = APIRouter(prefix="/api/shipments", tags=["shipments"])


@router.get("", response_model=list[ShipmentOut])
async def list_shipments(db: Session = Depends(get_db)) -> list[ShipmentOut]:
    """Tutte le spedizioni, ordinate (non consegnate prima). Prima di
    rispondere, aggiorna quelle Poste non consegnate il cui ultimo poll è
    stantio (vedi is_shipment_stale) — best-effort, un corriere irraggiungibile
    non fa fallire la lista, finisce in last_poll_error per quella riga."""
    items = db.scalars(select(Shipment)).all()
    await refresh_stale_shipments(db, items)
    return [shipment_item_out(s) for s in sort_shipments(items)]


@router.post("", response_model=ShipmentOut, status_code=201)
async def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)) -> ShipmentOut:
    item = Shipment(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    # Refresh immediato best-effort: senza, la spedizione resterebbe senza
    # stato finché non arriva la prossima GET stantia.
    item = await refresh_shipment(db, item)
    return shipment_item_out(item)


@router.patch("/{shipment_id}", response_model=ShipmentOut)
async def update_shipment(shipment_id: int, payload: ShipmentUpdate, db: Session = Depends(get_db)) -> ShipmentOut:
    item = db.get(Shipment, shipment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Spedizione non trovata")
    changes = payload.model_dump(exclude_unset=True)
    tracking_changed = "tracking_number" in changes and changes["tracking_number"] != item.tracking_number
    for field, value in changes.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    if tracking_changed:
        # Un numero di tracking diverso invalida stato/storico letti finora.
        item.last_polled_at = None
        item = await refresh_shipment(db, item)
    return shipment_item_out(item)


@router.delete("/{shipment_id}", status_code=204)
def delete_shipment(shipment_id: int, db: Session = Depends(get_db)) -> None:
    item = db.get(Shipment, shipment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Spedizione non trovata")
    db.delete(item)
    db.commit()


@router.post("/{shipment_id}/refresh", response_model=ShipmentOut)
async def force_refresh_shipment(shipment_id: int, db: Session = Depends(get_db)) -> ShipmentOut:
    """Refresh manuale, ignora la soglia di stale — pulsante "Aggiorna" nel
    tab Spedizioni. Un fallimento del corriere non è un errore HTTP: torna
    comunque 200 con last_poll_error valorizzato, così la UI può mostrarlo
    senza un toast di errore generico."""
    item = db.get(Shipment, shipment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Spedizione non trovata")
    item = await refresh_shipment(db, item)
    return shipment_item_out(item)
