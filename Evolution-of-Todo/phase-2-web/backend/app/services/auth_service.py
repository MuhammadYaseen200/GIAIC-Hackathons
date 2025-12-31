"""Authentication service for user registration and login.

Provides business logic for:
- User registration with email/password
- User authentication
- User lookup by ID or email
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import hash_password, verify_password
from app.models.user import User


class AuthService:
    """Service for user authentication operations.

    Attributes:
        session: Async database session for queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize AuthService with database session.

        Args:
            session: Async database session.
        """
        self.session = session

    async def register(self, email: str, password: str) -> User:
        """Register a new user with email and password.

        Args:
            email: User's email address.
            password: Plain text password (will be hashed).

        Returns:
            User: Newly created user instance.

        Raises:
            ValueError: If email is already registered.
        """
        # Check if email already exists
        existing = await self.get_user_by_email(email)
        if existing:
            raise ValueError(f"Email '{email}' is already registered")

        # Create new user with hashed password
        user = User(
            email=email.lower().strip(),
            password_hash=hash_password(password),
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        """Authenticate a user by email and password.

        Args:
            email: User's email address.
            password: Plain text password to verify.

        Returns:
            User | None: User instance if credentials valid, None otherwise.
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get a user by their ID.

        Args:
            user_id: UUID of the user to find.

        Returns:
            User | None: User instance if found, None otherwise.
        """
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by their email address.

        Args:
            email: Email address to search for.

        Returns:
            User | None: User instance if found, None otherwise.
        """
        statement = select(User).where(User.email == email.lower().strip())
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
