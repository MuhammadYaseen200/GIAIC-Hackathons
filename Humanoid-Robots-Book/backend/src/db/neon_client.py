"""
Neon Serverless Postgres Database Client
Handles database connections and session management for the Physical AI textbook backend.
"""

# import os
# from typing import AsyncGenerator
# from contextlib import asynccontextmanager
# import asyncpg
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
# from sqlalchemy.orm import declarative_base
# from sqlalchemy.pool import NullPool
# import logging

# logger = logging.getLogger(__name__)

# # SQLAlchemy declarative base
# Base = declarative_base()


# class NeonClient:
#     """
#     Async database client for Neon Serverless Postgres.

#     Uses SQLAlchemy for ORM operations and asyncpg for connection pooling.
#     Optimized for serverless environments with connection pooling disabled (NullPool).
#     """

#     def __init__(self, database_url: str | None = None):
#         """
#         Initialize the Neon database client.

#         Args:
#             database_url: PostgreSQL connection string. If None, reads from DATABASE_URL env var.
#         """
#         self.database_url = database_url or os.getenv("DATABASE_URL")

#         if not self.database_url:
#             raise ValueError(
#                 "DATABASE_URL environment variable not set. "
#                 "Please configure your Neon connection string."
#             )

#         # Convert postgres:// to postgresql+asyncpg:// for SQLAlchemy
#         if self.database_url.startswith("postgres://"):
#             self.database_url = self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
#         elif self.database_url.startswith("postgresql://"):
#             self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

#         # Create async engine with NullPool for serverless (no connection pooling)
#         self.engine = create_async_engine(
#             self.database_url,
#             poolclass=NullPool,  # Disable pooling for serverless
#             echo=False,  # Set to True for SQL query logging
#             future=True,
#         )

#         # Create async session factory
#         self.async_session_maker = async_sessionmaker(
#             self.engine,
#             class_=AsyncSession,
#             expire_on_commit=False,
#             autocommit=False,
#             autoflush=False,
#         )

#         logger.info("NeonClient initialized successfully")

#     @asynccontextmanager
#     async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
#         """
#         Async context manager for database sessions.

#         Usage:
#             async with neon_client.get_session() as session:
#                 result = await session.execute(query)

#         Yields:
#             AsyncSession: SQLAlchemy async session
#         """
#         async with self.async_session_maker() as session:
#             try:
#                 yield session
#                 await session.commit()
#             except Exception as e:
#                 await session.rollback()
#                 logger.error(f"Database session error: {e}")
#                 raise
#             finally:
#                 await session.close()

#     async def execute_raw_sql(self, sql: str, *args) -> list:
#         """
#         Execute raw SQL query directly using asyncpg.

#         Useful for migrations, schema changes, and complex queries.

#         Args:
#             sql: SQL query string
#             *args: Query parameters

#         Returns:
#             List of records (dictionaries)
#         """
#         conn = await asyncpg.connect(
#             self.database_url.replace("postgresql+asyncpg://", "postgresql://")
#         )
#         try:
#             result = await conn.fetch(sql, *args)
#             return [dict(record) for record in result]
#         except Exception as e:
#             logger.error(f"Raw SQL execution error: {e}")
#             raise
#         finally:
#             await conn.close()

#     async def execute_migration(self, migration_file: str) -> None:
#         """
#         Execute a SQL migration file.

#         Args:
#             migration_file: Path to .sql migration file
#         """
#         with open(migration_file, "r") as f:
#             sql = f.read()

#         conn = await asyncpg.connect(
#             self.database_url.replace("postgresql+asyncpg://", "postgresql://")
#         )
#         try:
#             await conn.execute(sql)
#             logger.info(f"Migration {migration_file} executed successfully")
#         except Exception as e:
#             logger.error(f"Migration execution error: {e}")
#             raise
#         finally:
#             await conn.close()

#     async def health_check(self) -> bool:
#         """
#         Check if database connection is healthy.

#         Returns:
#             bool: True if connection is successful
#         """
#         try:
#             conn = await asyncpg.connect(
#                 self.database_url.replace("postgresql+asyncpg://", "postgresql://")
#             )
#             await conn.execute("SELECT 1")
#             await conn.close()
#             logger.info("Database health check passed")
#             return True
#         except Exception as e:
#             logger.error(f"Database health check failed: {e}")
#             return False

#     async def close(self) -> None:
#         """
#         Close database engine and all connections.
#         """
#         await self.engine.dispose()
#         logger.info("NeonClient closed")


# # Global client instance (singleton pattern)
# _neon_client: NeonClient | None = None


# def get_neon_client() -> NeonClient:
#     """
#     Get or create the global NeonClient instance.

#     Returns:
#         NeonClient: Singleton database client
#     """
#     global _neon_client
#     if _neon_client is None:
#         _neon_client = NeonClient()
#     return _neon_client


# async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
#     """
#     Dependency injection function for FastAPI endpoints.

#     Usage:
#         @app.get("/users")
#         async def get_users(session: AsyncSession = Depends(get_db_session)):
#             result = await session.execute(select(User))
#             return result.scalars().all()

#     Yields:
#         AsyncSession: Database session
#     """
#     client = get_neon_client()
#     async with client.get_session() as session:
#         yield session


import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from src.config import settings

logger = logging.getLogger(__name__)

# 1. Setup Database URL (Fixing Postgres Driver for Async)
db_url = settings.database_url
if db_url and db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

# 2. Create Engine
engine = create_async_engine(
    db_url,
    echo=settings.debug,
    future=True
)

# 3. Create Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# --- REQUIRED FUNCTIONS ---

async def get_async_session():
    """Dependency for getting async session (Used by API Routes)"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Alias for compatibility
get_db_session = get_async_session

class NeonClient:
    """
    Wrapper for Database operations.
    """
    def __init__(self):
        self.engine = engine
        self.SessionLocal = AsyncSessionLocal

    # --- RENAMED TO MATCH MAIN.PY ---
    async def health_check(self):
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

# Singleton instance helper
def get_neon_client():
    return NeonClient()