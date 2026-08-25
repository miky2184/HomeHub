# HomeHub — Documento di Architettura

> Stato: bozza di design, nessun codice ancora presente nel repo.
> Obiettivo: sostituire MagicMirror con una dashboard famiglia su misura, verticale, no-touch (navigazione a Magic Trackpad), eseguita su NUC + monitor Arzopa in cucina.

## 1. Contesto e vincoli hardware

- **Display**: Arzopa portatile, orientamento verticale (ritratto), risoluzione effettiva **1080×1920**.
- **Compute**: Intel NUC, sempre acceso, in cucina.
- **Input**: nessun touch. Navigazione tramite Magic Trackpad (puntatore, click, eventualmente gesture a due dita per swipe orizzontale tra tab). Nessuna tastiera presunta connessa in modo permanente.
- **Modalità d'uso**: schermo "always-on" in ambiente cucina, letto a distanza (font grandi, alto contrasto, dark theme preferibile per luce ambientale serale).
- **Sostituisce**: l'attuale installazione MagicMirror (giudicata troppo limitante/rigida come piattaforma di moduli).

## 2. Decisioni architetturali (confermate con l'utente)

| Decisione | Scelta |
|---|---|
| Integrazione con le web app già esistenti (finanze, menu casa, home inventory) | **Aggregazione via API**: HomeHub non fa iframe embedding, chiama le API REST di quelle app e ne normalizza i dati in una UI coerente |
| Frontend | **React + Vite** (TypeScript) |
| Backend | **Sì, un servizio aggregatore dedicato** ("BFF" – Backend For Frontend) che gira sul NUC |
| Persistenza | **PostgreSQL già disponibile** (istanza esistente), con **schema dedicato `homehub`** (confermato) per dati manuali (menu, allenamenti), cache e config, separato dalle tabelle delle altre app |
| Backend stack | **Python + FastAPI** (coerente con lo stack delle 3 web app esistenti, tutte in Python) |
| Monitor | Arzopa, risoluzione **1080×1920** (verticale) — usata come riferimento per griglia/breakpoint del frontend |
| Allenamenti | Comunicati dal coach via WhatsApp → l'utente li crea e li assegna ai giorni **direttamente su Garmin Connect** (non più inserimento manuale in HomeHub come ipotizzato all'inizio); ✅ HomeHub legge il piano da lì (`get_scheduled_workouts`) e gli allenamenti svolti da **`dieta.allenamento`** (altra web app dell'utente sullo stesso Postgres, già sincronizzata da Garmin con dati più ricchi — FC, passo, TSS, dislivello). Tab di **sola lettura** in HomeHub, niente editing manuale — vedi `backend/app/adapters/garmin.py` e `backend/app/db/dieta_models.py` |
| Lettura vs scrittura | La dashboard **non è di sola lettura in generale**: azioni previste per spuntare/aggiungere articoli Bring!, aggiungere eventi calendario, modificare menu, ecc. — eccezioni sola lettura: **Allenamenti** (il piano si programma su Garmin, non in HomeHub), **Menu scuola/merende** (data entry in Impostazioni), **Home Inventory** (creare/modificare/eliminare oggetti resta nella web app dedicata; da HomeHub si può solo aggiustare la quantità con +/-) |
| Multi-utente | **No**: vista unica e condivisa per tutta la famiglia, nessun account per persona/switch di utenza — chi guarda il monitor vede/agisce direttamente. ✅ C'è però un **login unico e condiviso** (una sola password per tutti, sessione di 30 giorni) per proteggere l'app: non è un login multi-utente, è il cancello d'ingresso, vedi §8 |
| API non ufficiali | Va bene usarle in generale (non solo per Bring!), tenendo presente il rischio di breaking change e isolandole dietro gli adapter del backend |
| Deliverable di questa fase | Solo documento di design (nessuno scaffolding di codice per ora) |

## 3. Vista d'insieme

```
┌─────────────────────────────────────────────────────────────────┐
│  NUC (kiosk, Chromium fullscreen, autostart via systemd)         │
│                                                                   │
│  ┌───────────────────────┐        ┌───────────────────────────┐ │
│  │  Frontend (React/Vite) │  HTTP  │  Backend aggregator (BFF)  │ │
│  │  - Home                │◄──────►│  - Adapter/Calendar        │ │
│  │  - Tab: Calendario     │  REST  │  - Adapter/Bring!          │ │
│  │  - Tab: Menu           │  (+SSE │  - Adapter/Menu app        │ │
│  │  - Tab: Allenamenti    │  poll) │  - Adapter/Inventory app    │ │
│  │  - Tab: Spesa (Bring!) │        │  - Adapter/Finance app      │ │
│  │  - Tab: Home Inventory │        │  - Cache/normalizzazione   │ │
│  │  - Tab: Finanze (opz.) │        │  - Azioni (write) verso    │ │
│  └───────────────────────┘        │    Bring!/Calendar/Menu/…  │ │
│                                    └──────────┬────────────────┘ │
└───────────────────────────────────────────────┼──────────────────┘
                                                 │
                          ┌──────────────────────┼───────────────────────┐
                          ▼                      ▼                       ▼
                Google Calendar API      Bring! API (non ufficiale)   Web app esistenti
                (OAuth2)                 (credenziali account)        (finanze / menu / inventory)
                                                                       via loro API REST interne
                                                 │
                                                 ▼
                                    PostgreSQL (istanza esistente, schema dedicato HomeHub)
                                    dati manuali (menu, allenamenti), cache, config
```

Il frontend **non parla mai direttamente** con Google, Bring! o le altre web app: passa sempre dal backend aggregatore. Questo tiene tutti i secret (OAuth token, credenziali Bring!, eventuali API key delle altre app) fuori dal browser e centralizza cache/retry/normalizzazione.

## 4. Frontend (React + Vite)

### 4.1 Layout

- Struttura a **rail laterale + area contenuto**, adatta a schermo verticale:
  - Rail verticale (icone grandi, sempre visibile) per passare da Home ai vari tab.
  - Area principale: Home (riepilogo compatto di tutto) oppure vista di dettaglio del tab selezionato.
- Home = dashboard "a colpo d'occhio": card per calendario di oggi, meteo, menu del giorno (scuola + casa), prossimo allenamento, evidenze lista spesa, alert home inventory (es. scorte in esaurimento).
- Ogni tab di dettaglio è una vista dedicata e più ricca del riepilogo in Home.

### 4.2 Navigazione no-touch

- Click del puntatore sul rail per cambiare tab (target grandi, pensati per trackpad non per touch fine).
- Supporto opzionale a swipe a due dita (eventi `wheel` orizzontali) per cambiare tab senza mirare col puntatore.
- **Idle/attract mode**: dopo N minuti di inattività, la dashboard torna automaticamente alla Home (evita che resti "bloccata" su un tab di dettaglio tutto il giorno).
- Nessuna dipendenza da tastiera; eventuali shortcut da tastiera solo come bonus opzionale.

### 4.1.1 Wireframe Home (dettaglio)

Layout pensato per la risoluzione reale **1080×1920** (verticale):

```
┌──┬─────────────────────────────┐
│▣ │  18:42          ☀ 27°       │  ← rail 52-64px + status strip
│  │  Domenica 23 agosto         │    (ora, data, meteo)
│◷ │                             │
│  │ ┌─────────────────────────┐ │
│🍴│ │ Oggi                     │ │  ← card agenda: 2-3 eventi
│  │ │ ● 10:00  Piscina Sofia   │ │    di oggi (pallino colorato
│🏋│ │ ● 19:30  Cena dai nonni  │ │    = calendario di origine)
│  │ └─────────────────────────┘ │
│🛒│ ┌─────────────────────────┐ │
│  │ │ Menu di oggi             │ │  ← card menu: scuola | casa
│📦│ │ Scuola      │ Casa       │ │    affiancati
│  │ │ Pasta pom.  │ Pollo forno│ │
│💰│ └─────────────────────────┘ │
│  │ ┌─────────────────────────┐ │
│  │ │ Prossimo allenamento  ✓  │ │  ← card allenamento, con
│  │ │ Corsa 8km + core         │ │    azione rapida "segna fatto"
│  │ └─────────────────────────┘ │
│  │ ┌─────────────────────────┐ │
│  │ │ Lista della spesa    [6] │ │  ← card spesa: badge conteggio
│  │ │ ☐ Latte                  │ │    + primi articoli, spuntabili
│  │ │ ☐ Uova                   │ │
│  │ └─────────────────────────┘ │
│  │ ┌─────────────────────────┐ │
│  │ │ ⚠ Scorte in esaurimento  │ │  ← card alert (colore warning),
│  │ │ Detersivo, carta igien.  │ │    solo se ci sono alert attivi
│  │ └─────────────────────────┘ │
└──┴─────────────────────────────┘
```

Note di design:

- **Rail** (sinistra, ~52–64px): icone Home, Calendario, Todo, Manutenzione, Menu, Allenamenti, Spesa, Home Inventory, Impostazioni. Tab attivo evidenziato con sfondo colorato (accent), gli altri neutri. Target di click generosi (min. ~48px) pensati per puntatore trackpad, non per touch di precisione.
- **Status strip** in alto: ora (grande, sempre visibile, fa anche da "screensaver" leggero quando non ci sono notifiche urgenti), data, meteo compatto.
- **Card Home = riepilogo, non l'elenco completo**: ogni card mostra solo i primi 2-3 elementi rilevanti; cliccando sulla card (o sull'icona del tab corrispondente nel rail) si apre la vista di dettaglio completa in quel tab.
- **Ordine delle card** riflette priorità d'uso in cucina: agenda di oggi → menu del giorno → prossimo allenamento → spesa → alert inventory. Facilmente riordinabile in seguito senza cambiare struttura.
- **Azioni inline dalla Home**: spunta articolo spesa, "segna allenamento fatto" — le azioni più frequenti non richiedono di entrare nel tab di dettaglio. Azioni più complesse (aggiungere un evento, modificare il menu settimanale) restano nei tab dedicati.
- **Card alert (es. scorte in esaurimento)** compare solo quando c'è qualcosa da segnalare, con colore di stato (`warning`) per distinguerla dalle card informative neutre — evita rumore visivo quando non ci sono alert.
- Su schermo reale, dimensioni tipografiche e padding vanno scalati parecchio rispetto a un mockup in miniatura: ora/data ben leggibili da 2-3 metri di distanza (es. ora ~72-96px, testo card ~28-32px), mantenendo comunque la stessa gerarchia relativa mostrata sopra.

### 4.3 Stack tecnico

- React + Vite + TypeScript.
- **TanStack Query** per fetching/caching/polling dei dati dal backend (i dati sono quasi tutti "poll ogni N minuti", non serve realtime spinto; SSE opzionale in futuro per aggiornamenti push, es. Bring! aggiornata da un familiare col telefono).
- Stato UI locale (tab attivo, idle timer) con uno store leggero (Zustand o semplice Context).
- Tema scuro di default, tipografia grande, palette ad alto contrasto per lettura a distanza.
- Build statica servita in produzione (nginx o server statico minimale) dentro il container/servizio sul NUC.

## 5. Tab / Moduli previsti

| Tab | Contenuto | Fonte dati |
|---|---|---|
| **Home** | Riepilogo: santo del giorno + frase/proverbio del giorno (al posto del sottotitolo statico), meteo, menu del giorno, ✅ **card "Oggi"**: eventi di oggi **+ prossimo allenamento nella stessa card** (sotto una linea di separazione, con la data — "Oggi"/"Domani"/giorno della settimana — e il pulsante "segna come fatto"), non più due card separate, ✅ **lista della spesa** su riga intera (conteggio + un'anteprima dei primi N prodotti sotto una linea di separazione, N configurabile in Impostazioni, di default 5) invece di un semplice conteggio più una seconda card separata più in basso, ✅ **Casa** su riga intera (era appaiata alla lista della spesa), alert inventory, ✅ **Manutenzione**: conteggio delle attività ricorrenti scadute/da fare oggi + le prime 3, con un pulsante "Fatto oggi" diretto dalla card (visibile solo se c'è qualcosa da fare) | Backend aggregatore (già normalizzato). Santo: API gratuita non ufficiale [santodelgiorno.it](https://www.santodelgiorno.it/), cache 24h. Frase: nessuna API italiana affidabile esiste (verificato) → lista curata di proverbi in `backend/app/services/quotes.py`, rotazione per giorno dell'anno. Meteo: ✅ [Open-Meteo](https://open-meteo.com/) (gratuita, senza chiave) — card dedicata con temperatura+condizione attuali, prossime 4 ore, ✅ prossimi 2 giorni (min/max + condizione), e un avviso se pioggia/neve sono previste più tardi in giornata (8-22) pur non piovendo ora — geocoding di `WEATHER_CITY` una tantum (cache 7gg) + previsioni (cache 15min), vedi `backend/app/adapters/weather.py` |
| **Calendario** | Vista mensile/settimanale Google Calendar, eventi dei vari membri famiglia con colori distinti. ✅ CRUD completo: click su un evento apre modifica (titolo/orario/tutto il giorno/calendario) o eliminazione (con conferma) | Google Calendar API (via backend, OAuth) — `perform_action("update_event"/"delete_event")` in `backend/app/adapters/google_calendar.py` |
| **Menu** | Menu scolastico a **rotazione di 4 settimane** (il volantino della scuola, invariato per mesi, solo pranzo della figlia) + merende mattina/pomeriggio fisse per giorno (sempre della figlia) + **tutti i pasti di casa degli adulti** (colazione, spuntini, pranzo, cena — la figlia pranza a scuola, ma per gli altri pasti/gli altri membri della famiglia si legge da qui) | ✅ Template + ancora ciclo su Postgres (data entry in Impostazioni, non in Cucina/Home che sono sola lettura) + ✅ pasti di casa letti direttamente da `dieta.menu_settimanale` (stesso Postgres, altra web app dell'utente — il piano nutrizionale copre tutta la famiglia), niente API REST di mezzo — vedi `backend/app/db/dieta_models.py:menu_settimanale_table` e `HomeMeals` in `backend/app/schemas/common.py` |
| **Allenamenti** | Piano settimanale (sola lettura) + dettaglio dell'allenamento svolto in una modale | ✅ Piano da Garmin Connect (API non ufficiale, `get_scheduled_workouts`); allenamenti svolti da `dieta.allenamento` (altra web app dell'utente, già sincronizzata da Garmin con dati più ricchi: FC, passo, TSS, dislivello...) — stesso Postgres di homehub, schema diverso |
| **Spesa (Bring!)** | Lista della spesa condivisa, con possibilità di spuntare/aggiungere articoli | Bring! API (non ufficiale, via backend) |
| **Home Inventory** | ✅ Oggetti scaduti o in scadenza entro 7gg (stessa soglia "warning" della web app dedicata), con contenitore associato. Creare/modificare/eliminare oggetti resta nella web app `home_inventory_web`. ✅ Un pulsante "Aggiungi a Bring!" per ogni alert manda l'articolo (nome + quantità/unità come specifica) sulla lista della spesa in un click. ✅ **"Cerca in tutti i contenitori"**: ricerca trasversale per nome su tutti gli oggetti, per trovare in che contenitore è finito qualcosa senza aprirli uno a uno. ✅ **"Sfoglia per contenitore"**: selettore con tutti i contenitori (anche vuoti) e il loro contenuto completo, non solo ciò che scade a breve — sostituisce il foglio di carta sul frigo per sapere cosa c'è nei cassetti del freezer (cucina/terrazzo), senza doverli aprire. ✅ Pulsanti +/- su ogni oggetto (sia nella ricerca che nello sfoglia per contenitore) per aggiustare rapidamente la quantità (es. +6 comprando un fardello d'acqua, -1 bevendo un vino) senza aprire `home_inventory_web` | Lettura diretta dello schema Postgres `home_inventory` (stesso Postgres di homehub, altra web app dell'utente — niente API REST, come per `dieta.allenamento`) — vedi `backend/app/db/home_inventory_models.py` e `get_inventory_by_container`/`adjust_item_quantity` in `backend/app/services/aggregator.py`. L'aggiustamento quantità è l'unica scrittura su questo schema, via `PATCH /api/inventory/items/{id}/quantity` — clampata a 0, non elimina mai l'oggetto. Scrittura verso Bring! riusa `/api/shopping` (stesso adapter della tab Spesa) |
| **Todo** | ✅ Todo list condivisa di famiglia (no multi-utente/login): titolo, priorità (alta/media/bassa), scadenza opzionale, "per chi" (etichetta libera, non un vero assegnatario). CRUD completo nel tab; in Home una card mostra il conteggio degli aperti + i primi 3 per priorità/scadenza | Tabella propria `homehub.todo_item` — vedi `backend/app/db/models.py:TodoItem` e `backend/app/api/routes/todo.py` |
| **Manutenzione** | ✅ Attività di casa **ricorrenti per intervallo** (non una tantum come i Todo): "pulire il filtro della lavastoviglie ogni 3 mesi", "annaffiare le piante ogni settimana". Titolo, intervallo in giorni (con preset rapidi: 1/2 settimane, 1/3/6 mesi, 1 anno), data dell'ultima volta fatta (opzionale — mai fatta = considerata scaduta da subito), "per chi" libero, note. La prossima scadenza si ricalcola da sola (last_done_date + intervallo) ad ogni "Fatto oggi", non è un campo salvato. CRUD completo nel tab, ordinato per urgenza (più in ritardo prima); in Home una card mostra il conteggio scadute/da fare oggi + le prime 3, con un pulsante "Fatto oggi" diretto | Tabella propria `homehub.chore` — vedi `backend/app/db/models.py:Chore`, `backend/app/api/routes/chores.py` e `chore_item_out`/`sort_chores`/`get_chore_summary` in `backend/app/services/aggregator.py` |
| **Impostazioni** | ✅ Organizzata in sezioni (non più un unico elenco di card): **Famiglia & Aspetto** (nome famiglia mostrato nel saluto in Home; quanti prodotti mostrare nell'anteprima della lista della spesa in Home; palette di sfondo dell'app, si applica subito), **Meteo** (nome da visualizzare, latitudine/longitudine — priorità sulle coordinate, niente geocoding se compilate), **Menu scuola** (template rotazione 4 settimane, merende, punto di partenza ciclo — invariato), **Integrazioni** (credenziali Google Calendar/Bring!/Garmin: se compilate qui vincono su `.env`, per cambiarle senza accedere al NUC; i campi segreto non vengono mai rimandati al frontend dopo il salvataggio, solo un flag "impostato"), **Sicurezza** (cambia la password unica di login — richiede quella attuale — ed "Esci" da questo browser) | `homehub.app_config` (key/value) via `GET/PUT /api/settings` — vedi `backend/app/core/runtime_settings.py` (unico lettore, con fallback a `.env` campo per campo) e `backend/app/api/routes/settings.py` (unico scrittore, invalida anche le sessioni già autenticate degli adapter e la cache del geocoding se le credenziali/il meteo cambiano) |

> **Finanze**: implementata (percentuali di budget + promemoria scadenze, mai importi — vedi storico Git) e poi **rimossa deliberatamente**: non è un'informazione da colpo d'occhio quotidiano come le altre card, non giustificava la complessità che si portava dietro (credenziali JWT verso `python-finanze-api`, modalità ospiti dedicata solo a nasconderla). Nessun residuo nel codice: niente tab, niente adapter, niente `guest_mode`.

## 6. Azioni supportate dalla dashboard (non solo lettura)

La dashboard deve poter scrivere, non solo mostrare. Elenco (non esaustivo) delle azioni pensate per il rilascio iniziale, per tab:

| Tab | Azioni |
|---|---|
| Calendario | Aggiunta rapida evento (titolo, data/ora, calendario di destinazione); ✅ modifica ed eliminazione (click su un evento) |
| Menu (Cucina/Home) | Nessuna: tab di sola lettura. Data entry del template menu scuola/merende (2 volte l'anno) e del punto di partenza del ciclo, in Impostazioni |
| Allenamenti | Nessuna (tab di sola lettura): il piano si programma su Garmin Connect, non in HomeHub — vedi §5. Click su un allenamento svolto apre il dettaglio in una modale |
| Spesa (Bring!) | Spuntare articoli come presi, aggiungere nuovi articoli, rimuovere articoli |
| Home Inventory | Creare/modificare/eliminare oggetti resta nella web app `home_inventory_web` dedicata. ✅ Azioni possibili da qui: "Aggiungi a Bring!" per un articolo in scadenza (scrive solo su Bring!, mai su home_inventory); +/- sulla quantità di un oggetto esistente (unica scrittura su home_inventory, mai creazione/eliminazione) |
| Todo | CRUD completo: creare, modificare (titolo/priorità/scadenza/assegnatario), segnare come fatto, eliminare (con conferma) |
| Manutenzione | CRUD completo: creare, modificare (titolo/intervallo/assegnatario/note), "Fatto oggi" (aggiorna last_done_date, disponibile anche dalla card in Home), eliminare (con conferma) |
| Impostazioni | ✅ Salvataggio di nome famiglia, palette di sfondo, meteo (nome/lat/lon) e credenziali integrazioni (Google/Bring!/Garmin) — scrive su `homehub.app_config`, mai su `.env`. Un campo lasciato vuoto rimuove l'override e torna al valore di `.env` |

Implicazioni di design:
- Ogni azione passa dal backend aggregatore, che la inoltra alla fonte giusta (Google Calendar, Bring!, Postgres per i dati manuali, o l'API della web app esistente) e poi invalida/aggiorna la cache così la UI si aggiorna in modo coerente (via refetch di TanStack Query, eventualmente SSE per notificare cambi fatti da altri dispositivi, es. l'app Bring! sul telefono).
- Essendo no-touch/no-login e ad uso condiviso in cucina, le azioni vanno pensate con conferme leggere ma senza frizioni eccessive (niente form complessi: tap rapidi, input minimi, magari con auto-save invece di "salva" esplicito dove sensato).
- Nessuna azione distruttiva "silenziosa": cancellazioni (es. rimuovere un evento) meritano comunque un piccolo step di conferma per evitare tocchi accidentali col trackpad.

## 7. Backend aggregatore (BFF)

### 7.1 Responsabilità

- Espone un'unica API REST coerente al frontend (uno schema dati "HomeHub", non gli schemi eterogenei delle fonti), sia in lettura che in scrittura.
- Gestisce OAuth2 con Google Calendar (token storage + refresh automatico) e le chiamate di scrittura (creazione eventi).
- Gestisce sessione/credenziali Bring! (libreria non ufficiale, es. `bring-shopping` per Node o `python-bring-api` per Python), sia per leggere la lista sia per modificarla.
- Menu di casa e home inventory si leggono direttamente dai rispettivi schemi Postgres (`dieta.menu_settimanale`, `home_inventory`), niente API REST di mezzo — nessuna web app esterna resta da integrare via API REST generica (finanze è stata valutata, implementata e poi rimossa deliberatamente, vedi §5).
- Cache per ridurre il numero di chiamate esterne (polling schedulato, es. calendario ogni 5', Bring! ogni 2', menu ogni 15'); le letture dirette da Postgres (dieta, home_inventory) non serve cacciarle, sono query locali, non chiamate di rete.
- Storage per i dati "manuali" (menu scolastico, piano allenamenti) su **PostgreSQL** (istanza già esistente — HomeHub userà un proprio schema dedicato, per non mischiarsi con le tabelle delle altre app).
- Config/secret management: base in `.env` locale sul NUC (credenziali Postgres, OAuth Google, credenziali Bring!/Garmin), mai nel repo — ✅ dalla pagina Impostazioni si può sovrascrivere qualunque campo "personalizzabile" (incluse le credenziali delle integrazioni) su `homehub.app_config`, che vince su `.env` se compilato: comodo per cambiare una credenziale senza accedere al NUC. Vedi `backend/app/core/runtime_settings.py`.

### 7.1.1 Schema Postgres (bozza iniziale)

Tabelle indicative nello schema dedicato `homehub`:
- `school_menu(id, week_start_date, day_of_week, meal_text, created_at, updated_at)`
- `training_plan(id, week_start_date, day_of_week, session_text, done boolean, from_garmin boolean, created_at, updated_at)` — `from_garmin` distingue le righe ancora solo specchio del piano Garmin (auto-eliminabili se Garmin non pianifica più nulla quel giorno) da quelle modificate a mano, vedi migrazione `0004_training_from_garmin.py`
- `chore(id, title, interval_days, last_done_date, assignee, notes, created_at, updated_at)` — attività di casa ricorrenti per intervallo (Manutenzione), vedi migrazione `0005_chores.py`
- `todo_item(id, title, assignee, priority, due_date, done boolean, created_at, updated_at)` — vedi migrazione `0003_todo.py`
- `cache_entries(source, key, payload jsonb, fetched_at)` *(opzionale, se si preferisce cache persistente a cache in memoria)*
- `app_config(key, value)` — ✅ override da Impostazioni che vincono sul corrispondente campo di `.env` (incluse le credenziali Google/Bring!/Garmin, scelta esplicita per gestirle da UI): nome famiglia, palette di sfondo, meteo (nome/lat/lon), credenziali integrazioni. Chiave assente o vuota = si usa `.env`. Vedi `backend/app/core/runtime_settings.py` (unico lettore) e `backend/app/api/routes/settings.py` (unico scrittore)

### 7.2 Stack tecnico — deciso

**Python + FastAPI**, per coerenza con le 3 web app esistenti (tutte in Python): stile di codice condiviso, possibilità di riusare modelli/utility, e un solo linguaggio lato server da mantenere.

Librerie di riferimento per gli adapter:
- **Google Calendar**: `google-api-python-client` + `google-auth-oauthlib` (OAuth2, token refresh) — ✅ integrato (`backend/app/adapters/google_calendar.py`); setup una tantum del refresh token in `backend/scripts/google_oauth_setup.py`.
- **Bring!**: `bring-api` (non ufficiale, async/aiohttp) — ✅ integrato (`backend/app/adapters/bring.py`).
- **Garmin Connect**: `garminconnect` (non ufficiale) — ✅ integrato (`backend/app/adapters/garmin.py`); setup una tantum del login/MFA in `backend/scripts/garmin_login_setup.py`.
- **Postgres**: SQLAlchemy (+ Alembic per le migrazioni dello schema `homehub`).
- **Scheduling/polling**: `APScheduler` (o task periodici gestiti da FastAPI + `asyncio`) per i job di refresh cache.

### 7.3 Pattern "adapter"

Ogni integrazione esterna è isolata in un modulo/adapter con la stessa interfaccia sia per la lettura (`fetch()`, `normalize()`, `cacheTtl`) sia per la scrittura (`performAction(action, payload)`), così aggiungere una nuova fonte o una nuova azione in futuro (es. meteo, un nuovo servizio) non tocca il resto del backend.

## 8. Deployment sul NUC

- **Docker Compose** con due servizi: `frontend` (build statica + nginx) e `backend` (Python/FastAPI). Nessun container Postgres da gestire: HomeHub si collega all'istanza Postgres già esistente (solo credenziali/connection string in `.env`, più migrazione Alembic per creare lo schema dedicato `homehub`).
- **Un solo punto d'ingresso esposto**: nginx (nel container frontend) serve la SPA e fa da reverse proxy verso il backend su `/api/*`; il backend non pubblica alcuna porta sull'host, è raggiungibile solo dal frontend via rete Docker interna. Riduce la superficie esposta a una sola porta, importante dato che l'utente ha scelto di rendere HomeHub raggiungibile anche da fuori casa via port forwarding sul router (vedi DEPLOY.md).
- ✅ **Login unico e condiviso** (una sola password per tutta la famiglia, non account per persona — coerente con "no multi-utente", §2): un cookie di sessione firmato, valido **30 giorni**, così sul NUC in pratica non si vede quasi mai una volta fatto il primo accesso. Sostituisce la Basic Auth di nginx usata prima (rimossa: Chrome/Edge con policy aziendali bloccavano in silenzio il popup nativo, impedendo l'accesso da remoto — un form di login normale non ha questo problema). Protegge **tutte** le rotte `/api/*` (tranne login/health), non solo l'accesso da fuori LAN: prima di questa feature, con la Basic Auth disattivata per il problema del popup, la porta esposta sul router era raggiungibile da chiunque su internet senza nessuna autenticazione. Password hashata con bcrypt (mai in chiaro), sovrascrivibile da Impostazioni → Sicurezza (che invalida anche tutte le sessioni già aperte, non solo quella di chi la cambia) o via `backend/scripts/generate_password_hash.py`. Vedi `backend/app/core/auth.py`, il middleware in `backend/app/main.py` e [DEPLOY.md](DEPLOY.md).
- Chromium in **kiosk mode**, autostart via systemd, puntato su `http://localhost` (o porta del frontend).
- systemd con `Restart=always` sia per i container che per il processo Chromium, per resilienza dopo reboot/crash.
- Rotazione schermo: già gestita a livello OS (dato che MagicMirror gira già verticale sullo stesso setup).

## 9. Punti operativi — risolti

1. **Raggiungibilità Postgres**: confermato che l'istanza è raggiungibile sulla **stessa LAN** del NUC → connection string diretta (`host:porta` della LAN) in `.env`, nessun tunnel/VPN necessario. Consigliato comunque creare un **utente Postgres dedicato** con permessi limitati al solo schema `homehub` (niente accesso alle tabelle delle altre app), per isolamento.

## 10. Roadmap proposta (fasi)

- **Fase 0 — Scaffolding** ✅ *(fatto)*: monorepo `frontend/` (React + Vite + TS, rail + routing per tutti i tab, TanStack Query, idle/attract mode) e `backend/` (FastAPI, adapter per tutte le fonti con dati mock finché mancano le credenziali reali, modelli/migrazione Alembic per lo schema `homehub`, route REST complete), più `docker-compose.yml` e `.env.example`. Kiosk mode (Chromium + systemd) non ancora configurato: è un passo di deploy sul NUC reale, non scaffolding di codice.
- **Fase 1 — Backend base**: skeleton BFF ✅, connessione al Postgres esistente (schema `homehub`) ✅, integrazione Google Calendar (lettura + aggiunta evento) ✅ *(vedi `backend/app/adapters/google_calendar.py`)*, Home con card calendario reali ✅, meteo ✅ *(Open-Meteo, gratuita e senza chiave, vedi `backend/app/adapters/weather.py`)*.
- **Fase 2 — Menu & Allenamenti**: ✅ fatto. Tab Menu con template scuola/merende a rotazione (data entry in Impostazioni) + ✅ tutti i pasti di casa (colazione/spuntini/pranzo/cena) letti da `dieta.menu_settimanale`; tab Allenamenti da Garmin Connect + `dieta.allenamento`.
- **Fase 3 — Spesa & Inventory**: ✅ fatto. Bring! (lettura + spunta/aggiunta/rimozione articoli, vedi `backend/app/adapters/bring.py`); home inventory in sola lettura, alert oggetti scaduti/in scadenza entro 7gg letti direttamente dallo schema Postgres `home_inventory` (vedi `backend/app/db/home_inventory_models.py`), niente azioni di scrittura (gestione lasciata alla web app dedicata).
- **Fase 3.1 — Todo list**: ✅ fatto. Todo list condivisa di famiglia con priorità/scadenza/assegnatario libero, CRUD completo nel tab dedicato, card riepilogo in Home — vedi `backend/app/api/routes/todo.py` e `frontend/src/pages/TodoPage.tsx`.
- **Fase 4 — Finanze & rifiniture azioni**: tab Finanze implementata (percentuali di budget + promemoria scadenze, mai importi) e poi **rimossa deliberatamente** — non è un'informazione da colpo d'occhio quotidiano, non giustificava la complessità (credenziali JWT, modalità ospiti dedicata). Resta da fare la revisione UX generale delle azioni di scrittura (conferme, feedback visivo, gestione errori di rete verso le fonti esterne).
- **Fase 5 — Polish & go-live**: idle/attract mode, gestione errori/offline dei singoli adapter, dismissione MagicMirror, deploy definitivo systemd+Docker sul NUC.
- **Fase 6 — Estensioni future**: sync automatico allenamenti da Garmin Connect ✅ *(fatto, vedi sopra)*, SSE per aggiornamenti push multi-dispositivo, altri moduli.

---

Il documento è ora sostanzialmente completo. Restano solo i due dettagli operativi del §9 (meccanismo di auth verso le API delle app esistenti, raggiungibilità del Postgres dal NUC) da chiarire prima o durante lo scaffolding — non bloccano l'inizio del lavoro.
