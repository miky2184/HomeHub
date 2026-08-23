"""Schema dati unificato "HomeHub": ciò che il frontend consuma, indipendentemente
dalla fonte reale (Google, Bring!, le web app esistenti, o le tabelle manuali)."""

from datetime import date, datetime

from pydantic import BaseModel


class CalendarEvent(BaseModel):
    id: str
    calendar_id: str
    calendar_label: str  # es. "Famiglia", "Scuola" — per il pallino colorato in UI
    title: str
    start: datetime
    end: datetime
    all_day: bool = False


class CalendarEventCreate(BaseModel):
    calendar_id: str
    title: str
    start: datetime
    end: datetime
    all_day: bool = False


class MenuDay(BaseModel):
    day_of_week: int
    school_meal: str | None = None
    home_meal: str | None = None


class MenuWeek(BaseModel):
    week_start_date: date
    days: list[MenuDay]


class SchoolMenuUpsert(BaseModel):
    week_start_date: date
    day_of_week: int
    meal_text: str


class TrainingSessionOut(BaseModel):
    id: int
    week_start_date: date
    day_of_week: int
    session_text: str
    done: bool


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
    id: str
    item_name: str
    quantity: float | None = None
    unit: str | None = None
    reason: str = "low_stock"


class WeatherSnapshot(BaseModel):
    temperature_c: float | None = None
    condition: str | None = None


class HomeSummary(BaseModel):
    now: datetime
    weather: WeatherSnapshot | None = None
    today_events: list[CalendarEvent]
    today_menu: MenuDay | None = None
    next_training: TrainingSessionOut | None = None
    shopping_preview: list[ShoppingItem]
    shopping_total_count: int
    inventory_alerts: list[InventoryAlert]
