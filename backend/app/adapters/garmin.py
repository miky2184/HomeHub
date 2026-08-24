"""Adapter Garmin Connect — integrazione reale tramite la libreria non
ufficiale `garminconnect` (https://pypi.org/project/garminconnect/).

Workflow reale dell'utente (non quello ipotizzato inizialmente): il coach
manda gli allenamenti via WhatsApp, l'utente li **crea e li assegna ai
giorni direttamente su Garmin Connect** (calendario "Allenamenti"). Quindi
Garmin stesso è la fonte del piano *pianificato*, non un inserimento manuale
in HomeHub:
- `client.get_scheduled_workouts(year, month)` ritorna, per un mese, gli
  allenamenti pianificati (`itemType: "workout"`, con `title`/`date`).
- Il piano scritto a mano in app.db.models.TrainingSession resta come
  fallback per i giorni senza un allenamento assegnato su Garmin (o se
  Garmin non è configurato): non è stato rimosso, solo reso secondario.

Gli allenamenti **svolti** invece NON si leggono da qui: l'utente li
sincronizza già, con dati molto più ricchi (FC, passo, TSS, dislivello...),
in `dieta.allenamento` tramite un'altra sua web app — vedi
`app/db/dieta_models.py` e `services/aggregator.get_dieta_activity`. Evita
anche di far fare a due servizi diversi lo stesso login su Garmin (rischio
concreto di rate limiting, osservato durante lo sviluppo).

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

    async def fetch(self) -> list[dict]:
        raise NotImplementedError("Usare fetch_calendar_month: Garmin non ha un concetto di 'lista unica'")

    def normalize(self, raw: list[dict]) -> list[dict]:
        return raw


# Eccezioni da trattare come "Garmin irraggiungibile o sessione scaduta" —
# non devono far fallire il resto della pagina Allenamenti, solo
# quell'arricchimento specifico (vedi services/aggregator.py).
GARMIN_ERRORS = (GarminConnectAuthenticationError, GarminConnectConnectionError)
