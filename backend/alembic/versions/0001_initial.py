"""Schema iniziale HomeHub: menu scolastico, piano allenamenti, config

Revision ID: 0001
Revises:
Create Date: 2026-08-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "homehub"


def upgrade() -> None:
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

    op.create_table(
        "training_plan",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("week_start_date", sa.Date(), nullable=False, index=True),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("session_text", sa.Text(), nullable=False),
        sa.Column("done", sa.Boolean(), nullable=False, server_default=sa.false()),
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
        "uq_training_plan_week_day", "training_plan", ["week_start_date", "day_of_week"], schema=SCHEMA
    )

    op.create_table(
        "app_config",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("app_config", schema=SCHEMA)
    op.drop_table("training_plan", schema=SCHEMA)
    op.drop_table("school_menu", schema=SCHEMA)
