"""Shared HITL approval check for all social MCP servers."""
from __future__ import annotations
import json
import os

_HITL_REQUIRED_ERROR = {
    "isError": True,
    "content": json.dumps({
        "error": "HITL_REQUIRED",
        "message": "Social posting requires human approval. Submit via social_poster.py workflow.",
    }),
}


def check_hitl_approval() -> dict | None:
    """Return error dict if HITL not approved; None if approved.

    Approval requires H0_HITL_APPROVED=1 environment variable,
    which social_poster.py sets only after human WhatsApp confirmation.
    Directory-existence checks are intentionally NOT used — they are
    trivially bypassable by any agent creating the directory.
    """
    if os.environ.get("H0_HITL_APPROVED") == "1":
        return None
    return _HITL_REQUIRED_ERROR
