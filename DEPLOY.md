# Deploy su NUC — prima messa in piedi

Guida passo-passo per portare HomeHub sul NUC via Git e vederlo girare per la
prima volta con Docker Compose (Docker è già installato, come confermato).

## 1. Clonare il repo sul NUC

```bash
git clone git@github.com:miky2184/HomeHub.git
cd HomeHub
```

Se il NUC non ha ancora una chiave SSH autorizzata su GitHub, usa in alternativa l'HTTPS:

```bash
git clone https://github.com/miky2184/HomeHub.git
```

## 2. Configurare il backend (`backend/.env`)

```bash
cp backend/.env.example backend/.env
```

Apri `backend/.env` e compila **almeno**:

- `DATABASE_URL`: connection string reale verso il Postgres esistente sulla LAN, con lo schema dedicato, es.
  `postgresql+psycopg://homehub:LA_TUA_PASSWORD@IP_POSTGRES:5432/nome_db`
- Lascia vuote per ora `GOOGLE_*`, `BRING_*`, `*_APP_*`: senza queste, quegli adapter continuano a rispondere con dati di esempio (vedi ARCHITECTURE.md §9) — non bloccano l'avvio, solo quella parte di Home resta "finta" finché non li configuriamo uno per uno.
- Home inventory non ha variabili da compilare (legge/scrive sempre direttamente lo schema `home_inventory` sullo stesso Postgres). L'utente Postgres di `DATABASE_URL` (es. `homehub`) deve avere **SELECT** su `home_inventory.items`, `home_inventory.containers` e `home_inventory.categories`, più **UPDATE** su `home_inventory.items` (serve solo per il +/- rapido di quantità dalla tab Casa — creare/eliminare oggetti resta compito di `home_inventory_web`) — se non li ha già (es. perché è un ruolo diverso da quello usato da `home_inventory_web`), concedili con:
  ```sql
  GRANT USAGE ON SCHEMA home_inventory TO homehub;
  GRANT SELECT ON home_inventory.items, home_inventory.containers, home_inventory.categories TO homehub;
  GRANT UPDATE (quantity) ON home_inventory.items TO homehub;
  ```
- Stesso discorso per `dieta.menu_settimanale` (cena di casa) — se non è già coperta dal grant fatto per `dieta.allenamento`:
  ```sql
  GRANT USAGE ON SCHEMA dieta TO homehub;
  GRANT SELECT ON dieta.menu_settimanale TO homehub;
  ```
## 3. Creare lo schema `homehub` sul Postgres

Dal NUC (o da qualunque macchina che raggiunge il Postgres), con un Python locale o dentro il container backend dopo il build:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head
```

Questo crea lo schema `homehub` e le tabelle `training_plan` / `app_config` / `school_menu_template` / `school_menu_cycle_anchor` / `snack_template` / `todo_item` / `chore`. Senza questo passaggio, la Home risponderà con errore (dipende dal Postgres per il menu scolastico e il prossimo allenamento — vedi ARCHITECTURE.md §7.1).

> **Nota se avevi già eseguito le migrazioni prima del 24/08/2026**: la migrazione `0002` sostituisce la vecchia tabella `school_menu` (mai popolata con dati reali) con il nuovo modello a rotazione di 4 settimane — è un `DROP TABLE` sicuro solo perché non c'era nulla dentro. Dopo `alembic upgrade head`, compila il menu scuola e le merende da Impostazioni (non più da Cucina, che ora è sola lettura). La migrazione `0003` aggiunge solo la tabella `todo_item` (nuova, nessun impatto sulle altre). La migrazione `0004` aggiunge solo la colonna `training_plan.from_garmin` (nuova, default `false` sulle righe esistenti — nessun impatto sui dati già presenti, risolve solo gli "allenamenti fantasma" che restavano visibili dopo che Garmin li spostava/rimuoveva). La migrazione `0005` aggiunge solo la tabella `chore` (nuova, per il tab Manutenzione — nessun impatto sulle altre).

> **Nota**: usa sempre `python -m alembic ...` e non `alembic ...` da solo. Su alcune distribuzioni (Debian/Ubuntu) esiste un pacchetto di sistema `python3-alembic` che finisce prima nel `PATH` anche a venv attivo — `alembic` da solo lo invocherebbe, fallendo con `ModuleNotFoundError: pydantic_settings` perché quell'alembic di sistema non vede i pacchetti del venv. `python -m alembic` usa sempre l'interprete del venv attivo e non ha questo problema.

## 4. Impostare la password di login di HomeHub

L'autenticazione non è più a livello nginx (niente più Basic Auth/`.htpasswd`): HomeHub ha una sua pagina di login, con una password unica condivisa da tutta la famiglia e una sessione che dura **30 giorni** (una volta fatto login su un browser/dispositivo, in pratica non lo richiede quasi più). Protegge sia l'accesso da fuori LAN sia da dentro casa — vedi ARCHITECTURE.md §8 per i motivi del cambio.

```bash
cd backend
source .venv/bin/activate
python scripts/generate_password_hash.py
# chiede la password a video (non appare mentre la scrivi) e stampa
# APP_PASSWORD_HASH=... e, se manca, SESSION_SECRET_KEY=...
cd ..
```

Copia le righe stampate in `backend/.env`. Senza `APP_PASSWORD_HASH` il login resta disattivato (tutte le richieste passano, comodo appena dopo aver aggiornato il deploy con questa versione) — compilalo prima di lasciare l'app raggiungibile stabilmente. `SESSION_SECRET_KEY` va messa una volta e non toccata più: cambiarla (o lasciarla vuota, nel qual caso ne viene generata una diversa ad ogni riavvio) disconnette tutti quelli che avevano già fatto login.

Una volta che l'app è raggiungibile, la password si può anche cambiare dalla UI (Impostazioni → Sicurezza, richiede quella attuale) senza dover più toccare `.env` o riavviare nulla — quel cambiamento disconnette anche automaticamente tutte le sessioni già aperte, non solo quella di chi la cambia.

## 5. Build e avvio con Docker Compose

Il frontend ora fa anche da reverse proxy: il backend **non pubblica più nessuna porta** sull'host, è raggiungibile solo dal container frontend (rete Docker interna). L'unico punto d'ingresso è la porta **8444** del frontend (host → container 80), sia per la UI che per `/api/*`.

```bash
docker compose up -d --build
```

Verifica (dalla LAN, senza bisogno di credenziali):

```bash
curl http://localhost:8444/api/health
# {"status":"ok"}
```

Poi apri `http://localhost:8444` (o `http://IP_NUC:8444`) nel browser: dovresti vedere la Home con rail laterale, calendario/spesa/inventory con dati di esempio, e menu/allenamenti vuoti finché non li compili tu dalla UI.

> **Fuso orario del container**: `backend/Dockerfile` imposta esplicitamente `TZ=Europe/Rome` (con `tzdata` installato), perché l'immagine base `python:3.12-slim` di default gira in UTC. Senza questo, `datetime.now()` nel backend resta sfasato di 1-2 ore rispetto all'ora locale italiana — bug reale riscontrato nel meteo (l'elenco delle prossime ore mostrava anche ore già passate). Se in futuro sposti il deploy su un host con un fuso di sistema diverso, ricordati che questa impostazione vive nel Dockerfile, non nel `docker-compose.yml`.

## Esposizione su internet (port forwarding)

> ⚠️ **Se stai aggiornando un deploy precedente**: prima di questa versione la Basic Auth di nginx era disattivata (per il problema del popup bloccato da Chrome/Edge, vedi sotto) e la porta **8444** era raggiungibile da chiunque su internet **senza alcuna autenticazione**, in lettura e scrittura. Fai il passo 4 (impostare `APP_PASSWORD_HASH`) **prima** di lasciare l'accesso esterno attivo dopo l'aggiornamento — altrimenti l'app resta comunque aperta a tutti come prima, solo senza più nemmeno il tentativo di Basic Auth.

Hai scelto di rendere HomeHub raggiungibile anche da fuori casa via port forwarding sul router, sulla porta **8444** (esterna e interna).

- **Sul router**: una sola regola, esterna `8444` → interna `8444` verso l'IP del NUC. **Non forwardare mai la 8000**: il backend non è più raggiungibile dall'host, quindi non c'è nulla da aprire per lui.
- Sia da dentro casa sia da fuori, la password di login (passo 4) è la stessa e protegge allo stesso modo: non c'è più una whitelist di IP di LAN che bypassa il login come con la vecchia Basic Auth — una volta fatto login su un dispositivo, la sessione dura 30 giorni, quindi in pratica non lo richiede quasi più.
- **Limite di questa configurazione**: il traffico verso la porta esposta viaggia in HTTP semplice, non cifrato — su internet, in teoria intercettabile lungo il percorso (molto meno probabile del semplice bersagliamento automatico della porta, ma non escluso; anche il cookie di sessione viaggerebbe in chiaro). Se vuoi eliminare anche questo rischio, le opzioni più semplici sono: (a) un dominio + certificato Let's Encrypt davanti a nginx (**ricordati anche di mettere `SESSION_COOKIE_SECURE=true` in `.env`** a quel punto, altrimenti il cookie non verrebbe più inviato affatto), oppure (b) sostituire il port forwarding con una VPN verso casa (es. Tailscale), che cifra tutto e non richiede porte aperte. Per ora procediamo così, come richiesto.
- Il vecchio problema della Basic Auth (**browser aziendali/gestiti, es. Edge con policy IT, bloccavano in silenzio il popup nativo** su siti HTTP semplice — nessun errore, il popup semplicemente non appariva mai) non si applica più: il login di HomeHub è un form HTML normale, non un popup del browser.

## 5. Iterare pagina per pagina

Da qui in avanti possiamo lavorare una pagina alla volta (rifiniture UI, poi via via le integrazioni reali — Google Calendar, Bring!, le tue app). Ad ogni modifica sul Mac:

```bash
git add -A && git commit -m "..." && git push
```

e sul NUC:

```bash
git pull
docker compose up -d --build
```

## Nota sul kiosk mode

Non ancora configurato in questa fase (l'obiettivo ora è solo "vederlo funzionare"). Quando saremo pronti per l'uso reale in cucina, lo step successivo è Chromium in kiosk mode con autostart via systemd, puntato su `http://localhost:8444` (vedi ARCHITECTURE.md §8).
