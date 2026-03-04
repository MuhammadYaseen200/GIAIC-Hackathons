"""Calendar OAuth2 authentication for MCP server — T024.

Follows the same pattern as mcp_servers/gmail/auth.py.
Scope: calendar.readonly (read-only access to Google Calendar).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from watchers.utils import atomic_write

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class AuthRequiredError(Exception):
    """Raised when OAuth token is missing or cannot be refreshed without browser flow."""


_calendar_service = None  # module-level singleton


def get_calendar_service():
    """Return authenticated Google Calendar API service.

    Token must already exist (from HT-011 / scripts/calendar_auth.py).
    Never opens browser flow — raises AuthRequiredError if auth needed.
    Caches service singleton across tool calls for performance.
    Token is refreshed automatically if expired but has refresh token.
    """
    global _calendar_service
    if _calendar_service is not None:
        return _calendar_service

    token_path = Path(os.environ.get("CALENDAR_TOKEN_PATH", "calendar_token.json"))
    creds_path = Path(os.environ.get("CALENDAR_CREDENTIALS_PATH", "credentials.json"))

    creds = None
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except (ValueError, KeyError):
            token_path.unlink(missing_ok=True)

    if creds and creds.valid:
        pass  # token is fresh — use as-is
    elif creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        atomic_write(token_path, creds.to_json())
    else:
        raise AuthRequiredError(
            "Calendar OAuth token missing or expired. "
            "Run 'python3 scripts/calendar_auth.py' to authenticate."
        )

    _calendar_service = build("calendar", "v3", credentials=creds)
    return _calendar_service


def reset_service_cache():
    """Reset cached service singleton. Used in tests for isolation."""
    global _calendar_service
    _calendar_service = None
