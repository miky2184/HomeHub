"""Login unico e condiviso (vedi app/core/auth.py). Uniche rotte pubbliche
sotto /api/ oltre a /api/health — l'app le usa per sapere se mostrare la
pagina di login e per farlo. Tutte le altre rotte passano dal middleware in
main.py, che le blocca senza un cookie di sessione valido."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import SESSION_COOKIE_NAME, SESSION_MAX_AGE_SECONDS, create_session_token, hash_password, verify_password, verify_session_token
from app.core.runtime_settings import effective_settings, refresh_overrides
from app.db.base import get_db
from app.db.models import AppConfig

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


def _is_authenticated(request: Request) -> bool:
    es = effective_settings()
    if not es.app_password_hash:
        return True  # login non ancora configurato: vedi core/config.py
    return verify_session_token(request.cookies.get(SESSION_COOKIE_NAME), es.session_secret_key, es.app_password_hash)


def require_auth(request: Request) -> None:
    """Dependency per le rotte che vogliono il controllo esplicito qui
    (change-password, logout) — la protezione delle altre rotte dell'app
    passa invece dal middleware globale in main.py, non da questa."""
    if not _is_authenticated(request):
        raise HTTPException(status_code=401, detail="Non autenticato")


@router.get("/status")
def auth_status(request: Request) -> dict:
    es = effective_settings()
    return {"auth_required": bool(es.app_password_hash), "authenticated": _is_authenticated(request)}


@router.post("/login")
def login(payload: LoginRequest, response: Response) -> dict:
    es = effective_settings()
    if not es.app_password_hash:
        return {"ok": True}  # login non configurato: vedi core/config.py
    if not verify_password(payload.password, es.app_password_hash):
        raise HTTPException(status_code=401, detail="Password errata")

    token = create_session_token(es.session_secret_key, es.app_password_hash)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=es.session_cookie_secure,
    )
    return {"ok": True}


@router.post("/logout")
def logout(response: Response, _: None = Depends(require_auth)) -> dict:
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"ok": True}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest, db: Session = Depends(get_db), _: None = Depends(require_auth)
) -> dict:
    es = effective_settings()
    if not es.app_password_hash or not verify_password(payload.current_password, es.app_password_hash):
        raise HTTPException(status_code=401, detail="Password attuale errata")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="La nuova password deve avere almeno 8 caratteri")

    new_hash = hash_password(payload.new_password)
    row = db.get(AppConfig, "app_password_hash")
    if row is None:
        db.add(AppConfig(key="app_password_hash", value=new_hash))
    else:
        row.value = new_hash
    db.commit()
    refresh_overrides(db)
    return {"ok": True}
