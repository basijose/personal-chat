"""add archived flag to conversations

Revision ID: 0002_conversation_archived
Revises: 0001_initial
Create Date: 2026-08-26 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_conversation_archived"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("conversations", "archived")
