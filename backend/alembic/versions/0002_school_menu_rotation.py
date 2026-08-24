"""Menu scolastico a rotazione (4 settimane) + merende fisse settimanali

Sostituisce school_menu (un valore per ogni settimana reale, mai popolato)
con un modello a template: il volantino della scuola è un ciclo di 4
settimane che si ripete, non un inserimento per ogni settimana reale.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "homehub"


def upgrade() -> None:
    op.drop_table("school_menu", schema=SCHEMA)

    op.create_table(
        "school_menu_template",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cycle_week", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("meal_text", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        schema=SCHEMA,
    )
    op.create_unique_constraint(
        "uq_school_menu_template", "school_menu_template", ["cycle_week", "day_of_week"], schema=SCHEMA
    )

    op.create_table(
        "school_menu_cycle_anchor",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("anchor_monday", sa.Date(), nullable=False),
        sa.Column("anchor_cycle_week", sa.Integer(), nullable=False),
        schema=SCHEMA,
    )

    op.create_table(
        "snack_template",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("snack_type", sa.String(length=20), nullable=False),
        sa.Column("snack_text", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        schema=SCHEMA,
    )
    op.create_unique_constraint(
        "uq_snack_template", "snack_template", ["day_of_week", "snack_type"], schema=SCHEMA
    )


def downgrade() -> None:
    op.drop_table("snack_template", schema=SCHEMA)
    op.drop_table("school_menu_cycle_anchor", schema=SCHEMA)
    op.drop_table("school_menu_template", schema=SCHEMA)

    op.create_table(
        "school_menu",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("week_start_date", sa.Date(), nullable=False, index=True),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("meal_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        schema=SCHEMA,
    )
    op.create_unique_constraint(
        "uq_school_menu_week_day", "school_menu", ["week_start_date", "day_of_week"], schema=SCHEMA
    )
