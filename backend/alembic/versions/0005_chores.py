"""Manutenzione: attività di casa ricorrenti per intervallo

Nuova tabella chore: titolo, intervallo in giorni, data dell'ultima volta
fatta (nullable — mai fatta = scaduta da subito), "per chi" libero come
in todo_item, note opzionali. Diversa da todo_item: non una-tantum, la
prossima scadenza si ricalcola ogni volta da last_done_date + interval_days
(vedi services/aggregator.chore_item_out).

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "homehub"


def upgrade() -> None:
    op.create_table(
        "chore",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("last_done_date", sa.Date(), nullable=True),
        sa.Column("assignee", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.CheckConstraint("interval_days > 0", name="ck_chore_interval_positive"),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("chore", schema=SCHEMA)
