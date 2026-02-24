"""Unit tests for MCPClient fallback protocol (orchestrator/mcp_client.py)."""
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from orchestrator.mcp_client import MCPClient, MCPUnavailableError


@pytest.fixture
def client(tmp_path):
    return MCPClient("test_server", ["python3", "fake_server.py"], tmp_path)


@pytest.mark.asyncio
async def test_fallback_called_when_mcp_fails(client, tmp_path):
    """When MCP fails, fallback is called and mcp_fallback is logged."""
    with patch.object(client, "_invoke_tool", side_effect=RuntimeError("MCP down")):
        fallback_called = False

        async def fallback():
            nonlocal fallback_called
            fallback_called = True
            return {"result": "fallback_ok"}

        result = await client.call_tool("read_note", {"path": "test.md"}, fallback=fallback)

        assert fallback_called, "Fallback must be called when MCP fails"
        assert result == {"result": "fallback_ok"}

        # Verify mcp_fallback log was written
        log_files = list(tmp_path.glob("Logs/mcp_fallback_*.jsonl"))
        assert log_files, "mcp_fallback log file must be created"
        entry = json.loads(log_files[0].read_text().strip())
        assert entry["event"] == "mcp_fallback"
        assert entry["server"] == "test_server"
        assert entry["tool"] == "read_note"
        assert entry["severity"] == "WARNING"


@pytest.mark.asyncio
async def test_mcp_unavailable_raised_when_no_fallback(client):
    """When MCP fails and no fallback provided, MCPUnavailableError is raised."""
    with patch.object(client, "_invoke_tool", side_effect=RuntimeError("MCP down")):
        with pytest.raises(MCPUnavailableError):
            await client.call_tool("read_note", {"path": "test.md"}, fallback=None)


@pytest.mark.asyncio
async def test_escalation_logged_when_fallback_fails(client, tmp_path):
    """When both MCP and fallback fail, mcp_escalation is logged."""
    with patch.object(client, "_invoke_tool", side_effect=RuntimeError("MCP down")):

        async def failing_fallback():
            raise RuntimeError("Fallback also failed")

        with pytest.raises(MCPUnavailableError):
            await client.call_tool("send_email", {}, fallback=failing_fallback)

        log_files = list(tmp_path.glob("Logs/mcp_fallback_*.jsonl"))
        assert log_files, "Log file must exist"
        entries = [
            json.loads(line)
            for line in log_files[0].read_text().strip().splitlines()
            if line.strip()
        ]
        events = [e["event"] for e in entries]
        assert "mcp_fallback" in events, "mcp_fallback event must be logged"
        assert "mcp_escalation" in events, "mcp_escalation event must be logged"


@pytest.mark.asyncio
async def test_success_no_fallback_called(client):
    """When MCP succeeds, fallback is NOT called."""
    with patch.object(client, "_invoke_tool", return_value={"message_id": "msg-1"}):
        fallback_called = False

        def fallback():
            nonlocal fallback_called
            fallback_called = True

        result = await client.call_tool("send_email", {}, fallback=fallback)

        assert not fallback_called, "Fallback must NOT be called on MCP success"
        assert result["message_id"] == "msg-1"


@pytest.mark.asyncio
async def test_sync_fallback_supported(client):
    """Sync (non-async) fallback callables are supported."""
    with patch.object(client, "_invoke_tool", side_effect=RuntimeError("MCP down")):

        def sync_fallback():
            return {"result": "sync_fallback_ok"}

        result = await client.call_tool("some_tool", {}, fallback=sync_fallback)
        assert result == {"result": "sync_fallback_ok"}


@pytest.mark.asyncio
async def test_fallback_result_wraps_non_dict(client):
    """Non-dict fallback return value is wrapped in {result: ...}."""
    with patch.object(client, "_invoke_tool", side_effect=RuntimeError("MCP down")):

        def fallback():
            return "string_result"

        result = await client.call_tool("some_tool", {}, fallback=fallback)
        assert result == {"result": "string_result"}


@pytest.mark.asyncio
async def test_timeout_triggers_fallback(client, tmp_path):
    """Timeout triggers fallback and logs mcp_fallback."""
    import asyncio

    async def slow_invoke(tool_name, arguments):
        await asyncio.sleep(10)
        return {}

    with patch.object(client, "_invoke_tool", side_effect=slow_invoke):
        fallback_called = False

        async def fallback():
            nonlocal fallback_called
            fallback_called = True
            return {"result": "timeout_fallback"}

        result = await client.call_tool(
            "slow_tool", {}, fallback=fallback, timeout=0.01
        )

        assert fallback_called, "Fallback must be called on timeout"
        assert result == {"result": "timeout_fallback"}


@pytest.mark.asyncio
async def test_log_contains_error_detail(client, tmp_path):
    """mcp_fallback log entry must include the error string."""
    with patch.object(client, "_invoke_tool", side_effect=RuntimeError("Connection refused")):
        with pytest.raises(MCPUnavailableError):
            await client.call_tool("any_tool", {})

        log_files = list(tmp_path.glob("Logs/mcp_fallback_*.jsonl"))
        entry = json.loads(log_files[0].read_text().strip())
        assert "Connection refused" in entry["error"]
