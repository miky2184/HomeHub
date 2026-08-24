"""Adapter Garmin Connect (Fase 6, ora attiva) — integrazione reale tramite
la libreria non ufficiale `garminconnect` (https://pypi.org/project/garminconnect/).

Idea: confrontare, giorno per giorno, il piano allenamenti inserito a mano
(app.db.models.TrainingSession) con le attività effettivamente registrate su
Garmin quel giorno. Se c'è un'attività, la sessione pianificata viene marcata
automaticamente come "fatta" (vedi app/api/routes/training.py) e viene
mostrato un breve riepilogo (es. "Corsa · 8.2 km · 42:15").

Login e MFA: Garmin richiede spesso un codice MFA al primo login interattivo.
Il flusso qui è pensato per **non** richiederlo ad ogni richiesta HTTP:
- `backend/scripts/garmin_login_setup.py` va eseguito una tantum (a mano, con
  un terminale) per fare il login iniziale ed eventualmente inserire il
  codice MFA; salva una sessione riutilizzabile in `backend/.garmin_tokens/`.
- A runtime, l'adapter carica quella sessione salvata: se è ancora valida non
  serve alcuna interazione. Se è scaduta/mancante, l'adapter fallisce con un
  errore chiaro invece di restare in attesa di un MFA che non può arrivare
  (nessun terminale interattivo in un servizio backend).

Finché GARMIN_EMAIL/GARMIN_PASSWORD non sono configurate (o il setup non è
stato fatto), l'adapter è semplicemente "non configurato" e non fa nulla:
il piano allenamenti resta gestito solo manualmente, senza errori.
"""

from datetime import date
from pathlib import Path

from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError

from app.adapters.base import SourceAdapter
from app.core.config import get_settings

settings = get_settings()

TOKENSTORE_DIR = Path(__file__).resolve().parent.parent.parent / ".garmin_tokens"


class GarminAdapter(SourceAdapter):
    cache_ttl = 3600  # le attività di un giorno passato non cambiano più

    def __init__(self) -> None:
        self._client: Garmin | None = None

    @property
    def is_configured(self) -> bool:
        return bool(settings.garmin_email and settings.garmin_password)

    def _get_client(self) -> Garmin:
        if self._client is None:
            client = Garmin(settings.garmin_email, settings.garmin_password)
            # tokenstore: se il setup una tantum è già stato fatto, qui non
            # serve nessuna interazione (nessun prompt_mfa passato di proposito:
            # a runtime, se serve davvero un MFA, deve fallire in modo chiaro,
            # non restare in attesa di un input che non arriverà mai).
            client.login(str(TOKENSTORE_DIR))
            self._client = client
        return self._client

    async def fetch_activities_for_date(self, day: date) -> list[dict]:
        """Attività Garmin registrate in un giorno specifico, in un formato
        già leggero da mostrare in UI (niente dati grezzi dell'API)."""
        if not self.is_configured:
            return []
        client = self._get_client()
        raw = client.get_activities_by_date(day.isoformat(), day.isoformat())
        return [self._summarize(activity) for activity in raw]

    @staticmethod
    def _summarize(activity: dict) -> dict:
        name = activity.get("activityName") or activity.get("activityType", {}).get("typeKey", "Attività")
        distance_km = round(activity["distance"] / 1000, 1) if activity.get("distance") else None
        duration_min = round(activity["duration"] / 60) if activity.get("duration") else None
        parts = [name]
        if distance_km:
            parts.append(f"{distance_km} km")
        if duration_min:
            parts.append(f"{duration_min} min")
        return {"summary": " · ".join(parts), "raw_name": name}

    async def fetch(self) -> list[dict]:
        raise NotImplementedError("Usare fetch_activities_for_date: Garmin non ha un concetto di 'lista unica'")

    def normalize(self, raw: list[dict]) -> list[dict]:
        return raw


# Eccezioni da trattare come "Garmin irraggiungibile o sessione scaduta" nel
# gestore centralizzato (app/main.py) — non devono far fallire il resto della
# pagina Allenamenti, solo quella specifica arricchitura.
GARMIN_ERRORS = (GarminConnectAuthenticationError, GarminConnectConnectionError)
