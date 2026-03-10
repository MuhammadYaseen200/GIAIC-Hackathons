"""Integration tests for WhatsApp watcher (T011).

Full ingestion cycle with mocked Go bridge, verifying vault files,
YAML frontmatter, privacy_gate.jsonl logs, and atomic write guarantees.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest


@pytest.fixture
def integration_vault(tmp_path):
    """Create a full vault structure for integration tests."""
    vault = tmp_path / "vault"
    (vault / "Needs_Action").mkdir(parents=True)
    (vault / "Logs").mkdir(parents=True)
    (vault / "Pending_Approval").mkdir(parents=True)
    (vault / "Approved").mkdir(parents=True)
    (vault / "Rejected").mkdir(parents=True)
    return vault


def make_bridge_messages():
    """Two messages from the Go bridge, then empty on subsequent polls."""
    return [
        {
            "id": "MSG_INT_001",
            "from": "923001111111@s.whatsapp.net",
            "pushName": "Ali Hassan",
            "body": "Hi, can we meet tomorrow?",
            "type": "text",
            "caption": None,
            "timestamp": "2026-03-02T14:30:22Z",
        },
        {
            "id": "MSG_INT_002",
            "from": "923002222222@s.whatsapp.net",
            "pushName": "Sara Ahmed",
            "body": "Please check the attached image",
            "type": "image",
            "caption": "Project screenshot",
            "timestamp": "2026-03-02T14:31:00Z",
        },
    ]


@pytest.fixture
def mock_httpx_transport():
    """Mock httpx transport that returns bridge messages once, then empty."""
    call_count = {"n": 0}

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        if "/messages" in str(request.url):
            if call_count["n"] == 0:
                call_count["n"] += 1
                return httpx.Response(200, json=make_bridge_messages())
            return httpx.Response(200, json=[])
        if "/health" in str(request.url):
            return httpx.Response(200, json={"status": "ok", "number": "+15550001234"})
        if "/send" in str(request.url):
            return httpx.Response(200, json={"id": "sent_001", "status": "sent"})
        return httpx.Response(404)

    return httpx.MockTransport(mock_handler)


@pytest.fixture
def integration_watcher(integration_vault, mock_httpx_transport, monkeypatch):
    """Create a WhatsAppWatcher with mocked httpx transport."""
    monkeypatch.setenv("OWNER_WHATSAPP_NUMBER", "+15550009876")
    monkeypatch.setenv("WHATSAPP_BRIDGE_URL", "http://localhost:8080")
    monkeypatch.setenv("WHATSAPP_BACKEND", "go_bridge")

    from watchers.whatsapp_watcher import WhatsAppWatcher

    w = WhatsAppWatcher(
        name="whatsapp_watcher",
        poll_interval=60,
        vault_path=str(integration_vault),
    )
    w._http_client = httpx.AsyncClient(transport=mock_httpx_transport)
    # Mock the privacy alert sender to avoid real MCP calls
    w._send_privacy_alert = AsyncMock()
    return w


class TestFullIngestionCycle:
    """Run full ingestion cycle with 2 messages from mocked Go bridge."""

    @pytest.mark.asyncio
    async def test_two_messages_create_two_vault_files(
        self, integration_watcher, integration_vault
    ):
        from watchers.whatsapp_watcher import RawWhatsAppMessage

        messages = await integration_watcher.poll()
        assert len(messages) == 2

        for msg in messages:
            await integration_watcher.process_item(msg)

        needs_action = integration_vault / "Needs_Action"
        vault_files = list(needs_action.glob("*.md"))
        assert len(vault_files) == 2, f"Expected 2 vault files, got {len(vault_files)}"

    @pytest.mark.asyncio
    async def test_vault_files_have_correct_yaml_frontmatter(
        self, integration_watcher, integration_vault
    ):
        messages = await integration_watcher.poll()
        for msg in messages:
            await integration_watcher.process_item(msg)

        needs_action = integration_vault / "Needs_Action"
        vault_files = sorted(needs_action.glob("*.md"))

        for vf in vault_files:
            content = vf.read_text(encoding="utf-8")
            # Check required frontmatter fields
            assert "type: whatsapp_message" in content
            assert "sender_number:" in content
            assert "received_at:" in content
            assert "media_type:" in content
            assert "status: needs_action" in content

    @pytest.mark.asyncio
    async def test_media_message_has_blocked_body(
        self, integration_watcher, integration_vault
    ):
        messages = await integration_watcher.poll()
        for msg in messages:
            await integration_watcher.process_item(msg)

        needs_action = integration_vault / "Needs_Action"
        # The image message (MSG_INT_002) should have blocked body
        image_files = list(needs_action.glob("*-wa-MSG_INT_002.md"))
        assert len(image_files) == 1
        content = image_files[0].read_text(encoding="utf-8")
        assert "[MEDIA" in content and "content not stored" in content


class TestPrivacyGateLogging:
    """Verify privacy_gate.jsonl log entries are created."""

    @pytest.mark.asyncio
    async def test_privacy_log_entries_created(
        self, integration_watcher, integration_vault
    ):
        messages = await integration_watcher.poll()
        for msg in messages:
            await integration_watcher.process_item(msg)

        log_path = integration_vault / "Logs" / "privacy_gate.jsonl"
        assert log_path.exists(), "privacy_gate.jsonl should be created"

        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        entries = [json.loads(line) for line in lines if line.strip()]
        assert len(entries) >= 2, f"Expected at least 2 log entries, got {len(entries)}"

        # Check log entry fields
        for entry in entries:
            assert "message_id" in entry
            assert "sender_number" in entry
            assert "redaction_applied" in entry or "media_blocked" in entry
            assert "timestamp" in entry


class TestNoPartialFiles:
    """Verify atomic_write guarantees — no partial files on disk."""

    @pytest.mark.asyncio
    async def test_no_tmp_files_remain(
        self, integration_watcher, integration_vault
    ):
        messages = await integration_watcher.poll()
        for msg in messages:
            await integration_watcher.process_item(msg)

        needs_action = integration_vault / "Needs_Action"
        # No .tmp files should remain
        tmp_files = list(needs_action.glob("*.tmp"))
        assert len(tmp_files) == 0, f"Found partial/tmp files: {tmp_files}"

        # All files should be .md
        all_files = list(needs_action.iterdir())
        for f in all_files:
            assert f.suffix == ".md", f"Unexpected file: {f}"
