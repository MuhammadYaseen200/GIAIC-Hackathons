#!/usr/bin/env python3
"""Obsidian vault MCP server — FastMCP entry point. Direct filesystem access, no Obsidian app."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

from mcp_servers.obsidian.models import (
    ListNotesInput,
    MoveNoteInput,
    ReadNoteInput,
    SearchNotesInput,
    WriteNoteInput,
)
from mcp_servers.obsidian.tools import ObsidianTools

VAULT_PATH = Path(os.environ.get("VAULT_PATH", "./vault")).resolve()
if not VAULT_PATH.exists():
    raise EnvironmentError(
        f"VAULT_PATH does not exist: {VAULT_PATH}. Set VAULT_PATH in .env"
    )

mcp = FastMCP("obsidian_mcp")
_tools = ObsidianTools(vault_path=VAULT_PATH)


@mcp.tool(
    name="health_check",
    annotations={"title": "Obsidian MCP Health Check", "readOnlyHint": True},
)
async def health_check() -> str:
    """Verify Obsidian MCP server is operational and vault directory is accessible.

    Returns: JSON with status='ok', vault_path, note_count — or error object.
    """
    return json.dumps(await _tools.health_check())


@mcp.tool(
    name="read_note",
    annotations={"title": "Read Vault Note", "readOnlyHint": True, "idempotentHint": True},
)
async def read_note(params: ReadNoteInput) -> str:
    """Read a vault note by vault-relative path. Returns frontmatter dict and body text.

    Args: path (str) vault-relative, e.g. 'Needs_Action/email-001.md'
    Returns: JSON with path, frontmatter (dict), body (str) — or error object.
    """
    return json.dumps(await _tools.read_note(params.path))


@mcp.tool(
    name="write_note",
    annotations={
        "title": "Write Vault Note",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
async def write_note(params: WriteNoteInput) -> str:
    """Write a vault note atomically (temp+rename). Creates parent dirs if needed.

    Args: path (str), frontmatter (dict), body (str)
    Returns: written note content for round-trip verification — or error object.
    """
    return json.dumps(await _tools.write_note(params.path, params.frontmatter, params.body))


@mcp.tool(
    name="list_notes",
    annotations={"title": "List Vault Notes", "readOnlyHint": True, "idempotentHint": True},
)
async def list_notes(params: ListNotesInput) -> str:
    """List notes in vault directory, optionally filtered by frontmatter field:value.

    Args: directory (str), filter (str|None) e.g. 'status:pending'
    Returns: JSON with notes list (path entries) and count — or error object.
    """
    return json.dumps(await _tools.list_notes(params.directory, params.filter))


@mcp.tool(
    name="move_note",
    annotations={
        "title": "Move Vault Note",
        "readOnlyHint": False,
        "destructiveHint": False,
    },
)
async def move_note(params: MoveNoteInput) -> str:
    """Move a vault note from source to destination path.

    Args: source (str), destination (str) — both vault-relative
    Returns: JSON with moved=True, source, destination — or error object.
    """
    return json.dumps(await _tools.move_note(params.source, params.destination))


@mcp.tool(
    name="search_notes",
    annotations={"title": "Search Vault Notes", "readOnlyHint": True},
)
async def search_notes(params: SearchNotesInput) -> str:
    """Full-text search across all vault notes (case-insensitive substring).

    Args: query (str) — text to find in note body or frontmatter values
    Returns: JSON with notes list (path + snippet) and count — or error object.
    """
    return json.dumps(await _tools.search_notes(params.query))


if __name__ == "__main__":
    mcp.run()
