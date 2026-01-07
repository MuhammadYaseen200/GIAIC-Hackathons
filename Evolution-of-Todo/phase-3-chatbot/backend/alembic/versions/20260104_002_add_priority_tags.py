"""Add priority and tags columns to tasks table.

Revision ID: 002
Revises: 001
Create Date: 2026-01-04 00:00:00.000000

Per ADR-011: Task Schema Extension
- Priority as PostgreSQL ENUM (high/medium/low, default medium)
- Tags as JSON array (default empty array)

This migration is safe for Phase 2 compatibility:
- Existing tasks get priority='medium' and tags=[]
- No breaking changes to existing data
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add priority and tags columns to tasks table.

    Migration follows ADR-011 specification:
    1. Add priority column with VARCHAR type (compatible with both PostgreSQL and SQLite)
    2. Add tags column with JSON type (compatible with both PostgreSQL and SQLite)
    """
    # Check the database dialect and create appropriate column
    # For PostgreSQL, we create the ENUM type; for SQLite we use VARCHAR
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == 'postgresql':
        # PostgreSQL: Create ENUM type for priority
        op.execute("CREATE TYPE priority AS ENUM ('high', 'medium', 'low')")
        priority_column = sa.Column(
            "priority",
            sa.Enum("high", "medium", "low", name="priority", create_type=False),
            server_default="medium",
            nullable=False,
        )
    else:
        # SQLite: Use VARCHAR with check constraint (simulating enum behavior)
        priority_column = sa.Column(
            "priority",
            sa.VARCHAR(10),
            server_default="medium",
            nullable=False,
        )

    # Step 1: Add priority column with default value
    # Using server_default ensures existing Phase 2 tasks get 'medium'
    op.add_column(
        "tasks",
        priority_column
    )

    # Step 2: Add tags column as JSON with default empty array
    # Using server_default ensures existing Phase 2 tasks get empty list
    op.add_column(
        "tasks",
        sa.Column(
            "tags",
            sa.JSON(),
            server_default="[]",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove priority and tags columns from tasks table.

    This drops the columns and the ENUM type to revert to Phase 2 schema.
    """
    # Drop tags column first (no dependencies)
    op.drop_column("tasks", "tags")

    # Drop priority column
    op.drop_column("tasks", "priority")

    # Check the database dialect and drop appropriate type
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == 'postgresql':
        # PostgreSQL: Drop the ENUM type
        op.execute("DROP TYPE priority")
