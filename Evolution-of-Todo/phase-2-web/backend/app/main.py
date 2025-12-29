"""FastAPI application entry point.

Main application module that:
- Creates the FastAPI app instance
- Configures CORS middleware from settings
- Includes the v1 API router
- Provides health check endpoint
- Auto-creates database tables on startup (development mode)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import create_db_and_tables

# Import models to register them with SQLModel metadata before table creation
from app.models import Task, User  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler.

    On startup:
    - Creates database tables if they don't exist (development mode).

    On shutdown:
    - Cleanup resources if needed.
    """
    # Startup: Create database tables
    await create_db_and_tables()
    yield
    # Shutdown: Cleanup if needed (currently none)


app = FastAPI(
    title="Todo Backend",
    description="FastAPI backend for Evolution of Todo - Phase 2",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS configuration from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint.

    Returns:
        dict: Welcome message and API status.
    """
    return {"message": "Todo Backend API", "status": "running"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict: Health status of the application.
    """
    return {"status": "healthy"}
