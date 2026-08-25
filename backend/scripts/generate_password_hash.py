"""Script una tantum per impostare la password di login di HomeHub.

Chiede una password a video (nascosta, non appare mentre la scrivi) e
stampa le due righe da copiare in backend/.env: l'hash bcrypt della
password (mai la password in chiaro: né in .env né altrove) e, se manca,
una nuova chiave di firma delle sessioni. Va rieseguito ogni volta che si
vuole cambiare la password da qui invece che dalla UI (Impostazioni >
Sicurezza, disponibile una volta che l'app è già raggiungibile).

Uso:
    cd backend
    source .venv/bin/activate
    python scripts/generate_password_hash.py
"""

import getpass
import pathlib
import secrets
import sys

from dotenv import dotenv_values

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.core.auth import hash_password  # noqa: E402

ENV_FILE = pathlib.Path(__file__).resolve().parent.parent / ".env"


def main() -> None:
    password = getpass.getpass("Nuova password di HomeHub: ")
    if len(password) < 8:
        print("Errore: la password deve avere almeno 8 caratteri.")
        raise SystemExit(1)
    confirm = getpass.getpass("Ripetila: ")
    if password != confirm:
        print("Errore: le due password non coincidono.")
        raise SystemExit(1)

    password_hash = hash_password(password)
    print("\nAggiungi (o sostituisci) in backend/.env:\n")
    print(f"APP_PASSWORD_HASH={password_hash}")

    # Guardiamo il file .env così com'è su disco, non get_settings(): quella
    # una volta chiamata genera già in memoria una chiave provvisoria se
    # manca (per non bloccare lo sviluppo locale), quindi la vedrebbe sempre
    # "già impostata" anche quando .env non ce l'ha — e questa riga non
    # comparirebbe mai.
    existing = dotenv_values(ENV_FILE)
    if not existing.get("SESSION_SECRET_KEY"):
        print(f"SESSION_SECRET_KEY={secrets.token_hex(32)}")
    print(
        "\nSenza SESSION_SECRET_KEY in .env ne viene generata una diversa "
        "ad ogni riavvio del backend, disconnettendo tutti — se .env ne ha "
        "già una, lasciala com'è."
    )


if __name__ == "__main__":
    main()
