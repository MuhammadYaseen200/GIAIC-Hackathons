"""Pydantic v2 models for LinkedIn MCP server."""
import time
from typing import Literal, Optional

from pydantic import BaseModel, Field


class PostUpdateInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000, description="Post text content")
    visibility: Literal["PUBLIC", "CONNECTIONS"] = Field("PUBLIC", description="Post visibility")


class PostUpdateResult(BaseModel):
    success: bool
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


class ProfileResult(BaseModel):
    success: bool
    person_urn: Optional[str] = None
    display_name: Optional[str] = None
    error: Optional[str] = None


class HealthCheckResult(BaseModel):
    healthy: bool
    token_valid: bool
    token_expires_in_seconds: Optional[int] = None
    api_reachable: bool
    error: Optional[str] = None


class LinkedInCredentials(BaseModel):
    """Stored in linkedin_token.json."""

    access_token: str
    refresh_token: Optional[str] = None
    expires_at: float = Field(default_factory=lambda: time.time() + 3600)
    person_urn: Optional[str] = None
    token_type: str = "Bearer"
