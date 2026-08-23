from fastapi import APIRouter

from app.adapters.google_calendar import GoogleCalendarAdapter
from app.schemas.common import CalendarEvent, CalendarEventCreate
from app.services import cache
from app.services.aggregator import calendar_adapter, get_calendar_events

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/events", response_model=list[CalendarEvent])
async def list_events() -> list[CalendarEvent]:
    return await get_calendar_events()


@router.post("/events", response_model=CalendarEvent)
async def add_event(payload: CalendarEventCreate) -> CalendarEvent:
    adapter: GoogleCalendarAdapter = calendar_adapter
    event = await adapter.perform_action("add_event", payload.model_dump())
    cache.invalidate("calendar_events")
    return event
