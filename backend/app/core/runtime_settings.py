"""Config "effettiva": parte dai valori .env (Settings, immutabile) e
sovrascrive con quanto salvato in app_config dalla pagina Impostazioni, se
presente e non vuoto — altrimenti resta il valore da .env. Vale anche per le
credenziali delle integrazioni (Google/Bring!/Garmin): scelta esplicita
dell'utente, per poterle gestire da UI senza toccare il file .env sul NUC.

Uniche scritture su app_config: api/routes/settings.py. Consumatori degli
override: services/aggregator.py (weather, family_name) e gli adapter
(google_calendar.py, bring.py, garmin.py) — chiamano effective_settings()
invece di leggere il singleton di get_settings() direttamente.

_overrides è una cache in-memory di processo (non una query Postgres ad ogni
singola lettura): la ricarica refresh_overrides() all'avvio dell'app e ad
ogni salvataggio da Impostazioni, non ad ogni richiesta.
"""

import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import AppConfig

logger = logging.getLogger(__name__)

# Campo app_config -> tipo per il parsing di value (sempre testo su riga).
FIELD_TYPES: dict[str, type] = {
    # Scritto solo da api/routes/auth.py:change_password (non dalla PUT
    # generica di Impostazioni, che richiede invece la verifica esplicita
    # della password attuale) — letto qui insieme a tutto il resto perché
    # il middleware di autenticazione legge comunque da effective_settings().
    "app_password_hash": str,
    "family_name": str,
    "weather_city": str,
    "weather_latitude": float,
    "weather_longitude": float,
    "background_theme": str,
    "shopping_preview_limit": int,
    "google_client_id": str,
    "google_client_secret": str,
    "google_refresh_token": str,
    "google_calendar_ids": list,
    "bring_email": str,
    "bring_password": str,
    "garmin_email": str,
    "garmin_password": str,
}

# Mai restituiti al frontend dopo il salvataggio: GET /api/settings ritorna
# solo "<campo>_set" (bool), mai il valore vero — vedi api/routes/settings.py.
SECRET_FIELDS = {"google_client_secret", "google_refresh_token", "bring_password", "garmin_password"}

_overrides: dict[str, object] = {}


def refresh_overrides(db: Session) -> None:
    """Ricarica la cache in-memory da app_config. Da chiamare all'avvio
    dell'app (main.py, lifespan) e subito dopo ogni scrittura da
    Impostazioni, così l'override è effettivo senza riavviare il backend."""
    global _overrides
    rows = db.execute(select(AppConfig)).scalars().all()
    parsed: dict[str, object] = {}
    for row in rows:
        field_type = FIELD_TYPES.get(row.key)
        if field_type is None or not row.value:
            continue
        try:
            parsed[row.key] = json.loads(row.value) if field_type is list else field_type(row.value)
        except (ValueError, json.JSONDecodeError):
            logger.warning("app_config: valore non valido per %s, ignorato", row.key)
    _overrides = parsed


def effective_settings() -> Settings:
    """Copia di Settings con gli override sopra ai valori .env — una copia
    nuova ad ogni chiamata (non muta il singleton di get_settings()), così
    rimuovere un override da Impostazioni torna semplicemente al valore
    .env originale invece di restare "sporco" per sempre."""
    if not _overrides:
        return get_settings()
    return get_settings().model_copy(update=_overrides)


def overridden_keys(db: Session) -> set[str]:
    """Chiavi che hanno oggi una riga in app_config (usato solo per i campi
    segreti, per sapere se mostrare "impostato" nel form senza mai rimandare
    il valore vero al frontend)."""
    return set(db.execute(select(AppConfig.key)).scalars().all())
