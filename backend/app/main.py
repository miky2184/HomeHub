import logging
from contextlib import asynccontextmanager

from bring_api.exceptions import BringException
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError as GoogleHttpError

from app.api.routes import auth, calendar, chores, home, inventory, menu, settings as settings_routes, shopping, todo, training
from app.core.auth import SESSION_COOKIE_NAME, verify_session_token
from app.core.config import get_settings
from app.core.runtime_settings import effective_settings, refresh_overrides
from app.db.base import SessionLocal
from app.services.aggregator import bring_adapter

settings = get_settings()
logger = logging.getLogger(__name__)

# Uniche rotte /api/ accessibili senza sessione valida: servono proprio a
# sapere se serve il login e a farlo. Tutto il resto sotto /api/ passa dal
# middleware qui sotto — un solo posto invece di aggiungere una dependency
# ad ogni singolo router già esistente.
_PUBLIC_API_PATHS = {"/api/health", "/api/auth/status", "/api/auth/login"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Carica gli override salvati da Impostazioni (app_config) prima di
    # accettare richieste, altrimenti gli adapter partirebbero con le sole
    # credenziali di .env finché non arriva la prima chiamata a
    # PUT /api/settings. Non blocca l'avvio se il DB non è ancora
    # raggiungibile (stesso principio del resto dell'app: parte comunque,
    # fallisce solo sulle rotte che dipendono da Postgres).
    try:
        db = SessionLocal()
        try:
            refresh_overrides(db)
        finally:
            db.close()
    except Exception:
        logger.exception("Impossibile caricare gli override da Impostazioni all'avvio, uso solo .env")

    yield
    # chiude la sessione HTTP verso Bring! (se mai aperta), evita di lasciarla
    # appesa allo spegnimento del processo
    await bring_adapter.aclose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Blocca ogni rotta /api/ (tranne quelle di login, vedi
    _PUBLIC_API_PATHS) senza un cookie di sessione valido — vedi
    app/core/auth.py. Registrato dopo CORSMiddleware qui sopra: in Starlette
    il primo middleware aggiunto resta il più esterno, quindi CORS avvolge
    anche questo e aggiunge comunque i suoi header alle risposte 401 che
    restituiamo qui, non solo a quelle che arrivano fino alle rotte vere."""
    if request.url.path.startswith("/api/") and request.url.path not in _PUBLIC_API_PATHS:
        es = effective_settings()
        if es.app_password_hash:  # "" = login non configurato, vedi core/config.py
            token = request.cookies.get(SESSION_COOKIE_NAME)
            if not verify_session_token(token, es.session_secret_key, es.app_password_hash):
                return JSONResponse(status_code=401, content={"detail": "Non autenticato"})
    return await call_next(request)


@app.exception_handler(BringException)
async def bring_exception_handler(request: Request, exc: BringException) -> JSONResponse:
    # Non propaghiamo lo stack trace grezzo al client: credenziali sbagliate
    # o Bring! momentaneamente irraggiungibile non devono sembrare un bug
    # nostro, ma un problema di quella specifica integrazione.
    return JSONResponse(
        status_code=503,
        content={"detail": f"Bring! non raggiungibile o credenziali non valide: {exc}"},
    )


@app.exception_handler(GoogleAuthError)
async def google_auth_exception_handler(request: Request, exc: GoogleAuthError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": f"Google Calendar: refresh token non valido o revocato ({exc})"},
    )


@app.exception_handler(GoogleHttpError)
async def google_http_exception_handler(request: Request, exc: GoogleHttpError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": f"Google Calendar non raggiungibile: {exc}"},
    )


app.include_router(auth.router)
app.include_router(home.router)
app.include_router(calendar.router)
app.include_router(menu.router)
app.include_router(training.router)
app.include_router(shopping.router)
app.include_router(inventory.router)
app.include_router(todo.router)
app.include_router(chores.router)
app.include_router(settings_routes.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
