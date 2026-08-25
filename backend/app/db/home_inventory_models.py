"""Accesso allo schema "home_inventory" — l'altra web app dell'utente per la
gestione dell'inventario di casa (home_inventory_web, vedi le sue DDL reali
in categories/containers/items/movements).

Stesso Postgres di homehub, schema diverso. Per lo più sola lettura: creare/
modificare/eliminare oggetti resta compito della web app dedicata (che ha
già tutta la UI per farlo); qui HomeHub legge ciò che serve per l'alert di
scadenza e per "sfoglia per contenitore" in Home/Casa — per questo sono
`Table` Core e non modelli dichiarativi, e mappiamo solo le colonne che
usiamo davvero. Unica eccezione in scrittura: l'aggiustamento rapido della
quantità (+/- dalla tab Casa, vedi services/aggregator.adjust_item_quantity)
per non dover aprire home_inventory_web solo per segnare "bevuto un vino" o
"comprato un fardello d'acqua".
"""

from sqlalchemy import Column, Date, Integer, MetaData, String, Table

home_inventory_metadata = MetaData(schema="home_inventory")

items_table = Table(
    "items",
    home_inventory_metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(200)),
    Column("container_id", Integer),
    Column("category_id", Integer),
    Column("quantity", Integer),
    Column("unit_measure", String(20)),
    Column("expiry_date", Date),
)

containers_table = Table(
    "containers",
    home_inventory_metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100)),
)

categories_table = Table(
    "categories",
    home_inventory_metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100)),
)
