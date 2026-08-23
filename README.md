# HomeHub

Home Hub — una dashboard personale per la famiglia che aggrega calendario, liste della spesa, menu, allenamenti, finanze, home inventory e API custom in un unico display verticale.

Il design completo (architettura, wireframe, decisioni) è in [ARCHITECTURE.md](ARCHITECTURE.md).

## Struttura del repo

```
frontend/   React + Vite + TypeScript — la dashboard (rail laterale + Home + tab di dettaglio)
backend/    Python + FastAPI — backend aggregatore (BFF) verso Google Calendar, Bring!,
            le web app esistenti (finanze/menu/inventory) e le tabelle manuali su Postgres
docker-compose.yml   deploy dei due servizi sul NUC (Postgres è un'istanza esterna già esistente)
```

## Sviluppo locale

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # compila le credenziali (Postgres, Google, Bring!, ...)
uvicorn app.main:app --reload --port 8000
```

Senza credenziali configurate in `.env`, gli adapter (Google Calendar, Bring!, home inventory, menu di casa) rispondono con dati di esempio: utile per sviluppare/testare il frontend senza integrazioni reali. Le rotte che leggono/scrivono le tabelle manuali (menu scolastico, allenamenti) richiedono invece un Postgres raggiungibile — vedi `DATABASE_URL` in `.env`.

Migrazioni schema (`homehub`):

```bash
python -m alembic upgrade head
```

(usa `python -m alembic`, non `alembic` da solo — vedi la nota in DEPLOY.md sui conflitti con un eventuale `alembic` di sistema)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Il dev server proxya automaticamente `/api` verso `http://localhost:8000` (vedi `vite.config.ts`): non serve creare un `.env` a meno di voler puntare a un backend diverso (`frontend/.env.example`).

## Deploy sul NUC

```bash
docker compose up -d --build
```

Richiede `backend/.env` compilato (vedi `backend/.env.example`) e il Postgres esistente raggiungibile sulla LAN.
