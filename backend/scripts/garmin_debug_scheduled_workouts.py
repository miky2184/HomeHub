"""Script diagnostico temporaneo: stampa la risposta grezza di
get_scheduled_workouts() per il mese corrente, così possiamo vedere i nomi
reali dei campi (workoutId, data, nome, tipo, ecc.) prima di scrivere il
parsing definitivo nell'adapter — invece di indovinarli.

Usa la sessione già salvata da garmin_login_setup.py (nessun nuovo login).

Uso:
    cd backend
    source .venv/bin/activate
    python scripts/garmin_debug_scheduled_workouts.py
"""

import json
import pathlib
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from garminconnect import Garmin  # noqa: E402

from app.adapters.garmin import TOKENSTORE_DIR  # noqa: E402
from app.core.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    client = Garmin(settings.garmin_email, settings.garmin_password)
    client.login(str(TOKENSTORE_DIR))

    today = date.today()
    data = client.get_scheduled_workouts(today.year, today.month)
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
