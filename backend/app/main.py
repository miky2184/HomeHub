from contextlib import asynccontextmanager

from bring_api.exceptions import BringException
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError as GoogleHttpError

from app.api.routes import calendar, home, inventory, menu, shopping, training
from app.core.config import get_settings
from app.services.aggregator import bring_adapter

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
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


app.include_router(home.router)
app.include_router(calendar.router)
app.include_router(menu.router)
app.include_router(training.router)
app.include_router(shopping.router)
app.include_router(inventory.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
