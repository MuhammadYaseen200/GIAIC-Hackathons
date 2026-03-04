"""Contract tests for WhatsApp MCP server (T010).

Validates send_message and health_check tool outputs against
the contracts defined in whatsapp-tools.json.
"""

import json
from pathlib import Path
from typing import Literal

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACT_PATH = PROJECT_ROOT / "specs" / "008-hitl-whatsapp-silver" / "contracts" / "whatsapp-tools.json"


@pytest.fixture
def contract():
    """Load the WhatsApp MCP tool contract."""
    assert CONTRACT_PATH.exists(), f"Contract file not found: {CONTRACT_PATH}"
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def send_message_tool(contract):
    """Extract send_message tool definition."""
    tools = {t["name"]: t for t in contract["tools"]}
    assert "send_message" in tools
    return tools["send_message"]


@pytest.fixture
def health_check_tool(contract):
    """Extract health_check tool definition."""
    tools = {t["name"]: t for t in contract["tools"]}
    assert "health_check" in tools
    return tools["health_check"]


class TestSendMessageOutputSchema:
    """Validate send_message success output matches outputSchema."""

    def test_success_output_has_required_fields(self, send_message_tool):
        from mcp_servers.whatsapp.models import SendMessageResult

        result = SendMessageResult(
            message_id="msg_123",
            status="sent",
            sent_at="2026-03-02T14:30:22Z",
        )
        data = result.model_dump()

        required = send_message_tool["outputSchema"]["required"]
        for field in required:
            assert field in data, f"Missing required field: {field}"

    def test_status_is_valid_enum(self, send_message_tool):
        from mcp_servers.whatsapp.models import SendMessageResult

        result = SendMessageResult(
            message_id="msg_123",
            status="sent",
            sent_at="2026-03-02T14:30:22Z",
        )
        valid_statuses = send_message_tool["outputSchema"]["properties"]["status"]["enum"]
        assert result.status in valid_statuses


class TestErrorResponseFormat:
    """Validate error response has isError=True + JSON body with error/message."""

    def test_error_response_structure(self, contract):
        from mcp_servers.whatsapp.models import MCPError

        error = MCPError(error="send_failed", message="Bridge timeout")
        error_dict = error.model_dump()

        error_schema = contract["errorFormat"]["schema"]
        required_fields = error_schema["required"]
        for field in required_fields:
            assert field in error_dict, f"Missing required error field: {field}"

    def test_error_with_isError_flag(self):
        """Simulating what the server returns on error."""
        from mcp_servers.whatsapp.models import MCPError

        error = MCPError(error="send_failed", message="Connection refused")
        response = {"isError": True, "content": json.dumps(error.model_dump())}

        assert response["isError"] is True
        parsed = json.loads(response["content"])
        assert "error" in parsed
        assert "message" in parsed


class TestHealthCheckResponseShape:
    """Validate health_check returns correct response shape."""

    def test_health_check_result_shape(self, health_check_tool):
        from mcp_servers.whatsapp.models import HealthCheckResult

        result = HealthCheckResult(
            status="healthy",
            connected_number="+923001234567",
            backend="go_bridge",
            bridge_url="http://localhost:8080",
        )
        data = result.model_dump()

        required = health_check_tool["outputSchema"]["required"]
        for field in required:
            assert field in data, f"Missing required health_check field: {field}"

    def test_health_check_status_enum(self, health_check_tool):
        from mcp_servers.whatsapp.models import HealthCheckResult

        for status in ["healthy", "degraded", "down"]:
            result = HealthCheckResult(
                status=status,
                backend="go_bridge",
            )
            valid = health_check_tool["outputSchema"]["properties"]["status"]["enum"]
            assert result.status in valid


class TestMCPErrorCodeLiteral:
    """Validate error codes are limited to defined MCPErrorCode Literal values."""

    def test_all_error_codes_valid(self, contract):
        from mcp_servers.whatsapp.models import MCPError

        valid_codes = contract["errorFormat"]["schema"]["properties"]["error"]["enum"]

        for code in valid_codes:
            # Should not raise validation error
            error = MCPError(error=code, message=f"Test {code}")
            assert error.error == code

    def test_invalid_error_code_rejected(self):
        from pydantic import ValidationError
        from mcp_servers.whatsapp.models import MCPError

        with pytest.raises(ValidationError):
            MCPError(error="invalid_code_xyz", message="Should fail")
