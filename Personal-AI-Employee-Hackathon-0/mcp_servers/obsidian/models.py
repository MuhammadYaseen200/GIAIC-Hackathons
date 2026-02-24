"""Pydantic v2 I/O models for Obsidian MCP tools.

Used for input validation (FastMCP auto-generates inputSchema from these)
and output schema documentation.
"""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

MCPErrorCode = Literal[
    "not_found",
    "permission_denied",
    "parse_error",
    "internal_error",
]


class MCPError(BaseModel):
    """Standard error response returned by all Obsidian MCP tools."""

    error: MCPErrorCode
    message: str
    details: Optional[dict] = None


class ReadNoteInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    path: str = Field(
        ...,
        description="Vault-relative path, e.g. 'Needs_Action/email-001.md'",
        min_length=1,
    )


class WriteNoteInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    path: str = Field(
        ...,
        description="Vault-relative path (parent directories created if missing)",
        min_length=1,
    )
    frontmatter: dict = Field(
        ...,
        description="YAML frontmatter fields as a key-value dict",
    )
    body: str = Field(
        default="",
        description="Markdown body content (written after the frontmatter block)",
    )


class ListNotesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    directory: str = Field(
        ...,
        description="Vault-relative directory, e.g. 'Needs_Action'",
        min_length=1,
    )
    filter: Optional[str] = Field(
        None,
        description=(
            "Frontmatter filter in 'field:value' format (exact match), "
            "e.g. 'status:pending'"
        ),
    )


class MoveNoteInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source: str = Field(
        ...,
        description="Vault-relative source path",
        min_length=1,
    )
    destination: str = Field(
        ...,
        description="Vault-relative destination path",
        min_length=1,
    )


class SearchNotesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ...,
        description="Text to search for in notes (case-insensitive substring match)",
        min_length=1,
    )
