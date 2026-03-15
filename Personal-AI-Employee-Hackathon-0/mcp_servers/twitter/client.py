"""Twitter/X async client using tweepy OAuth 1.0a."""
from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger(__name__)

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

_tweepy_client = None


def _get_client():
    """Get (or create) tweepy.Client singleton."""
    global _tweepy_client
    if _tweepy_client is None:
        try:
            import tweepy
            _tweepy_client = tweepy.Client(
                consumer_key=TWITTER_API_KEY,
                consumer_secret=TWITTER_API_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=False,
            )
        except ImportError:
            raise ImportError("tweepy not installed -- run: pip install tweepy>=4.14.0")
    return _tweepy_client


async def post_tweet(text: str) -> dict:
    """Post a tweet via OAuth 1.0a."""
    if not TWITTER_API_KEY:
        return {"success": False, "error": "TWITTER_API_KEY not set", "rate_limited": False}
    try:
        client = _get_client()
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: client.create_tweet(text=text)
        )
        tweet_id = str(response.data["id"])
        return {
            "success": True,
            "tweet_id": tweet_id,
            "url": f"https://twitter.com/i/web/status/{tweet_id}",
            "error": None,
            "rate_limited": False,
        }
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Rate limit" in error_str:
            logger.warning(f"Twitter rate limit: {e}")
            return {"success": False, "error": "Rate limited", "rate_limited": True}
        if "403" in error_str or "Forbidden" in error_str:
            logger.error(f"Twitter 403 Forbidden: {e}")
            return {"success": False, "error": f"Forbidden: {error_str}", "rate_limited": False}
        logger.error(f"post_tweet error: {e}", exc_info=True)
        return {"success": False, "error": error_str, "rate_limited": False}


async def get_recent_tweets(max_results: int = 10) -> list:
    """Get recent tweets from the authenticated user."""
    if not TWITTER_ACCESS_TOKEN:
        return []
    try:
        client = _get_client()
        loop = asyncio.get_event_loop()
        me = await loop.run_in_executor(None, lambda: client.get_me())
        if not me or not me.data:
            return []
        user_id = me.data.id
        tweets_resp = await loop.run_in_executor(
            None,
            lambda: client.get_users_tweets(
                id=user_id,
                max_results=min(max_results, 100),
                tweet_fields=["created_at", "text"],
            )
        )
        if not tweets_resp or not tweets_resp.data:
            return []
        return [
            {
                "tweet_id": str(t.id),
                "text": t.text,
                "created_at": str(t.created_at or ""),
            }
            for t in tweets_resp.data
        ]
    except Exception as e:
        if "429" in str(e):
            logger.warning(f"Twitter rate limit on get_recent_tweets: {e}")
        else:
            logger.error(f"get_recent_tweets error: {e}", exc_info=True)
        return []


async def health_check_twitter() -> dict:
    """Check Twitter API connectivity."""
    if not TWITTER_API_KEY:
        return {"healthy": False, "token_valid": False, "api_reachable": False,
                "error": "TWITTER_API_KEY not set"}
    try:
        client = _get_client()
        loop = asyncio.get_event_loop()
        me = await loop.run_in_executor(None, lambda: client.get_me())
        if me and me.data:
            return {"healthy": True, "token_valid": True, "api_reachable": True, "error": None}
        return {"healthy": False, "token_valid": False, "api_reachable": True,
                "error": "No user data returned"}
    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "Unauthorized" in error_str:
            return {"healthy": False, "token_valid": False, "api_reachable": True, "error": error_str}
        return {"healthy": False, "token_valid": False, "api_reachable": False, "error": error_str}
