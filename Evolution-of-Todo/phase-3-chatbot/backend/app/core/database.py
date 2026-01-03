"""Async database session management with SQLModel.

Supports both:
- PostgreSQL via asyncpg (production)
- SQLite via aiosqlite (development fallback)

Provides:
- AsyncEngine for database connections
- Async session factory
- FastAPI dependency for session injection
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings


def _is_sqlite_url(url: str) -> bool:
    """Check if the database URL is for SQLite.

    Args:
        url: Database connection URL.

    Returns:
        True if SQLite URL, False otherwise.
    """
    return url.startswith("sqlite")


def _create_engine_for_url(url: str):
    """Create async engine with appropriate settings for the database type.

    Args:
        url: Database connection URL.

    Returns:
        AsyncEngine configured for the database type.
    """
    if _is_sqlite_url(url):
        # SQLite configuration (development)
        # SQLite does not support pool_size, max_overflow, or pool_pre_ping
        return create_async_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
    else:
        # PostgreSQL configuration (production)
        return create_async_engine(
            url,
            echo=False,  # Set to True for SQL query logging in development
            pool_pre_ping=True,  # Verify connections before use
            pool_size=5,  # Connection pool size
            max_overflow=10,  # Max connections above pool_size
        )


# Create async engine based on DATABASE_URL
async_engine = _create_engine_for_url(settings.DATABASE_URL)

# Async session factory
async_session_factory = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency that provides an async database session.

    Yields:
        AsyncSession: SQLAlchemy async session for database operations.

    Example:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_db_and_tables() -> None:
    """Create all database tables from SQLModel metadata.

    Note: In production, use Alembic migrations instead.
    This is useful for testing or initial development.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_db_and_tables() -> None:
    """Drop all database tables.

    Warning: This is destructive and should only be used in testing.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
