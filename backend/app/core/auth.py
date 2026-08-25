"""Login unico e condiviso per tutta la famiglia (niente account per
persona — coerente con la scelta "no multi-utente" di HomeHub, vedi
ARCHITECTURE.md §2). Sostituisce la Basic Auth di nginx (disattivata da
tempo perché Chrome/Edge bloccavano in silenzio il popup nativo, vedi
frontend/nginx.conf): qui è un form normale, quindi nessun popup da
bloccare.

Sessione: un cookie httpOnly con dentro solo una scadenza (30 giorni) e
un'impronta della password corrente, il tutto firmato con HMAC — nessun ID
utente da portare, visto che l'accesso è binario (dentro o fuori), non
serve un vero JWT con più campi. L'impronta lega il token alla password
attuale: cambiarla (o azzerare il relativo override in Impostazioni)
invalida automaticamente tutte le sessioni già emesse, non solo quella di
chi la cambia — comodo se si pensa che la password vecchia sia girata
troppo. La chiave di firma è session_secret_key (core/config.py); la
password stessa è verificata contro app_password_hash (bcrypt), mai in
chiaro.
"""

import hashlib
import hmac
import time

import bcrypt

SESSION_COOKIE_NAME = "hh_session"
SESSION_MAX_AGE_SECONDS = 30 * 24 * 3600  # 30 giorni, per non dover rifare login ad ogni visita


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # hash malformato (es. valore residuo non valido in app_config) —
        # trattato come "password sbagliata", non come errore del server.
        return False


def create_session_token(secret_key: str, password_hash: str, max_age_seconds: int = SESSION_MAX_AGE_SECONDS) -> str:
    expires_at = int(time.time()) + max_age_seconds
    fingerprint = _password_fingerprint(password_hash)
    payload = f"{expires_at}.{fingerprint}"
    return f"{payload}.{_sign(payload, secret_key)}"


def verify_session_token(token: str | None, secret_key: str, password_hash: str) -> bool:
    if not token or token.count(".") != 2:
        return False
    expires_at_raw, fingerprint, signature = token.split(".")
    payload = f"{expires_at_raw}.{fingerprint}"
    if not hmac.compare_digest(_sign(payload, secret_key), signature):
        return False
    # Impronta diversa da quella della password attuale: è stata cambiata
    # (o il suo override rimosso) dopo l'emissione di questo token, quindi
    # non è più valido — a prescindere dalla scadenza.
    if not hmac.compare_digest(fingerprint, _password_fingerprint(password_hash)):
        return False
    try:
        expires_at = int(expires_at_raw)
    except ValueError:
        return False
    return time.time() < expires_at


def _password_fingerprint(password_hash: str) -> str:
    return hashlib.sha256(password_hash.encode("utf-8")).hexdigest()[:16]


def _sign(payload: str, secret_key: str) -> str:
    return hmac.new(secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
