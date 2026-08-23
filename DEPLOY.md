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

## 3. Creare lo schema `homehub` sul Postgres

Dal NUC (o da qualunque macchina che raggiunge il Postgres), con un Python locale o dentro il container backend dopo il build:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

Questo crea lo schema `homehub` e le tabelle `school_menu` / `training_plan` / `app_config`. Senza questo passaggio, la Home risponderà con errore (dipende dal Postgres per il menu scolastico e il prossimo allenamento — vedi ARCHITECTURE.md §7.1).

## 4. Generare le credenziali Basic Auth (`frontend/.htpasswd`)

Il frontend fa anche da reverse proxy verso il backend (un solo entry point, porta 80 — vedi sotto "Esposizione su internet"). Da dentro la LAN di casa non viene mai richiesta l'autenticazione; serve solo a chi arriva da fuori tramite il port forwarding.

```bash
cd frontend
# richiede il pacchetto "apache2-utils" (Debian/Ubuntu) o "httpd-tools" (RHEL) per il comando htpasswd
sudo apt install -y apache2-utils   # se non già presente
htpasswd -c .htpasswd homehub
# ti chiede la password interattivamente: scegline una robusta, non la condividere in chat/commit
cd ..
```

`frontend/.htpasswd` è escluso da Git (vedi `frontend/.gitignore`): resta solo sul NUC.

Se la subnet della tua LAN non è `192.168.1.0/24`, apri [frontend/nginx.conf](frontend/nginx.conf) e correggi le righe `allow 192.168.1.0/24;` con quella corretta (es. `192.168.0.0/24`) — altrimenti i dispositivi di casa si troverebbero comunque a dover fare login.

## 5. Build e avvio con Docker Compose

Il frontend ora fa anche da reverse proxy: il backend **non pubblica più nessuna porta** sull'host, è raggiungibile solo dal container frontend (rete Docker interna). L'unico punto d'ingresso è la porta 80 del frontend, sia per la UI che per `/api/*`.

```bash
docker compose up -d --build
```

Verifica (dalla LAN, senza bisogno di credenziali):

```bash
curl http://localhost/api/health
# {"status":"ok"}
```

Poi apri `http://localhost` (o `http://IP_NUC`) nel browser: dovresti vedere la Home con rail laterale, calendario/spesa/inventory con dati di esempio, e menu/allenamenti vuoti finché non li compili tu dalla UI.

## Esposizione su internet (port forwarding)

Hai scelto di rendere HomeHub raggiungibile anche da fuori casa via port forwarding sul router. Con la configurazione sopra:

- **Apri una sola porta sul router**: la 80 (o, meglio, mappala su una porta esterna non standard, es. esterna `443x`/`8443` → interna `80`, così gli scanner automatici che bersagliano la porta 80 di default ti trovano meno facilmente). **Non forwardare mai la 8000**: il backend non è più raggiungibile dall'host, quindi non c'è nulla da aprire per lui.
- Da dentro casa (subnet configurata in `frontend/nginx.conf`) l'app resta senza login, come da progetto originale.
- Da fuori casa, il browser chiederà la Basic Auth (utente/password creati al passo 4).
- **Limite di questa configurazione**: il traffico verso la porta esposta viaggia in HTTP semplice, non cifrato — su internet, in teoria intercettabile lungo il percorso (molto meno probabile del semplice bersagliamento automatico della porta, ma non escluso). Se vuoi eliminare anche questo rischio in un secondo momento, le opzioni più semplici sono: (a) un dominio + certificato Let's Encrypt davanti a nginx, oppure (b) sostituire il port forwarding con una VPN verso casa (es. Tailscale), che cifra tutto e non richiede porte aperte. Per ora procediamo così, come richiesto.

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

Non ancora configurato in questa fase (l'obiettivo ora è solo "vederlo funzionare"). Quando saremo pronti per l'uso reale in cucina, lo step successivo è Chromium in kiosk mode con autostart via systemd, puntato su `http://localhost` (vedi ARCHITECTURE.md §8).
