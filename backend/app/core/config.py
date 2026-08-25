"""Configurazione centralizzata dell'app, letta da variabili d'ambiente (.env)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Generale ---
    app_name: str = "HomeHub backend"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:5173"]

    # --- Personalizzazione da Impostazioni (nessun equivalente "di sistema":
    # esistono solo per essere sovrascritti da app_config, vedi
    # app/core/runtime_settings.py — questi default valgono solo se non è
    # mai stato salvato nulla da Impostazioni) ---
    family_name: str = ""
    background_theme: str = ""  # chiave della palette (vedi frontend/src/lib/palette.ts), "" = predefinito

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

    # --- Schema "dieta" (stesso Postgres di homehub, altra web app): usato
    # sia per gli allenamenti svolti (dieta.allenamento) sia per la cena di
    # casa (dieta.menu_settimanale, il piano nutrizionale copre tutta la
    # famiglia) — stesso user_id per entrambi.
    dieta_user_id: int | None = None

    # --- Schema "home_inventory" (stesso Postgres, altra web app: niente
    # config qui, si legge sempre — vedi app/db/home_inventory_models.py e
    # app/services/aggregator.py:get_inventory_alerts) ---

    # --- Meteo (Open-Meteo, gratuita, senza chiave) ---
    # weather_city è sempre usata come etichetta mostrata in UI. Se
    # weather_latitude/longitude sono compilate, hanno la priorità per il
    # meteo vero e proprio (niente geocoding, coordinate esatte di casa
    # invece del centro città) — altrimenti si geocodifica weather_city.
    weather_city: str = "Milano"
    weather_latitude: float | None = None
    weather_longitude: float | None = None

    # --- Cache/polling (secondi) ---
    cache_ttl_calendar: int = 300
    cache_ttl_bring: int = 120
    cache_ttl_apps: int = 900


@lru_cache
def get_settings() -> Settings:
    return Settings()
