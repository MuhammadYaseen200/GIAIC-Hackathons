"""Pydantic v2 models for Twitter/X MCP."""
from __future__ import annotations

from pydantic import BaseModel, field_validator


class TweetInput(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def tweet_length(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Tweet text cannot be empty")
        if len(v) > 280:
            raise ValueError(f"Tweet exceeds 280 char limit: {len(v)}")
        return v


class TweetResult(BaseModel):
    success: bool
    tweet_id: str | None = None
    url: str | None = None
    error: str | None = None
    rate_limited: bool = False


class RecentTweet(BaseModel):
    tweet_id: str
    text: str
    created_at: str


class RecentTweetsResult(BaseModel):
    success: bool
    tweets: list[RecentTweet] = []
    error: str | None = None


class TwitterHealthResult(BaseModel):
    healthy: bool
    token_valid: bool = False
    api_reachable: bool = False
    error: str | None = None
