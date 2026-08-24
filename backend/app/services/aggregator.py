"""Costruisce l'HomeSummary chiamando i vari adapter (con cache) e leggendo le
tabelle manuali (menu scolastico, allenamenti) dal Postgres dedicato."""

import asyncio
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.bring import BringAdapter
from app.adapters.finance import FinanceAdapter, parse_upcoming_expenses
from app.adapters.garmin import GarminAdapter
from app.adapters.google_calendar import GoogleCalendarAdapter
from app.adapters.santo_del_giorno import fetch_saint_of_day
from app.adapters.weather import condition_label, fetch_weather_snapshot, geocode_city, parse_hourly, precipitation_alert
from app.core.config import get_settings
from app.db.dieta_models import GIORNI_SETTIMANA_IT, allenamento_table, menu_settimanale_table
from app.db.home_inventory_models import containers_table, items_table
from app.db.models import (
    AppConfig,
    SchoolMenuCycleAnchor,
    SchoolMenuTemplateEntry,
    SnackTemplateEntry,
    TodoItem,
    TrainingSession as TrainingSessionModel,
)
from app.schemas.common import (
    FinanceSummary,
    HomeMeals,
    HomeSummary,
    HourlyForecast,
    InventoryAlert,
    MenuDay,
    TodoItemOut,
    TodoSummary,
    TrainingActivityDetail,
    TrainingSessionOut,
    WeatherSnapshot,
)
from app.services import cache
from app.services.quotes import quote_of_day

settings = get_settings()

# Dopo quest'ora, Home mostra il menu/le merende di domani invece che di
# oggi (comodo la sera, per sapere cosa preparare al mattino).
MENU_CUTOFF_HOUR = 20

calendar_adapter = GoogleCalendarAdapter()
bring_adapter = BringAdapter()
garmin_adapter = GarminAdapter()
finance_adapter = FinanceAdapter()

GUEST_MODE_CONFIG_KEY = "guest_mode"

# Soglia per gli alert di scadenza in Home: solo scaduti o in scadenza entro
# questi giorni (stessa soglia "warning" del frontend di home_inventory_web,
# escludiamo la fascia più morbida a 30gg per non appesantire la Home).
INVENTORY_ALERT_DAYS = 7


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


async def get_calendar_events():
    raw = await cache.get_or_set("calendar_events", calendar_adapter.cache_ttl, calendar_adapter.fetch)
    return calendar_adapter.normalize(raw)


async def get_shopping_items():
    raw = await cache.get_or_set("shopping_items", bring_adapter.cache_ttl, bring_adapter.fetch)
    return bring_adapter.normalize(raw)


def get_inventory_alerts(db: Session, today: date) -> list[InventoryAlert]:
    """Oggetti scaduti o in scadenza entro INVENTORY_ALERT_DAYS, letti da
    home_inventory.items (altra web app dell'utente — vedi
    app/db/home_inventory_models.py). Sola lettura, nessuna cache: query
    locale su Postgres, non una chiamata di rete."""
    cutoff = today + timedelta(days=INVENTORY_ALERT_DAYS)
    rows = db.execute(
        select(
            items_table.c.id,
            items_table.c.name,
            items_table.c.quantity,
            items_table.c.unit_measure,
            items_table.c.expiry_date,
            containers_table.c.name.label("container_name"),
        )
        .select_from(items_table.outerjoin(containers_table, items_table.c.container_id == containers_table.c.id))
        .where(items_table.c.expiry_date.is_not(None), items_table.c.expiry_date <= cutoff)
        .order_by(items_table.c.expiry_date.asc())
    ).all()

    alerts = []
    for row in rows:
        days = (row.expiry_date - today).days
        reason = "expired" if days < 0 else ("critical" if days <= 3 else "warning")
        alerts.append(
            InventoryAlert(
                id=row.id,
                item_name=row.name,
                quantity=row.quantity,
                unit=row.unit_measure,
                expiry_date=row.expiry_date,
                days_to_expiry=days,
                container_name=row.container_name,
                reason=reason,
            )
        )
    return alerts


TODO_PRIORITY_ORDER = {"alta": 0, "media": 1, "bassa": 2}


def sort_todos(items: list[TodoItem]) -> list[TodoItem]:
    """Priorità (alta→bassa), poi scadenza più vicina (chi non ne ha una
    resta in fondo), poi data di creazione — stesso ordine ovunque (tab
    Todo e top 3 in Home)."""
    return sorted(
        items,
        key=lambda i: (TODO_PRIORITY_ORDER.get(i.priority, 1), i.due_date or date.max, i.created_at),
    )


def todo_item_out(item: TodoItem) -> TodoItemOut:
    return TodoItemOut(
        id=item.id,
        title=item.title,
        assignee=item.assignee,
        priority=item.priority,
        due_date=item.due_date,
        done=item.done,
        created_at=item.created_at,
    )


def get_todo_summary(db: Session) -> TodoSummary:
    """Conteggio dei todo aperti + i primi 3 per priorità/scadenza, per la
    card 'Da fare' in Home. I todo completati non contano e non compaiono
    qui (restano visibili nel tab Todo completo)."""
    pending = [i for i in db.scalars(select(TodoItem)).all() if not i.done]
    top = sort_todos(pending)[:3]
    return TodoSummary(pending_count=len(pending), top=[todo_item_out(i) for i in top])


def get_guest_mode(db: Session) -> bool:
    """Modalità ospiti: quando attiva, nasconde l'intera sezione Finanze
    (tab + card Home) — non solo lato UI, il backend smette proprio di
    calcolare/restituire quei dati (vedi build_home_summary e
    api/routes/finance.py). Persistita in app_config, non in .env, perché
    va accesa/spenta al volo dall'utente, non in fase di deploy."""
    row = db.get(AppConfig, GUEST_MODE_CONFIG_KEY)
    return row is not None and row.value == "true"


def set_guest_mode(db: Session, enabled: bool) -> bool:
    row = db.get(AppConfig, GUEST_MODE_CONFIG_KEY)
    value = "true" if enabled else "false"
    if row:
        row.value = value
    else:
        db.add(AppConfig(key=GUEST_MODE_CONFIG_KEY, value=value))
    db.commit()
    return enabled


async def get_finance_summary(db: Session) -> FinanceSummary | None:
    """None se la modalità ospiti è attiva o l'integrazione non è
    configurata: in quel caso la Home/il tab Finanze non mostrano proprio
    la sezione, non solo dati vuoti. Sola lettura via API della web app
    finanze (mai una query diretta su home.finance: /dare_avere e
    /budget-forecast-all hanno già tutta la logica di business — vedi
    app/adapters/finance.py). Ogni fetch è isolato: se una delle due fonti
    fallisce, l'altra continua a funzionare invece di rompere l'intera
    card (widget decorativo, non deve mai rompere la Home)."""
    if get_guest_mode(db) or not finance_adapter.is_configured:
        return None
    try:
        raw = await cache.get_or_set("finance_budget", finance_adapter.cache_ttl, finance_adapter.fetch)
        categories = finance_adapter.normalize(raw)
    except Exception:
        categories = []
    try:
        dare_avere_raw = await cache.get_or_set(
            "finance_dare_avere", finance_adapter.cache_ttl, finance_adapter.fetch_dare_avere
        )
        upcoming_expenses = parse_upcoming_expenses(dare_avere_raw)
    except Exception:
        upcoming_expenses = []
    return FinanceSummary(categories=categories, upcoming_expenses=upcoming_expenses)


# Chiavi pasto nel jsonb di dieta.menu_settimanale → campo HomeMeals
# corrispondente. La figlia pranza a scuola (school_meal, da un'altra
# fonte), ma gli adulti in casa fanno tutti i pasti qui, non solo la cena.
PASTO_FIELD_MAP = {
    "colazione": "breakfast",
    "spuntino_mattina": "snack_morning",
    "pranzo": "lunch",
    "spuntino_pomeriggio": "snack_afternoon",
    "cena": "dinner",
    "spuntino_sera": "snack_evening",
}


def get_home_meals(db: Session, day: date) -> HomeMeals:
    """Tutti i pasti di casa per un giorno (colazione, spuntini, pranzo,
    cena), letti da dieta.menu_settimanale (altra web app dell'utente sullo
    stesso Postgres — il piano nutrizionale copre tutta la famiglia, non
    solo lui). Ogni pasto è multi-riga se ha più portate, stesso formato del
    menu scuola (vedi components/MealList.tsx). Sola lettura, nessuna
    cache: query locale su Postgres, non una chiamata di rete. Tutti i
    campi None se non c'è una settimana di menu che copre quel giorno."""
    empty = HomeMeals()
    if settings.dieta_user_id is None:
        return empty
    row = db.execute(
        select(menu_settimanale_table.c.menu).where(
            menu_settimanale_table.c.user_id == settings.dieta_user_id,
            menu_settimanale_table.c.data_inizio <= day,
            menu_settimanale_table.c.data_fine >= day,
        )
    ).first()
    if row is None or row.menu is None:
        return empty
    giorno_nome = GIORNI_SETTIMANA_IT[day.weekday()]
    pasti = row.menu.get("day", {}).get(giorno_nome, {}).get("pasto", {})

    def meal_text(pasto_key: str) -> str | None:
        ricette = pasti.get(pasto_key, {}).get("ricette", [])
        nomi = [r["nome_ricetta"] for r in ricette if r.get("nome_ricetta")]
        return "\n".join(nomi) if nomi else None

    return HomeMeals(**{field: meal_text(pasto_key) for pasto_key, field in PASTO_FIELD_MAP.items()})


async def get_weather() -> WeatherSnapshot | None:
    """Meteo attuale + prossime 4 ore + avviso pioggia/neve (Open-Meteo, vedi
    adapters/weather.py). Se WEATHER_LATITUDE/LONGITUDE sono configurate,
    hanno la priorità (coordinate esatte di casa, niente geocoding); altrimenti
    si geocodifica WEATHER_CITY una volta e si tiene in cache a lungo (non
    cambia). Il meteo vero e proprio viene comunque aggiornato ogni 15 minuti.
    Come gli altri arricchimenti decorativi della Home, non solleva mai
    eccezioni: se il servizio non risponde, semplicemente non mostra nulla."""
    try:
        if settings.weather_latitude is not None and settings.weather_longitude is not None:
            coords = (settings.weather_latitude, settings.weather_longitude)
        elif settings.weather_city:
            coords = await cache.get_or_set(
                "weather_coords", 7 * 24 * 3600, lambda: geocode_city(settings.weather_city)
            )
        else:
            return None
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
    """MenuDay completo per una data: menu scuola (pranzo della figlia) +
    merende scuola dal template a rotazione, più tutti i pasti di casa
    (colazione/spuntini/pranzo/cena degli adulti) da dieta.menu_settimanale
    — qualunque giorno rientri nella settimana generata lì, non solo oggi."""
    return MenuDay(
        date=day,
        day_of_week=day.weekday(),
        school_meal=get_school_meal(db, day),
        home_meals=get_home_meals(db, day),
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

    inventory_alerts = get_inventory_alerts(db, today)
    todos = get_todo_summary(db)

    menu_day = await build_menu_day(db, effective_menu_date(now))
    today_menu = (
        menu_day
        if any(
            [
                menu_day.school_meal,
                menu_day.snack_morning,
                menu_day.snack_afternoon,
                *menu_day.home_meals.model_dump().values(),
            ]
        )
        else None
    )

    next_training = get_next_training(db, today)
    saint_of_day = await get_saint_of_day(today)
    weather = await get_weather()
    guest_mode = get_guest_mode(db)
    finance = await get_finance_summary(db)

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
        todos=todos,
        finance=finance,
        guest_mode=guest_mode,
    )
