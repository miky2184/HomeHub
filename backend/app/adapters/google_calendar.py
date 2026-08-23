"""Adapter Google Calendar.

TODO (integrazione reale):
- completare il flusso OAuth2 (google-auth-oauthlib) per ottenere il refresh
  token una tantum e salvarlo in .env (GOOGLE_REFRESH_TOKEN)
- usare google-api-python-client per leggere gli eventi dei calendari in
  GOOGLE_CALENDAR_IDS e per creare nuovi eventi (azione "add_event")

Finché le credenziali OAuth non sono configurate, l'adapter ritorna dati di
esempio, così il resto dell'app (Home, tab Calendario) è già utilizzabile.
"""

from datetime import datetime, timedelta

from app.adapters.base import WritableSourceAdapter
from app.core.config import get_settings
from app.schemas.common import CalendarEvent

settings = get_settings()


class GoogleCalendarAdapter(WritableSourceAdapter):
    cache_ttl = settings.cache_ttl_calendar

    @property
    def is_configured(self) -> bool:
        return bool(settings.google_refresh_token and settings.google_client_id)

    async def fetch(self) -> list[dict]:
        if not self.is_configured:
            return self._mock_events()
        # TODO: chiamata reale a Google Calendar API con le credenziali OAuth
        raise NotImplementedError("Integrazione Google Calendar non ancora configurata")

    def normalize(self, raw: list[dict]) -> list[CalendarEvent]:
        return [CalendarEvent(**item) for item in raw]

    async def perform_action(self, action: str, payload: dict) -> CalendarEvent:
        if action != "add_event":
            raise ValueError(f"Azione non supportata: {action}")
        if not self.is_configured:
            # In assenza di credenziali reali, restituiamo comunque un evento
            # "creato" così il frontend può essere sviluppato/testato.
            return CalendarEvent(
                id="mock-new-event",
                calendar_id=payload["calendar_id"],
                calendar_label="Famiglia",
                title=payload["title"],
                start=payload["start"],
                end=payload["end"],
                all_day=payload.get("all_day", False),
            )
        # TODO: chiamata reale di scrittura verso Google Calendar API
        raise NotImplementedError("Integrazione Google Calendar non ancora configurata")

    @staticmethod
    def _mock_events() -> list[dict]:
        now = datetime.now()
        today_10 = now.replace(hour=10, minute=0, second=0, microsecond=0)
        today_1930 = now.replace(hour=19, minute=30, second=0, microsecond=0)
        return [
            {
                "id": "mock-1",
                "calendar_id": "famiglia",
                "calendar_label": "Famiglia",
                "title": "Piscina Sofia",
                "start": today_10,
                "end": today_10 + timedelta(hours=1),
                "all_day": False,
            },
            {
                "id": "mock-2",
                "calendar_id": "famiglia",
                "calendar_label": "Famiglia",
                "title": "Cena dai nonni",
                "start": today_1930,
                "end": today_1930 + timedelta(hours=2),
                "all_day": False,
            },
        ]
