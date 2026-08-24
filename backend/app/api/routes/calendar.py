from fastapi import APIRouter

from app.adapters.google_calendar import GoogleCalendarAdapter
from app.schemas.common import CalendarEvent, CalendarEventCreate, CalendarEventUpdate, CalendarInfo
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


@router.patch("/events/{event_id}", response_model=CalendarEvent)
async def update_event(event_id: str, payload: CalendarEventUpdate) -> CalendarEvent:
    adapter: GoogleCalendarAdapter = calendar_adapter
    event = await adapter.perform_action("update_event", {"event_id": event_id, **payload.model_dump()})
    cache.invalidate("calendar_events")
    return event


@router.delete("/events/{event_id}", status_code=204)
async def delete_event(event_id: str, calendar_id: str) -> None:
    """calendar_id come query param: un evento Google Calendar è sempre
    scoped a un calendario specifico, serve per sapere dove cercarlo."""
    adapter: GoogleCalendarAdapter = calendar_adapter
    await adapter.perform_action("delete_event", {"event_id": event_id, "calendar_id": calendar_id})
    cache.invalidate("calendar_events")
