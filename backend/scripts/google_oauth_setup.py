"""Script una tantum per ottenere il GOOGLE_REFRESH_TOKEN.

Esegui questo script su una macchina CON BROWSER (va benissimo il tuo Mac,
non serve farlo sul NUC): apre una pagina di consenso Google, ti chiede di
autorizzare l'accesso al tuo calendario, e stampa il refresh token da
copiare in backend/.env (GOOGLE_REFRESH_TOKEN). Il refresh token non scade
(finché non revochi l'accesso da https://myaccount.google.com/permissions),
quindi va fatto una sola volta.

Richiede GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET già presenti in .env
(quelli dell'app OAuth "Desktop" creata su Google Cloud Console).

Uso:
    cd backend
    source .venv/bin/activate
    python scripts/google_oauth_setup.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: E402

from app.core.config import get_settings  # noqa: E402

# Accesso completo al calendario (lettura + scrittura eventi, incluse le
# azioni di aggiunta evento previste dalla dashboard — vedi ARCHITECTURE.md §6)
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main() -> None:
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret:
        print("Errore: GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET devono essere già in backend/.env")
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    # access_type=offline + prompt=consent: garantiscono che Google restituisca
    # sempre un refresh_token, anche se l'app era già stata autorizzata prima.
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")

    if not credentials.refresh_token:
        print("Google non ha restituito un refresh_token. Riprova revocando prima l'accesso")
        print("da https://myaccount.google.com/permissions e rilanciando questo script.")
        sys.exit(1)

    print("\nFatto! Copia questa riga in backend/.env sul NUC:\n")
    print(f"GOOGLE_REFRESH_TOKEN={credentials.refresh_token}")
    print("\nNon condividerla in chat, log o commit: dà accesso completo al tuo calendario Google.")


if __name__ == "__main__":
    main()
