from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import Chore
from app.schemas.common import ChoreCreate, ChoreOut, ChoreUpdate
from app.services.aggregator import chore_item_out, sort_chores

router = APIRouter(prefix="/api/chores", tags=["chores"])


@router.get("", response_model=list[ChoreOut])
def list_chores(db: Session = Depends(get_db)) -> list[ChoreOut]:
    """Tutte le attività ricorrenti, ordinate per urgenza (vedi sort_chores)
    — a differenza dei todo qui non c'è un filtro "solo da fare": sono
    sempre tutte "attive", non esiste uno stato "fatta per sempre"."""
    today = date.today()
    items = [chore_item_out(c, today) for c in db.scalars(select(Chore)).all()]
    return sort_chores(items)


@router.post("", response_model=ChoreOut, status_code=201)
def create_chore(payload: ChoreCreate, db: Session = Depends(get_db)) -> ChoreOut:
    chore = Chore(**payload.model_dump())
    db.add(chore)
    db.commit()
    db.refresh(chore)
    return chore_item_out(chore, date.today())


@router.patch("/{chore_id}", response_model=ChoreOut)
def update_chore(chore_id: int, payload: ChoreUpdate, db: Session = Depends(get_db)) -> ChoreOut:
    """PATCH parziale: usato sia dal form di modifica (titolo/intervallo/
    assegnatario/note) sia dal pulsante "Fatto oggi" ({"last_done_date":
    <oggi>})."""
    chore = db.get(Chore, chore_id)
    if not chore:
        raise HTTPException(status_code=404, detail="Attività non trovata")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(chore, field, value)
    db.commit()
    db.refresh(chore)
    return chore_item_out(chore, date.today())


@router.delete("/{chore_id}", status_code=204)
def delete_chore(chore_id: int, db: Session = Depends(get_db)) -> None:
    chore = db.get(Chore, chore_id)
    if not chore:
        raise HTTPException(status_code=404, detail="Attività non trovata")
    db.delete(chore)
    db.commit()
