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

import logging
import threading
from datetime import date
from pathlib import Path

from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError

from app.adapters.base import SourceAdapter
from app.core.config import get_settings
from app.core.runtime_settings import effective_settings

settings = get_settings()
logger = logging.getLogger(__name__)

TOKENSTORE_DIR = Path(__file__).resolve().parent.parent.parent / ".garmin_tokens"


class GarminAdapter(SourceAdapter):
    cache_ttl = 1800  # il chiamante (aggregator) applica questo TTL alla cache per mese

    def __init__(self) -> None:
        self._client: Garmin | None = None
        # fetch_calendar_month è sincrono e viene lanciato con
        # asyncio.to_thread per mesi diversi (Home e Attività possono
        # chiederne uno ciascuno quasi in contemporanea) — sono thread OS
        # reali, non semplici coroutine sullo stesso event loop, quindi
        # serve un threading.Lock (un asyncio.Lock non protegge tra thread
        # diversi) per non far scattare due login() in parallelo sullo
        # stesso account: è esattamente il rischio di rate limiting che il
        # docstring del modulo dice di voler evitare.
        self._client_lock = threading.Lock()

    @property
    def is_configured(self) -> bool:
        es = effective_settings()
        return bool(es.garmin_email and es.garmin_password)

    def _get_client(self) -> Garmin:
        with self._client_lock:
            if self._client is None:
                es = effective_settings()
                client = Garmin(es.garmin_email, es.garmin_password)
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
    def scheduled_workouts_by_date(calendar_month: dict) -> dict[str, dict]:
        """Data (YYYY-MM-DD) -> {"title": ..., "sport_type": ...} per
        l'allenamento assegnato quel giorno. Se più allenamenti sono
        assegnati allo stesso giorno, i titoli vengono uniti con " + " e si
        tiene lo sport_type del primo (nella pratica è sempre lo stesso)."""
        titles: dict[str, list[str]] = {}
        sport_types: dict[str, str] = {}
        for item in calendar_month.get("calendarItems", []):
            if item.get("itemType") != "workout" or not item.get("title"):
                continue
            # TEMPORANEO: per capire se una data "sbagliata" (es. un
            # allenamento di giovedì che appare sotto venerdì in HomeHub)
            # viene già così da Garmin o nasce nel nostro codice — vedi
            # conversazione del 26/08/2026. Da togliere una volta chiarito.
            logger.warning("[garmin-debug] item grezzo: date=%r title=%r", item.get("date"), item.get("title"))
            titles.setdefault(item["date"], []).append(item["title"].strip())
            sport_types.setdefault(item["date"], item.get("sportTypeKey"))
        return {
            day: {"title": " + ".join(dict.fromkeys(names)), "sport_type": sport_types.get(day)}
            for day, names in titles.items()
        }

    async def fetch(self) -> list[dict]:
        raise NotImplementedError("Usare fetch_calendar_month: Garmin non ha un concetto di 'lista unica'")

    def normalize(self, raw: list[dict]) -> list[dict]:
        return raw


# Eccezioni da trattare come "Garmin irraggiungibile o sessione scaduta" —
# non devono far fallire il resto della pagina Allenamenti, solo
# quell'arricchimento specifico (vedi services/aggregator.py).
GARMIN_ERRORS = (GarminConnectAuthenticationError, GarminConnectConnectionError)
