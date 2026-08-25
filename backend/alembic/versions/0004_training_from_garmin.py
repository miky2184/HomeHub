"""training_plan: colonna from_garmin

Distingue le righe che sono ancora solo uno specchio del piano Garmin
(from_garmin=true) da quelle modificate a mano dall'utente. Serve a
get_week_training per eliminare un giorno quando Garmin non lo pianifica
più (es. allenamento spostato a un altro giorno) invece di mostrare per
sempre un allenamento fantasma — vedi backend/app/api/routes/training.py.

Righe già esistenti: default false (trattate come "manuali", quindi non
verranno mai auto-eliminate) — conservativo, non sappiamo retroattivamente
quali fossero solo uno specchio di Garmin.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "homehub"


def upgrade() -> None:
    op.add_column(
        "training_plan",
        sa.Column("from_garmin", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_column("training_plan", "from_garmin", schema=SCHEMA)
