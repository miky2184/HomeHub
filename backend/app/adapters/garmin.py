"""Adapter Garmin Connect — Fase 6 (roadmap), non ancora attivo.

Idea: leggere gli allenamenti effettivamente svolti da Garmin Connect (account
già disponibile, vedi ARCHITECTURE.md §2/§9) e confrontarli con il piano
settimanale inserito manualmente (app.db.models.TrainingSession), così da
marcare automaticamente una sessione come "fatta".

TODO quando si arriva a questa fase:
- autenticazione con `python-garminconnect` (API non ufficiale) usando
  GARMIN_EMAIL / GARMIN_PASSWORD da .env
- job periodico (APScheduler) che sincronizza le attività recenti
- logica di match tra attività Garmin e sessione pianificata (es. per data/tipo)
"""

from app.adapters.base import SourceAdapter
from app.core.config import get_settings

settings = get_settings()


class GarminAdapter(SourceAdapter):
    cache_ttl = 3600

    @property
    def is_configured(self) -> bool:
        return bool(settings.garmin_email and settings.garmin_password)

    async def fetch(self) -> list[dict]:
        raise NotImplementedError("Integrazione Garmin pianificata per una fase futura (roadmap Fase 6)")

    def normalize(self, raw: list[dict]) -> list[dict]:
        return raw
