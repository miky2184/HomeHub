"""Configurazione centralizzata dell'app, letta da variabili d'ambiente (.env)."""

import logging
import secrets
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Generale ---
    app_name: str = "HomeHub backend"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:5173"]

    # --- Login (unico, condiviso da tutta la famiglia — niente account per
    # persona, coerente con la scelta "no multi-utente" di HomeHub). Vuoto =
    # login disattivato (nessuna password ancora configurata): tutte le
    # richieste passano, comodo per non restare bloccati fuori subito dopo
    # il primo deploy di questa feature. app_password_hash è sovrascrivibile
    # da app_config (vedi runtime_settings.py): la "Cambia password" in
    # Impostazioni scrive lì, .env resta solo il valore iniziale. Genera
    # l'hash con backend/scripts/generate_password_hash.py — vedi DEPLOY.md.
    # In .env va scritto con i "$" raddoppiati ($$): un hash bcrypt è pieno
    # di "$", e "docker compose" interpola anche il contenuto dei file
    # caricati con "env_file:" come se fossero riferimenti a variabili
    # ($UlAhzEuW... veniva letto come "sostituisci con la variabile
    # UlAhzEuW", inesistente → stringa vuota, troncando l'hash a metà: bug
    # reale riscontrato in produzione). "$$" è la sequenza che Compose
    # stesso usa per un "$" letterale, quindi la despia lui da solo passando
    # il valore al container. Il validator qui sotto la despia anche per chi
    # lancia il backend fuori Docker (dove .env viene letto raw, senza
    # quel passaggio di Compose) — vedi backend/scripts/generate_password_hash.py,
    # che stampa già la versione raddoppiata pronta da incollare.
    app_password_hash: str = ""
    # Chiave per firmare il cookie di sessione (30 giorni, vedi core/auth.py)
    # — deve restare la stessa tra un riavvio e l'altro, altrimenti ogni
    # riavvio del backend disconnette tutti. Se lasciata vuota ne genero una
    # casuale all'avvio (solo per non bloccare lo sviluppo locale): in
    # produzione va messa in .env, altrimenti ogni deploy fa relogin a tutti.
    session_secret_key: str = ""
    # true solo se HomeHub è servito in HTTPS: un cookie "Secure" su HTTP
    # semplice non verrebbe mai inviato dal browser, disconnettendo tutti.
    session_cookie_secure: bool = False

    # --- Personalizzazione da Impostazioni (nessun equivalente "di sistema":
    # esistono solo per essere sovrascritti da app_config, vedi
    # app/core/runtime_settings.py — questi default valgono solo se non è
    # mai stato salvato nulla da Impostazioni) ---
    family_name: str = ""
    background_theme: str = ""  # chiave della palette (vedi frontend/src/lib/palette.ts), "" = predefinito
    shopping_preview_limit: int = 5  # quanti prodotti mostrare nell'anteprima della card "Lista della spesa" in Home

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

    @field_validator("app_password_hash")
    @classmethod
    def _unescape_dollar(cls, v: str) -> str:
        # Vedi il commento sul campo sopra: "$$" -> "$". Un hash bcrypt vero
        # non contiene mai "$$" di suo (i tre separatori "$2b$12$..." non
        # sono mai adiacenti), quindi questa sostituzione è sempre sicura
        # anche se il valore arriva già "giusto" (es. da .env letto fuori
        # Docker, o da un vecchio hash salvato prima di questa modifica).
        return v.replace("$$", "$")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.session_secret_key:
        logger.warning(
            "SESSION_SECRET_KEY non impostata in .env: ne uso una generata al volo, "
            "che cambierà (disconnettendo tutti) ad ogni riavvio del backend. "
            "Impostala in .env per una sessione stabile tra i riavvii."
        )
        settings.session_secret_key = secrets.token_hex(32)
    return settings
