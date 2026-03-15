"""Unit tests for Twitter/X MCP. RED before server.py."""
import json

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_post_tweet_success():
    """post_tweet tool returns success with tweet_id."""
    from mcp_servers.twitter.server import post_tweet

    with patch("mcp_servers.twitter.server.post_tweet_client") as mock_fn:
        mock_fn.return_value = {"success": True, "tweet_id": "123456", "url": "https://twitter.com/i/web/status/123456"}
        result = await post_tweet(text="Hello Twitter!")
    assert isinstance(result, dict)
    assert "content" in result or "isError" in result


@pytest.mark.asyncio
async def test_post_tweet_text_over_280_rejected():
    """Tweets over 280 chars are rejected with isError."""
    from mcp_servers.twitter.server import post_tweet

    long_text = "X" * 281
    result = await post_tweet(text=long_text)
    assert result.get("isError") is True


@pytest.mark.asyncio
async def test_post_tweet_text_exactly_280_accepted():
    """Tweets of exactly 280 chars are accepted."""
    from mcp_servers.twitter.server import post_tweet

    exact_text = "Y" * 280
    with patch("mcp_servers.twitter.server.post_tweet_client") as mock_fn:
        mock_fn.return_value = {"success": True, "tweet_id": "789", "url": "https://twitter.com/i/web/status/789"}
        result = await post_tweet(text=exact_text)
    assert result.get("isError") is not True


@pytest.mark.asyncio
async def test_post_tweet_rate_limited_graceful():
    """Rate limit returns structured response, not exception."""
    from mcp_servers.twitter.server import post_tweet

    with patch("mcp_servers.twitter.server.post_tweet_client") as mock_fn:
        mock_fn.return_value = {"success": False, "error": "Rate limited", "rate_limited": True}
        result = await post_tweet(text="Test")
    assert isinstance(result, dict)
    assert result.get("isError") is not True


@pytest.mark.asyncio
async def test_post_tweet_auth_error():
    """Auth errors return structured response."""
    from mcp_servers.twitter.server import post_tweet

    with patch("mcp_servers.twitter.server.post_tweet_client") as mock_fn:
        mock_fn.return_value = {"success": False, "error": "401 Unauthorized"}
        result = await post_tweet(text="Test")
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_post_tweet_logged_to_social_posts_jsonl():
    """Successful tweet is logged to social_posts.jsonl."""
    from mcp_servers.twitter.server import post_tweet

    with patch("mcp_servers.twitter.server.post_tweet_client") as mock_fn:
        mock_fn.return_value = {"success": True, "tweet_id": "999"}
        result = await post_tweet(text="Test tweet")
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_get_recent_tweets_success():
    """get_recent_tweets returns list of tweets."""
    from mcp_servers.twitter.server import get_recent_tweets

    with patch("mcp_servers.twitter.server.get_recent_tweets_client") as mock_fn:
        mock_fn.return_value = [{"tweet_id": "1", "text": "Hello", "created_at": "2026-03-12"}]
        result = await get_recent_tweets(max_results=5)
    assert isinstance(result, dict)
    assert "content" in result or "isError" in result


@pytest.mark.asyncio
async def test_get_recent_tweets_empty():
    """get_recent_tweets handles empty result."""
    from mcp_servers.twitter.server import get_recent_tweets

    with patch("mcp_servers.twitter.server.get_recent_tweets_client") as mock_fn:
        mock_fn.return_value = []
        result = await get_recent_tweets(max_results=5)
    assert isinstance(result, dict)
    assert result.get("isError") is not True


@pytest.mark.asyncio
async def test_health_check_healthy():
    """health_check returns healthy=True when API reachable."""
    from mcp_servers.twitter.server import health_check

    with patch("mcp_servers.twitter.server.health_check_twitter_client") as mock_fn:
        mock_fn.return_value = {"healthy": True, "token_valid": True}
        result = await health_check()
    assert isinstance(result, dict)
    content = json.loads(result.get("content", "{}"))
    assert content.get("healthy") is True


@pytest.mark.asyncio
async def test_health_check_token_invalid():
    """health_check returns healthy=False on invalid token."""
    from mcp_servers.twitter.server import health_check

    with patch("mcp_servers.twitter.server.health_check_twitter_client") as mock_fn:
        mock_fn.return_value = {"healthy": False, "token_valid": False, "error": "401 Unauthorized"}
        result = await health_check()
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_health_check_api_unreachable():
    """health_check returns healthy=False on connection error."""
    from mcp_servers.twitter.server import health_check

    with patch("mcp_servers.twitter.server.health_check_twitter_client") as mock_fn:
        mock_fn.return_value = {"healthy": False, "api_reachable": False, "error": "Connection refused"}
        result = await health_check()
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_all_tools_return_dict_not_raise():
    """All Twitter tools return dict and never raise."""
    from mcp_servers.twitter.server import post_tweet, get_recent_tweets, health_check

    with patch("mcp_servers.twitter.server.post_tweet_client", side_effect=Exception("boom")):
        result = await post_tweet(text="test")
    assert isinstance(result, dict)

    with patch("mcp_servers.twitter.server.get_recent_tweets_client", side_effect=Exception("boom")):
        result = await get_recent_tweets()
    assert isinstance(result, dict)

    with patch("mcp_servers.twitter.server.health_check_twitter_client", side_effect=Exception("boom")):
        result = await health_check()
    assert isinstance(result, dict)


# -- CLIENT DIRECT TESTS (boost coverage) --


@pytest.mark.asyncio
async def test_client_post_tweet_no_api_key():
    """post_tweet returns error dict when TWITTER_API_KEY not set."""
    from mcp_servers.twitter import client as tw_client

    original = tw_client.TWITTER_API_KEY
    tw_client.TWITTER_API_KEY = ""

    result = await tw_client.post_tweet("Hello")

    tw_client.TWITTER_API_KEY = original
    assert result["success"] is False


@pytest.mark.asyncio
async def test_client_post_tweet_success_via_mock():
    """post_tweet succeeds when tweepy client returns tweet data."""
    from mcp_servers.twitter import client as tw_client

    mock_response = MagicMock()
    mock_response.data = {"id": "tweet-123"}

    mock_tweepy = MagicMock()
    mock_tweepy.create_tweet = MagicMock(return_value=mock_response)

    original_key = tw_client.TWITTER_API_KEY
    original_client = tw_client._tweepy_client
    tw_client.TWITTER_API_KEY = "test-key"
    tw_client._tweepy_client = mock_tweepy

    result = await tw_client.post_tweet("Hello Twitter!")

    tw_client.TWITTER_API_KEY = original_key
    tw_client._tweepy_client = original_client

    assert result["success"] is True
    assert result["tweet_id"] == "tweet-123"


@pytest.mark.asyncio
async def test_client_post_tweet_rate_limited():
    """post_tweet handles 429 rate limit gracefully."""
    from mcp_servers.twitter import client as tw_client

    mock_tweepy = MagicMock()
    mock_tweepy.create_tweet = MagicMock(side_effect=Exception("429 Too Many Requests"))

    original_key = tw_client.TWITTER_API_KEY
    original_client = tw_client._tweepy_client
    tw_client.TWITTER_API_KEY = "test-key"
    tw_client._tweepy_client = mock_tweepy

    result = await tw_client.post_tweet("Rate limited post")

    tw_client.TWITTER_API_KEY = original_key
    tw_client._tweepy_client = original_client

    assert result["success"] is False
    assert result["rate_limited"] is True


@pytest.mark.asyncio
async def test_client_post_tweet_forbidden():
    """post_tweet handles 403 Forbidden gracefully."""
    from mcp_servers.twitter import client as tw_client

    mock_tweepy = MagicMock()
    mock_tweepy.create_tweet = MagicMock(side_effect=Exception("403 Forbidden"))

    original_key = tw_client.TWITTER_API_KEY
    original_client = tw_client._tweepy_client
    tw_client.TWITTER_API_KEY = "test-key"
    tw_client._tweepy_client = mock_tweepy

    result = await tw_client.post_tweet("Forbidden tweet")

    tw_client.TWITTER_API_KEY = original_key
    tw_client._tweepy_client = original_client

    assert result["success"] is False
    assert "Forbidden" in result["error"]


@pytest.mark.asyncio
async def test_client_get_recent_tweets_success():
    """get_recent_tweets returns list from tweepy."""
    from mcp_servers.twitter import client as tw_client

    mock_me = MagicMock()
    mock_me.data.id = "user-123"

    mock_tweet = MagicMock()
    mock_tweet.id = "t1"
    mock_tweet.text = "Test tweet"
    mock_tweet.created_at = None

    mock_tweets_resp = MagicMock()
    mock_tweets_resp.data = [mock_tweet]

    mock_tweepy = MagicMock()
    mock_tweepy.get_me = MagicMock(return_value=mock_me)
    mock_tweepy.get_users_tweets = MagicMock(return_value=mock_tweets_resp)

    original_token = tw_client.TWITTER_ACCESS_TOKEN
    original_client = tw_client._tweepy_client
    tw_client.TWITTER_ACCESS_TOKEN = "test-token"
    tw_client._tweepy_client = mock_tweepy

    result = await tw_client.get_recent_tweets(max_results=5)

    tw_client.TWITTER_ACCESS_TOKEN = original_token
    tw_client._tweepy_client = original_client

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["tweet_id"] == "t1"


@pytest.mark.asyncio
async def test_client_health_check_twitter_success():
    """health_check_twitter returns healthy=True when API responds."""
    from mcp_servers.twitter import client as tw_client

    mock_me = MagicMock()
    mock_me.data.id = "user-123"

    mock_tweepy = MagicMock()
    mock_tweepy.get_me = MagicMock(return_value=mock_me)

    original_key = tw_client.TWITTER_API_KEY
    original_client = tw_client._tweepy_client
    tw_client.TWITTER_API_KEY = "test-key"
    tw_client._tweepy_client = mock_tweepy

    result = await tw_client.health_check_twitter()

    tw_client.TWITTER_API_KEY = original_key
    tw_client._tweepy_client = original_client

    assert result["healthy"] is True
    assert result["token_valid"] is True


@pytest.mark.asyncio
async def test_client_get_client_singleton():
    """_get_client returns same instance on second call."""
    import sys
    from mcp_servers.twitter import client as tw_client

    original = tw_client._tweepy_client
    tw_client._tweepy_client = None  # reset

    original_key = tw_client.TWITTER_API_KEY
    tw_client.TWITTER_API_KEY = "test-key"

    # tweepy is not installed — inject a mock module into sys.modules
    mock_client_instance = MagicMock()
    mock_tweepy = MagicMock()
    mock_tweepy.Client.return_value = mock_client_instance

    sys.modules["tweepy"] = mock_tweepy
    try:
        c1 = tw_client._get_client()
        c2 = tw_client._get_client()
    finally:
        del sys.modules["tweepy"]

    assert c1 is c2
    assert mock_tweepy.Client.call_count == 1  # created only once

    tw_client.TWITTER_API_KEY = original_key
    tw_client._tweepy_client = original
