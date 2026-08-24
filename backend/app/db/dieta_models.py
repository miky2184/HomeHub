"""Lettura (sola lettura) dello schema "dieta" — appartiene a un'altra web
app dell'utente (gestione menu/dieta), che sincronizza già gli allenamenti
svolti da Garmin con dati più ricchi di quelli ottenibili dalla sola API
Garmin (FC, passo, TSS, dislivello, effetto allenamento, ...).

Stesso Postgres di homehub (vedi ARCHITECTURE.md), schema diverso. Nessun
ORM mapping scrivibile di proposito: HomeHub non deve mai scrivere qui,
solo leggere — per questo sono `Table` Core e non modelli dichiarativi con
Base condivisa con app.db.models (che invece sono le tabelle di HomeHub).
"""

from sqlalchemy import BigInteger, Column, Date, Float, Integer, MetaData, Table, Text
from sqlalchemy.dialects.postgresql import JSONB

dieta_metadata = MetaData(schema="dieta")

allenamento_table = Table(
    "allenamento",
    dieta_metadata,
    Column("id", BigInteger, primary_key=True),
    Column("user_id", BigInteger),
    Column("garmin_id", BigInteger),
    Column("tipo", Text),
    Column("data", Date),
    Column("titolo", Text),
    Column("distanza_m", Float),
    Column("calorie", Integer),
    Column("durata_sec", Integer),
    Column("fc_media", Integer),
    Column("fc_max", Integer),
    Column("te_aerobico", Float),
    Column("passo_sec", Integer),
    Column("cadenza", Integer),
    Column("tss", Float),
    Column("ascesa_m", Integer),
    Column("swolf", Float),
    Column("frequenza_vogate", Float),
)

# Menu di casa (cena): il piano nutrizionale che l'utente genera/gestisce
# nella web app "dieta" copre tutta la famiglia, non solo lui — HomeHub
# legge da qui la cena del giorno per la Home/Cucina. Struttura della
# colonna jsonb `menu` (vedi dieta/app/services/menu_services.py):
# menu["day"][<nome giorno IT senza accenti>]["pasto"][<colazione|
# spuntino_mattina|pranzo|spuntino_pomeriggio|cena|spuntino_sera>]
# = {"ids": [...], "ricette": [{"nome_ricetta": ..., ...}, ...]}
menu_settimanale_table = Table(
    "menu_settimanale",
    dieta_metadata,
    Column("id", Integer, primary_key=True),
    Column("data_inizio", Date),
    Column("data_fine", Date),
    Column("menu", JSONB),
    Column("user_id", BigInteger),
)

# Chiavi giorno usate nel jsonb "menu", nello stesso ordine di date.weekday()
# (0=lunedì ... 6=domenica) — nomi italiani minuscoli senza accenti, esatti
# come scritti da dieta/app/routes/menu_giornaliero_route.py.
GIORNI_SETTIMANA_IT = ["lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato", "domenica"]
