"""Unit tests for WhatsApp watcher (T009).

Tests process_item(), deduplication, Privacy Gate integration,
media handling, privacy alerts, and validate_prerequisites().
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@dataclass
class FakeRawMessage:
    """Minimal stand-in mirroring RawWhatsAppMessage fields."""

    message_id: str = "3EB0C767D61B84A12345"
    sender_number: str = "923001234567"
    sender_name: str | None = "Ahmed Khan"
    body: str = "Hello, can we schedule a meeting?"
    media_type: str = "text"
    caption: str | None = None
    received_at: str = "2026-03-02T14:30:22Z"


@pytest.fixture
def wa_vault(tmp_path):
    """Create vault directories for WhatsApp watcher tests."""
    vault = tmp_path / "vault"
    (vault / "Needs_Action").mkdir(parents=True)
    (vault / "Logs").mkdir(parents=True)
    return vault


@pytest.fixture
def mock_bridge_send():
    """Mock for WhatsApp MCP send_message (privacy alerts)."""
    return AsyncMock(return_value={"message_id": "sent_1", "status": "sent", "sent_at": "2026-03-02T14:31:00Z"})


@pytest.fixture
def watcher(wa_vault, mock_bridge_send, monkeypatch):
    """Create a WhatsAppWatcher instance with mocked dependencies."""
    monkeypatch.setenv("OWNER_WHATSAPP_NUMBER", "+923009876543")
    monkeypatch.setenv("WHATSAPP_BRIDGE_URL", "http://localhost:8080")
    monkeypatch.setenv("WHATSAPP_BACKEND", "go_bridge")

    from watchers.whatsapp_watcher import WhatsAppWatcher

    w = WhatsAppWatcher(
        name="whatsapp_watcher",
        poll_interval=60,
        vault_path=str(wa_vault),
    )
    w._send_privacy_alert = mock_bridge_send
    return w


class TestProcessItemWritesCorrectFilename:
    """process_item() writes correct filename format to vault/Needs_Action/."""

    @pytest.mark.asyncio
    async def test_filename_format(self, watcher, wa_vault):
        from watchers.whatsapp_watcher import RawWhatsAppMessage

        msg = RawWhatsAppMessage(
            message_id="3EB0C767D61B84A12345",
            sender_number="923001234567",
            sender_name="Ahmed Khan",
            body="Hello world",
            media_type="text",
            caption=None,
            received_at="2026-03-02T14:30:22Z",
        )
        await watcher.process_item(msg)

        files = list((wa_vault / "Needs_Action").glob("*-wa-3EB0C767D61B84A12345.md"))
        assert len(files) == 1, f"Expected 1 file, found {len(files)}"
        # Filename should start with YYYYMMDD-HHMMSS
        fname = files[0].name
        assert fname.endswith("-wa-3EB0C767D61B84A12345.md")
        # Verify YAML frontmatter in the file
        content = files[0].read_text(encoding="utf-8")
        assert "type: whatsapp_message" in content
        assert "sender_number:" in content
        assert "status: needs_action" in content


class TestDeduplication:
    """Same message_id does not create a second file."""

    @pytest.mark.asyncio
    async def test_duplicate_message_skipped(self, watcher, wa_vault):
        from watchers.whatsapp_watcher import RawWhatsAppMessage

        msg = RawWhatsAppMessage(
            message_id="DEDUP_TEST_001",
            sender_number="923001234567",
            sender_name="Test",
            body="First message",
            media_type="text",
            caption=None,
            received_at="2026-03-02T14:30:22Z",
        )
        await watcher.process_item(msg)
        await watcher.process_item(msg)  # duplicate

        files = list((wa_vault / "Needs_Action").glob("*-wa-DEDUP_TEST_001.md"))
        assert len(files) == 1, "Duplicate message should NOT create a second file"


class TestPrivacyGateCalledBeforeVaultWrite:
    """Privacy Gate is called BEFORE the vault file is written."""

    @pytest.mark.asyncio
    async def test_privacy_gate_called(self, wa_vault, monkeypatch):
        monkeypatch.setenv("OWNER_WHATSAPP_NUMBER", "+923009876543")
        monkeypatch.setenv("WHATSAPP_BRIDGE_URL", "http://localhost:8080")
        monkeypatch.setenv("WHATSAPP_BACKEND", "go_bridge")

        call_order = []

        original_run_privacy_gate = None
        from watchers import privacy_gate as pg_module

        original_run_privacy_gate = pg_module.run_privacy_gate

        def tracking_privacy_gate(body, media_type, caption=None):
            call_order.append("privacy_gate")
            return original_run_privacy_gate(body, media_type, caption)

        from watchers import utils as utils_module

        original_atomic_write = utils_module.atomic_write

        def tracking_atomic_write(filepath, content):
            call_order.append("atomic_write")
            return original_atomic_write(filepath, content)

        monkeypatch.setattr(
            "watchers.whatsapp_watcher.run_privacy_gate", tracking_privacy_gate
        )
        monkeypatch.setattr(
            "watchers.whatsapp_watcher.atomic_write", tracking_atomic_write
        )

        from watchers.whatsapp_watcher import RawWhatsAppMessage, WhatsAppWatcher

        w = WhatsAppWatcher(name="test_wa", poll_interval=60, vault_path=str(wa_vault))
        w._send_privacy_alert = AsyncMock()

        msg = RawWhatsAppMessage(
            message_id="PG_ORDER_TEST",
            sender_number="923001234567",
            sender_name="Test",
            body="My password: secret123",
            media_type="text",
            caption=None,
            received_at="2026-03-02T14:30:22Z",
        )
        await w.process_item(msg)

        # Privacy gate must be called before any atomic_write
        assert "privacy_gate" in call_order, "Privacy gate was never called"
        pg_idx = call_order.index("privacy_gate")
        aw_indices = [i for i, v in enumerate(call_order) if v == "atomic_write"]
        assert len(aw_indices) > 0, "atomic_write was never called"
        assert pg_idx < aw_indices[0], "Privacy gate must be called BEFORE atomic_write"


class TestMediaMessage:
    """Media message body is replaced with '[MEDIA - content not stored]'."""

    @pytest.mark.asyncio
    async def test_media_body_replaced(self, watcher, wa_vault):
        from watchers.whatsapp_watcher import RawWhatsAppMessage

        msg = RawWhatsAppMessage(
            message_id="MEDIA_TEST_001",
            sender_number="923001234567",
            sender_name="Test",
            body="some binary content",
            media_type="image",
            caption="A photo",
            received_at="2026-03-02T14:30:22Z",
        )
        await watcher.process_item(msg)

        files = list((wa_vault / "Needs_Action").glob("*-wa-MEDIA_TEST_001.md"))
        assert len(files) == 1
        content = files[0].read_text(encoding="utf-8")
        assert "[MEDIA" in content and "content not stored" in content


class TestPrivacyAlertSent:
    """Privacy alert is sent when redaction_applied=True."""

    @pytest.mark.asyncio
    async def test_alert_on_redaction(self, watcher, wa_vault, mock_bridge_send):
        from watchers.whatsapp_watcher import RawWhatsAppMessage

        msg = RawWhatsAppMessage(
            message_id="REDACT_ALERT_001",
            sender_number="923001234567",
            sender_name="Ahmed",
            body="My password: supersecret123",
            media_type="text",
            caption=None,
            received_at="2026-03-02T14:30:22Z",
        )
        await watcher.process_item(msg)

        mock_bridge_send.assert_called_once()
        alert_body = mock_bridge_send.call_args[1].get("body") or mock_bridge_send.call_args[0][1] if len(mock_bridge_send.call_args[0]) > 1 else mock_bridge_send.call_args[1].get("body", "")
        # Alert should NOT contain the original sensitive content
        assert "supersecret123" not in str(mock_bridge_send.call_args)

    @pytest.mark.asyncio
    async def test_alert_on_media_block(self, watcher, wa_vault, mock_bridge_send):
        from watchers.whatsapp_watcher import RawWhatsAppMessage

        msg = RawWhatsAppMessage(
            message_id="MEDIA_ALERT_001",
            sender_number="923001234567",
            sender_name="Ahmed",
            body="image data",
            media_type="image",
            caption=None,
            received_at="2026-03-02T14:30:22Z",
        )
        await watcher.process_item(msg)

        mock_bridge_send.assert_called_once()


class TestValidatePrerequisites:
    """validate_prerequisites() raises when OWNER_WHATSAPP_NUMBER missing."""

    def test_missing_owner_number_raises(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OWNER_WHATSAPP_NUMBER", raising=False)
        monkeypatch.setenv("WHATSAPP_BRIDGE_URL", "http://localhost:8080")
        monkeypatch.setenv("WHATSAPP_BACKEND", "go_bridge")

        from watchers.whatsapp_watcher import WhatsAppWatcher

        vault = tmp_path / "vault"
        (vault / "Needs_Action").mkdir(parents=True)
        (vault / "Logs").mkdir(parents=True)

        w = WhatsAppWatcher(
            name="test_wa", poll_interval=60, vault_path=str(vault)
        )
        with pytest.raises(Exception):  # PrerequisiteError or ValueError
            w.validate_prerequisites()
