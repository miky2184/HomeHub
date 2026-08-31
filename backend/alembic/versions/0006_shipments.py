"""Spedizioni: tracking pacchi (per ora solo Poste Italiane)

Nuova tabella shipment: numero di tracking + corriere, più i campi cache
dell'ultimo stato letto dal corriere (status, delivered, ultimo evento,
storico eventi in JSON, timestamp/errore dell'ultimo poll). Lo stato si
aggiorna on-demand (nessuno scheduler in background) quando il tab
Spedizioni/la card Home vengono aperti e last_polled_at è più vecchio della
soglia — vedi services/aggregator.refresh_shipment.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "homehub"


def upgrade() -> None:
    op.create_table(
        "shipment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tracking_number", sa.String(length=64), nullable=False),
        sa.Column("carrier", sa.String(length=30), nullable=False, server_default="poste_italiane"),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("delivered", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_event_description", sa.Text(), nullable=True),
        sa.Column("last_event_location", sa.Text(), nullable=True),
        sa.Column("events", sa.JSON(), nullable=True),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_poll_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.CheckConstraint("carrier in ('poste_italiane', 'altro')", name="ck_shipment_carrier"),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("shipment", schema=SCHEMA)
