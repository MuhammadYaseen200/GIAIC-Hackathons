"""User model for authentication and authorization."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """User model representing registered users.

    Attributes:
        id: Unique identifier for the user (UUID, auto-generated).
        email: User's email address (unique, indexed, max 254 chars).
        password_hash: Bcrypt-hashed password (required).
        created_at: Timestamp when user was created (UTC, auto-generated).
    """

    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique user identifier",
    )
    email: str = Field(
        max_length=254,
        unique=True,
        index=True,
        description="User email address",
    )
    password_hash: str = Field(
        description="Bcrypt-hashed password",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Account creation timestamp (UTC)",
    )
