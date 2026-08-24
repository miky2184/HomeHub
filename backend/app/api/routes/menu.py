from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import SchoolMenuCycleAnchor, SchoolMenuTemplateEntry, SnackTemplateEntry
from app.schemas.common import (
    MenuSettings,
    MenuWeek,
    SchoolMenuCycleAnchorOut,
    SchoolMenuTemplateEntryOut,
    SchoolMenuTemplateUpsert,
    SnackTemplateEntryOut,
    SnackTemplateUpsert,
)
from app.services.aggregator import build_menu_day

router = APIRouter(prefix="/api/menu", tags=["menu"])


@router.get("/week", response_model=MenuWeek)
async def get_week_menu(week_start_date: date, db: Session = Depends(get_db)) -> MenuWeek:
    """Settimana completa (lun-dom): menu scuola + merende dal template a
    rotazione, cena di casa da dieta.menu_settimanale (vedi
    services/aggregator.build_menu_day). Sola lettura: la data entry vive in
    Impostazioni (endpoint /settings sotto) o nella web app dieta, non qui."""
    days = [await build_menu_day(db, week_start_date + timedelta(days=i)) for i in range(7)]
    return MenuWeek(week_start_date=week_start_date, days=days)


@router.get("/settings", response_model=MenuSettings)
def get_menu_settings(db: Session = Depends(get_db)) -> MenuSettings:
    """Tutto quanto serve alla pagina Impostazioni per la data entry del
    template scuola/merende (che cambia un paio di volte l'anno, non ad ogni
    settimana — vedi ARCHITECTURE.md)."""
    template = db.scalars(select(SchoolMenuTemplateEntry)).all()
    anchor = db.get(SchoolMenuCycleAnchor, 1)
    snacks = db.scalars(select(SnackTemplateEntry)).all()
    return MenuSettings(
        school_template=[
            SchoolMenuTemplateEntryOut(cycle_week=e.cycle_week, day_of_week=e.day_of_week, meal_text=e.meal_text)
            for e in template
        ],
        cycle_anchor=(
            SchoolMenuCycleAnchorOut(anchor_monday=anchor.anchor_monday, anchor_cycle_week=anchor.anchor_cycle_week)
            if anchor
            else None
        ),
        snacks=[
            SnackTemplateEntryOut(day_of_week=e.day_of_week, snack_type=e.snack_type, snack_text=e.snack_text)
            for e in snacks
        ],
    )


@router.put("/settings/school-template", response_model=list[SchoolMenuTemplateEntryOut])
def upsert_school_template(
    payload: SchoolMenuTemplateUpsert, db: Session = Depends(get_db)
) -> list[SchoolMenuTemplateEntryOut]:
    for item in payload.entries:
        entry = db.scalar(
            select(SchoolMenuTemplateEntry).where(
                SchoolMenuTemplateEntry.cycle_week == item.cycle_week,
                SchoolMenuTemplateEntry.day_of_week == item.day_of_week,
            )
        )
        if entry:
            entry.meal_text = item.meal_text
        else:
            db.add(SchoolMenuTemplateEntry(**item.model_dump()))
    db.commit()
    return payload.entries


@router.put("/settings/school-anchor", response_model=SchoolMenuCycleAnchorOut)
def upsert_school_anchor(payload: SchoolMenuCycleAnchorOut, db: Session = Depends(get_db)) -> SchoolMenuCycleAnchorOut:
    anchor = db.get(SchoolMenuCycleAnchor, 1)
    if anchor:
        anchor.anchor_monday = payload.anchor_monday
        anchor.anchor_cycle_week = payload.anchor_cycle_week
    else:
        db.add(SchoolMenuCycleAnchor(id=1, **payload.model_dump()))
    db.commit()
    return payload


@router.put("/settings/snacks", response_model=list[SnackTemplateEntryOut])
def upsert_snacks(payload: SnackTemplateUpsert, db: Session = Depends(get_db)) -> list[SnackTemplateEntryOut]:
    for item in payload.entries:
        entry = db.scalar(
            select(SnackTemplateEntry).where(
                SnackTemplateEntry.day_of_week == item.day_of_week,
                SnackTemplateEntry.snack_type == item.snack_type,
            )
        )
        if entry:
            entry.snack_text = item.snack_text
        else:
            db.add(SnackTemplateEntry(**item.model_dump()))
    db.commit()
    return payload.entries
