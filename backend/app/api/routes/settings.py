from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services.aggregator import get_guest_mode, set_guest_mode

router = APIRouter(prefix="/api/settings", tags=["settings"])


class GuestModeOut(BaseModel):
    enabled: bool


class GuestModeUpdate(BaseModel):
    enabled: bool


@router.get("/guest-mode", response_model=GuestModeOut)
def read_guest_mode(db: Session = Depends(get_db)) -> GuestModeOut:
    """Letta dal Rail (per nascondere la tab Finanze) e da Impostazioni."""
    return GuestModeOut(enabled=get_guest_mode(db))


@router.put("/guest-mode", response_model=GuestModeOut)
def update_guest_mode(payload: GuestModeUpdate, db: Session = Depends(get_db)) -> GuestModeOut:
    """Quando attiva, nasconde l'intera sezione Finanze (tab + card Home):
    il backend smette di calcolare/restituire quei dati, non solo la UI."""
    return GuestModeOut(enabled=set_guest_mode(db, payload.enabled))
