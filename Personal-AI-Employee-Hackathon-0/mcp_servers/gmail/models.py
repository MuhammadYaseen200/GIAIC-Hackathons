"""Pydantic v2 I/O models for Gmail MCP tools.

Used for input validation (FastMCP auto-generates inputSchema from these)
and output schema documentation.
"""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

MCPErrorCode = Literal[
    "auth_required",
    "not_found",
    "rate_limited",
    "send_failed",
    "permission_denied",
    "internal_error",
]


class MCPError(BaseModel):
    """Standard error response returned by all Gmail MCP tools."""

    error: MCPErrorCode
    message: str
    details: Optional[dict] = None


class SendEmailInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    to: str = Field(..., description="Recipient email address", min_length=3)
    subject: str = Field(..., description="Email subject line", min_length=1)
    body: str = Field(..., description="Plain-text email body", min_length=1)
    reply_to_message_id: Optional[str] = Field(
        None,
        description="Gmail message ID to thread reply (sets In-Reply-To header)",
    )


class ListEmailsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        default="is:unread",
        description="Gmail search query (e.g. 'is:unread', 'from:boss@co.com')",
    )
    max_results: int = Field(
        default=10,
        description="Maximum number of results to return (1–100)",
        ge=1,
        le=100,
    )


class GetEmailInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    message_id: str = Field(
        ...,
        description="Gmail message ID from list_emails result",
        min_length=1,
    )


class MoveEmailInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    message_id: str = Field(
        ...,
        description="Gmail message ID to move",
        min_length=1,
    )
    destination_label: str = Field(
        ...,
        description="Target Gmail label (e.g. 'INBOX', 'DONE', 'AI_PROCESSED')",
        min_length=1,
    )


class AddLabelInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    message_id: str = Field(
        ...,
        description="Gmail message ID to label",
        min_length=1,
    )
    label_name: str = Field(
        ...,
        description="Label to apply (created automatically if it doesn't exist)",
        min_length=1,
    )
