"""Task model for todo items."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    """Task model representing todo items.

    Attributes:
        id: Unique identifier for the task (UUID, auto-generated).
        user_id: Foreign key to User.id (indexed for multi-tenancy).
        title: Task title (1-200 characters, required).
        description: Task description (max 1000 chars, default empty).
        completed: Whether task is completed (default False).
        created_at: Timestamp when task was created (UTC, auto-generated).
        updated_at: Timestamp when task was last updated (UTC, auto-update).
    """

    __tablename__ = "tasks"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique task identifier",
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        description="Owner user ID (multi-tenancy key)",
    )
    title: str = Field(
        min_length=1,
        max_length=200,
        description="Task title",
    )
    description: str = Field(
        default="",
        max_length=1000,
        description="Task description",
    )
    completed: bool = Field(
        default=False,
        description="Task completion status",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Task creation timestamp (UTC)",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
        description="Last update timestamp (UTC)",
    )
