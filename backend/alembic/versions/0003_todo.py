"""Todo list condivisa di famiglia

Nuova tabella todo_item: titolo, priorità (alta/media/bassa), assegnatario
libero ("per chi"), scadenza opzionale, stato fatto/non fatto.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "homehub"


def upgrade() -> None:
    op.create_table(
        "todo_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("assignee", sa.String(length=100), nullable=True),
        sa.Column("priority", sa.String(length=10), nullable=False, server_default="media"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("done", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.CheckConstraint("priority IN ('alta', 'media', 'bassa')", name="ck_todo_item_priority"),
        schema=SCHEMA,
    )
    op.create_index("idx_todo_item_done", "todo_item", ["done"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_table("todo_item", schema=SCHEMA)
