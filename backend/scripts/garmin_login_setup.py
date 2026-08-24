"""Script una tantum per il login iniziale a Garmin Connect.

Va eseguito con un terminale interattivo (va benissimo la sessione SSH sul
NUC stessa, non serve un browser): fa login con GARMIN_EMAIL/GARMIN_PASSWORD
da .env e, se Garmin lo richiede, chiede a video il codice MFA (quello che
ricevi via email o dall'app Garmin Connect). Alla fine salva una sessione
riutilizzabile in backend/.garmin_tokens/, così l'app non chiederà più
interazione ad ogni richiesta — finché quella sessione resta valida.

Uso:
    cd backend
    source .venv/bin/activate
    python scripts/garmin_login_setup.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from garminconnect import Garmin  # noqa: E402

from app.adapters.garmin import TOKENSTORE_DIR  # noqa: E402
from app.core.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    if not settings.garmin_email or not settings.garmin_password:
        print("Errore: GARMIN_EMAIL e GARMIN_PASSWORD devono essere già in backend/.env")
        sys.exit(1)

    client = Garmin(
        settings.garmin_email,
        settings.garmin_password,
        prompt_mfa=lambda: input("Codice MFA Garmin (dall'app o dall'email): "),
    )
    client.login(str(TOKENSTORE_DIR))

    print(f"\nFatto! Sessione salvata in {TOKENSTORE_DIR}")
    print("Non serve rilanciare questo script a meno che la sessione non scada o venga revocata.")


if __name__ == "__main__":
    main()
