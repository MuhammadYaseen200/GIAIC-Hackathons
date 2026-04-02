"""Odoo session authentication — singleton pattern."""
import logging
import os
import httpx

logger = logging.getLogger(__name__)

ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB") or ""
ODOO_USER = os.getenv("ODOO_USER") or ""
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")

_session_id: str | None = None


class OdooAuthError(Exception):
    """Raised when Odoo authentication fails."""
    pass


async def get_odoo_session(client: httpx.AsyncClient) -> str:
    """Get (or create) a valid Odoo session ID."""
    global _session_id
    if _session_id:
        return _session_id

    if not ODOO_DB:
        raise OdooAuthError("ODOO_DB environment variable is required but not set")
    if not ODOO_USER:
        raise OdooAuthError("ODOO_USER environment variable is required but not set")

    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "id": 1,
        "params": {
            "db": ODOO_DB,
            "login": ODOO_USER,
            "password": ODOO_PASSWORD,
        }
    }

    try:
        response = await client.post(
            f"{ODOO_URL}/web/session/authenticate",
            json=payload,
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("result", {}).get("uid"):
            # Extract session_id from cookie
            session_cookie = response.cookies.get("session_id")
            if session_cookie:
                _session_id = session_cookie
                return _session_id
            # Some Odoo versions return session_id in result
            session_from_result = data["result"].get("session_id", "")
            if session_from_result:
                _session_id = session_from_result
                return _session_id
            raise OdooAuthError("No session_id in auth response")

        error_msg = data.get("error", {}).get("message", "Unknown auth error")
        raise OdooAuthError(f"Authentication failed: {error_msg}")

    except httpx.RequestError as e:
        raise OdooAuthError(f"Connection error: {e}") from e


def reset_session_cache() -> None:
    """Clear cached session (call on 401/session expired)."""
    global _session_id
    _session_id = None
    logger.info("Odoo session cache cleared")
