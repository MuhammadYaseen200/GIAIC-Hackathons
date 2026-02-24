"""Gmail OAuth2 authentication for MCP server. Reuses token lifecycle from gmail_watcher.py."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from watchers.utils import atomic_write

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


class AuthRequiredError(Exception):
    """Raised when OAuth token is missing or cannot be refreshed without browser flow."""


_gmail_service = None  # module-level singleton


def get_gmail_service():
    """Return authenticated Gmail API service. Token must already exist (from HT-002).

    Never opens browser flow — raises AuthRequiredError if auth needed.
    Caches service singleton across tool calls for performance.
    Token is refreshed automatically if expired but has refresh token.
    """
    global _gmail_service
    if _gmail_service is not None:
        return _gmail_service

    token_path = Path(os.environ.get("GMAIL_TOKEN_PATH", "token.json"))
    creds_path = Path(os.environ.get("GMAIL_CREDENTIALS_PATH", "credentials.json"))

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
            "Gmail OAuth token missing or expired. "
            "Run 'python3 scripts/gmail_auth.py' to authenticate."
        )

    _gmail_service = build("gmail", "v1", credentials=creds)
    return _gmail_service


def reset_service_cache():
    """Reset cached service singleton. Used in tests for isolation."""
    global _gmail_service
    _gmail_service = None
