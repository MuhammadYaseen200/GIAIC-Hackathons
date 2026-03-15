"""Pydantic v2 models for Facebook/Instagram MCP."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


class FacebookPostInput(BaseModel):
    text: str
    visibility: Literal["EVERYONE", "FRIENDS"] = "EVERYONE"

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Post text cannot be empty")
        if len(v) > 63206:
            raise ValueError(f"Facebook post exceeds 63206 char limit: {len(v)}")
        return v


class InstagramMediaInput(BaseModel):
    caption: str
    image_url: str | None = None

    @field_validator("caption")
    @classmethod
    def caption_limit(cls, v: str) -> str:
        if len(v) > 2200:
            raise ValueError(f"Instagram caption exceeds 2200 char limit: {len(v)}")
        return v


class PostResult(BaseModel):
    success: bool
    post_id: str | None = None
    url: str | None = None
    platform: str = ""
    error: str | None = None


class RecentPost(BaseModel):
    post_id: str
    message: str
    created_time: str
    platform: str


class RecentPostsResult(BaseModel):
    success: bool
    posts: list[RecentPost] = []
    error: str | None = None


class FacebookHealthResult(BaseModel):
    healthy: bool
    page_reachable: bool = False
    token_valid: bool = False
    error: str | None = None
