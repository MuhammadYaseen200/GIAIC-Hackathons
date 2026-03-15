"""Integration tests for Odoo MCP — require live Odoo instance."""
import pytest

pytestmark = pytest.mark.skipif(
    not __import__("os").getenv("ODOO_LIVE"),
    reason="Set ODOO_LIVE=1 to run integration tests"
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_odoo_health_check_live():
    """Live health check against Odoo Docker instance."""
    import httpx
    from mcp_servers.odoo.client import health_check_odoo

    async with httpx.AsyncClient() as client:
        result = await health_check_odoo(client)

    assert "healthy" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_odoo_get_invoices_due_live():
    """Live invoice query against Odoo."""
    import httpx
    from mcp_servers.odoo.client import get_invoices_due_data

    async with httpx.AsyncClient() as client:
        result = await get_invoices_due_data(client, days=7)

    assert isinstance(result, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_odoo_session_auth_live():
    """Live session authentication."""
    import httpx
    from mcp_servers.odoo.auth import get_odoo_session

    async with httpx.AsyncClient() as client:
        session = await get_odoo_session(client)

    assert session and len(session) > 0
