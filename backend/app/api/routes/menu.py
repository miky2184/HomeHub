from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import SchoolMenuEntry
from app.schemas.common import MenuDay, MenuWeek, SchoolMenuUpsert
from app.services.aggregator import get_home_meal_today

router = APIRouter(prefix="/api/menu", tags=["menu"])


@router.get("/week", response_model=MenuWeek)
async def get_week_menu(week_start_date: date, db: Session = Depends(get_db)) -> MenuWeek:
    """Menu scolastico completo per la settimana (inserito a mano) + menu di casa
    per il solo giorno odierno (l'app menu di casa esistente espone per ora solo
    "il piatto di oggi" — vedi TODO in app.adapters.menu_app)."""
    entries = db.scalars(
        select(SchoolMenuEntry).where(SchoolMenuEntry.week_start_date == week_start_date)
    ).all()
    school_by_day = {e.day_of_week: e.meal_text for e in entries}

    today = date.today()
    home_meal_today = await get_home_meal_today() if _week_of(today) == week_start_date else None

    days = [
        MenuDay(
            day_of_week=i,
            school_meal=school_by_day.get(i),
            home_meal=home_meal_today if i == today.weekday() else None,
        )
        for i in range(7)
    ]
    return MenuWeek(week_start_date=week_start_date, days=days)


@router.put("/school", response_model=MenuDay)
def upsert_school_menu(payload: SchoolMenuUpsert, db: Session = Depends(get_db)) -> MenuDay:
    entry = db.scalar(
        select(SchoolMenuEntry).where(
            SchoolMenuEntry.week_start_date == payload.week_start_date,
            SchoolMenuEntry.day_of_week == payload.day_of_week,
        )
    )
    if entry:
        entry.meal_text = payload.meal_text
    else:
        entry = SchoolMenuEntry(**payload.model_dump())
        db.add(entry)
    db.commit()
    return MenuDay(day_of_week=payload.day_of_week, school_meal=payload.meal_text)


def _week_of(d: date) -> date:
    from datetime import timedelta

    return d - timedelta(days=d.weekday())
