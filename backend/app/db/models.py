"""Tabelle "manuali" di HomeHub: menu scolastico (a rotazione), merende e
piano allenamenti (quest'ultimo ormai perlopiù sostituito da Garmin/dieta,
vedi services/aggregator.py, ma la tabella resta come fallback)."""

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, Date, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class SchoolMenuTemplateEntry(Base):
    """Il "volantino" della scuola: menu a rotazione di 4 settimane, lun-ven.
    Cambia un paio di volte l'anno (data entry in Impostazioni), non ad ogni
    settimana reale — vedi SchoolMenuCycleAnchor per il collegamento tra
    settimana reale e settimana del ciclo."""

    __tablename__ = "school_menu_template"
    __table_args__ = (UniqueConstraint("cycle_week", "day_of_week", name="uq_school_menu_template"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cycle_week: Mapped[int] = mapped_column(Integer)  # 1..4
    day_of_week: Mapped[int] = mapped_column(Integer)  # 0 = lunedì ... 4 = venerdì
    meal_text: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SchoolMenuCycleAnchor(Base):
    """Punto di riferimento per calcolare, per qualunque settimana reale, a
    quale settimana del ciclo di 4 corrisponde: "a partire da questo lunedì,
    siamo alla settimana N". Una sola riga attiva (id=1); va aggiornata solo
    quando la scuola comunica un nuovo volantino/riparte la numerazione."""

    __tablename__ = "school_menu_cycle_anchor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    anchor_monday: Mapped[date] = mapped_column(Date)
    anchor_cycle_week: Mapped[int] = mapped_column(Integer)  # 1..4


class SnackTemplateEntry(Base):
    """Merenda mattina/pomeriggio: fissa per giorno della settimana, identica
    ogni settimana (a differenza del menu scuola, nessuna rotazione multi-
    settimana). Data entry in Impostazioni."""

    __tablename__ = "snack_template"
    __table_args__ = (UniqueConstraint("day_of_week", "snack_type", name="uq_snack_template"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_of_week: Mapped[int] = mapped_column(Integer)  # 0 = lunedì ... 4 = venerdì
    snack_type: Mapped[str] = mapped_column(String(20))  # "mattina" | "pomeriggio"
    snack_text: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TrainingSession(Base):
    __tablename__ = "training_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_start_date: Mapped[date] = mapped_column(Date, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer)
    session_text: Mapped[str] = mapped_column(Text)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    # True se session_text è ancora solo uno specchio del piano Garmin (mai
    # modificato a mano) — permette a get_week_training di eliminare la riga
    # quando Garmin non pianifica più nulla quel giorno (es. allenamento
    # spostato a domani), invece di lasciare un allenamento fantasma per
    # sempre. False appena l'utente lo modifica da UI (PUT /api/training):
    # da quel momento è un inserimento suo, non va più cancellato solo
    # perché Garmin cambia idea.
    from_garmin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TodoItem(Base):
    """Todo list condivisa di famiglia (no multi-utente: una lista sola,
    "per chi" è solo un'etichetta libera, non un vero assegnatario/login)."""

    __tablename__ = "todo_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    assignee: Mapped[str | None] = mapped_column(String(100), default=None)
    priority: Mapped[str] = mapped_column(String(10), default="media")  # "alta" | "media" | "bassa"
    due_date: Mapped[date | None] = mapped_column(Date, default=None)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Chore(Base):
    """Attività di casa ricorrenti per intervallo (non a data fissa come gli
    eventi di calendario): "pulire il filtro della lavastoviglie ogni 90
    giorni", non "compra il latte" (quello è un Todo, una tantum). La
    prossima scadenza si calcola da last_done_date + interval_days (mai
    fatta → considerata scaduta da subito, vedi
    services/aggregator.chore_item_out). "per chi" libero come in Todo."""

    __tablename__ = "chore"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    interval_days: Mapped[int] = mapped_column(Integer)
    last_done_date: Mapped[date | None] = mapped_column(Date, default=None)
    assignee: Mapped[str | None] = mapped_column(String(100), default=None)
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Shipment(Base):
    """Spedizione tracciata manualmente (numero + corriere), letta on-demand
    dal corriere quando il tab Spedizioni/la card Home vengono aperti e
    l'ultimo poll è più vecchio di STALE_AFTER_MINUTES (vedi
    services/aggregator.refresh_shipment) — nessuno scheduler in background,
    stesso principio "poll on read con TTL" già usato per meteo/Bring!/
    Garmin (vedi services/cache.py), solo che qui il TTL è persistito sulla
    riga (last_polled_at) invece che in cache in-memory, perché lo stato va
    mostrato anche appena aperta la pagina, prima di un eventuale refresh.
    Solo carrier="poste_italiane" ha tracking automatico oggi (vedi
    adapters/poste_italiane.py); "altro" è un contenitore manuale senza
    refresh, per corrieri non ancora supportati."""

    __tablename__ = "shipment"
    __table_args__ = (CheckConstraint("carrier in ('poste_italiane', 'altro')", name="ck_shipment_carrier"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tracking_number: Mapped[str] = mapped_column(String(64))
    carrier: Mapped[str] = mapped_column(String(30), default="poste_italiane")
    label: Mapped[str | None] = mapped_column(Text, default=None)  # nota libera, es. "Scarpe Sofia"
    status: Mapped[str | None] = mapped_column(Text, default=None)  # ultimo "sintesiStato" grezzo del corriere
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    last_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    last_event_description: Mapped[str | None] = mapped_column(Text, default=None)
    last_event_location: Mapped[str | None] = mapped_column(Text, default=None)
    # Storico completo eventi: [{"at": iso, "description": ..., "location": ...}, ...]
    events: Mapped[list | None] = mapped_column(JSON, default=None)
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    last_poll_error: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AppConfig(Base):
    """Config runtime key/value, sovrascrivibile dalla pagina Impostazioni:
    se una chiave è presente qui (e non vuota) vince sul corrispondente
    campo di .env — incluse le credenziali delle integrazioni (Google/
    Bring!/Garmin), scelta esplicita dell'utente per poterle gestire da UI
    senza toccare il file sul NUC. Vedi app/core/runtime_settings.py (unico
    lettore) e api/routes/settings.py (unico scrittore)."""

    __tablename__ = "app_config"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
