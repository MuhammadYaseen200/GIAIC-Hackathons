"""Shared test fixtures for the watcher and orchestrator test suites."""

import base64
import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from watchers.models import Classification, EmailItem


@pytest.fixture
def tmp_vault(tmp_path):
    """Create a temporary vault directory with canonical structure."""
    vault = tmp_path / "vault"
    (vault / "Needs_Action").mkdir(parents=True)
    (vault / "Inbox").mkdir(parents=True)
    (vault / "Logs").mkdir(parents=True)
    (vault / "Done").mkdir(parents=True)
    return vault


@pytest.fixture
def sample_email_item():
    """Pre-built EmailItem for testing."""
    return EmailItem(
        message_id="msg_abc123",
        sender="alice@example.com",
        recipients=["bob@example.com"],
        subject="Meeting Follow-up: Q1 Review",
        body="Hi Bob,\n\nPlease review the attached Q1 report.\n\nThanks,\nAlice",
        date="2026-02-17T10:30:00Z",
        labels=["INBOX", "UNREAD"],
        classification=Classification.ACTIONABLE,
        has_attachments=True,
        raw_size=4096,
    )


@pytest.fixture
def sample_informational_email():
    """Pre-built informational EmailItem."""
    return EmailItem(
        message_id="msg_news456",
        sender="newsletter@techdigest.com",
        recipients=["user@example.com"],
        subject="Weekly Tech Newsletter - Issue #42",
        body="This week in tech...\n\nUnsubscribe: link",
        date="2026-02-17T08:00:00Z",
        labels=["INBOX", "UNREAD"],
        classification=Classification.INFORMATIONAL,
        has_attachments=False,
        raw_size=2048,
    )


@pytest.fixture
def sample_raw_gmail_message():
    """Raw Gmail API message dict matching messages.get(format='full') response."""
    body_text = "Hi Bob,\n\nPlease review the attached Q1 report.\n\nThanks,\nAlice"
    encoded_body = base64.urlsafe_b64encode(body_text.encode()).decode()

    return {
        "id": "msg_abc123",
        "threadId": "thread_xyz",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "Please review the attached Q1 report.",
        "payload": {
            "mimeType": "multipart/mixed",
            "headers": [
                {"name": "From", "value": "Alice <alice@example.com>"},
                {"name": "To", "value": "bob@example.com"},
                {"name": "Subject", "value": "Meeting Follow-up: Q1 Review"},
                {"name": "Date", "value": "Mon, 17 Feb 2026 10:30:00 +0000"},
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": encoded_body, "size": len(body_text)},
                },
                {
                    "mimeType": "application/pdf",
                    "filename": "Q1_Report.pdf",
                    "body": {"attachmentId": "att_001", "size": 102400},
                },
            ],
        },
        "sizeEstimate": 4096,
    }


@pytest.fixture
def mock_gmail_service():
    """Mocked google-api-python-client Gmail service Resource."""
    service = MagicMock()

    # messages().list()
    list_result = {
        "messages": [{"id": "msg_abc123", "threadId": "thread_xyz"}],
        "resultSizeEstimate": 1,
    }
    service.users().messages().list().execute.return_value = list_result

    # messages().get()
    service.users().messages().get().execute.return_value = {
        "id": "msg_abc123",
        "labelIds": ["INBOX", "UNREAD"],
        "payload": {
            "headers": [
                {"name": "From", "value": "alice@example.com"},
                {"name": "To", "value": "bob@example.com"},
                {"name": "Subject", "value": "Test Email"},
                {"name": "Date", "value": "Mon, 17 Feb 2026 10:30:00 +0000"},
            ],
            "parts": [],
        },
        "sizeEstimate": 1024,
    }

    return service


@pytest.fixture
def mock_env(tmp_path):
    """Create a temp .env with credential paths and set env vars."""
    creds_path = tmp_path / "credentials.json"
    token_path = tmp_path / "token.json"

    # Write a minimal credentials.json
    creds_path.write_text(json.dumps({
        "installed": {
            "client_id": "test-id.apps.googleusercontent.com",
            "client_secret": "test-secret",
            "redirect_uris": ["http://localhost"],
        }
    }))

    env_file = tmp_path / ".env"
    env_file.write_text(
        f"GMAIL_CREDENTIALS_PATH={creds_path}\n"
        f"GMAIL_TOKEN_PATH={token_path}\n"
    )

    # Set environment variables
    os.environ["GMAIL_CREDENTIALS_PATH"] = str(creds_path)
    os.environ["GMAIL_TOKEN_PATH"] = str(token_path)

    yield {
        "env_file": env_file,
        "credentials_path": creds_path,
        "token_path": token_path,
    }

    # Cleanup
    os.environ.pop("GMAIL_CREDENTIALS_PATH", None)
    os.environ.pop("GMAIL_TOKEN_PATH", None)


# =============================================================================
# Phase 3: Ralph Wiggum Orchestrator fixtures
# =============================================================================

_PENDING_EMAIL_FRONTMATTER = """\
---
type: email
status: pending
source: gmail
message_id: test_msg_001
from: Sarah Li <sarah@example.com>
subject: Product Roadmap Discussion
date_received: Thu, 19 Feb 2026 21:02:14 +0000
date_processed: '2026-02-19T21:24:44.000000+00:00'
classification: actionable
priority: standard
has_attachments: false
watcher: gmail_watcher
---
Hi,

I wanted to follow up on our product roadmap discussion from last week.
Could you share the updated timeline for Q2 features?

Best,
Sarah
"""


@pytest.fixture
def tmp_vault_dir(tmp_path):
    """Temporary vault directory with canonical orchestrator sub-structure.

    Creates: Needs_Action/, Logs/, Done/, Drafts/, Inbox/
    This mirrors the production vault layout used by RalphWiggumOrchestrator.
    """
    vault = tmp_path / "vault"
    for subdir in ("Needs_Action", "Logs", "Done", "Drafts", "Inbox"):
        (vault / subdir).mkdir(parents=True)
    return vault


@pytest.fixture
def mock_email_file(tmp_vault_dir):
    """A valid vault markdown file with status: pending in Needs_Action/.

    Returns the Path to the created file.
    """
    email_path = tmp_vault_dir / "Needs_Action" / "test_msg_001.md"
    email_path.write_text(_PENDING_EMAIL_FRONTMATTER, encoding="utf-8")
    return email_path


@pytest.fixture
def mock_llm_decision_json():
    """Minimal valid LLMDecision JSON string — 'archive' decision."""
    return json.dumps({
        "decision": "archive",
        "confidence": 0.92,
        "reasoning": "This is a newsletter with no action required.",
        "reply_body": None,
        "delegation_target": None,
        "info_needed": None,
    })


@pytest.fixture
def mock_llm_draft_reply_json():
    """Valid LLMDecision JSON string — 'draft_reply' decision."""
    return json.dumps({
        "decision": "draft_reply",
        "confidence": 0.85,
        "reasoning": "Email requires a direct response about the roadmap timeline.",
        "reply_body": (
            "Hi Sarah,\n\nThank you for following up. "
            "I'll share the updated Q2 timeline by end of week.\n\nBest regards"
        ),
        "delegation_target": None,
        "info_needed": None,
    })


@pytest.fixture
def mock_llm_delegate_json():
    """Valid LLMDecision JSON string — 'delegate' decision."""
    return json.dumps({
        "decision": "delegate",
        "confidence": 0.78,
        "reasoning": "This falls under the engineering team's scope.",
        "reply_body": None,
        "delegation_target": "Engineering Manager — roadmap decisions are their domain.",
        "info_needed": None,
    })


@pytest.fixture
def mock_llm_needs_info_json():
    """Valid LLMDecision JSON string — 'needs_info' decision."""
    return json.dumps({
        "decision": "needs_info",
        "confidence": 0.60,
        "reasoning": "Cannot triage without knowing which product line this refers to.",
        "reply_body": None,
        "delegation_target": None,
        "info_needed": "Which specific product line and Q2 milestone is this about?",
    })
