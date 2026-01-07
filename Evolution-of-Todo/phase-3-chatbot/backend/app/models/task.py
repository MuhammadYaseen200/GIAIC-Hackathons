"""Task model for todo items."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return current UTC time as timezone-naive datetime for PostgreSQL compatibility."""
    return datetime.utcnow()


class Priority(str, Enum):
    """Task priority levels.

    Values defined by the project constitution (Intermediate Level Features).
    Uses lowercase enum names to match PostgreSQL enum values.
    """

    high = "high"
    medium = "medium"
    low = "low"


class Task(SQLModel, table=True):
    """Task model representing todo items.

    Attributes:
        id: Unique identifier for the task (UUID, auto-generated).
        user_id: Foreign key to User.id (indexed for multi-tenancy).
        title: Task title (1-200 characters, required).
        description: Task description (max 1000 chars, default empty).
        completed: Whether task is completed (default False).
        priority: Task priority level (high/medium/low, default medium).
        tags: Task categorization labels (max 10 tags, each max 50 chars).
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
    priority: Priority = Field(
        default=Priority.medium,
        description="Task priority level (high/medium/low)",
    )
    tags: list[str] = Field(
        default_factory=list,
        sa_type=JSON,
        description="Task categorization labels (max 10 tags, each max 50 chars)",
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Task creation timestamp (UTC)",
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column_kwargs={"onupdate": utc_now},
        description="Last update timestamp (UTC)",
    )
