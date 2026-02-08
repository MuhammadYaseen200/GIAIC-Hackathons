"""FastAPI application entry point.

Main application module that:
- Creates the FastAPI app instance
- Configures CORS middleware from settings
- Includes the v1 API router
- Provides health check endpoint

Note: Database tables are managed via Alembic migrations, not auto-created on startup.
This ensures serverless compatibility (Vercel, AWS Lambda, etc).

Windows Note: psycopg3 requires SelectorEventLoop.
Start via: uv run python run_server.py
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import create_db_and_tables
from app.core.rate_limit import limiter

# Import models to register them with SQLModel metadata
from app.models import Task, User  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Creates database tables on startup (for development with SQLite).
    Production should use Alembic migrations.
    """
    await create_db_and_tables()
    yield


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
# Methods and headers are explicitly whitelisted to reduce CSRF attack surface.
# Only REST methods used by the frontend and essential headers are permitted.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
)

# ---------------------------------------------------------------------------
# Rate Limiting Configuration
# Prevents API abuse and OpenRouter cost exposure.
# Default: 30 requests/minute per client IP address.
# Uses slowapi (built on top of limits library).
# Limiter instance is defined in app.core.rate_limit to avoid circular imports.
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# Global Exception Handler: Project-wide error response format
# AC-008 criterion 2: {"success": false, "error": {"code": "...", "message": "..."}}
#
# Transforms FastAPI's default HTTPException format from:
#   {"detail": {"code": "...", "message": "..."}}
# To the project-standard format:
#   {"success": false, "error": {"code": "...", "message": "..."}}
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Transform HTTPException responses to project-wide error format.

    Handles two cases:
    1. Structured detail (dict with "code" key) - pass through as error object
    2. Unstructured detail (string) - wrap in standard error format

    Args:
        request: The incoming HTTP request.
        exc: The HTTPException raised by endpoint code.

    Returns:
        JSONResponse with {"success": false, "error": {"code": ..., "message": ...}}
    """
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        # Structured error from our endpoints (e.g., SESSION_LIMIT, FORBIDDEN)
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": exc.detail},
        )
    # Fallback for unstructured errors (e.g., FastAPI's default 401/422)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "ERROR",
                "message": str(exc.detail),
            },
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all handler for unhandled exceptions.

    Prevents stack traces from leaking to clients. Logs the full
    traceback server-side for debugging.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred.",
            },
        },
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
