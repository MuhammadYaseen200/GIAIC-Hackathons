"""Tests for WhatsApp GoBridge, PywaStub, and MCP server tools."""

import importlib
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_servers.whatsapp.bridge import GoBridge, PywaStub, _to_jid
from mcp_servers.whatsapp.models import HealthCheckResult, SendMessageResult


# ── _to_jid tests ──────────────────────────────────────────────────────────────


class TestToJid:
    def test_strips_plus_from_number(self):
        assert _to_jid("+15550001234") == "15550001234@s.whatsapp.net"

    def test_no_plus_unchanged(self):
        assert _to_jid("15550001234") == "15550001234@s.whatsapp.net"


# ── GoBridge tests ─────────────────────────────────────────────────────────────


class TestGoBridgeSend:
    @pytest.mark.asyncio
    async def test_send_success_returns_result(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "msg_abc", "status": "sent"}

        with patch("mcp_servers.whatsapp.bridge.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_resp)
            MockClient.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            bridge = GoBridge()
            result = await bridge.send(to="+15550001234", body="Hello LinkedIn")

        assert isinstance(result, SendMessageResult)
        assert result.message_id == "msg_abc"
        assert result.status == "sent"

    @pytest.mark.asyncio
    async def test_send_non_200_raises_value_error(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"

        with patch("mcp_servers.whatsapp.bridge.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_resp)
            MockClient.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            bridge = GoBridge()
            with pytest.raises(ValueError, match="send_failed"):
                await bridge.send(to="+15550001234", body="Hello")


class TestGoBridgeHealth:
    @pytest.mark.asyncio
    async def test_health_returns_healthy_on_405(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 405

        with patch("mcp_servers.whatsapp.bridge.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_resp)
            MockClient.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            bridge = GoBridge()
            result = await bridge.health()

        assert isinstance(result, HealthCheckResult)
        assert result.status == "healthy"
        assert result.backend == "go_bridge"

    @pytest.mark.asyncio
    async def test_health_returns_healthy_on_200(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("mcp_servers.whatsapp.bridge.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_resp)
            MockClient.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            bridge = GoBridge()
            result = await bridge.health()

        assert result.status == "healthy"

    @pytest.mark.asyncio
    async def test_health_returns_unhealthy_on_exception(self):
        import httpx

        with patch("mcp_servers.whatsapp.bridge.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(
                side_effect=httpx.ConnectError("refused")
            )
            MockClient.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            bridge = GoBridge()
            result = await bridge.health()

        assert result.status == "unhealthy"
        assert result.backend == "go_bridge"


class TestPywaStub:
    @pytest.mark.asyncio
    async def test_send_raises_not_implemented(self):
        stub = PywaStub()
        with pytest.raises(NotImplementedError):
            await stub.send(to="+15550001234", body="hello")

    @pytest.mark.asyncio
    async def test_health_raises_not_implemented(self):
        stub = PywaStub()
        with pytest.raises(NotImplementedError):
            await stub.health()


# ── WhatsApp MCP server tests ──────────────────────────────────────────────────


class TestGetBridge:
    def test_get_bridge_returns_go_bridge(self, monkeypatch):
        monkeypatch.setenv("WHATSAPP_BACKEND", "go_bridge")
        import mcp_servers.whatsapp.server as srv

        importlib.reload(srv)
        bridge = srv._get_bridge()
        assert isinstance(bridge, GoBridge)

    def test_get_bridge_returns_pywa_stub(self, monkeypatch):
        monkeypatch.setenv("WHATSAPP_BACKEND", "pywa")
        import mcp_servers.whatsapp.server as srv

        importlib.reload(srv)
        bridge = srv._get_bridge()
        assert isinstance(bridge, PywaStub)

    def test_get_bridge_raises_on_unknown_backend(self, monkeypatch):
        monkeypatch.setenv("WHATSAPP_BACKEND", "unknown_backend")
        import mcp_servers.whatsapp.server as srv

        importlib.reload(srv)
        with pytest.raises(ValueError, match="Unknown WHATSAPP_BACKEND"):
            srv._get_bridge()


class TestServerSendMessage:
    @pytest.mark.asyncio
    async def test_send_message_success(self, monkeypatch):
        monkeypatch.setenv("WHATSAPP_BACKEND", "go_bridge")
        import mcp_servers.whatsapp.server as srv

        importlib.reload(srv)

        mock_result = SendMessageResult(
            message_id="msg_123", status="sent", sent_at="2026-03-02T10:00:00Z"
        )

        with patch.object(srv, "GoBridge") as MockBridge:
            instance = AsyncMock()
            instance.send = AsyncMock(return_value=mock_result)
            MockBridge.return_value = instance

            result = await srv.send_message(to="+15550001234", body="Test message")

        assert result["message_id"] == "msg_123"
        assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_message_returns_error_on_exception(self, monkeypatch):
        monkeypatch.setenv("WHATSAPP_BACKEND", "go_bridge")
        import mcp_servers.whatsapp.server as srv

        importlib.reload(srv)

        with patch.object(srv, "GoBridge") as MockBridge:
            instance = AsyncMock()
            instance.send = AsyncMock(side_effect=ValueError("send_failed: 500"))
            MockBridge.return_value = instance

            result = await srv.send_message(to="+15550001234", body="Test")

        assert result.get("isError") is True
        assert "send_failed" in result.get("content", "")


class TestServerHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_success(self, monkeypatch):
        monkeypatch.setenv("WHATSAPP_BACKEND", "go_bridge")
        import mcp_servers.whatsapp.server as srv

        importlib.reload(srv)

        mock_result = HealthCheckResult(
            status="healthy",
            connected_number=None,
            backend="go_bridge",
            bridge_url="http://localhost:8080",
        )

        with patch.object(srv, "GoBridge") as MockBridge:
            instance = AsyncMock()
            instance.health = AsyncMock(return_value=mock_result)
            MockBridge.return_value = instance

            result = await srv.health_check()

        assert result["status"] == "healthy"
        assert result["backend"] == "go_bridge"

    @pytest.mark.asyncio
    async def test_health_check_returns_error_on_exception(self, monkeypatch):
        monkeypatch.setenv("WHATSAPP_BACKEND", "go_bridge")
        import mcp_servers.whatsapp.server as srv

        importlib.reload(srv)

        with patch.object(srv, "GoBridge") as MockBridge:
            instance = AsyncMock()
            instance.health = AsyncMock(side_effect=Exception("bridge down"))
            MockBridge.return_value = instance

            result = await srv.health_check()

        assert result.get("isError") is True
