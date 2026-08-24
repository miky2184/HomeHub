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
- Home inventory non ha variabili da compilare (legge sempre direttamente lo schema `home_inventory` sullo stesso Postgres). L'unico requisito è che l'utente Postgres di `DATABASE_URL` (es. `homehub`) abbia **SELECT** su `home_inventory.items` e `home_inventory.containers` — se non l'ha già (es. perché è un ruolo diverso da quello usato da `home_inventory_web`), concedilo con:
  ```sql
  GRANT USAGE ON SCHEMA home_inventory TO homehub;
  GRANT SELECT ON home_inventory.items, home_inventory.containers TO homehub;
  ```
- Stesso discorso per `dieta.menu_settimanale` (cena di casa) — se non è già coperta dal grant fatto per `dieta.allenamento`:
  ```sql
  GRANT USAGE ON SCHEMA dieta TO homehub;
  GRANT SELECT ON dieta.menu_settimanale TO homehub;
  ```
- Finanze: **nessun grant sul DB** — sia le percentuali di budget (`/budget-forecast-all`) sia le prossime scadenze (`/dare_avere`) passano dall'API REST di quell'app, non da una query diretta su `home.finance` (vedi ARCHITECTURE.md §5). Compila `FINANCE_APP_BASE_URL`/`FINANCE_USERNAME`/`FINANCE_PASSWORD` in `.env` (stesso account personale già usato sulla web app finanze) — senza queste tre, il tab/la card Finanze restano vuoti (non mostrano dati finti, a differenza degli altri adapter, vista la sensibilità dei dati).

## 3. Creare lo schema `homehub` sul Postgres

Dal NUC (o da qualunque macchina che raggiunge il Postgres), con un Python locale o dentro il container backend dopo il build:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head
```

Questo crea lo schema `homehub` e le tabelle `training_plan` / `app_config` / `school_menu_template` / `school_menu_cycle_anchor` / `snack_template` / `todo_item`. Senza questo passaggio, la Home risponderà con errore (dipende dal Postgres per il menu scolastico e il prossimo allenamento — vedi ARCHITECTURE.md §7.1).

> **Nota se avevi già eseguito le migrazioni prima del 24/08/2026**: la migrazione `0002` sostituisce la vecchia tabella `school_menu` (mai popolata con dati reali) con il nuovo modello a rotazione di 4 settimane — è un `DROP TABLE` sicuro solo perché non c'era nulla dentro. Dopo `alembic upgrade head`, compila il menu scuola e le merende da Impostazioni (non più da Cucina, che ora è sola lettura). La migrazione `0003` aggiunge solo la tabella `todo_item` (nuova, nessun impatto sulle altre).

> **Nota**: usa sempre `python -m alembic ...` e non `alembic ...` da solo. Su alcune distribuzioni (Debian/Ubuntu) esiste un pacchetto di sistema `python3-alembic` che finisce prima nel `PATH` anche a venv attivo — `alembic` da solo lo invocherebbe, fallendo con `ModuleNotFoundError: pydantic_settings` perché quell'alembic di sistema non vede i pacchetti del venv. `python -m alembic` usa sempre l'interprete del venv attivo e non ha questo problema.

## 4. Generare le credenziali Basic Auth (`frontend/.htpasswd`)

Il frontend fa anche da reverse proxy verso il backend (un solo entry point, porta **8444** — vedi sotto "Esposizione su internet"). Da dentro la LAN di casa non viene mai richiesta l'autenticazione; serve solo a chi arriva da fuori tramite il port forwarding.

```bash
cd frontend
# richiede il pacchetto "apache2-utils" (Debian/Ubuntu) o "httpd-tools" (RHEL) per il comando htpasswd
sudo apt install -y apache2-utils   # se non già presente
htpasswd -c -s .htpasswd homehub
# ti chiede la password interattivamente: scegline una robusta, non la condividere in chat/commit
cd ..
```

> **Importante**: usa sempre `-s` (hash SHA, formato `{SHA}...`). Il container frontend è basato su `nginx:alpine` (musl libc), che **non supporta l'hash `$apr1$`** generato di default da `htpasswd` — nginx non riuscirebbe mai a validare la password (401 anche con le credenziali giuste, senza nessun errore esplicito). `-s` fa usare a nginx la sua verifica SHA1 interna, che funziona su qualunque immagine.

`frontend/.htpasswd` è escluso da Git (vedi `frontend/.gitignore`): resta solo sul NUC.

Se hai già creato il file con `htpasswd -c .htpasswd ...` (senza `-s`) e noti un 401 persistente anche con le credenziali corrette, rigeneralo con `-s` e fai `docker compose restart frontend`.

Se la subnet della tua LAN non è `192.168.1.0/24`, apri [frontend/nginx.conf](frontend/nginx.conf) e correggi le righe `allow 192.168.1.0/24;` con quella corretta (es. `192.168.0.0/24`) — altrimenti i dispositivi di casa si troverebbero comunque a dover fare login.

> **Nota**: `nginx.conf` viene copiato dentro l'immagine al build (`COPY nginx.conf ...` nel Dockerfile) — se lo modifichi devi rifare `docker compose up -d --build` (non basta un riavvio) perché la modifica abbia effetto.

> **Perché `curl http://localhost:8444/...` sul NUC chiede la password anche se sei "in LAN"**: il traffico verso `localhost`, passando per il port mapping di Docker, arriva a nginx con un IP sorgente NAT-ato nel bridge Docker (non `127.0.0.1`) — per questo `nginx.conf` whitelista anche `172.16.0.0/12` (le subnet dei bridge Docker, un range privato quindi sicuro). Con quella regola sia `curl` sul NUC sia il kiosk stesso puntato su `localhost:8444` funzionano senza login.

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

> ⚠️ **Stato attuale: Basic Auth disattivata temporaneamente** (commentata in `frontend/nginx.conf`), su richiesta esplicita per poter lavorare da remoto senza il blocco del popup su Chrome/Edge. In questo momento la porta **8444** è raggiungibile da chiunque su internet **senza alcuna autenticazione**, in lettura e scrittura (calendario, spesa, inventory, ecc.). Da ripristinare prima di lasciare l'accesso esterno attivo stabilmente — o, più semplice, rimuovere la regola di port forward sul router quando l'accesso da fuori casa non serve più (vedi nota in cima a `frontend/nginx.conf` per come riattivarla).

Hai scelto di rendere HomeHub raggiungibile anche da fuori casa via port forwarding sul router, sulla porta **8444** (esterna e interna). Con la configurazione (Basic Auth attiva):

- **Sul router**: una sola regola, esterna `8444` → interna `8444` verso l'IP del NUC. **Non forwardare mai la 8000**: il backend non è più raggiungibile dall'host, quindi non c'è nulla da aprire per lui.
- Da dentro casa (subnet configurata in `frontend/nginx.conf`) l'app resta senza login, come da progetto originale.
- Da fuori casa, il browser chiederà la Basic Auth (utente/password creati al passo 4).
- **Limite di questa configurazione**: il traffico verso la porta esposta viaggia in HTTP semplice, non cifrato — su internet, in teoria intercettabile lungo il percorso (molto meno probabile del semplice bersagliamento automatico della porta, ma non escluso). Se vuoi eliminare anche questo rischio in un secondo momento, le opzioni più semplici sono: (a) un dominio + certificato Let's Encrypt davanti a nginx, oppure (b) sostituire il port forwarding con una VPN verso casa (es. Tailscale), che cifra tutto e non richiede porte aperte. Per ora procediamo così, come richiesto.
- **Browser aziendali/gestiti (es. Edge con policy IT) possono bloccare in silenzio il popup di Basic Auth su siti HTTP semplice** (non HTTPS), per policy di sicurezza dell'organizzazione — nessun errore esplicito, il popup semplicemente non appare mai, anche con server e credenziali corretti (verificato: da Safari/browser personale funziona regolarmente). Non è un problema di HomeHub e non è risolvibile lato server; le opzioni sono usare un browser/dispositivo personale, oppure passare a HTTPS (vedi punto sopra) che in genere non è soggetto alle stesse restrizioni.

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
