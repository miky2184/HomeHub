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


class CalendarEventUpdate(BaseModel):
    """Stessi campi di CalendarEventCreate: la modifica sostituisce sempre
    titolo/orario/tipo per intero (niente PATCH parziale), coerente col
    form di modifica che li mostra/invia tutti insieme."""

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


class InventoryItem(BaseModel):
    """Una riga in un contenitore, per "Sfoglia per contenitore" in Casa —
    a differenza di InventoryAlert non è legata a una scadenza imminente:
    è la lista completa di cosa c'è in quel cassetto/ripiano, per sostituire
    il foglio di carta sul frigo."""

    id: int
    name: str
    quantity: float | None = None
    unit: str | None = None
    expiry_date: date | None = None
    category: str | None = None


class InventoryContainer(BaseModel):
    id: int
    name: str
    items: list[InventoryItem]


class InventoryQuantityDelta(BaseModel):
    """+1/-1 (o +6, -1...) sulla quantità di un oggetto esistente da Casa —
    es. +6 comprando un fardello d'acqua, -1 bevendo un vino. Unica scrittura
    che HomeHub fa su home_inventory: niente creazione/eliminazione oggetti,
    quella resta in home_inventory_web."""

    delta: int


class HourlyForecast(BaseModel):
    time: datetime
    temperature_c: float | None = None
    condition: str | None = None
    precipitation_probability: int | None = None


class DailyForecast(BaseModel):
    date: date
    condition: str | None = None
    temperature_min: float | None = None
    temperature_max: float | None = None
    precipitation_probability_max: int | None = None


class WeatherSnapshot(BaseModel):
    temperature_c: float | None = None
    condition: str | None = None
    city: str | None = None
    hourly: list[HourlyForecast] = []
    daily: list[DailyForecast] = []  # da domani in poi, oggi già coperto da hourly
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


class HomeSummary(BaseModel):
    now: datetime
    family_name: str = ""  # da Impostazioni, mostrato nel saluto in Home
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


class AppSettingsOut(BaseModel):
    """Config effettiva (env + override), per popolare il form in
    Impostazioni. I campi segreto non tornano mai col valore vero: solo
    "<campo>_set" per sapere se è sovrascritto da qui (true) o si sta usando
    .env (false) — vedi runtime_settings.SECRET_FIELDS."""

    family_name: str = ""
    weather_city: str = "Milano"
    weather_latitude: float | None = None
    weather_longitude: float | None = None
    background_theme: str = ""
    google_client_id: str = ""
    google_client_secret_set: bool = False
    google_refresh_token_set: bool = False
    google_calendar_ids: list[str] = []
    bring_email: str = ""
    bring_password_set: bool = False
    garmin_email: str = ""
    garmin_password_set: bool = False


class AppSettingsUpdate(BaseModel):
    """PATCH parziale: solo i campi inviati vengono toccati (vedi
    exclude_unset in api/routes/settings.py). Per un campo inviato,
    stringa vuota/None = rimuovi l'override e torna a .env; qualunque altro
    valore = sovrascrivi. Per i campi segreto, lasciare il form vuoto invia
    semplicemente il campo non impostato nel payload (nessuna modifica);
    serve un'azione esplicita di "ripristina .env" nel frontend per inviare
    la stringa vuota e cancellare l'override."""

    family_name: str | None = None
    weather_city: str | None = None
    weather_latitude: float | None = None
    weather_longitude: float | None = None
    background_theme: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_refresh_token: str | None = None
    google_calendar_ids: list[str] | None = None
    bring_email: str | None = None
    bring_password: str | None = None
    garmin_email: str | None = None
    garmin_password: str | None = None
