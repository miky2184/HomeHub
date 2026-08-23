"""Costruisce l'HomeSummary chiamando i vari adapter (con cache) e leggendo le
tabelle manuali (menu scolastico, allenamenti) dal Postgres dedicato."""

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.bring import BringAdapter
from app.adapters.google_calendar import GoogleCalendarAdapter
from app.adapters.inventory_app import InventoryAdapter
from app.adapters.menu_app import HomeMenuAdapter
from app.db.models import SchoolMenuEntry, TrainingSession as TrainingSessionModel
from app.schemas.common import HomeSummary, MenuDay, TrainingSessionOut
from app.services import cache

calendar_adapter = GoogleCalendarAdapter()
bring_adapter = BringAdapter()
inventory_adapter = InventoryAdapter()
home_menu_adapter = HomeMenuAdapter()


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


async def get_calendar_events():
    raw = await cache.get_or_set("calendar_events", calendar_adapter.cache_ttl, calendar_adapter.fetch)
    return calendar_adapter.normalize(raw)


async def get_shopping_items():
    raw = await cache.get_or_set("shopping_items", bring_adapter.cache_ttl, bring_adapter.fetch)
    return bring_adapter.normalize(raw)


async def get_inventory_alerts():
    raw = await cache.get_or_set("inventory_alerts", inventory_adapter.cache_ttl, inventory_adapter.fetch)
    return inventory_adapter.normalize(raw)


async def get_home_meal_today() -> str | None:
    raw = await cache.get_or_set("home_meal_today", home_menu_adapter.cache_ttl, home_menu_adapter.fetch)
    return home_menu_adapter.normalize(raw)


def get_school_meal_today(db: Session, today: date) -> str | None:
    week_start = _week_start(today)
    entry = db.scalar(
        select(SchoolMenuEntry).where(
            SchoolMenuEntry.week_start_date == week_start,
            SchoolMenuEntry.day_of_week == today.weekday(),
        )
    )
    return entry.meal_text if entry else None


def get_next_training(db: Session, today: date) -> TrainingSessionOut | None:
    week_start = _week_start(today)
    session = db.scalar(
        select(TrainingSessionModel)
        .where(TrainingSessionModel.done.is_(False))
        .where(
            (TrainingSessionModel.week_start_date > week_start)
            | (
                (TrainingSessionModel.week_start_date == week_start)
                & (TrainingSessionModel.day_of_week >= today.weekday())
            )
        )
        .order_by(TrainingSessionModel.week_start_date, TrainingSessionModel.day_of_week)
        .limit(1)
    )
    if not session:
        return None
    return TrainingSessionOut(
        id=session.id,
        week_start_date=session.week_start_date,
        day_of_week=session.day_of_week,
        session_text=session.session_text,
        done=session.done,
    )


async def build_home_summary(db: Session) -> HomeSummary:
    now = datetime.now()
    today = now.date()

    events = await get_calendar_events()
    today_events = [e for e in events if e.start.date() == today]

    shopping_items = await get_shopping_items()
    unchecked = [i for i in shopping_items if not i.checked]

    inventory_alerts = await get_inventory_alerts()

    school_meal = get_school_meal_today(db, today)
    home_meal = await get_home_meal_today()
    today_menu = (
        MenuDay(day_of_week=today.weekday(), school_meal=school_meal, home_meal=home_meal)
        if (school_meal or home_meal)
        else None
    )

    next_training = get_next_training(db, today)

    return HomeSummary(
        now=now,
        weather=None,  # TODO: adapter meteo (es. Open-Meteo), non ancora implementato
        today_events=today_events,
        today_menu=today_menu,
        next_training=next_training,
        shopping_preview=unchecked[:4],
        shopping_total_count=len(shopping_items),
        inventory_alerts=inventory_alerts,
    )
