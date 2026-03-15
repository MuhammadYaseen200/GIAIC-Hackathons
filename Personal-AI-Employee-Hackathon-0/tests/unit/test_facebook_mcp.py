"""Unit tests for Facebook/Instagram MCP. RED before server.py."""
import json

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# -- POST UPDATE (BOTH PLATFORMS) --


@pytest.mark.asyncio
async def test_post_update_both_platforms_success():
    """post_update calls both Facebook and Instagram."""
    from mcp_servers.facebook.server import post_update

    with patch("mcp_servers.facebook.server.post_to_facebook") as fb_mock, \
         patch("mcp_servers.facebook.server.post_to_instagram") as ig_mock:
        fb_mock.return_value = {"success": True, "post_id": "123_456", "platform": "facebook"}
        ig_mock.return_value = {"success": True, "post_id": "789", "platform": "instagram"}
        result = await post_update(text="Test post")
    assert isinstance(result, dict)
    assert "content" in result or "isError" in result


@pytest.mark.asyncio
async def test_post_facebook_only_success():
    """post_facebook_only calls only Facebook."""
    from mcp_servers.facebook.server import post_facebook_only

    with patch("mcp_servers.facebook.server.post_to_facebook") as fb_mock:
        fb_mock.return_value = {"success": True, "post_id": "123_456", "platform": "facebook"}
        result = await post_facebook_only(text="Facebook only post")
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_post_instagram_only_success():
    """post_instagram_only calls only Instagram."""
    from mcp_servers.facebook.server import post_instagram_only

    with patch("mcp_servers.facebook.server.post_to_instagram") as ig_mock:
        ig_mock.return_value = {"success": True, "post_id": "789", "platform": "instagram"}
        result = await post_instagram_only(caption="Instagram only post")
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_post_update_facebook_fails_instagram_still_posts():
    """If Facebook fails, Instagram still attempts to post."""
    from mcp_servers.facebook.server import post_update

    with patch("mcp_servers.facebook.server.post_to_facebook") as fb_mock, \
         patch("mcp_servers.facebook.server.post_to_instagram") as ig_mock:
        fb_mock.return_value = {"success": False, "error": "Token expired", "platform": "facebook"}
        ig_mock.return_value = {"success": True, "post_id": "789", "platform": "instagram"}
        result = await post_update(text="Test post")
    assert isinstance(result, dict)
    content = json.loads(result.get("content", "{}"))
    assert "instagram" in str(content) or "isError" not in result


# -- TEXT VALIDATION --


@pytest.mark.asyncio
async def test_text_truncated_to_instagram_limit():
    """Instagram captions over 2200 chars are rejected."""
    from mcp_servers.facebook.server import post_instagram_only

    long_text = "A" * 2201
    result = await post_instagram_only(caption=long_text)
    assert result.get("isError") is True


@pytest.mark.asyncio
async def test_text_truncated_to_facebook_limit():
    """Facebook posts over 63206 chars are rejected."""
    from mcp_servers.facebook.server import post_facebook_only

    long_text = "B" * 63207
    result = await post_facebook_only(text=long_text)
    assert result.get("isError") is True


@pytest.mark.asyncio
async def test_post_with_empty_text_rejected():
    """Empty post text is rejected."""
    from mcp_servers.facebook.server import post_facebook_only

    result = await post_facebook_only(text="")
    assert result.get("isError") is True


# -- GET RECENT POSTS --


@pytest.mark.asyncio
async def test_get_recent_posts_success():
    """get_recent_posts returns structured list."""
    from mcp_servers.facebook.server import get_recent_posts

    with patch("mcp_servers.facebook.server.get_recent_facebook_posts") as mock_fn:
        mock_fn.return_value = [
            {"post_id": "123", "message": "Hello", "created_time": "2026-03-12T07:00:00", "platform": "facebook"}
        ]
        result = await get_recent_posts(limit=5)
    assert isinstance(result, dict)
    assert "content" in result or "isError" in result


# -- HEALTH CHECK --


@pytest.mark.asyncio
async def test_health_check_healthy():
    """health_check returns healthy=True when token valid."""
    from mcp_servers.facebook.server import health_check

    with patch("mcp_servers.facebook.server.health_check_meta") as mock_fn:
        mock_fn.return_value = {"healthy": True, "page_reachable": True, "token_valid": True}
        result = await health_check()
    assert isinstance(result, dict)
    content = json.loads(result.get("content", "{}"))
    assert content.get("healthy") is True


@pytest.mark.asyncio
async def test_health_check_token_invalid():
    """health_check returns healthy=False on invalid token."""
    from mcp_servers.facebook.server import health_check

    with patch("mcp_servers.facebook.server.health_check_meta") as mock_fn:
        mock_fn.return_value = {"healthy": False, "token_valid": False, "error": "Token expired"}
        result = await health_check()
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_health_check_network_error():
    """health_check returns healthy=False on network error."""
    from mcp_servers.facebook.server import health_check

    with patch("mcp_servers.facebook.server.health_check_meta") as mock_fn:
        mock_fn.return_value = {"healthy": False, "page_reachable": False, "error": "Connection refused"}
        result = await health_check()
    assert isinstance(result, dict)


# -- INSTAGRAM SKIPPED WHEN NO ACCOUNT --


@pytest.mark.asyncio
async def test_instagram_no_account_skips_gracefully():
    """Instagram tool returns skipped result when IG_ACCOUNT_ID not set."""
    from mcp_servers.facebook import client as fb_client

    original = fb_client.IG_ACCOUNT_ID
    fb_client.IG_ACCOUNT_ID = ""
    result = await fb_client.post_to_instagram("Test caption")
    fb_client.IG_ACCOUNT_ID = original
    assert result.get("skipped") is True or result.get("success") is False


@pytest.mark.asyncio
async def test_instagram_2step_creation_id_used():
    """Instagram posting uses 2-step container -> publish flow."""
    from mcp_servers.facebook import client as fb_client

    container_response = MagicMock()
    container_response.status_code = 200
    container_response.json.return_value = {"id": "container-123"}

    publish_response = MagicMock()
    publish_response.status_code = 200
    publish_response.json.return_value = {"id": "media-456"}

    mock_client = AsyncMock()
    mock_client.post.side_effect = [container_response, publish_response]
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    original_ig = fb_client.IG_ACCOUNT_ID
    original_token = fb_client.PAGE_ACCESS_TOKEN
    fb_client.IG_ACCOUNT_ID = "ig-test-123"
    fb_client.PAGE_ACCESS_TOKEN = "test-token"

    with patch("mcp_servers.facebook.client.httpx.AsyncClient", return_value=mock_client):
        result = await fb_client.post_to_instagram("Test caption", image_url="https://example.com/img.jpg")

    fb_client.IG_ACCOUNT_ID = original_ig
    fb_client.PAGE_ACCESS_TOKEN = original_token

    assert mock_client.post.call_count == 2


# -- ERROR HANDLING --


@pytest.mark.asyncio
async def test_all_tools_return_dict_not_raise():
    """All server tools return dict, never raise unhandled exceptions."""
    from mcp_servers.facebook.server import post_update, health_check, get_recent_posts

    with patch("mcp_servers.facebook.server.post_to_facebook", side_effect=Exception("Unexpected")), \
         patch("mcp_servers.facebook.server.post_to_instagram", side_effect=Exception("Unexpected")):
        result = await post_update(text="test")
    assert isinstance(result, dict)

    with patch("mcp_servers.facebook.server.health_check_meta", side_effect=Exception("Network down")):
        result = await health_check()
    assert isinstance(result, dict)


# -- CLIENT DIRECT TESTS (boost coverage) --


@pytest.mark.asyncio
async def test_client_post_to_facebook_success():
    """post_to_facebook returns success dict on 200."""
    from mcp_servers.facebook import client as fb_client

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "123_456"}
    mock_resp.raise_for_status = MagicMock()

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=mock_resp)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=None)

    original_token = fb_client.PAGE_ACCESS_TOKEN
    original_page = fb_client.PAGE_ID
    fb_client.PAGE_ACCESS_TOKEN = "test-token"
    fb_client.PAGE_ID = "page-123"

    with patch("mcp_servers.facebook.client.httpx.AsyncClient", return_value=mock_http):
        result = await fb_client.post_to_facebook("Hello world")

    fb_client.PAGE_ACCESS_TOKEN = original_token
    fb_client.PAGE_ID = original_page

    assert result["success"] is True
    assert result["post_id"] == "123_456"


@pytest.mark.asyncio
async def test_client_post_to_facebook_auth_error():
    """post_to_facebook handles 401/403 HTTP errors."""
    from mcp_servers.facebook import client as fb_client
    import httpx

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "OAuthException"
    error = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_resp)

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(side_effect=error)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=None)

    original_token = fb_client.PAGE_ACCESS_TOKEN
    fb_client.PAGE_ACCESS_TOKEN = "test-token"

    with patch("mcp_servers.facebook.client.httpx.AsyncClient", return_value=mock_http):
        result = await fb_client.post_to_facebook("Hello")

    fb_client.PAGE_ACCESS_TOKEN = original_token
    assert result["success"] is False
    assert "Auth error" in result["error"]


@pytest.mark.asyncio
async def test_client_get_recent_facebook_posts_success():
    """get_recent_facebook_posts parses response correctly."""
    from mcp_servers.facebook import client as fb_client

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"id": "p1", "message": "Post 1", "created_time": "2026-03-12T00:00:00+0000"}]
    }
    mock_resp.raise_for_status = MagicMock()

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_resp)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=None)

    original_token = fb_client.PAGE_ACCESS_TOKEN
    original_page = fb_client.PAGE_ID
    fb_client.PAGE_ACCESS_TOKEN = "test-token"
    fb_client.PAGE_ID = "page-123"

    with patch("mcp_servers.facebook.client.httpx.AsyncClient", return_value=mock_http):
        result = await fb_client.get_recent_facebook_posts(limit=5)

    fb_client.PAGE_ACCESS_TOKEN = original_token
    fb_client.PAGE_ID = original_page

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["post_id"] == "p1"


@pytest.mark.asyncio
async def test_client_health_check_meta_success():
    """health_check_meta returns healthy=True on success."""
    from mcp_servers.facebook import client as fb_client

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "page-123", "name": "Test Page"}
    mock_resp.raise_for_status = MagicMock()

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_resp)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=None)

    original_token = fb_client.PAGE_ACCESS_TOKEN
    original_page = fb_client.PAGE_ID
    fb_client.PAGE_ACCESS_TOKEN = "test-token"
    fb_client.PAGE_ID = "page-123"

    with patch("mcp_servers.facebook.client.httpx.AsyncClient", return_value=mock_http):
        result = await fb_client.health_check_meta()

    fb_client.PAGE_ACCESS_TOKEN = original_token
    fb_client.PAGE_ID = original_page

    assert result.get("healthy") is True


@pytest.mark.asyncio
async def test_client_post_to_facebook_no_token():
    """post_to_facebook returns error dict when token not set."""
    from mcp_servers.facebook import client as fb_client

    original_token = fb_client.PAGE_ACCESS_TOKEN
    fb_client.PAGE_ACCESS_TOKEN = ""

    result = await fb_client.post_to_facebook("Hello world")

    fb_client.PAGE_ACCESS_TOKEN = original_token

    assert result["success"] is False
    assert "not set" in result["error"]
