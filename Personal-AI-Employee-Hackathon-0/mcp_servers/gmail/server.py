#!/usr/bin/env python3
"""Gmail MCP server — FastMCP entry point. Exposes Gmail tools over stdio JSON-RPC."""
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

from mcp_servers.gmail.auth import AuthRequiredError, get_gmail_service, reset_service_cache
from mcp_servers.gmail.models import (
    AddLabelInput,
    GetEmailInput,
    ListEmailsInput,
    MoveEmailInput,
    SendEmailInput,
)
from mcp_servers.gmail.tools import GmailTools

VAULT_PATH = Path(os.environ.get("VAULT_PATH", "./vault"))


@asynccontextmanager
async def lifespan(server):
    """Validate env and warm up Gmail service at startup."""
    for key in ["GMAIL_CREDENTIALS_PATH", "GMAIL_TOKEN_PATH"]:
        if not os.environ.get(key):
            raise EnvironmentError(f"Missing required env var: {key}")
    try:
        get_gmail_service()  # warm-up: validates token on startup
    except AuthRequiredError:
        pass  # health_check will report the error; don't crash server
    yield
    reset_service_cache()


mcp = FastMCP("gmail_mcp", lifespan=lifespan)
_tools = GmailTools(vault_path=VAULT_PATH)


@mcp.tool(
    name="health_check",
    annotations={
        "title": "Gmail MCP Health Check",
        "readOnlyHint": True,
        "destructiveHint": False,
    },
)
async def health_check() -> str:
    """Verify Gmail MCP server is operational and OAuth token is valid.

    Returns: JSON with status='ok' and authenticated_as email, or error object.
    """
    result = await _tools.health_check()
    return json.dumps(result)


@mcp.tool(
    name="send_email",
    annotations={
        "title": "Send Gmail Email",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
    },
)
async def send_email(params: SendEmailInput) -> str:
    """Send an email via authenticated Gmail account. Writes pre-action audit log first.

    Args: to (str), subject (str), body (str), reply_to_message_id (str|None)
    Returns: JSON with message_id, thread_id, sent_at — or error object.
    """
    result = await _tools.send_email(
        to=params.to,
        subject=params.subject,
        body=params.body,
        reply_to_message_id=params.reply_to_message_id,
    )
    return json.dumps(result)


@mcp.tool(
    name="list_emails",
    annotations={
        "title": "List Gmail Emails",
        "readOnlyHint": True,
        "idempotentHint": True,
    },
)
async def list_emails(params: ListEmailsInput) -> str:
    """List emails matching a Gmail search query.

    Args: query (str), max_results (int, 1-100)
    Returns: JSON with emails list and total_count — or error object.
    """
    result = await _tools.list_emails(query=params.query, max_results=params.max_results)
    return json.dumps(result)


@mcp.tool(
    name="get_email",
    annotations={
        "title": "Get Gmail Email",
        "readOnlyHint": True,
        "idempotentHint": True,
    },
)
async def get_email(params: GetEmailInput) -> str:
    """Get full email content by message ID.

    Args: message_id (str)
    Returns: JSON with id, subject, sender, to, date, body, has_attachments — or error object.
    """
    result = await _tools.get_email(message_id=params.message_id)
    return json.dumps(result)


@mcp.tool(
    name="move_email",
    annotations={
        "title": "Move Gmail Email",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
async def move_email(params: MoveEmailInput) -> str:
    """Move email to a destination Gmail label.

    Args: message_id (str), destination_label (str)
    Returns: JSON with moved=True, message_id, label — or error object.
    """
    result = await _tools.move_email(
        message_id=params.message_id,
        destination_label=params.destination_label,
    )
    return json.dumps(result)


@mcp.tool(
    name="add_label",
    annotations={
        "title": "Add Gmail Label",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
async def add_label(params: AddLabelInput) -> str:
    """Apply a Gmail label to an email. Creates the label if it doesn't exist.

    Args: message_id (str), label_name (str)
    Returns: JSON with labeled=True, message_id, label — or error object.
    """
    result = await _tools.add_label(
        message_id=params.message_id,
        label_name=params.label_name,
    )
    return json.dumps(result)


if __name__ == "__main__":
    mcp.run()
