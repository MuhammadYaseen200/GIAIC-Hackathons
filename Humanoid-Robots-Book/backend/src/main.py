"""
FastAPI Backend Entry Point
Main application for Physical AI & Humanoid Robotics textbook backend.
"""

# from contextlib import asynccontextmanager
# from typing import AsyncGenerator
# import logging
# from fastapi import FastAPI, Depends, HTTPException, status, Request
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded
# import uvicorn

# from .config import get_settings, Settings
# from .db.neon_client import get_neon_client, NeonClient
# from .db.qdrant_setup import get_qdrant_manager, QdrantManager
# from .chat.gemini_service import get_gemini_service

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
# )
# logger = logging.getLogger(__name__)


# @asynccontextmanager
# async def lifespan(app: FastAPI) -> AsyncGenerator:
#     """
#     Application lifespan manager for startup and shutdown events.

#     Handles:
#     - Database connection initialization
#     - Qdrant client initialization
#     - Resource cleanup on shutdown
#     """
#     settings = get_settings()
#     logger.info(f"Starting {settings.app_name} in {settings.environment} mode")

#     # Initialize database client
#     try:
#         neon_client = get_neon_client()
#         is_healthy = await neon_client.health_check()
#         if not is_healthy:
#             logger.error("Neon database health check failed!")
#             raise RuntimeError("Database connection failed")
#         logger.info("✓ Neon database connected successfully")
#     except Exception as e:
#         logger.error(f"Failed to initialize Neon client: {e}")
#         raise

#     # Initialize Qdrant client
#     try:
#         qdrant_manager = get_qdrant_manager()
#         is_healthy = await qdrant_manager.health_check()
#         if not is_healthy:
#             logger.error("Qdrant health check failed!")
#             raise RuntimeError("Qdrant connection failed")
#         logger.info("✓ Qdrant vector database connected successfully")
#     except Exception as e:
#         logger.error(f"Failed to initialize Qdrant client: {e}")
#         raise

#     logger.info("Application startup complete")

#     yield  # Application runs here

#     # Shutdown: cleanup resources
#     logger.info("Shutting down application...")
#     try:
#         await neon_client.close()
#         await qdrant_manager.close()
#         logger.info("✓ Resources cleaned up successfully")
#     except Exception as e:
#         logger.error(f"Error during shutdown: {e}")


# # Create FastAPI application
# app = FastAPI(
#     title="Physical AI & Humanoid Robotics API",
#     description="Backend API for interactive textbook with RAG chatbot",
#     version="1.0.0",
#     docs_url="/docs",
#     redoc_url="/redoc",
#     openapi_url="/openapi.json",
#     lifespan=lifespan,
# )

# # Configure rate limiting
# limiter = Limiter(key_func=get_remote_address)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# # Configure CORS
# settings = get_settings()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.allowed_origins,
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
#     allow_headers=["*"],
#     expose_headers=["*"],
# )


# # ============================================================================
# # Health Check Endpoints
# # ============================================================================


# @app.get("/", tags=["Root"])
# async def root():
#     """Root endpoint with API information."""
#     return {
#         "name": settings.app_name,
#         "version": "1.0.0",
#         "status": "operational",
#         "environment": settings.environment,
#         "docs": "/docs",
#     }


# @app.get("/health", tags=["Health"])
# async def health_check():
#     """
#     Comprehensive health check for all services.

#     Checks:
#     - Database connectivity
#     - Qdrant connectivity
#     - Application status
#     """
#     health_status = {
#         "status": "healthy",
#         "services": {},
#     }

#     # Check Neon database
#     try:
#         neon_client = get_neon_client()
#         db_healthy = await neon_client.health_check()
#         health_status["services"]["database"] = "healthy" if db_healthy else "unhealthy"
#     except Exception as e:
#         logger.error(f"Database health check failed: {e}")
#         health_status["services"]["database"] = "unhealthy"
#         health_status["status"] = "degraded"

#     # Check Qdrant
#     try:
#         qdrant_manager = get_qdrant_manager()
#         qdrant_healthy = await qdrant_manager.health_check()
#         health_status["services"]["qdrant"] = "healthy" if qdrant_healthy else "unhealthy"
#     except Exception as e:
#         logger.error(f"Qdrant health check failed: {e}")
#         health_status["services"]["qdrant"] = "unhealthy"
#         health_status["status"] = "degraded"

#     # Check Gemini
#     try:
#         gemini_service = get_gemini_service()
#         gemini_healthy = await gemini_service.health_check()
#         health_status["services"]["gemini"] = "available" if gemini_healthy else "unavailable"
#     except Exception as e:
#         logger.error(f"Gemini health check failed: {e}")
#         health_status["services"]["gemini"] = "unavailable"
#         health_status["status"] = "degraded"

#     # Return 503 if any service is unhealthy
#     status_code = (
#         status.HTTP_200_OK
#         if health_status["status"] == "healthy"
#         else status.HTTP_503_SERVICE_UNAVAILABLE
#     )

#     return JSONResponse(content=health_status, status_code=status_code)


# @app.get("/health/db", tags=["Health"])
# async def health_check_database():
#     """Database-specific health check."""
#     try:
#         neon_client = get_neon_client()
#         is_healthy = await neon_client.health_check()
#         if is_healthy:
#             return {"status": "healthy", "service": "neon_postgres"}
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#                 detail="Database health check failed",
#             )
#     except Exception as e:
#         logger.error(f"Database health check error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail=str(e),
#         )


# @app.get("/health/qdrant", tags=["Health"])
# async def health_check_qdrant():
#     """Qdrant-specific health check."""
#     try:
#         qdrant_manager = get_qdrant_manager()
#         is_healthy = await qdrant_manager.health_check()
#         if is_healthy:
#             stats = qdrant_manager.get_collection_stats()
#             return {
#                 "status": "healthy",
#                 "service": "qdrant_cloud",
#                 "collection_stats": stats,
#             }
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#                 detail="Qdrant health check failed",
#             )
#     except Exception as e:
#         logger.error(f"Qdrant health check error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail=str(e),
#         )


# # ============================================================================
# # API Route Modules
# # ============================================================================

# # Import and include chat router
# from .chat.routes import router as chat_router

# app.include_router(chat_router, tags=["Chat"])

# # Additional routers (to be implemented in future phases)
# # from .auth.routes import router as auth_router
# # from .personalize.routes import router as personalize_router
# # from .translate.routes import router as translate_router
# # app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
# # app.include_router(personalize_router, prefix="/api/personalize", tags=["Personalization"])
# # app.include_router(translate_router, prefix="/api/translate", tags=["Translation"])


# # ============================================================================
# # Error Handlers
# # ============================================================================


# @app.exception_handler(404)
# async def not_found_handler(request, exc):
#     """Handle 404 Not Found errors."""
#     return JSONResponse(
#         status_code=404,
#         content={
#             "error": "Not Found",
#             "message": f"The requested resource '{request.url.path}' was not found",
#         },
#     )


# @app.exception_handler(500)
# async def internal_error_handler(request, exc):
#     """Handle 500 Internal Server errors."""
#     logger.error(f"Internal server error: {exc}")
#     return JSONResponse(
#         status_code=500,
#         content={
#             "error": "Internal Server Error",
#             "message": "An unexpected error occurred. Please try again later.",
#         },
#     )


# # ============================================================================
# # Development Server (for local testing)
# # ============================================================================

# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True,  # Auto-reload on code changes
#         log_config=settings.get_log_config(),
#     )

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.config import settings
from src.db.neon_client import get_neon_client
from src.db.qdrant_setup import get_qdrant_manager
from src.chat.routes import router as chat_router

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")
    
    # Check Database Connection
    neon_client = get_neon_client()
    is_db_healthy = await neon_client.health_check()
    if is_db_healthy:
        logger.info("✓ Neon database connected successfully")
    else:
        logger.error("✗ Neon database connection failed")

    # Check Vector DB Connection
    qdrant_manager = get_qdrant_manager()
    is_qdrant_healthy = await qdrant_manager.health_check()
    if is_qdrant_healthy:
        logger.info("✓ Qdrant connected successfully")
    else:
        logger.error("✗ Qdrant connection failed")

    yield
    
    # --- Shutdown ---
    logger.info("Shutting down application...")

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan
)

# --- CORS (Allow Frontend to Talk to Backend) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTER SETUP (The Fix for 404) ---
# We explicitly add the prefix "/api" so /api/chat works
app.include_router(chat_router, prefix="/api", tags=["Chat"])

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app_name} API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.environment}