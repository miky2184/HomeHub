"""Lettura (sola lettura) dello schema "home" — l'altra web app dell'utente
per la gestione delle finanze (python-finanze-api), stesso Postgres di
homehub.

Usata SOLO per il widget "prossime scadenze" (nessun endpoint dedicato in
quell'app per questo, vedi ARCHITECTURE.md §5): tipo_conto=0 = movimento
"da avere"/pianificato, value negativo = uscita (in arrivo). Non leggiamo
mai la colonna `value` nel widget — solo per filtrare, mai per mostrarla:
HomeHub gira su un monitor in cucina visibile anche dagli ospiti, niente
importi. Il resto delle finanze (percentuali di budget) passa invece
dall'API REST di quell'app (app/adapters/finance.py), che ha già la
logica di calcolo budget/proiezione — qui serve solo questa tabella.
"""

from sqlalchemy import BigInteger, Column, Date, MetaData, Numeric, String, Table

finance_metadata = MetaData(schema="home")

finance_table = Table(
    "finance",
    finance_metadata,
    Column("id", BigInteger, primary_key=True),
    Column("data_val", Date),
    Column("tipo_conto", BigInteger),
    Column("beneficiario", BigInteger),
    Column("value", Numeric),
    Column("id_db", BigInteger),
)

beneficiario_table = Table(
    "beneficiario",
    finance_metadata,
    Column("id", BigInteger, primary_key=True),
    Column("descrizione", String(255)),
    Column("id_db", BigInteger),
)
