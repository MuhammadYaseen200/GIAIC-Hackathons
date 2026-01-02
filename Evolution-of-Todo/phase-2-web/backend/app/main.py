"""FastAPI application entry point.

Main application module that:
- Creates the FastAPI app instance
- Configures CORS middleware from settings
- Includes the v1 API router
- Provides health check endpoint

Note: Database tables are managed via Alembic migrations, not auto-created on startup.
This ensures serverless compatibility (Vercel, AWS Lambda, etc).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

# Import models to register them with SQLModel metadata
from app.models import Task, User  # noqa: F401


app = FastAPI(
    title="Todo Backend",
    description="FastAPI backend for Evolution of Todo - Phase 2",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
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
