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
from app.adapters.santo_del_giorno import fetch_saint_of_day
from app.adapters.weather import condition_label, fetch_weather_snapshot, geocode_city, parse_hourly, precipitation_alert
from app.core.config import get_settings
from app.db.dieta_models import allenamento_table
from app.db.models import (
    SchoolMenuCycleAnchor,
    SchoolMenuTemplateEntry,
    SnackTemplateEntry,
    TrainingSession as TrainingSessionModel,
)
from app.schemas.common import (
    HomeSummary,
    HourlyForecast,
    MenuDay,
    TrainingActivityDetail,
    TrainingSessionOut,
    WeatherSnapshot,
)
from app.services import cache
from app.services.quotes import quote_of_day

settings = get_settings()

# Dopo quest'ora, Home mostra il menu/le merende di domani invece che di
# oggi (comodo la sera, per sapere cosa preparare al mattino). Il menu di
# casa resta legato a "oggi" finché l'adapter della web app menu non sa
# rispondere anche per una data futura (vedi adapters/menu_app.py).
MENU_CUTOFF_HOUR = 20

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


async def get_weather() -> WeatherSnapshot | None:
    """Meteo attuale + prossime 4 ore + avviso pioggia/neve per WEATHER_CITY
    (Open-Meteo, vedi adapters/weather.py). Le coordinate della città vengono
    geocodificate una volta e tenute in cache a lungo (non cambiano); il
    meteo vero e proprio ogni 15 minuti. Come gli altri arricchimenti
    decorativi della Home, non solleva mai eccezioni: se il servizio non
    risponde, semplicemente non mostra nulla."""
    if not settings.weather_city:
        return None
    try:
        coords = await cache.get_or_set(
            "weather_coords", 7 * 24 * 3600, lambda: geocode_city(settings.weather_city)
        )
        if not coords:
            return None
        raw = await cache.get_or_set("weather_raw", 900, lambda: fetch_weather_snapshot(*coords))

        now = datetime.now()
        current = raw.get("current", {})
        current_code = current.get("weather_code")

        return WeatherSnapshot(
            temperature_c=current.get("temperature_2m"),
            condition=condition_label(current_code),
            city=settings.weather_city,
            hourly=[HourlyForecast(**h) for h in parse_hourly(raw, now, count=4)],
            precipitation_alert=precipitation_alert(raw, now, current_code),
        )
    except Exception:
        return None


async def get_saint_of_day(day: date) -> str | None:
    """Santo del giorno da santodelgiorno.it, con cache di 24h (cambia una
    volta al giorno). Se il servizio non è raggiungibile, nessun errore
    verso il chiamante: è un dettaglio decorativo in Home, non deve romperla."""
    try:
        return await cache.get_or_set(f"saint_{day.isoformat()}", 24 * 3600, lambda: fetch_saint_of_day(day))
    except Exception:
        return None


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


def compute_cycle_week(real_monday: date, anchor_monday: date, anchor_cycle_week: int, num_weeks: int = 4) -> int:
    """A quale settimana del ciclo (1..num_weeks) corrisponde una settimana
    reale, dato un punto di riferimento "da anchor_monday si parte dalla
    settimana anchor_cycle_week". Funziona anche per settimane precedenti
    l'ancora (differenza negativa: % in Python su interi negativi resta
    comunque nell'intervallo [0, num_weeks), coerente con quanto serve qui)."""
    weeks_diff = (real_monday - anchor_monday).days // 7
    return ((anchor_cycle_week - 1 + weeks_diff) % num_weeks) + 1


def get_school_meal(db: Session, day: date) -> str | None:
    """Menu scolastico per un giorno, dal template a rotazione + l'ancora
    (vedi db.models.SchoolMenuTemplateEntry/SchoolMenuCycleAnchor). None nel
    weekend o se il template/l'ancora non sono ancora stati compilati in
    Impostazioni."""
    if day.weekday() > 4:  # weekend, la scuola non serve pasti
        return None
    anchor = db.get(SchoolMenuCycleAnchor, 1)
    if anchor is None:
        return None
    cycle_week = compute_cycle_week(_week_start(day), anchor.anchor_monday, anchor.anchor_cycle_week)
    entry = db.scalar(
        select(SchoolMenuTemplateEntry).where(
            SchoolMenuTemplateEntry.cycle_week == cycle_week,
            SchoolMenuTemplateEntry.day_of_week == day.weekday(),
        )
    )
    return entry.meal_text if entry else None


def get_snack(db: Session, day: date, snack_type: str) -> str | None:
    """Merenda (mattina/pomeriggio) per un giorno: fissa per giorno della
    settimana, stessa ogni settimana. None nel weekend."""
    if day.weekday() > 4:
        return None
    entry = db.scalar(
        select(SnackTemplateEntry).where(
            SnackTemplateEntry.day_of_week == day.weekday(),
            SnackTemplateEntry.snack_type == snack_type,
        )
    )
    return entry.snack_text if entry else None


def effective_menu_date(now: datetime) -> date:
    """Oggi, o già domani se è tardi (vedi MENU_CUTOFF_HOUR)."""
    if now.hour >= MENU_CUTOFF_HOUR:
        return now.date() + timedelta(days=1)
    return now.date()


async def build_menu_day(db: Session, day: date) -> MenuDay:
    """MenuDay completo per una data: menu scuola + merende dal template,
    menu di casa solo se `day` è davvero oggi (l'adapter non sa ancora
    rispondere per altre date)."""
    home_meal = await get_home_meal_today() if day == date.today() else None
    return MenuDay(
        date=day,
        day_of_week=day.weekday(),
        school_meal=get_school_meal(db, day),
        home_meal=home_meal,
        snack_morning=get_snack(db, day, "mattina"),
        snack_afternoon=get_snack(db, day, "pomeriggio"),
    )


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

    menu_day = await build_menu_day(db, effective_menu_date(now))
    today_menu = (
        menu_day
        if any([menu_day.school_meal, menu_day.home_meal, menu_day.snack_morning, menu_day.snack_afternoon])
        else None
    )

    next_training = get_next_training(db, today)
    saint_of_day = await get_saint_of_day(today)
    weather = await get_weather()

    return HomeSummary(
        now=now,
        weather=weather,
        saint_of_day=saint_of_day,
        quote_of_day=quote_of_day(today),
        today_events=today_events,
        today_menu=today_menu,
        next_training=next_training,
        shopping_preview=unchecked[:4],
        shopping_total_count=len(shopping_items),
        inventory_alerts=inventory_alerts,
    )
