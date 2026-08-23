"""Setup SQLAlchemy: engine, sessione, base dichiarativa sullo schema dedicato `homehub`."""

from collections.abc import Generator

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy import create_engine

from app.core.config import get_settings

settings = get_settings()

# Tutte le tabelle HomeHub vivono nello schema dedicato, isolate dalle altre app
# che condividono la stessa istanza Postgres.
metadata = MetaData(schema=settings.database_schema)


class Base(DeclarativeBase):
    metadata = metadata


# La connessione è creata qui ma non viene aperta finché non serve davvero
# (nessuna query all'avvio dell'app): il backend può quindi partire anche se
# il Postgres non è momentaneamente raggiungibile, e fallire solo sulle rotte
# che leggono/scrivono dati manuali.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
