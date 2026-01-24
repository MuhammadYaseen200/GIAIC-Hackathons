"""Conversation model for AI chatbot history.

Stores conversation threads and messages between users and the AI assistant.
Messages are stored as a JSON array to preserve conversation state.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return current UTC time as timezone-naive datetime for PostgreSQL compatibility."""
    return datetime.utcnow()


class MessageRole(str):
    """Message role type for conversation messages.

    Represents who sent a message in the conversation.
    """

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(SQLModel, table=True):
    """Conversation model representing AI chat threads.

    A conversation contains an ordered list of messages exchanged between
    a user and the AI assistant. Messages are stored as JSON for flexibility
    and to support different message formats (text, tool calls, etc.).

    Attributes:
        id: Unique identifier for the conversation (UUID, auto-generated).
        user_id: Foreign key to User.id (indexed for multi-tenancy).
        messages: Ordered list of conversation messages as JSON.
            Each message is a dict with: role, content, tool_calls?, timestamp?
        created_at: Timestamp when conversation was created (UTC, auto-generated).
        updated_at: Timestamp when conversation was last updated (UTC, auto-update).
    """

    __tablename__ = "conversations"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique conversation identifier",
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        description="Owner user ID (multi-tenancy key)",
    )
    title: str | None = Field(
        default=None,
        description="Conversation title for display in thread list",
    )
    messages: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_type=JSON,
        description="Ordered list of conversation messages",
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Conversation creation timestamp (UTC)",
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column_kwargs={"onupdate": utc_now},
        description="Last update timestamp (UTC)",
    )
