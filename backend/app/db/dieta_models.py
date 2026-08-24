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
