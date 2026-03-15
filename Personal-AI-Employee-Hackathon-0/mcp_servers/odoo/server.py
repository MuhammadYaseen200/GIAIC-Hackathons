"""Odoo MCP Server — FastMCP tools for financial data.

Tools:
  - get_gl_summary() -> GL summary (assets, liabilities, equity)
  - get_ar_aging() -> Accounts Receivable aging report
  - get_invoices_due(days_ahead) -> Invoices due within N days
  - health_check() -> Odoo connectivity status

Registration: Add to ~/.claude.json mcpServers:
  "odoo_mcp": {
    "command": "python3",
    "args": ["<project_root>/mcp_servers/odoo/server.py"],
    "env": {}
  }
"""
import json
import logging

import httpx
from mcp.server.fastmcp import FastMCP

from mcp_servers.odoo.client import (
    get_gl_summary_data,
    get_ar_aging_data,
    get_invoices_due_data,
    health_check_odoo,
)

logger = logging.getLogger(__name__)
mcp = FastMCP("odoo")

# Expose client functions as module-level names for test patching
health_check_odoo_data = health_check_odoo


def _error(msg: str) -> dict:
    """Return a standard error response dict."""
    return {"isError": True, "content": json.dumps({"error": msg})}


@mcp.tool()
async def get_gl_summary() -> dict:
    """Get General Ledger summary (total assets, liabilities, equity, net income)."""
    try:
        async with httpx.AsyncClient() as client:
            result = await get_gl_summary_data(client)
        return {"content": json.dumps(result)}
    except Exception as e:
        logger.error(f"get_gl_summary error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


@mcp.tool()
async def get_ar_aging() -> dict:
    """Get Accounts Receivable aging report (0-30, 31-60, 61-90, 90+ days)."""
    try:
        async with httpx.AsyncClient() as client:
            result = await get_ar_aging_data(client)
        return {"content": json.dumps(result)}
    except Exception as e:
        logger.error(f"get_ar_aging error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


@mcp.tool()
async def get_invoices_due(days_ahead: int = 7) -> dict:
    """Get invoices due within the next N days.

    Args:
        days_ahead: Number of days to look ahead (default: 7)
    """
    try:
        if days_ahead < 0:
            return _error("days_ahead must be non-negative")
        async with httpx.AsyncClient() as client:
            result = await get_invoices_due_data(client, days=days_ahead)
        return {"content": json.dumps(result)}
    except Exception as e:
        logger.error(f"get_invoices_due error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


@mcp.tool()
async def health_check() -> dict:
    """Check Odoo MCP server health and connectivity."""
    try:
        async with httpx.AsyncClient() as client:
            result = await health_check_odoo(client)
        return {"content": json.dumps(result)}
    except Exception as e:
        logger.error(f"health_check error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


if __name__ == "__main__":
    mcp.run()
