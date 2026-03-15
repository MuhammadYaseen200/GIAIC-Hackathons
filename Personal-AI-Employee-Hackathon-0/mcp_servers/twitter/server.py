"""Twitter/X MCP Server -- FastMCP tools."""
from __future__ import annotations

import json
import logging

from mcp.server.fastmcp import FastMCP

from mcp_servers.twitter.client import (
    post_tweet as post_tweet_client,
    get_recent_tweets as get_recent_tweets_client,
    health_check_twitter as health_check_twitter_client,
)
from mcp_servers.twitter.models import TweetInput, TweetResult, RecentTweetsResult, TwitterHealthResult

logger = logging.getLogger(__name__)
mcp = FastMCP("twitter")


def _error(msg: str) -> dict:
    return {"isError": True, "content": json.dumps({"error": msg})}


@mcp.tool()
async def post_tweet(text: str) -> dict:
    """Post a tweet to Twitter/X.

    Args:
        text: Tweet content (<=280 chars)
    """
    try:
        try:
            TweetInput(text=text)
        except Exception as e:
            return _error(f"Validation error: {e}")
        result = await post_tweet_client(text)
        return {"content": json.dumps(result)}
    except Exception as e:
        logger.error(f"post_tweet error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


@mcp.tool()
async def get_recent_tweets(max_results: int = 10) -> dict:
    """Get recent tweets from the authenticated account.

    Args:
        max_results: Number of tweets to return (max: 100)
    """
    try:
        tweets = await get_recent_tweets_client(max_results)
        result = RecentTweetsResult(success=True, tweets=tweets)  # type: ignore
        return {"content": json.dumps(result.model_dump())}
    except Exception as e:
        logger.error(f"get_recent_tweets error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


@mcp.tool()
async def health_check() -> dict:
    """Check Twitter/X MCP connectivity and token validity."""
    try:
        result = await health_check_twitter_client()
        return {"content": json.dumps(result)}
    except Exception as e:
        logger.error(f"health_check error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


if __name__ == "__main__":
    mcp.run()
