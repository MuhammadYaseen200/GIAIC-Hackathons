"""Unit tests for Odoo MCP server. Write RED first, then implement."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp_servers.odoo.models import GLSummary, ARAgingResult, InvoiceResult, OdooHealthResult


# -- AUTH TESTS ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_odoo_session_success():
    """get_odoo_session returns session_id on success."""
    from mcp_servers.odoo import auth
    auth._session_id = None  # reset singleton

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": {"uid": 1, "session_id": "test-session-123"}
    }
    mock_response.cookies = {}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    session = await auth.get_odoo_session(mock_client)
    assert session == "test-session-123"


@pytest.mark.asyncio
async def test_get_odoo_session_cached():
    """get_odoo_session returns cached value without HTTP call."""
    from mcp_servers.odoo import auth
    auth._session_id = "cached-session"

    mock_client = AsyncMock()
    session = await auth.get_odoo_session(mock_client)

    assert session == "cached-session"
    mock_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_get_odoo_session_auth_failure():
    """get_odoo_session raises OdooAuthError on failed auth."""
    from mcp_servers.odoo.auth import get_odoo_session, OdooAuthError
    from mcp_servers.odoo import auth
    auth._session_id = None

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "error": {"message": "Access Denied"}
    }
    mock_response.cookies = {}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with pytest.raises(OdooAuthError):
        await get_odoo_session(mock_client)


def test_reset_session_cache():
    """reset_session_cache clears _session_id."""
    from mcp_servers.odoo import auth
    auth._session_id = "some-session"
    auth.reset_session_cache()
    assert auth._session_id is None


# -- CLIENT TESTS -------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_invoices_due_returns_list():
    """get_invoices_due returns list of InvoiceResult objects."""
    from mcp_servers.odoo import client as odoo_client, auth
    auth._session_id = "mock-session"

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": [
            {"id": 1, "partner_id": [1, "ACME Corp"], "amount_residual": 500.0,
             "invoice_date_due": "2026-03-15", "currency_id": [1, "USD"]}
        ]
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch("mcp_servers.odoo.client.get_odoo_session", return_value="mock-session"):
        result = await odoo_client.get_invoices_due_data(mock_client, days=7)

    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_health_check_odoo_healthy():
    """health_check_odoo returns healthy=True when Odoo responds."""
    from mcp_servers.odoo import client as odoo_client

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": {"server_version": "17.0", "db": "h0_odoo"}
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    result = await odoo_client.health_check_odoo(mock_client)
    assert result["healthy"] is True


@pytest.mark.asyncio
async def test_health_check_odoo_connection_error():
    """health_check_odoo returns healthy=False on connection error."""
    import httpx
    from mcp_servers.odoo import client as odoo_client

    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.ConnectError("Connection refused")

    result = await odoo_client.health_check_odoo(mock_client)
    assert result["healthy"] is False
    assert "error" in result


# -- SERVER TOOL TESTS --------------------------------------------------------

@pytest.mark.asyncio
async def test_tool_get_gl_summary_returns_dict():
    """get_gl_summary tool returns dict with content key."""
    from mcp_servers.odoo.server import get_gl_summary

    with patch("mcp_servers.odoo.server.get_gl_summary_data") as mock_fn:
        mock_fn.return_value = GLSummary(total_assets=1000.0).model_dump()
        result = await get_gl_summary()

    assert isinstance(result, dict)
    assert "content" in result or "isError" in result


@pytest.mark.asyncio
async def test_tool_get_invoices_due_default_days():
    """get_invoices_due tool accepts days_ahead parameter."""
    from mcp_servers.odoo.server import get_invoices_due

    with patch("mcp_servers.odoo.server.get_invoices_due_data") as mock_fn:
        mock_fn.return_value = []
        result = await get_invoices_due(days_ahead=7)

    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_tool_health_check_returns_status():
    """health_check tool returns health status dict."""
    from mcp_servers.odoo.server import health_check

    with patch("mcp_servers.odoo.server.health_check_odoo_data") as mock_fn:
        mock_fn.return_value = {"healthy": True, "version": "17.0"}
        result = await health_check()

    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_tool_error_returns_is_error_flag():
    """Tools return isError flag on unexpected exceptions."""
    from mcp_servers.odoo.server import get_gl_summary

    with patch("mcp_servers.odoo.server.get_gl_summary_data") as mock_fn:
        mock_fn.side_effect = Exception("Unexpected error")
        result = await get_gl_summary()

    assert result.get("isError") is True


@pytest.mark.asyncio
async def test_tool_get_ar_aging_returns_dict():
    """get_ar_aging tool returns AR aging data."""
    from mcp_servers.odoo.server import get_ar_aging

    with patch("mcp_servers.odoo.server.get_ar_aging_data") as mock_fn:
        mock_fn.return_value = ARAgingResult().model_dump()
        result = await get_ar_aging()

    assert isinstance(result, dict)


# -- CLIENT DIRECT TESTS (boost coverage) --


@pytest.mark.asyncio
async def test_client_get_gl_summary_success():
    """get_gl_summary_data returns totals from RPC response."""
    from mcp_servers.odoo import client as odoo_client

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "result": [
            {"debit": 1000.0, "credit": 600.0, "account_id": [1, "Revenue"]},
            {"debit": 500.0, "credit": 200.0, "account_id": [2, "Expense"]},
        ]
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with patch("mcp_servers.odoo.client.get_odoo_session", return_value="test-sess"):
        result = await odoo_client.get_gl_summary_data(mock_client)

    assert result["total_assets"] == 1500.0
    assert result["total_liabilities"] == 800.0
    assert result["total_equity"] == 700.0


@pytest.mark.asyncio
async def test_client_get_gl_summary_zero_values_demo_data():
    """get_gl_summary_data returns 'Demo data' note on zero balances."""
    from mcp_servers.odoo import client as odoo_client

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"result": []}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with patch("mcp_servers.odoo.client.get_odoo_session", return_value="test-sess"):
        result = await odoo_client.get_gl_summary_data(mock_client)

    assert "Demo data" in result["note"]


@pytest.mark.asyncio
async def test_client_get_gl_summary_rpc_error():
    """get_gl_summary_data handles RPC error in response body."""
    from mcp_servers.odoo import client as odoo_client

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"error": {"message": "session expired"}}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with patch("mcp_servers.odoo.client.get_odoo_session", return_value="test-sess"), \
         patch("mcp_servers.odoo.client.reset_session_cache") as mock_reset:
        result = await odoo_client.get_gl_summary_data(mock_client)

    assert "RPC error" in result["note"]
    mock_reset.assert_called_once()


@pytest.mark.asyncio
async def test_client_get_gl_summary_auth_error():
    """get_gl_summary_data handles OdooAuthError gracefully."""
    from mcp_servers.odoo import client as odoo_client
    from mcp_servers.odoo.auth import OdooAuthError

    mock_client = AsyncMock()

    with patch("mcp_servers.odoo.client.get_odoo_session", side_effect=OdooAuthError("bad creds")):
        result = await odoo_client.get_gl_summary_data(mock_client)

    assert "Auth error" in result["note"]


@pytest.mark.asyncio
async def test_client_get_ar_aging_success():
    """get_ar_aging_data parses invoices into aging buckets."""
    from mcp_servers.odoo import client as odoo_client
    from datetime import date, timedelta

    today = date.today()
    overdue_45 = (today - timedelta(days=45)).isoformat()

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "result": [
            {"partner_id": [1, "Acme"], "amount_residual": 300.0,
             "invoice_date_due": overdue_45, "currency_id": [1, "USD"]},
        ]
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with patch("mcp_servers.odoo.client.get_odoo_session", return_value="test-sess"):
        result = await odoo_client.get_ar_aging_data(mock_client)

    assert result["total_receivable"] == 300.0
    assert len(result["partners"]) == 1
    assert result["partners"][0]["partner_name"] == "Acme"


@pytest.mark.asyncio
async def test_client_get_ar_aging_rpc_error():
    """get_ar_aging_data returns empty result on RPC error."""
    from mcp_servers.odoo import client as odoo_client

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"error": {"message": "access denied"}}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with patch("mcp_servers.odoo.client.get_odoo_session", return_value="test-sess"), \
         patch("mcp_servers.odoo.client.reset_session_cache"):
        result = await odoo_client.get_ar_aging_data(mock_client)

    assert result["total_receivable"] == 0.0
    assert result["partners"] == []


@pytest.mark.asyncio
async def test_client_get_ar_aging_auth_error():
    """get_ar_aging_data returns empty result on auth error."""
    from mcp_servers.odoo import client as odoo_client
    from mcp_servers.odoo.auth import OdooAuthError

    mock_client = AsyncMock()

    with patch("mcp_servers.odoo.client.get_odoo_session", side_effect=OdooAuthError("denied")):
        result = await odoo_client.get_ar_aging_data(mock_client)

    assert result["total_receivable"] == 0.0


@pytest.mark.asyncio
async def test_client_get_invoices_due_rpc_error():
    """get_invoices_due_data returns [] on RPC error."""
    from mcp_servers.odoo import client as odoo_client

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"error": {"message": "session invalid"}}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with patch("mcp_servers.odoo.client.get_odoo_session", return_value="test-sess"), \
         patch("mcp_servers.odoo.client.reset_session_cache"):
        result = await odoo_client.get_invoices_due_data(mock_client, days=7)

    assert result == []


@pytest.mark.asyncio
async def test_client_get_invoices_due_auth_error():
    """get_invoices_due_data returns [] on auth error."""
    from mcp_servers.odoo import client as odoo_client
    from mcp_servers.odoo.auth import OdooAuthError

    mock_client = AsyncMock()

    with patch("mcp_servers.odoo.client.get_odoo_session", side_effect=OdooAuthError("denied")):
        result = await odoo_client.get_invoices_due_data(mock_client, days=7)

    assert result == []


@pytest.mark.asyncio
async def test_client_get_invoices_due_with_days_remaining():
    """get_invoices_due_data computes days_remaining correctly."""
    from mcp_servers.odoo import client as odoo_client
    from datetime import date, timedelta

    today = date.today()
    due_in_3 = (today + timedelta(days=3)).isoformat()

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "result": [
            {"id": 42, "partner_id": [5, "Beta Inc"], "amount_residual": 750.0,
             "invoice_date_due": due_in_3, "currency_id": [1, "USD"]},
        ]
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with patch("mcp_servers.odoo.client.get_odoo_session", return_value="test-sess"):
        result = await odoo_client.get_invoices_due_data(mock_client, days=7)

    assert len(result) == 1
    assert result[0]["invoice_id"] == 42
    assert result[0]["partner_name"] == "Beta Inc"
    assert 2 <= result[0]["days_remaining"] <= 4  # ±1 day for UTC vs local timezone


# -- ADDITIONAL ODOO SERVER COVERAGE TESTS ------------------------------------


@pytest.mark.asyncio
async def test_tool_get_gl_summary_exception_returns_is_error():
    """get_gl_summary tool returns isError on unexpected exception."""
    from mcp_servers.odoo.server import get_gl_summary

    with patch("mcp_servers.odoo.server.get_gl_summary_data") as mock_fn:
        mock_fn.side_effect = RuntimeError("DB connection lost")
        result = await get_gl_summary()

    assert result.get("isError") is True
    assert "DB connection lost" in result["content"]


@pytest.mark.asyncio
async def test_tool_get_invoices_due_empty_list():
    """get_invoices_due tool handles empty list from client."""
    from mcp_servers.odoo.server import get_invoices_due

    with patch("mcp_servers.odoo.server.get_invoices_due_data") as mock_fn:
        mock_fn.return_value = []
        result = await get_invoices_due(days_ahead=7)

    assert isinstance(result, dict)
    assert "isError" not in result
    content = json.loads(result["content"])
    assert content == []


@pytest.mark.asyncio
async def test_tool_get_invoices_due_negative_days():
    """get_invoices_due tool returns error for negative days_ahead."""
    from mcp_servers.odoo.server import get_invoices_due

    result = await get_invoices_due(days_ahead=-1)

    assert result.get("isError") is True
    assert "non-negative" in result["content"]


@pytest.mark.asyncio
async def test_tool_get_invoices_due_exception_returns_is_error():
    """get_invoices_due tool returns isError on unexpected exception."""
    from mcp_servers.odoo.server import get_invoices_due

    with patch("mcp_servers.odoo.server.get_invoices_due_data") as mock_fn:
        mock_fn.side_effect = Exception("Session expired")
        result = await get_invoices_due(days_ahead=7)

    assert result.get("isError") is True
    assert "Session expired" in result["content"]


@pytest.mark.asyncio
async def test_tool_get_ar_aging_exception_returns_is_error():
    """get_ar_aging tool returns isError on unexpected exception."""
    from mcp_servers.odoo.server import get_ar_aging

    with patch("mcp_servers.odoo.server.get_ar_aging_data") as mock_fn:
        mock_fn.side_effect = Exception("Unexpected DB error")
        result = await get_ar_aging()

    assert result.get("isError") is True
    assert "Unexpected DB error" in result["content"]


@pytest.mark.asyncio
async def test_tool_health_check_exception_returns_is_error():
    """health_check tool returns isError on unexpected exception."""
    from mcp_servers.odoo.server import health_check

    with patch("mcp_servers.odoo.server.health_check_odoo") as mock_fn:
        mock_fn.side_effect = Exception("Connection refused")
        result = await health_check()

    assert result.get("isError") is True
    assert "Connection refused" in result["content"]


@pytest.mark.asyncio
async def test_tool_get_gl_summary_success_content():
    """get_gl_summary returns JSON content with expected fields."""
    from mcp_servers.odoo.server import get_gl_summary

    gl_data = {"total_assets": 5000.0, "total_liabilities": 2000.0,
               "total_equity": 3000.0, "net_income": 1000.0}

    with patch("mcp_servers.odoo.server.get_gl_summary_data") as mock_fn:
        mock_fn.return_value = gl_data
        result = await get_gl_summary()

    content = json.loads(result["content"])
    assert content["total_assets"] == 5000.0
    assert content["net_income"] == 1000.0


@pytest.mark.asyncio
async def test_tool_get_ar_aging_success_content():
    """get_ar_aging returns JSON content with aging data."""
    from mcp_servers.odoo.server import get_ar_aging

    aging_data = {"total_receivable": 1500.0, "partners": [],
                  "buckets": {"0-30": 500.0, "31-60": 1000.0}}

    with patch("mcp_servers.odoo.server.get_ar_aging_data") as mock_fn:
        mock_fn.return_value = aging_data
        result = await get_ar_aging()

    content = json.loads(result["content"])
    assert content["total_receivable"] == 1500.0


@pytest.mark.asyncio
async def test_tool_health_check_success_content():
    """health_check returns JSON content with health data."""
    from mcp_servers.odoo.server import health_check

    health_data = {"healthy": True, "version": "17.0", "db": "h0_odoo"}

    with patch("mcp_servers.odoo.server.health_check_odoo") as mock_fn:
        mock_fn.return_value = health_data
        result = await health_check()

    content = json.loads(result["content"])
    assert content["healthy"] is True
    assert content["version"] == "17.0"


def test_error_helper_returns_correct_format():
    """_error returns dict with isError=True and JSON content."""
    from mcp_servers.odoo.server import _error

    result = _error("test error message")
    assert result["isError"] is True
    content = json.loads(result["content"])
    assert content["error"] == "test error message"
