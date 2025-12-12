"""
Environment Configuration Management
Centralized configuration using Pydantic Settings for type safety and validation.
"""

import os
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings are type-validated and can have default values.
    Reads from .env file automatically if present.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================================================
    # Application Settings
    # ============================================================================
    app_name: str = Field(
        default="Physical AI & Humanoid Robotics API",
        description="Application name",
    )
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production",
        alias="NODE_ENV",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    # ============================================================================
    # Server Configuration
    # ============================================================================
    backend_url: str = Field(
        default="http://localhost:8000",
        description="Backend API URL",
    )
    allowed_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated CORS allowed origins",
    )

    @field_validator("allowed_origins")
    @classmethod
    def parse_allowed_origins(cls, v: str) -> List[str]:
        """Parse comma-separated origins into list."""
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    # ============================================================================
    # Database Configuration (Neon Serverless Postgres)
    # ============================================================================
    database_url: str = Field(
        ...,
        description="PostgreSQL connection string for Neon",
        min_length=10,
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses SSL mode for Neon."""
        if "neon.tech" in v and "sslmode" not in v:
            logger.warning("Adding sslmode=require to Neon database URL")
            separator = "&" if "?" in v else "?"
            return f"{v}{separator}sslmode=require"
        return v

    # ============================================================================
    # Vector Database Configuration (Qdrant Cloud)
    # ============================================================================
    qdrant_url: str = Field(
        ...,
        description="Qdrant Cloud cluster URL",
        pattern=r"^https://.+\.qdrant\.io$",
    )
    qdrant_api_key: str = Field(
        ...,
        description="Qdrant API key",
        min_length=20,
    )

    # ============================================================================
    # OpenAI Configuration
    # ============================================================================
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key for embeddings and chat",
        pattern=r"^sk-[a-zA-Z0-9]{48,}$",
    )
    openai_model: str = Field(
        default="gpt-4-turbo-preview",
        description="OpenAI chat model",
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model (1536 dimensions)",
    )
    openai_max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for OpenAI API",
        ge=1,
        le=10,
    )
    openai_timeout_seconds: int = Field(
        default=30,
        description="OpenAI API timeout in seconds",
        ge=10,
        le=120,
    )

    # ============================================================================
    # Authentication Configuration
    # ============================================================================
    auth_secret: str = Field(
        ...,
        description="Secret key for JWT token signing",
        min_length=32,
    )
    auth_url: str = Field(
        default="http://localhost:3000",
        description="Frontend URL for authentication redirects",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    jwt_expiration_minutes: int = Field(
        default=10080,  # 7 days
        description="JWT token expiration time in minutes",
        ge=60,
        le=43200,  # Max 30 days
    )

    # ============================================================================
    # RAG Configuration
    # ============================================================================
    rag_chunk_size: int = Field(
        default=512,
        description="Text chunk size in tokens for RAG",
        ge=128,
        le=2048,
    )
    rag_chunk_overlap: int = Field(
        default=50,
        description="Overlap between chunks in tokens",
        ge=0,
        le=512,
    )
    rag_top_k: int = Field(
        default=5,
        description="Number of top chunks to retrieve",
        ge=1,
        le=20,
    )
    rag_score_threshold: float = Field(
        default=0.7,
        description="Minimum similarity score for retrieval",
        ge=0.0,
        le=1.0,
    )

    # ============================================================================
    # Caching Configuration
    # ============================================================================
    cache_ttl_seconds: int = Field(
        default=3600,
        description="Cache TTL in seconds (1 hour default)",
        ge=60,
        le=86400,
    )

    # ============================================================================
    # Rate Limiting Configuration
    # ============================================================================
    rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum API requests per minute per user",
        ge=10,
        le=1000,
    )

    # ============================================================================
    # Logging Configuration
    # ============================================================================
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure valid log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            logger.warning(f"Invalid log level '{v}', defaulting to INFO")
            return "INFO"
        return v_upper

    # ============================================================================
    # Feature Flags
    # ============================================================================
    enable_personalization: bool = Field(
        default=True,
        description="Enable user personalization features",
    )
    enable_translation: bool = Field(
        default=True,
        description="Enable Urdu translation features",
    )
    enable_analytics: bool = Field(
        default=True,
        description="Enable user activity analytics",
    )

    def get_log_config(self) -> dict:
        """
        Get logging configuration dictionary.

        Returns:
            dict: Logging config for uvicorn/FastAPI
        """
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": self.log_level,
                "handlers": ["console"],
            },
        }


# Global settings instance (singleton pattern)
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get or create the global Settings instance.

    Returns:
        Settings: Application configuration
    """
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
            logger.info("Settings loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            raise
    return _settings


# Convenience function for dependency injection
def get_config() -> Settings:
    """
    FastAPI dependency for injecting settings.

    Usage:
        @app.get("/config")
        def get_config_endpoint(config: Settings = Depends(get_config)):
            return {"environment": config.environment}
    """
    return get_settings()
