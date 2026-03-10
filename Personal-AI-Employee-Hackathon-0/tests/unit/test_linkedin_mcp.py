"""Contract tests for LinkedIn MCP tools.

Written RED before implementation — must fail until server.py exists.
Tests all 6 post_update cases + 3 get_profile cases + 4 health_check cases
from contracts/linkedin_mcp_tools.md.
"""
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─── post_update contract tests ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_post_update_success():
    """post_update with valid text → returns post_id."""
    from mcp_servers.linkedin.server import post_update

    with patch(
        "mcp_servers.linkedin.server.post_to_linkedin", new_callable=AsyncMock
    ) as mock:
        mock.return_value = {"post_id": "urn:li:share:123", "raw": {}}
        result = await post_update(text="Hello LinkedIn", visibility="PUBLIC")
        data = json.loads(result["content"])
        assert data["success"] is True
        assert data["post_id"] == "urn:li:share:123"


@pytest.mark.asyncio
async def test_post_update_empty_text_rejected():
    """post_update with empty text → validation error before API call."""
    from mcp_servers.linkedin.server import post_update

    result = await post_update(text="", visibility="PUBLIC")
    assert result.get("isError") is True


@pytest.mark.asyncio
async def test_post_update_text_too_long_rejected():
    """post_update with >3000 chars → validation error."""
    from mcp_servers.linkedin.server import post_update

    result = await post_update(text="x" * 3001, visibility="PUBLIC")
    assert result.get("isError") is True


@pytest.mark.asyncio
async def test_post_update_auth_required():
    """post_update when token missing → isError with auth message."""
    from mcp_servers.linkedin.auth import AuthRequiredError
    from mcp_servers.linkedin.server import post_update

    with patch(
        "mcp_servers.linkedin.server.post_to_linkedin",
        side_effect=AuthRequiredError("No token"),
    ):
        result = await post_update(text="Test post", visibility="PUBLIC")
        assert result.get("isError") is True
        content_lower = result["content"].lower()
        assert "auth" in content_lower or "token" in content_lower


@pytest.mark.asyncio
async def test_post_update_api_error():
    """post_update when LinkedIn API returns error → isError."""
    from mcp_servers.linkedin.client import LinkedInAPIError
    from mcp_servers.linkedin.server import post_update

    with patch(
        "mcp_servers.linkedin.server.post_to_linkedin",
        side_effect=LinkedInAPIError(500, "Internal server error"),
    ):
        result = await post_update(text="Test post", visibility="PUBLIC")
        assert result.get("isError") is True


@pytest.mark.asyncio
async def test_post_update_auto_refresh_on_401():
    """post_update: client.py auto-refreshes on HTTP 401 and retries (SC-010).

    The 401 retry is handled inside client.py post_to_linkedin() at the HTTP
    response level — server.py only sees a LinkedInAPIError if the RETRY also
    fails. This test verifies the server-layer contract: a LinkedInAPIError
    raised by client (e.g. retry also 401) → isError; a successful retry
    (no exception) → success.
    """
    from mcp_servers.linkedin.client import LinkedInAPIError
    from mcp_servers.linkedin.server import post_update

    # Case 1: client raises LinkedInAPIError(401) — retry failed too.
    # Server must return isError, not re-raise.
    with patch(
        "mcp_servers.linkedin.server.post_to_linkedin",
        side_effect=LinkedInAPIError(401, "Unauthorized"),
    ):
        result = await post_update(text="Test post that triggers 401", visibility="PUBLIC")
        assert result.get("isError") is True
        # Error content must mention the status code or the word 'auth'/'linkedin'
        content = result["content"].lower()
        assert "401" in content or "auth" in content or "linkedin" in content

    # Case 2: client handles 401 internally and returns success (retry worked).
    # Server must return success.
    with patch(
        "mcp_servers.linkedin.server.post_to_linkedin",
        new_callable=AsyncMock,
        return_value={"post_id": "urn:li:share:789", "raw": {}},
    ):
        result = await post_update(text="Test post after refresh", visibility="PUBLIC")
        data = json.loads(result["content"])
        assert data["success"] is True
        assert data["post_id"] == "urn:li:share:789"


# ─── get_profile contract tests ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_profile_success():
    from mcp_servers.linkedin.server import get_profile

    with patch(
        "mcp_servers.linkedin.server.client_get_profile",
        new_callable=AsyncMock,
        return_value={"id": "abc123", "localizedFirstName": "M.Y", "localizedLastName": ""},
    ):
        result = await get_profile()
        data = json.loads(result["content"])
        assert data["success"] is True
        assert "urn:li:person:abc123" in data["person_urn"]


@pytest.mark.asyncio
async def test_get_profile_auth_required():
    from mcp_servers.linkedin.auth import AuthRequiredError
    from mcp_servers.linkedin.server import get_profile

    with patch(
        "mcp_servers.linkedin.server.client_get_profile",
        side_effect=AuthRequiredError("No token"),
    ):
        result = await get_profile()
        assert result.get("isError") is True


@pytest.mark.asyncio
async def test_get_profile_api_error():
    from mcp_servers.linkedin.client import LinkedInAPIError
    from mcp_servers.linkedin.server import get_profile

    with patch(
        "mcp_servers.linkedin.server.client_get_profile",
        side_effect=LinkedInAPIError(503, "Service unavailable"),
    ):
        result = await get_profile()
        assert result.get("isError") is True


# ─── health_check contract tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_check_all_healthy():
    """health_check returns healthy=True with token_expires_in_seconds > 0."""
    from mcp_servers.linkedin.server import health_check

    with patch(
        "mcp_servers.linkedin.server.health_check_api",
        new_callable=AsyncMock,
        return_value=True,
    ):
        with patch("mcp_servers.linkedin.server.get_linkedin_credentials") as mock_creds:
            future_ts = time.time() + 7200
            mock_creds.return_value = MagicMock(expires_at=future_ts)
            result = await health_check()
            data = json.loads(result["content"])
            assert data["healthy"] is True
            assert data["token_valid"] is True
            assert data["api_reachable"] is True
            # token_expires_in_seconds must be present and positive
            assert "token_expires_in_seconds" in data
            assert data["token_expires_in_seconds"] > 0


@pytest.mark.asyncio
async def test_health_check_api_unreachable():
    from mcp_servers.linkedin.server import health_check

    with patch(
        "mcp_servers.linkedin.server.health_check_api",
        new_callable=AsyncMock,
        return_value=False,
    ):
        with patch("mcp_servers.linkedin.server.get_linkedin_credentials") as mock_creds:
            mock_creds.return_value = MagicMock(expires_at=time.time() + 7200)
            result = await health_check()
            data = json.loads(result["content"])
            assert data["healthy"] is False
            assert data["api_reachable"] is False


@pytest.mark.asyncio
async def test_health_check_no_token():
    from mcp_servers.linkedin.auth import AuthRequiredError
    from mcp_servers.linkedin.server import health_check

    with patch(
        "mcp_servers.linkedin.server.get_linkedin_credentials",
        side_effect=AuthRequiredError("No token"),
    ):
        result = await health_check()
        data = json.loads(result["content"])
        assert data["healthy"] is False
        assert data["token_valid"] is False


@pytest.mark.asyncio
async def test_health_check_graceful_on_network_error():
    """health_check must not raise even if everything is broken (SC-010 degradation)."""
    from mcp_servers.linkedin.server import health_check

    with patch(
        "mcp_servers.linkedin.server.get_linkedin_credentials",
        side_effect=Exception("Network error"),
    ):
        result = await health_check()
        # Must return a dict, not raise
        assert isinstance(result, dict)
        data = json.loads(result["content"])
        assert data["healthy"] is False


@pytest.mark.asyncio
async def test_health_check_token_near_expiry():
    """health_check: server sets token_valid=True when get_linkedin_credentials() succeeds.

    Note: server.py does NOT apply a near-expiry buffer — it relies on
    auth.py's get_linkedin_credentials() to auto-refresh if near expiry.
    If auth.py successfully returns credentials (even near-expiry), server
    reports token_valid=True. The expires_in seconds will be small but >= 0.
    """
    from mcp_servers.linkedin.server import health_check

    with patch(
        "mcp_servers.linkedin.server.health_check_api",
        new_callable=AsyncMock,
        return_value=True,
    ):
        with patch("mcp_servers.linkedin.server.get_linkedin_credentials") as mock_creds:
            # expires in 60 seconds (within the 300s buffer — auth.py would normally
            # refresh, but here we mock credentials returning directly)
            near_expiry_ts = time.time() + 60
            mock_creds.return_value = MagicMock(expires_at=near_expiry_ts)
            result = await health_check()
            data = json.loads(result["content"])
            # get_linkedin_credentials() returned successfully → token_valid=True
            assert data["token_valid"] is True
            # token_expires_in_seconds must be present (could be 0 if exactly at boundary)
            assert "token_expires_in_seconds" in data
            assert data["token_expires_in_seconds"] >= 0
            # healthy = token_valid AND api_reachable
            assert data["healthy"] is True


# ─── auth.py unit tests ───────────────────────────────────────────────────────


def test_auth_load_token_missing(tmp_path, monkeypatch):
    """_load_token_file raises AuthRequiredError when file missing."""
    import mcp_servers.linkedin.auth as auth_mod

    monkeypatch.setattr(auth_mod, "TOKEN_FILE", tmp_path / "linkedin_token.json")
    auth_mod.reset_credentials_cache()
    with pytest.raises(auth_mod.AuthRequiredError):
        auth_mod._load_token_file()


def test_auth_load_token_present(tmp_path, monkeypatch):
    """_load_token_file returns credentials when file exists."""
    import json
    import time
    import mcp_servers.linkedin.auth as auth_mod

    token_file = tmp_path / "linkedin_token.json"
    token_file.write_text(
        json.dumps({
            "access_token": "test_access",
            "refresh_token": "test_refresh",
            "expires_at": time.time() + 7200,
            "person_urn": "urn:li:person:abc123",
            "token_type": "Bearer",
        })
    )
    monkeypatch.setattr(auth_mod, "TOKEN_FILE", token_file)
    auth_mod.reset_credentials_cache()
    creds = auth_mod._load_token_file()
    assert creds.access_token == "test_access"
    assert creds.person_urn == "urn:li:person:abc123"


def test_auth_save_token_file(tmp_path, monkeypatch):
    """_save_token_file writes credentials to disk via atomic_write."""
    import json
    import time
    import mcp_servers.linkedin.auth as auth_mod
    from mcp_servers.linkedin.models import LinkedInCredentials

    token_file = tmp_path / "linkedin_token.json"
    monkeypatch.setattr(auth_mod, "TOKEN_FILE", token_file)
    creds = LinkedInCredentials(
        access_token="saved_token",
        expires_at=time.time() + 3600,
        person_urn="urn:li:person:xyz",
    )
    auth_mod._save_token_file(creds)
    data = json.loads(token_file.read_text())
    assert data["access_token"] == "saved_token"


def test_auth_get_credentials_singleton(tmp_path, monkeypatch):
    """get_linkedin_credentials returns singleton and doesn't reload."""
    import json
    import time
    import mcp_servers.linkedin.auth as auth_mod

    token_file = tmp_path / "linkedin_token.json"
    token_file.write_text(
        json.dumps({
            "access_token": "singleton_token",
            "expires_at": time.time() + 7200,
            "person_urn": "urn:li:person:abc",
            "token_type": "Bearer",
        })
    )
    monkeypatch.setattr(auth_mod, "TOKEN_FILE", token_file)
    auth_mod.reset_credentials_cache()
    c1 = auth_mod.get_linkedin_credentials()
    c2 = auth_mod.get_linkedin_credentials()
    assert c1 is c2  # same object


def test_auth_get_person_urn_from_creds(tmp_path, monkeypatch):
    """get_person_urn returns URN from token file."""
    import json
    import time
    import mcp_servers.linkedin.auth as auth_mod

    token_file = tmp_path / "linkedin_token.json"
    token_file.write_text(
        json.dumps({
            "access_token": "tok",
            "expires_at": time.time() + 7200,
            "person_urn": "urn:li:person:myperson",
            "token_type": "Bearer",
        })
    )
    monkeypatch.setattr(auth_mod, "TOKEN_FILE", token_file)
    auth_mod.reset_credentials_cache()
    urn = auth_mod.get_person_urn()
    assert urn == "urn:li:person:myperson"


def test_auth_get_person_urn_raises_if_missing(tmp_path, monkeypatch):
    """get_person_urn raises AuthRequiredError when URN not set."""
    import json
    import time
    import mcp_servers.linkedin.auth as auth_mod

    token_file = tmp_path / "linkedin_token.json"
    token_file.write_text(
        json.dumps({
            "access_token": "tok",
            "expires_at": time.time() + 7200,
            "token_type": "Bearer",
        })
    )
    monkeypatch.setattr(auth_mod, "TOKEN_FILE", token_file)
    monkeypatch.delenv("LINKEDIN_PERSON_URN", raising=False)
    auth_mod.reset_credentials_cache()
    with pytest.raises(auth_mod.AuthRequiredError):
        auth_mod.get_person_urn()


def test_auth_refresh_no_refresh_token(tmp_path, monkeypatch):
    """_refresh_token raises AuthRequiredError when no refresh_token."""
    import json
    import time
    import mcp_servers.linkedin.auth as auth_mod
    from mcp_servers.linkedin.models import LinkedInCredentials

    monkeypatch.setattr(auth_mod, "TOKEN_FILE", tmp_path / "linkedin_token.json")
    creds = LinkedInCredentials(
        access_token="expired",
        refresh_token=None,
        expires_at=time.time() - 1,
    )
    with pytest.raises(auth_mod.AuthRequiredError, match="No refresh_token"):
        auth_mod._refresh_token(creds)


def test_auth_refresh_no_client_credentials(tmp_path, monkeypatch):
    """_refresh_token raises AuthRequiredError when env vars missing."""
    import json
    import time
    import mcp_servers.linkedin.auth as auth_mod
    from mcp_servers.linkedin.models import LinkedInCredentials

    monkeypatch.delenv("LINKEDIN_CLIENT_ID", raising=False)
    monkeypatch.delenv("LINKEDIN_CLIENT_SECRET", raising=False)
    creds = LinkedInCredentials(
        access_token="expired",
        refresh_token="rtoken",
        expires_at=time.time() - 1,
    )
    with pytest.raises(auth_mod.AuthRequiredError, match="LINKEDIN_CLIENT_ID"):
        auth_mod._refresh_token(creds)


# ─── auth.py _is_expired unit tests ───────────────────────────────────────────


def test_auth_is_expired_true():
    """_is_expired returns True when token is within the 300s buffer window."""
    import time
    import mcp_servers.linkedin.auth as auth_mod
    from mcp_servers.linkedin.models import LinkedInCredentials

    # Expired 1 second ago — definitely expired
    creds = LinkedInCredentials(
        access_token="tok",
        expires_at=time.time() - 1,
        person_urn="urn:li:person:x",
    )
    assert auth_mod._is_expired(creds) is True


def test_auth_is_expired_within_buffer_true():
    """_is_expired returns True when token expires within the default 300s buffer."""
    import time
    import mcp_servers.linkedin.auth as auth_mod
    from mcp_servers.linkedin.models import LinkedInCredentials

    # Expires in 60 seconds — within the 300s buffer, so considered expired
    creds = LinkedInCredentials(
        access_token="tok",
        expires_at=time.time() + 60,
        person_urn="urn:li:person:x",
    )
    assert auth_mod._is_expired(creds) is True


def test_auth_is_expired_false():
    """_is_expired returns False when token has plenty of time left (> 300s buffer)."""
    import time
    import mcp_servers.linkedin.auth as auth_mod
    from mcp_servers.linkedin.models import LinkedInCredentials

    # Expires in 1 hour — well outside the 300s buffer
    creds = LinkedInCredentials(
        access_token="tok",
        expires_at=time.time() + 3600,
        person_urn="urn:li:person:x",
    )
    assert auth_mod._is_expired(creds) is False


def test_auth_is_expired_custom_buffer():
    """_is_expired respects custom buffer_seconds argument."""
    import time
    import mcp_servers.linkedin.auth as auth_mod
    from mcp_servers.linkedin.models import LinkedInCredentials

    # Expires in 400 seconds — outside default 300s buffer but inside 600s buffer
    creds = LinkedInCredentials(
        access_token="tok",
        expires_at=time.time() + 400,
        person_urn="urn:li:person:x",
    )
    assert auth_mod._is_expired(creds, buffer_seconds=300) is False
    assert auth_mod._is_expired(creds, buffer_seconds=600) is True


# ─── client.py unit tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_client_post_to_linkedin_success():
    """post_to_linkedin returns post_id on 201 response."""
    import httpx
    from unittest.mock import MagicMock, AsyncMock
    import mcp_servers.linkedin.client as client_mod

    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.is_success = True
    mock_resp.headers = {"X-RestLi-Id": "urn:li:share:999"}
    mock_resp.content = b'{"id": "urn:li:share:999"}'
    mock_resp.json.return_value = {"id": "urn:li:share:999"}

    with patch("mcp_servers.linkedin.client.get_access_token", return_value="tok"):
        with patch("mcp_servers.linkedin.client.get_person_urn", return_value="urn:li:person:abc"):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value = mock_client

                result = await client_mod.post_to_linkedin("Hello LinkedIn", "PUBLIC")
                assert result["post_id"] == "urn:li:share:999"


@pytest.mark.asyncio
async def test_client_post_to_linkedin_api_error():
    """post_to_linkedin raises LinkedInAPIError on non-2xx."""
    import mcp_servers.linkedin.client as client_mod

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.is_success = False
    mock_resp.text = "Internal Server Error"

    with patch("mcp_servers.linkedin.client.get_access_token", return_value="tok"):
        with patch("mcp_servers.linkedin.client.get_person_urn", return_value="urn:li:person:abc"):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value = mock_client

                with pytest.raises(client_mod.LinkedInAPIError) as exc:
                    await client_mod.post_to_linkedin("test", "PUBLIC")
                assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_client_post_to_linkedin_401_triggers_refresh_and_retry():
    """post_to_linkedin retries once after HTTP 401 with a refreshed token.

    client.py handles 401 at the HTTP response level: resets credentials cache,
    calls get_access_token() again, and retries the POST once. If the retry
    succeeds, a result is returned; if the retry also fails, LinkedInAPIError
    is raised.
    """
    import mcp_servers.linkedin.client as client_mod

    # First response: 401 Unauthorized
    mock_401 = MagicMock()
    mock_401.status_code = 401
    mock_401.is_success = False
    mock_401.text = "Unauthorized"

    # Second response: 201 Created (after refresh)
    mock_201 = MagicMock()
    mock_201.status_code = 201
    mock_201.is_success = True
    mock_201.headers = {"X-RestLi-Id": "urn:li:share:refreshed"}
    mock_201.content = b'{}'
    mock_201.json.return_value = {}

    call_count = 0

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_401
        return mock_201

    with patch("mcp_servers.linkedin.client.get_access_token", return_value="new_token"):
        with patch("mcp_servers.linkedin.client.get_person_urn", return_value="urn:li:person:abc"):
            with patch("mcp_servers.linkedin.client.reset_credentials_cache") as mock_reset:
                with patch("httpx.AsyncClient") as mock_client_cls:
                    mock_client = AsyncMock()
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock(return_value=None)
                    mock_client.post = mock_post
                    mock_client_cls.return_value = mock_client

                    result = await client_mod.post_to_linkedin("Test retry", "PUBLIC")
                    # Retry succeeded — post_id from X-RestLi-Id header
                    assert result["post_id"] == "urn:li:share:refreshed"
                    # reset_credentials_cache must have been called once (on 401)
                    mock_reset.assert_called_once()
                    # HTTP POST was called twice: first (401) + retry (201)
                    assert call_count == 2


@pytest.mark.asyncio
async def test_client_post_to_linkedin_401_retry_also_fails():
    """post_to_linkedin raises LinkedInAPIError when both attempts return 401."""
    import mcp_servers.linkedin.client as client_mod

    mock_401 = MagicMock()
    mock_401.status_code = 401
    mock_401.is_success = False
    mock_401.text = "Unauthorized"

    with patch("mcp_servers.linkedin.client.get_access_token", return_value="stale_token"):
        with patch("mcp_servers.linkedin.client.get_person_urn", return_value="urn:li:person:abc"):
            with patch("mcp_servers.linkedin.client.reset_credentials_cache"):
                with patch("httpx.AsyncClient") as mock_client_cls:
                    mock_client = AsyncMock()
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock(return_value=None)
                    # Both calls return 401
                    mock_client.post = AsyncMock(return_value=mock_401)
                    mock_client_cls.return_value = mock_client

                    with pytest.raises(client_mod.LinkedInAPIError) as exc:
                        await client_mod.post_to_linkedin("Test", "PUBLIC")
                    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_client_get_profile_success():
    """get_profile returns profile data on 200 response."""
    import mcp_servers.linkedin.client as client_mod

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.is_success = True
    mock_resp.json.return_value = {"id": "abc123", "localizedFirstName": "Test"}

    with patch("mcp_servers.linkedin.client.get_access_token", return_value="tok"):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            result = await client_mod.get_profile()
            assert result["id"] == "abc123"


@pytest.mark.asyncio
async def test_client_get_profile_401_triggers_refresh_and_retry():
    """get_profile retries once after HTTP 401 — same retry pattern as post_to_linkedin."""
    import mcp_servers.linkedin.client as client_mod

    mock_401 = MagicMock()
    mock_401.status_code = 401
    mock_401.is_success = False
    mock_401.text = "Unauthorized"

    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.is_success = True
    mock_200.json.return_value = {"sub": "retried_user"}

    call_count = 0

    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_401
        return mock_200

    with patch("mcp_servers.linkedin.client.get_access_token", return_value="refreshed_token"):
        with patch("mcp_servers.linkedin.client.reset_credentials_cache") as mock_reset:
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client.get = mock_get
                mock_client_cls.return_value = mock_client

                result = await client_mod.get_profile()
                assert result["sub"] == "retried_user"
                mock_reset.assert_called_once()
                assert call_count == 2


@pytest.mark.asyncio
async def test_client_health_check_network_error():
    """health_check_api returns False on network error."""
    import mcp_servers.linkedin.client as client_mod

    with patch("mcp_servers.linkedin.client.get_access_token", return_value="tok"):
        with patch("httpx.AsyncClient", side_effect=Exception("Network down")):
            result = await client_mod.health_check_api()
            assert result is False


@pytest.mark.asyncio
async def test_client_health_check_returns_true_on_200():
    """health_check_api returns True when LinkedIn API responds with 200."""
    import mcp_servers.linkedin.client as client_mod

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("mcp_servers.linkedin.client.get_access_token", return_value="tok"):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            result = await client_mod.health_check_api()
            assert result is True


@pytest.mark.asyncio
async def test_client_health_check_returns_true_on_401():
    """health_check_api returns True on 401 — API is reachable even if token expired."""
    import mcp_servers.linkedin.client as client_mod

    mock_resp = MagicMock()
    mock_resp.status_code = 401

    with patch("mcp_servers.linkedin.client.get_access_token", return_value="expired_tok"):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            result = await client_mod.health_check_api()
            assert result is True


def test_linkedin_api_error_str():
    """LinkedInAPIError has correct string representation."""
    from mcp_servers.linkedin.client import LinkedInAPIError

    err = LinkedInAPIError(429, "Rate limit exceeded")
    assert "429" in str(err)
    assert "Rate limit exceeded" in str(err)


# ═══════════════════════════════════════════════════════════════════════════════
# COVERAGE EXPANSION: Missing paths in auth.py and server.py
# ═══════════════════════════════════════════════════════════════════════════════


# ─── auth.py: _refresh_token() success path (lines 65-85) ────────────────────


def test_auth_refresh_token_success(tmp_path, monkeypatch):
    """_refresh_token makes POST to LinkedIn OAuth and saves new credentials."""
    import json
    import time
    import mcp_servers.linkedin.auth as auth_mod
    from unittest.mock import MagicMock, patch
    from mcp_servers.linkedin.models import LinkedInCredentials

    token_file = tmp_path / "linkedin_token.json"
    monkeypatch.setattr(auth_mod, "TOKEN_FILE", token_file)
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "test_client_secret")

    creds = LinkedInCredentials(
        access_token="expired_token",
        refresh_token="valid_refresh_token",
        expires_at=time.time() - 1,
        person_urn="urn:li:person:abc",
    )

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 3600,
    }

    with patch("mcp_servers.linkedin.auth.httpx.post", return_value=mock_resp) as mock_post:
        new_creds = auth_mod._refresh_token(creds)

    mock_post.assert_called_once()
    assert new_creds.access_token == "new_access_token"
    assert new_creds.refresh_token == "new_refresh_token"
    # Token saved to file
    assert token_file.exists()
    saved = json.loads(token_file.read_text())
    assert saved["access_token"] == "new_access_token"


def test_auth_refresh_token_uses_existing_refresh_when_new_not_returned(tmp_path, monkeypatch):
    """_refresh_token keeps old refresh_token when new one not in response."""
    import time
    import mcp_servers.linkedin.auth as auth_mod
    from unittest.mock import MagicMock, patch
    from mcp_servers.linkedin.models import LinkedInCredentials

    token_file = tmp_path / "linkedin_token.json"
    monkeypatch.setattr(auth_mod, "TOKEN_FILE", token_file)
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "cid")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "csecret")

    creds = LinkedInCredentials(
        access_token="old",
        refresh_token="keep_this_refresh",
        expires_at=time.time() - 1,
    )

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"access_token": "fresh", "expires_in": 3600}
    # No "refresh_token" in response

    with patch("mcp_servers.linkedin.auth.httpx.post", return_value=mock_resp):
        new_creds = auth_mod._refresh_token(creds)

    assert new_creds.refresh_token == "keep_this_refresh"


# ─── auth.py: get_linkedin_credentials() auto-refresh (lines 94-95) ──────────


def test_auth_get_credentials_triggers_refresh_on_expiry(tmp_path, monkeypatch):
    """get_linkedin_credentials auto-refreshes when token is near expiry."""
    import json
    import time
    import mcp_servers.linkedin.auth as auth_mod
    from unittest.mock import patch
    from mcp_servers.linkedin.models import LinkedInCredentials

    token_file = tmp_path / "linkedin_token.json"
    token_file.write_text(json.dumps({
        "access_token": "near_expired",
        "refresh_token": "rtoken",
        "expires_at": time.time() + 60,  # within 300s buffer
        "person_urn": "urn:li:person:abc",
        "token_type": "Bearer",
    }))
    monkeypatch.setattr(auth_mod, "TOKEN_FILE", token_file)
    auth_mod.reset_credentials_cache()

    refreshed = LinkedInCredentials(
        access_token="refreshed_token",
        expires_at=time.time() + 3600,
    )

    with patch.object(auth_mod, "_refresh_token", return_value=refreshed) as mock_refresh:
        result = auth_mod.get_linkedin_credentials()
        mock_refresh.assert_called_once()
        assert result.access_token == "refreshed_token"

    auth_mod.reset_credentials_cache()


# ─── server.py: generic Exception in post_update (lines 58-60) ───────────────


@pytest.mark.asyncio
async def test_post_update_unexpected_exception_returns_error():
    """post_update catches unexpected RuntimeError and returns isError dict."""
    from mcp_servers.linkedin.server import post_update
    from unittest.mock import patch

    with patch(
        "mcp_servers.linkedin.server.post_to_linkedin",
        side_effect=RuntimeError("Unexpected network failure"),
    ):
        result = await post_update(text="Test post", visibility="PUBLIC")

    assert result.get("isError") is True
    assert "Unexpected" in result["content"] or "error" in result["content"].lower()


# ─── server.py: generic Exception in get_profile (lines 84-86) ───────────────


@pytest.mark.asyncio
async def test_get_profile_unexpected_exception_returns_error():
    """get_profile catches unexpected RuntimeError and returns isError dict."""
    from mcp_servers.linkedin.server import get_profile
    from unittest.mock import patch

    with patch(
        "mcp_servers.linkedin.server.client_get_profile",
        side_effect=RuntimeError("Unexpected DB error"),
    ):
        result = await get_profile()

    assert result.get("isError") is True


# ─── server.py: health_check_api raises Exception (lines 105-106) ────────────


@pytest.mark.asyncio
async def test_health_check_api_exception_returns_unhealthy():
    """health_check sets api_reachable=False when health_check_api raises."""
    import time
    import json
    from unittest.mock import MagicMock, patch
    from mcp_servers.linkedin.server import health_check

    with patch("mcp_servers.linkedin.server.get_linkedin_credentials") as mock_creds:
        mock_creds.return_value = MagicMock(expires_at=time.time() + 7200)
        with patch(
            "mcp_servers.linkedin.server.health_check_api",
            side_effect=Exception("Network partition"),
        ):
            result = await health_check()

    data = json.loads(result["content"])
    assert data["healthy"] is False
    assert data["api_reachable"] is False
    assert data["token_valid"] is True  # token was valid; only API failed
