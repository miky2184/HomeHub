from fastapi import APIRouter

from app.adapters.google_calendar import GoogleCalendarAdapter
from app.schemas.common import CalendarEvent, CalendarEventCreate, CalendarInfo
from app.services import cache
from app.services.aggregator import calendar_adapter, get_calendar_events

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/events", response_model=list[CalendarEvent])
async def list_events() -> list[CalendarEvent]:
    return await get_calendar_events()


@router.get("/calendars", response_model=list[CalendarInfo])
async def list_calendars() -> list[CalendarInfo]:
    """I calendari configurati (GOOGLE_CALENDAR_IDS), per il selettore nel
    form "Aggiungi evento" — niente più calendar_id inventati lato frontend."""
    adapter: GoogleCalendarAdapter = calendar_adapter
    return [CalendarInfo(**c) for c in await adapter.list_calendars()]


@router.post("/events", response_model=CalendarEvent)
async def add_event(payload: CalendarEventCreate) -> CalendarEvent:
    adapter: GoogleCalendarAdapter = calendar_adapter
    event = await adapter.perform_action("add_event", payload.model_dump())
    cache.invalidate("calendar_events")
    return event
