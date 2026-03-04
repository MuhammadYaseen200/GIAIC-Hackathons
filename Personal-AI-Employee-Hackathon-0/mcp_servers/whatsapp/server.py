"""WhatsApp MCP server — FastMCP + stdio transport (T014).

Exposes send_message and health_check tools.
Backend selectable via WHATSAPP_BACKEND env var (go_bridge | pywa).
Per ADR-0005: FastMCP + Pydantic v2 + stdio.
"""

import json
import os

from mcp.server.fastmcp import FastMCP

from mcp_servers.whatsapp.bridge import GoBridge, PywaStub
from mcp_servers.whatsapp.models import MCPError

WHATSAPP_BACKEND = os.getenv("WHATSAPP_BACKEND", "go_bridge")

mcp = FastMCP("whatsapp")


def _get_bridge():
    if WHATSAPP_BACKEND == "go_bridge":
        return GoBridge()
    elif WHATSAPP_BACKEND == "pywa":
        return PywaStub()
    else:
        raise ValueError(f"Unknown WHATSAPP_BACKEND: {WHATSAPP_BACKEND}")


@mcp.tool()
async def send_message(to: str, body: str) -> dict:
    """Send a WhatsApp message to a phone number."""
    bridge = _get_bridge()
    try:
        result = await bridge.send(to=to, body=body)
        return result.model_dump()
    except Exception as e:
        error = MCPError(error="send_failed", message=str(e))
        return {"isError": True, "content": json.dumps(error.model_dump())}


@mcp.tool()
async def health_check() -> dict:
    """Check WhatsApp bridge health."""
    bridge = _get_bridge()
    try:
        result = await bridge.health()
        return result.model_dump()
    except Exception as e:
        error = MCPError(error="mcp_unavailable", message=str(e))
        return {"isError": True, "content": json.dumps(error.model_dump())}


if __name__ == "__main__":
    mcp.run()
