"""Costruisce l'HomeSummary chiamando i vari adapter (con cache) e leggendo le
tabelle manuali (menu scolastico, allenamenti) dal Postgres dedicato."""

import asyncio
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.bring import BringAdapter
from app.adapters.garmin import GarminAdapter
from app.adapters.google_calendar import GoogleCalendarAdapter
from app.adapters.inventory_app import InventoryAdapter
from app.adapters.menu_app import HomeMenuAdapter
from app.core.config import get_settings
from app.db.dieta_models import allenamento_table
from app.db.models import SchoolMenuEntry, TrainingSession as TrainingSessionModel
from app.schemas.common import HomeSummary, MenuDay, TrainingActivityDetail, TrainingSessionOut
from app.services import cache

settings = get_settings()

calendar_adapter = GoogleCalendarAdapter()
bring_adapter = BringAdapter()
inventory_adapter = InventoryAdapter()
home_menu_adapter = HomeMenuAdapter()
garmin_adapter = GarminAdapter()


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


async def _get_garmin_calendar_month(year: int, month: int) -> dict:
    """Calendario Garmin di un mese (allenamenti pianificati + attività
    svolte), in cache per evitare di richiamare l'API ad ogni refresh della
    pagina Allenamenti. Non solleva eccezioni: se Garmin non è configurato o
    la chiamata fallisce (sessione scaduta, rete, ecc.), ritorna un
    calendario vuoto — è un arricchimento opzionale, non deve rompere la
    pagina.

    Nota da un test reale con credenziali sbagliate: la libreria Garmin, in
    caso di login fallito, ritenta con più metodi/backoff e può restare
    appesa **oltre un minuto** prima di arrendersi. Senza un timeout qui,
    un problema Garmin (credenziali scadute, rate limit, rete) bloccherebbe
    ad ogni refresh l'intera pagina Allenamenti. Timeout duro a 15s + una
    cache "negativa" di 60s sull'esito fallito, così le richieste successive
    falliscono subito invece di ritentare Garmin ogni volta."""
    if not garmin_adapter.is_configured:
        return {"calendarItems": []}
    key = f"garmin_calendar_{year}_{month:02d}"
    try:
        return await asyncio.wait_for(
            cache.get_or_set(
                key, garmin_adapter.cache_ttl, lambda: asyncio.to_thread(garmin_adapter.fetch_calendar_month, year, month)
            ),
            timeout=15,
        )
    except Exception:
        return await cache.get_or_set(key, 60, _empty_calendar)


async def _empty_calendar() -> dict:
    return {"calendarItems": []}


async def get_garmin_scheduled_workout(day: date) -> dict | None:
    """{"title": ..., "sport_type": ...} dell'allenamento assegnato su Garmin
    per quel giorno (se l'utente lo ha creato e assegnato lì — vedi docstring
    in adapters/garmin.py), o None se non c'è nulla."""
    calendar_month = await _get_garmin_calendar_month(day.year, day.month)
    return GarminAdapter.scheduled_workouts_by_date(calendar_month).get(day.isoformat())


def get_dieta_activity(db: Session, day: date) -> TrainingActivityDetail | None:
    """Allenamento svolto quel giorno, letto da dieta.allenamento (altra web
    app dell'utente, già sincronizzata da Garmin con dati più ricchi della
    sola API Garmin — vedi app/db/dieta_models.py). Nessuna cache: è una
    query locale su Postgres, non una chiamata di rete."""
    if settings.dieta_user_id is None:
        return None
    row = db.execute(
        allenamento_table.select().where(
            allenamento_table.c.user_id == settings.dieta_user_id,
            allenamento_table.c.data == day,
        )
    ).first()
    if row is None:
        return None
    return TrainingActivityDetail(**row._mapping)


def dieta_activity_summary(activity: TrainingActivityDetail) -> str:
    """Riepilogo breve per la card nella pagina Allenamenti, es.
    "Corsa · 8.2 km · 42 min"."""
    parts = [activity.titolo or activity.tipo or "Allenamento"]
    if activity.distanza_m:
        parts.append(f"{round(activity.distanza_m / 1000, 1)} km")
    if activity.durata_sec:
        parts.append(f"{round(activity.durata_sec / 60)} min")
    return " · ".join(parts)


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
