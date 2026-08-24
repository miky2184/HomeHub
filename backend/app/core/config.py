"""Configurazione centralizzata dell'app, letta da variabili d'ambiente (.env)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Generale ---
    app_name: str = "HomeHub backend"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:5173"]

    # --- Postgres (istanza esistente, schema dedicato) ---
    database_url: str = "postgresql+psycopg://homehub:homehub@localhost:5432/homehub"
    database_schema: str = "homehub"

    # --- Google Calendar (OAuth2) ---
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""
    google_calendar_ids: list[str] = []

    # --- Bring! (API non ufficiale) ---
    bring_email: str = ""
    bring_password: str = ""

    # --- Garmin Connect (API non ufficiale) — solo per il piano pianificato
    # (allenamenti assegnati ai giorni); gli allenamenti svolti si leggono
    # invece da dieta.allenamento (vedi sotto), già sincronizzata da un'altra
    # web app dell'utente con dati più ricchi della sola API Garmin.
    garmin_email: str = ""
    garmin_password: str = ""

    # --- Schema "dieta" (stesso Postgres di homehub, altra web app) ---
    dieta_user_id: int | None = None

    # --- Web app esistenti: API key per-servizio ---
    finance_app_base_url: str = ""
    finance_app_api_key: str = ""
    menu_app_base_url: str = ""
    menu_app_api_key: str = ""
    inventory_app_base_url: str = ""
    inventory_app_api_key: str = ""

    # --- Cache/polling (secondi) ---
    cache_ttl_calendar: int = 300
    cache_ttl_bring: int = 120
    cache_ttl_apps: int = 900


@lru_cache
def get_settings() -> Settings:
    return Settings()
