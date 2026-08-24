"""Adapter Google Calendar — integrazione reale via google-api-python-client
+ google-auth-oauthlib (OAuth2, refresh token).

Per ottenere GOOGLE_REFRESH_TOKEN la prima volta: esegui una tantum
`backend/scripts/google_oauth_setup.py` (vedi quel file per le istruzioni)
dopo aver messo GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET in .env.

Finché GOOGLE_REFRESH_TOKEN non è configurato, l'adapter ritorna dati di
esempio, così il resto dell'app (Home, tab Calendario) è già utilizzabile
senza aver fatto il setup OAuth.
"""

from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.adapters.base import WritableSourceAdapter
from app.core.config import get_settings
from app.schemas.common import CalendarEvent

settings = get_settings()

SCOPES = ["https://www.googleapis.com/auth/calendar"]
# Finestra di eventi letti ad ogni fetch: non serve uno storico infinito, solo
# passato recentissimo (per "Oggi" a cavallo di mezzanotte) + futuro prossimo
# (per la tab Agenda).
_LOOKBACK_DAYS = 1
_LOOKAHEAD_DAYS = 30


class GoogleCalendarAdapter(WritableSourceAdapter):
    cache_ttl = settings.cache_ttl_calendar

    def __init__(self) -> None:
        self._service = None
        self._calendar_labels: dict[str, str] = {}

    @property
    def is_configured(self) -> bool:
        return bool(
            settings.google_refresh_token and settings.google_client_id and settings.google_client_secret
        )

    def _get_service(self):
        """Costruisce (e mette in cache) il client Calendar. Il refresh
        dell'access token è comunque automatico ad ogni chiamata da parte
        della libreria (finché il refresh token resta valido); lo facciamo
        anche qui una volta per fallire subito con un errore chiaro se le
        credenziali configurate non sono valide."""
        if self._service is None:
            credentials = Credentials(
                token=None,
                refresh_token=settings.google_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                scopes=SCOPES,
            )
            credentials.refresh(Request())
            self._service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        return self._service

    def _label_for(self, service, calendar_id: str) -> str:
        if calendar_id not in self._calendar_labels:
            try:
                info = service.calendarList().get(calendarId=calendar_id).execute()
                self._calendar_labels[calendar_id] = info.get("summary", calendar_id)
            except HttpError:
                self._calendar_labels[calendar_id] = calendar_id
        return self._calendar_labels[calendar_id]

    async def list_calendars(self) -> list[dict]:
        """I calendari configurati (GOOGLE_CALENDAR_IDS) con il loro nome
        visualizzato — usato dal frontend per il selettore nel form "Aggiungi
        evento" (niente più calendar_id inventati lato client)."""
        if not self.is_configured:
            return [{"id": "famiglia", "label": "Famiglia"}]
        service = self._get_service()
        return [{"id": cal_id, "label": self._label_for(service, cal_id)} for cal_id in settings.google_calendar_ids]

    async def fetch(self) -> list[dict]:
        if not self.is_configured:
            return self._mock_events()

        # google-api-python-client è sincrono: per il nostro volume di
        # chiamate (poche, con cache davanti in aggregator/services/cache.py)
        # va bene chiamarlo direttamente; se in futuro servisse non bloccare
        # l'event loop, spostare in asyncio.to_thread.
        service = self._get_service()
        now = datetime.now(timezone.utc)
        time_min = (now - timedelta(days=_LOOKBACK_DAYS)).isoformat()
        time_max = (now + timedelta(days=_LOOKAHEAD_DAYS)).isoformat()

        raw_events: list[dict] = []
        for calendar_id in settings.google_calendar_ids:
            label = self._label_for(service, calendar_id)
            response = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            for event in response.get("items", []):
                is_all_day = "date" in event["start"]
                raw_events.append(
                    {
                        "id": event["id"],
                        "calendar_id": calendar_id,
                        "calendar_label": label,
                        "title": event.get("summary", "(senza titolo)"),
                        "start": event["start"].get("dateTime", event["start"].get("date")),
                        "end": event["end"].get("dateTime", event["end"].get("date")),
                        "all_day": is_all_day,
                    }
                )
        return raw_events

    def normalize(self, raw: list[dict]) -> list[CalendarEvent]:
        return [CalendarEvent(**item) for item in raw]

    async def perform_action(self, action: str, payload: dict) -> CalendarEvent | None:
        if action == "add_event":
            return self._add_event(payload)
        if action == "update_event":
            return self._update_event(payload)
        if action == "delete_event":
            self._delete_event(payload)
            return None
        raise ValueError(f"Azione non supportata: {action}")

    def _add_event(self, payload: dict) -> CalendarEvent:
        if not self.is_configured:
            return CalendarEvent(
                id="mock-new-event",
                calendar_id=payload["calendar_id"],
                calendar_label="Famiglia",
                title=payload["title"],
                start=payload["start"],
                end=payload["end"],
                all_day=payload.get("all_day", False),
            )

        service = self._get_service()
        calendar_id = payload["calendar_id"]
        start, end = payload["start"], payload["end"]
        all_day = payload.get("all_day", False)
        body = {
            "summary": payload["title"],
            "start": {"date": start.date().isoformat()} if all_day else {"dateTime": start.isoformat()},
            "end": {"date": end.date().isoformat()} if all_day else {"dateTime": end.isoformat()},
        }
        created = service.events().insert(calendarId=calendar_id, body=body).execute()
        return CalendarEvent(
            id=created["id"],
            calendar_id=calendar_id,
            calendar_label=self._label_for(service, calendar_id),
            title=created.get("summary", payload["title"]),
            start=start,
            end=end,
            all_day=all_day,
        )

    def _update_event(self, payload: dict) -> CalendarEvent:
        """Sostituisce titolo/orario/tipo per intero (stessi campi di
        CalendarEventCreate, vedi CalendarEventUpdate) — niente PATCH
        parziale: più semplice e coerente col form di modifica, che li
        mostra/invia sempre tutti insieme."""
        calendar_id, event_id = payload["calendar_id"], payload["event_id"]
        start, end = payload["start"], payload["end"]
        all_day = payload.get("all_day", False)

        if not self.is_configured:
            return CalendarEvent(
                id=event_id,
                calendar_id=calendar_id,
                calendar_label="Famiglia",
                title=payload["title"],
                start=start,
                end=end,
                all_day=all_day,
            )

        service = self._get_service()
        body = {
            "summary": payload["title"],
            "start": {"date": start.date().isoformat()} if all_day else {"dateTime": start.isoformat()},
            "end": {"date": end.date().isoformat()} if all_day else {"dateTime": end.isoformat()},
        }
        updated = service.events().patch(calendarId=calendar_id, eventId=event_id, body=body).execute()
        return CalendarEvent(
            id=updated["id"],
            calendar_id=calendar_id,
            calendar_label=self._label_for(service, calendar_id),
            title=updated.get("summary", payload["title"]),
            start=start,
            end=end,
            all_day=all_day,
        )

    def _delete_event(self, payload: dict) -> None:
        if not self.is_configured:
            return
        service = self._get_service()
        service.events().delete(calendarId=payload["calendar_id"], eventId=payload["event_id"]).execute()

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
