"""LinkedIn OAuth2 token lifecycle — ADR-0014.

Singleton pattern mirroring mcp_servers/gmail/auth.py.
Auto-refresh on 401, atomic_write for token save.
"""
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import httpx

from mcp_servers.linkedin.models import LinkedInCredentials
from watchers.utils import atomic_write

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOKEN_FILE = PROJECT_ROOT / "linkedin_token.json"
REFRESH_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# Singleton — module-level, reset on each process start
_credentials: Optional[LinkedInCredentials] = None


class AuthRequiredError(Exception):
    """Raised when token file is missing. Human must run scripts/linkedin_auth.py."""

    pass


def _load_token_file() -> LinkedInCredentials:
    if not TOKEN_FILE.exists():
        raise AuthRequiredError(
            f"linkedin_token.json not found at {TOKEN_FILE}. "
            "Run: python3 scripts/linkedin_auth.py"
        )
    raw = json.loads(TOKEN_FILE.read_text())
    return LinkedInCredentials(**raw)


def _save_token_file(creds: LinkedInCredentials) -> None:
    atomic_write(TOKEN_FILE, json.dumps(creds.model_dump(), indent=2))


def _is_expired(creds: LinkedInCredentials, buffer_seconds: int = 300) -> bool:
    """True if token expires within buffer_seconds (default 5 min)."""
    return time.time() >= (creds.expires_at - buffer_seconds)


def _refresh_token(creds: LinkedInCredentials) -> LinkedInCredentials:
    """Exchange refresh_token for new access_token. Raises httpx.HTTPError on failure."""
    if not creds.refresh_token:
        raise AuthRequiredError(
            "No refresh_token available. Re-run scripts/linkedin_auth.py "
            "(ensure offline_access scope was granted)."
        )
    client_id = os.environ.get("LINKEDIN_CLIENT_ID", "")
    client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise AuthRequiredError("LINKEDIN_CLIENT_ID or LINKEDIN_CLIENT_SECRET not set in .env")

    resp = httpx.post(
        REFRESH_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": creds.refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    new_creds = LinkedInCredentials(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", creds.refresh_token),
        expires_at=time.time() + data.get("expires_in", 3600),
        person_urn=creds.person_urn,
    )
    _save_token_file(new_creds)
    logger.info("LinkedIn token refreshed successfully.")
    return new_creds


def get_linkedin_credentials() -> LinkedInCredentials:
    """Return valid credentials, auto-refreshing if near expiry. Singleton."""
    global _credentials
    if _credentials is None:
        _credentials = _load_token_file()
    if _is_expired(_credentials):
        logger.info("LinkedIn token near expiry — refreshing.")
        _credentials = _refresh_token(_credentials)
    return _credentials


def reset_credentials_cache() -> None:
    """Force reload from disk on next call. Use in tests."""
    global _credentials
    _credentials = None


def get_access_token() -> str:
    """Convenience: return just the access token string."""
    return get_linkedin_credentials().access_token


def get_person_urn() -> str:
    """Return person URN. Raises AuthRequiredError if not set."""
    creds = get_linkedin_credentials()
    urn = creds.person_urn or os.environ.get("LINKEDIN_PERSON_URN", "")
    if not urn:
        raise AuthRequiredError(
            "person_urn not set. Run scripts/linkedin_auth.py and add "
            "LINKEDIN_PERSON_URN to .env."
        )
    return urn
