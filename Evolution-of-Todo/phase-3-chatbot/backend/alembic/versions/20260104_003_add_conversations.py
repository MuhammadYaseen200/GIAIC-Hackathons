"""Add conversations table for AI chatbot history.

Revision ID: 003
Revises: 002
Create Date: 2026-01-04 00:00:00.000000

Creates conversations table to store AI chatbot conversation threads.
Messages are stored as JSON to preserve conversation state and support
different message formats (text, tool calls, etc.).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create conversations table.

    Table structure:
    - id: UUID primary key
    - user_id: Foreign key to users.id (indexed for multi-tenancy)
    - messages: JSON array of conversation messages
    - created_at: Timestamp when conversation was created
    - updated_at: Timestamp when conversation was last updated
    """
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "messages",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_conversations_user_id"),
        "conversations",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop conversations table."""
    op.drop_index(op.f("ix_conversations_user_id"), table_name="conversations")
    op.drop_table("conversations")
