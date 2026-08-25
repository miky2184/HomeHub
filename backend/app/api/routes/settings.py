"""Uniche scritture su app_config (config runtime che vince su .env) —
vedi app/core/runtime_settings.py per come vengono lette altrove."""

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.runtime_settings import SECRET_FIELDS, effective_settings, overridden_keys, refresh_overrides
from app.db.base import get_db
from app.db.models import AppConfig
from app.schemas.common import AppSettingsOut, AppSettingsUpdate
from app.services import cache
from app.services.aggregator import bring_adapter, calendar_adapter, garmin_adapter

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Se uno di questi campi cambia, l'adapter corrispondente ha già una
# connessione/sessione autenticata in cache con le credenziali vecchie
# (vedi _get_service/_get_client negli adapter) — va invalidata subito,
# altrimenti continua a usare quella vecchia fino al riavvio del backend.
_GOOGLE_CREDENTIAL_FIELDS = {"google_client_id", "google_client_secret", "google_refresh_token"}
_BRING_CREDENTIAL_FIELDS = {"bring_email", "bring_password"}
_GARMIN_CREDENTIAL_FIELDS = {"garmin_email", "garmin_password"}
_WEATHER_FIELDS = {"weather_city", "weather_latitude", "weather_longitude"}


def _to_out(db: Session) -> AppSettingsOut:
    s = effective_settings()
    overridden = overridden_keys(db)
    return AppSettingsOut(
        family_name=s.family_name,
        weather_city=s.weather_city,
        weather_latitude=s.weather_latitude,
        weather_longitude=s.weather_longitude,
        background_theme=s.background_theme,
        shopping_preview_limit=s.shopping_preview_limit,
        google_client_id=s.google_client_id,
        google_client_secret_set="google_client_secret" in overridden,
        google_refresh_token_set="google_refresh_token" in overridden,
        google_calendar_ids=s.google_calendar_ids,
        bring_email=s.bring_email,
        bring_password_set="bring_password" in overridden,
        garmin_email=s.garmin_email,
        garmin_password_set="garmin_password" in overridden,
    )


@router.get("", response_model=AppSettingsOut)
def get_app_settings(db: Session = Depends(get_db)) -> AppSettingsOut:
    return _to_out(db)


@router.put("", response_model=AppSettingsOut)
async def update_app_settings(payload: AppSettingsUpdate, db: Session = Depends(get_db)) -> AppSettingsOut:
    changed = payload.model_dump(exclude_unset=True)

    for key, value in changed.items():
        # Vuoto per qualunque tipo (None, stringa vuota/spazi, o [] per i
        # campi lista come google_calendar_ids) rimuove l'override e torna
        # a .env — prima le liste non erano riconosciute, quindi svuotare
        # del tutto un campo lista lo salvava come override "esplicitamente
        # vuoto" invece di farlo tornare a .env come documentato.
        is_empty = (
            value is None
            or (isinstance(value, str) and value.strip() == "")
            or (isinstance(value, list) and len(value) == 0)
        )
        row = db.get(AppConfig, key)
        if is_empty:
            if row is not None:
                db.delete(row)
            continue
        stored_value = json.dumps(value) if isinstance(value, list) else str(value)
        if row is None:
            db.add(AppConfig(key=key, value=stored_value))
        else:
            row.value = stored_value

    db.commit()
    refresh_overrides(db)

    changed_keys = set(changed)
    if changed_keys & _GOOGLE_CREDENTIAL_FIELDS:
        calendar_adapter._service = None
    if changed_keys & _BRING_CREDENTIAL_FIELDS:
        await bring_adapter.aclose()  # chiude la sessione aiohttp vecchia, azzera _bring/_session/_list_uuid
    if changed_keys & _GARMIN_CREDENTIAL_FIELDS:
        garmin_adapter._client = None
    if changed_keys & _WEATHER_FIELDS:
        cache.invalidate("weather_coords")
        cache.invalidate("weather_raw")

    return _to_out(db)
