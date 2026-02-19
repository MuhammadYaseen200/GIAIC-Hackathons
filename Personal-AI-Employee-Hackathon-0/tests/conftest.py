"""Shared test fixtures for the watcher test suite."""

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
