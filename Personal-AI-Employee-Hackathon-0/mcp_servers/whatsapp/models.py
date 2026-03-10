"""Pydantic v2 models for WhatsApp MCP server (T012).

Defines input/output models for send_message and health_check tools,
plus shared MCPError model using ADR-0008 error taxonomy.
"""

from typing import Literal

from pydantic import BaseModel

MCPErrorCode = Literal[
    "auth_required",
    "not_found",
    "rate_limited",
    "permission_denied",
    "parse_error",
    "send_failed",
    "mcp_unavailable",
    "internal_error",
]


class SendMessageInput(BaseModel):
    to: str  # E.164 format e.g. +15550001234
    body: str  # max 4096 chars


class SendMessageResult(BaseModel):
    message_id: str
    status: str
    sent_at: str


class HealthCheckResult(BaseModel):
    status: str
    connected_number: str | None = None
    backend: str
    bridge_url: str | None = None


class MCPError(BaseModel):
    error: MCPErrorCode
    message: str
    details: dict | None = None
