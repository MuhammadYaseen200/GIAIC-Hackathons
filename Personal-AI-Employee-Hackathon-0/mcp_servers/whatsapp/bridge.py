"""Go bridge and pywa backend clients for WhatsApp MCP (T013).

GoBridge: sends messages via HTTP POST to the Go bridge at WHATSAPP_BRIDGE_URL.
PywaStub: placeholder for pywa Cloud API (not yet implemented).
"""

import os
from datetime import datetime, timezone

import httpx

from mcp_servers.whatsapp.models import HealthCheckResult, SendMessageResult

BRIDGE_URL = os.getenv("WHATSAPP_BRIDGE_URL", "http://localhost:8080")


def _to_jid(number: str) -> str:
    """E.164 (+923...) -> WhatsApp JID (923...@s.whatsapp.net)."""
    return number.lstrip("+") + "@s.whatsapp.net"


class GoBridge:
    """Send messages and check health via the Go bridge REST API."""

    async def send(self, to: str, body: str) -> SendMessageResult:
        jid = _to_jid(to)
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{BRIDGE_URL}/api/send",
                json={"recipient": jid, "message": body},
            )
        if resp.status_code != 200:
            raise ValueError(f"send_failed: {resp.status_code} {resp.text}")
        data = resp.json()
        return SendMessageResult(
            message_id=data.get("id", ""),
            status=data.get("status", "sent"),
            sent_at=datetime.now(timezone.utc).isoformat(),
        )

    async def health(self) -> HealthCheckResult:
        # The Go bridge doesn't expose a health endpoint; probe /api/send path
        # by hitting a lightweight GET that returns 405 (method not allowed) if alive
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{BRIDGE_URL}/api/send")
            alive = resp.status_code in (200, 405)
        except Exception:
            alive = False
        return HealthCheckResult(
            status="healthy" if alive else "unhealthy",
            connected_number=None,
            backend="go_bridge",
            bridge_url=BRIDGE_URL,
        )


class PywaStub:
    """Placeholder for pywa Cloud API backend (HT-012 pending)."""

    async def send(self, to: str, body: str) -> SendMessageResult:
        raise NotImplementedError("pywa not yet implemented — use go_bridge backend")

    async def health(self) -> HealthCheckResult:
        raise NotImplementedError("pywa not yet implemented")
