"""
SQLAlchemy Database Models for RAG Chatbot
Defines chat sessions, messages, and query logs for Neon Postgres.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""
    pass


class ChatSession(Base):
    """
    Represents a chat conversation session.

    A session is created when the user opens the chat widget and persists
    for the duration of the browser session.
    """
    __tablename__ = "chat_sessions"

    session_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique session identifier (UUID v4)"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Session creation timestamp"
    )
    chapter_context: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Chapter ID user was reading (e.g., 'module-1-ros2-basics/chapter-2')"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Browser user agent for analytics"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Record creation timestamp"
    )

    # Relationships
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        doc="All messages in this session"
    )
    query_logs: Mapped[list["QueryLog"]] = relationship(
        "QueryLog",
        back_populates="session",
        doc="All query logs for this session"
    )

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.session_id}, started_at={self.started_at})>"


class ChatMessage(Base):
    """
    Represents a single message in a chat conversation.

    Messages can be from either the user or the assistant (chatbot).
    Assistant messages include citations from the textbook.
    """
    __tablename__ = "chat_messages"

    message_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique message identifier"
    )
    session_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent session ID"
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Message sender: 'user' or 'assistant'"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Message text (markdown for assistant)"
    )
    citations: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Array of citation objects (assistant only)"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        doc="Message creation timestamp"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Record creation timestamp"
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant')",
            name="check_role"
        ),
        CheckConstraint(
            "LENGTH(content) BETWEEN 1 AND 10000",
            name="check_content_length"
        ),
    )

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.message_id}, role={self.role})>"


class QueryLog(Base):
    """
    Analytics record for chatbot query performance.

    Logs each chat query for monitoring response quality, latency,
    and token usage.
    """
    __tablename__ = "query_logs"

    query_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique log identifier"
    )
    session_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("chat_sessions.session_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Parent session (NULL if session deleted)"
    )
    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="User's original question"
    )
    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Assistant's response (without citations)"
    )
    tokens_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Total tokens (prompt + completion)"
    )
    response_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="End-to-end latency in milliseconds"
    )
    chunks_retrieved: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        doc="Number of vector chunks retrieved"
    )
    avg_similarity_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Average cosine similarity of retrieved chunks"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        doc="Query execution timestamp"
    )

    # Relationships
    session: Mapped[Optional["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="query_logs"
    )

    def __repr__(self) -> str:
        return f"<QueryLog(id={self.query_id}, tokens={self.tokens_used})>"
