"""Schema dati unificato "HomeHub": ciò che il frontend consuma, indipendentemente
dalla fonte reale (Google, Bring!, le web app esistenti, o le tabelle manuali)."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class CalendarEvent(BaseModel):
    id: str
    calendar_id: str
    calendar_label: str  # es. "Famiglia", "Scuola" — per il pallino colorato in UI
    title: str
    start: datetime
    end: datetime
    all_day: bool = False


class CalendarInfo(BaseModel):
    id: str
    label: str


class CalendarEventCreate(BaseModel):
    calendar_id: str
    title: str
    start: datetime
    end: datetime
    all_day: bool = False


class HomeMeals(BaseModel):
    """Tutti i pasti di casa di una giornata (letti da dieta.menu_settimanale
    — il piano nutrizionale copre tutta la famiglia): la figlia pranza a
    scuola (school_meal in MenuDay), ma gli adulti in casa fanno colazione,
    spuntini, pranzo e cena qui."""

    breakfast: str | None = None
    snack_morning: str | None = None
    lunch: str | None = None
    snack_afternoon: str | None = None
    dinner: str | None = None
    snack_evening: str | None = None


class MenuDay(BaseModel):
    date: date
    day_of_week: int
    school_meal: str | None = None  # pranzo scuola della figlia
    home_meals: HomeMeals = HomeMeals()
    snack_morning: str | None = None  # merenda scuola della figlia (mattina)
    snack_afternoon: str | None = None  # merenda scuola della figlia (pomeriggio)


class MenuWeek(BaseModel):
    week_start_date: date
    days: list[MenuDay]


class SchoolMenuTemplateEntryOut(BaseModel):
    cycle_week: int
    day_of_week: int
    meal_text: str


class SchoolMenuTemplateUpsert(BaseModel):
    entries: list[SchoolMenuTemplateEntryOut]


class SchoolMenuCycleAnchorOut(BaseModel):
    anchor_monday: date
    anchor_cycle_week: int


class SnackTemplateEntryOut(BaseModel):
    day_of_week: int
    snack_type: str  # "mattina" | "pomeriggio"
    snack_text: str


class SnackTemplateUpsert(BaseModel):
    entries: list[SnackTemplateEntryOut]


class MenuSettings(BaseModel):
    """Tutto quello che serve alla pagina Impostazioni per la data entry."""

    school_template: list[SchoolMenuTemplateEntryOut]
    cycle_anchor: SchoolMenuCycleAnchorOut | None
    snacks: list[SnackTemplateEntryOut]


class TrainingSessionOut(BaseModel):
    id: int
    week_start_date: date
    day_of_week: int
    session_text: str
    done: bool
    garmin_note: str | None = None  # es. "Corsa · 8.2 km · 42 min", se svolta (da dieta.allenamento)
    sport_type: str | None = None  # es. "running", per l'icona in UI — da dieta.allenamento o dal piano Garmin


class TrainingActivityDetail(BaseModel):
    """Dettaglio di un allenamento svolto, da dieta.allenamento (sincronizzata
    da un'altra web app dell'utente con dati più ricchi della sola API Garmin)."""

    data: date
    tipo: str | None = None
    titolo: str | None = None
    distanza_m: float | None = None
    durata_sec: int | None = None
    calorie: int | None = None
    fc_media: int | None = None
    fc_max: int | None = None
    te_aerobico: float | None = None
    passo_sec: int | None = None
    cadenza: int | None = None
    tss: float | None = None
    ascesa_m: int | None = None
    swolf: float | None = None


class TrainingSessionUpsert(BaseModel):
    week_start_date: date
    day_of_week: int
    session_text: str


class ShoppingItem(BaseModel):
    id: str
    name: str
    checked: bool = False
    specification: str | None = None


class ShoppingItemCreate(BaseModel):
    name: str
    specification: str | None = None


class InventoryAlert(BaseModel):
    """Oggetto in scadenza in home_inventory (schema della web app dedicata:
    non esiste un concetto di "scorta minima", solo expiry_date — vedi
    app/db/home_inventory_models.py). reason: "expired" | "critical" (≤3gg)
    | "warning" (≤7gg), stesse soglie usate nel frontend di quella app."""

    id: int
    item_name: str
    quantity: float | None = None
    unit: str | None = None
    expiry_date: date | None = None
    days_to_expiry: int | None = None
    container_name: str | None = None
    reason: str = "warning"


class HourlyForecast(BaseModel):
    time: datetime
    temperature_c: float | None = None
    condition: str | None = None
    precipitation_probability: int | None = None


class WeatherSnapshot(BaseModel):
    temperature_c: float | None = None
    condition: str | None = None
    city: str | None = None
    hourly: list[HourlyForecast] = []
    precipitation_alert: str | None = None  # es. "Possibile pioggia più tardi"


class TodoItemOut(BaseModel):
    id: int
    title: str
    assignee: str | None = None  # etichetta libera ("per chi"), non un vero utente/login
    priority: Literal["alta", "media", "bassa"] = "media"
    due_date: date | None = None
    done: bool = False
    created_at: datetime


class TodoItemCreate(BaseModel):
    title: str
    assignee: str | None = None
    priority: Literal["alta", "media", "bassa"] = "media"
    due_date: date | None = None


class TodoItemUpdate(BaseModel):
    """Tutti i campi opzionali: PATCH parziale (usato sia dal form di
    modifica sia dal semplice toggle "fatto")."""

    title: str | None = None
    assignee: str | None = None
    priority: Literal["alta", "media", "bassa"] | None = None
    due_date: date | None = None
    done: bool | None = None


class TodoSummary(BaseModel):
    pending_count: int
    top: list[TodoItemOut]  # prime 3 per priorità/scadenza, solo non fatti


class FinanceCategoryStatus(BaseModel):
    """MAI un importo: solo percentuali derivate (vedi app/adapters/finance.py).
    alert_level: 0 in linea, 1 attenzione (proiezione >80% del budget), 2 sopra budget."""

    label: str
    perc_speso: float
    perc_proiezione: float
    alert_level: Literal[0, 1, 2]


class UpcomingExpense(BaseModel):
    """Movimento pianificato non ancora contabilizzato (tipo_conto=0, uscita).
    Mai l'importo — solo chi/quando, per un promemoria al colpo d'occhio."""

    beneficiario: str | None = None
    due_date: date


class FinanceSummary(BaseModel):
    categories: list[FinanceCategoryStatus]
    upcoming_expenses: list[UpcomingExpense]


class HomeSummary(BaseModel):
    now: datetime
    weather: WeatherSnapshot | None = None
    saint_of_day: str | None = None  # es. "San Bartolomeo" (santodelgiorno.it)
    quote_of_day: str | None = None  # proverbio italiano, rotazione per giorno dell'anno
    today_events: list[CalendarEvent]
    today_menu: MenuDay | None = None
    next_training: TrainingSessionOut | None = None
    shopping_preview: list[ShoppingItem]
    shopping_total_count: int
    inventory_alerts: list[InventoryAlert]
    todos: TodoSummary
    finance: FinanceSummary | None = None  # None se modalità ospiti attiva o non configurato
    guest_mode: bool = False
