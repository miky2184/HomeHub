"""Adapter Garmin Connect — integrazione reale tramite la libreria non
ufficiale `garminconnect` (https://pypi.org/project/garminconnect/).

Workflow reale dell'utente (non quello ipotizzato inizialmente): il coach
manda gli allenamenti via WhatsApp, l'utente li **crea e li assegna ai
giorni direttamente su Garmin Connect** (calendario "Allenamenti"). Quindi
Garmin stesso è la fonte del piano, non un inserimento manuale in HomeHub:
- `client.get_scheduled_workouts(year, month)` ritorna, per un mese, sia gli
  allenamenti pianificati (`itemType: "workout"`, con `title`/`date`) sia le
  attività già svolte (`itemType: "activity"`) — un'unica chiamata copre
  entrambe le cose, verificata con dati reali (non documentazione, che per
  questo endpoint non ufficiale non esiste in modo affidabile):
  - `distance` è in **centimetri**, `duration` in **millisecondi** per gli
    item di tipo "activity" (verificato confrontando i valori con le distanze/
    durate reali delle attività: es. una nuotata di ~510m dava
    distance=51371).
- Il piano scritto a mano in app.db.models.TrainingSession resta come
  fallback per i giorni senza un allenamento assegnato su Garmin (o se
  Garmin non è configurato): non è stato rimosso, solo reso secondario.

Login e MFA: Garmin richiede spesso un codice MFA al primo login interattivo.
Il flusso qui è pensato per **non** richiederlo ad ogni richiesta HTTP:
- `backend/scripts/garmin_login_setup.py` va eseguito una tantum (a mano, con
  un terminale) per fare il login iniziale ed eventualmente inserire il
  codice MFA; salva una sessione riutilizzabile in `backend/.garmin_tokens/`.
- A runtime, l'adapter carica quella sessione salvata: se è ancora valida non
  serve alcuna interazione. Se è scaduta/mancante, fallisce con un errore
  chiaro invece di restare in attesa di un MFA che non può arrivare (nessun
  terminale interattivo in un servizio backend).

Finché GARMIN_EMAIL/GARMIN_PASSWORD non sono configurate (o il setup non è
stato fatto), l'adapter è semplicemente "non configurato" e non fa nulla.
"""

from datetime import date
from pathlib import Path

from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError

from app.adapters.base import SourceAdapter
from app.core.config import get_settings

settings = get_settings()

TOKENSTORE_DIR = Path(__file__).resolve().parent.parent.parent / ".garmin_tokens"


class GarminAdapter(SourceAdapter):
    cache_ttl = 1800  # il chiamante (aggregator) applica questo TTL alla cache per mese

    def __init__(self) -> None:
        self._client: Garmin | None = None

    @property
    def is_configured(self) -> bool:
        return bool(settings.garmin_email and settings.garmin_password)

    def _get_client(self) -> Garmin:
        if self._client is None:
            client = Garmin(settings.garmin_email, settings.garmin_password)
            # Nessun prompt_mfa passato di proposito: a runtime, se serve
            # davvero un MFA, deve fallire in modo chiaro (nessun terminale
            # interattivo qui), non restare in attesa di un input che non
            # arriverà mai. Il setup una tantum (garmin_login_setup.py) è il
            # posto giusto per gestire l'MFA.
            client.login(str(TOKENSTORE_DIR))
            self._client = client
        return self._client

    def fetch_calendar_month(self, year: int, month: int) -> dict:
        """Dati grezzi del calendario Garmin per un mese intero (allenamenti
        pianificati + attività svolte). Il chiamante (services/aggregator.py)
        mette in cache il risultato: qui nessuna cache, per restare un
        adapter "stupido" e facilmente testabile."""
        if not self.is_configured:
            return {"calendarItems": []}
        client = self._get_client()
        return client.get_scheduled_workouts(year, month)

    @staticmethod
    def scheduled_titles_by_date(calendar_month: dict) -> dict[str, str]:
        """Data (YYYY-MM-DD) -> titolo allenamento assegnato quel giorno.
        Se più allenamenti sono assegnati allo stesso giorno, i titoli
        vengono uniti con " + "."""
        titles: dict[str, list[str]] = {}
        for item in calendar_month.get("calendarItems", []):
            if item.get("itemType") != "workout" or not item.get("title"):
                continue
            titles.setdefault(item["date"], []).append(item["title"].strip())
        return {day: " + ".join(dict.fromkeys(names)) for day, names in titles.items()}

    @staticmethod
    def activity_summaries_by_date(calendar_month: dict) -> dict[str, list[str]]:
        """Data (YYYY-MM-DD) -> riepiloghi delle attività svolte quel giorno
        (es. "Modugno - 11km FL + 10×100 · 12.5 km · 68 min")."""
        summaries: dict[str, list[str]] = {}
        for item in calendar_month.get("calendarItems", []):
            if item.get("itemType") != "activity":
                continue
            title = item.get("title") or "Attività"
            distance_km = round(item["distance"] / 100_000, 1) if item.get("distance") else None
            duration_min = round(item["duration"] / 60_000) if item.get("duration") else None
            parts = [title]
            if distance_km:
                parts.append(f"{distance_km} km")
            if duration_min:
                parts.append(f"{duration_min} min")
            summaries.setdefault(item["date"], []).append(" · ".join(parts))
        return summaries

    async def fetch(self) -> list[dict]:
        raise NotImplementedError("Usare fetch_calendar_month: Garmin non ha un concetto di 'lista unica'")

    def normalize(self, raw: list[dict]) -> list[dict]:
        return raw


# Eccezioni da trattare come "Garmin irraggiungibile o sessione scaduta" —
# non devono far fallire il resto della pagina Allenamenti, solo
# quell'arricchimento specifico (vedi services/aggregator.py).
GARMIN_ERRORS = (GarminConnectAuthenticationError, GarminConnectConnectionError)
