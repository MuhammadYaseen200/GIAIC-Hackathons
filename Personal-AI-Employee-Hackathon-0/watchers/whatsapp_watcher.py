"""WhatsApp watcher — ingests messages via Go bridge to vault (T015).

Inherits BaseWatcher. Implements poll(), process_item(), validate_prerequisites().
Per FR-001–FR-006, FR-031–FR-039, ADR-0001, ADR-0010.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from watchers.base_watcher import BaseWatcher
from watchers.privacy_gate import PrivacyLogEntry, run_privacy_gate
from watchers.utils import PrerequisiteError, atomic_write, render_yaml_frontmatter


@dataclass
class RawWhatsAppMessage:
    """Raw message from Go bridge REST response."""

    message_id: str
    sender_number: str
    sender_name: str | None
    body: str
    media_type: str  # "text" | "image" | "audio" | "video" | "document"
    caption: str | None
    received_at: str  # ISO 8601


class WhatsAppWatcher(BaseWatcher):
    """Monitors WhatsApp incoming messages via Go bridge.

    WHATSAPP_BACKEND=go_bridge -> polls GET http://localhost:8080/messages
    """

    def __init__(
        self,
        name: str = "whatsapp_watcher",
        poll_interval: int = 60,
        vault_path: str = "vault",
    ) -> None:
        super().__init__(name=name, poll_interval=poll_interval, vault_path=vault_path)
        self._bridge_url = os.getenv("WHATSAPP_BRIDGE_URL", "http://localhost:8080")
        self._owner_number = os.getenv("OWNER_WHATSAPP_NUMBER", "")
        self._last_message_id: str = ""
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Return or create the httpx client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def poll(self) -> list[RawWhatsAppMessage]:
        """Fetch new incoming messages from the Go bridge."""
        client = await self._get_http_client()
        params = {}
        if self._last_message_id:
            params["since"] = self._last_message_id

        resp = await client.get(f"{self._bridge_url}/messages", params=params)
        resp.raise_for_status()

        raw_messages = resp.json()
        messages = []
        for msg in raw_messages:
            sender = msg.get("from", "")
            # Strip JID suffix if present
            if "@" in sender:
                sender = sender.split("@")[0]

            messages.append(
                RawWhatsAppMessage(
                    message_id=msg["id"],
                    sender_number=sender,
                    sender_name=msg.get("pushName"),
                    body=msg.get("body", ""),
                    media_type=msg.get("type", "text"),
                    caption=msg.get("caption"),
                    received_at=msg.get("timestamp", datetime.now(timezone.utc).isoformat()),
                )
            )

        if messages:
            self._last_message_id = messages[-1].message_id

        return messages

    async def process_item(self, item: Any) -> None:
        """Process a single WhatsApp message: Privacy Gate -> dedup -> vault write."""
        msg: RawWhatsAppMessage = item

        # Step 1: Privacy Gate (MUST be first — FR-031)
        pg_result = run_privacy_gate(
            body=msg.body,
            media_type=msg.media_type,
            caption=msg.caption,
        )

        # Step 2: Deduplication check (FR-005)
        needs_action_dir = self.vault_path / "Needs_Action"
        existing = list(needs_action_dir.glob(f"*-wa-{msg.message_id}.md"))
        if existing:
            return  # Already processed — skip

        # Step 3: Build vault note
        try:
            received_dt = datetime.fromisoformat(msg.received_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            received_dt = datetime.now(timezone.utc)

        filename = f"{received_dt.strftime('%Y%m%d-%H%M%S')}-wa-{msg.message_id}.md"

        frontmatter = {
            "type": "whatsapp_message",
            "message_id": msg.message_id,
            "sender_number": msg.sender_number,
            "sender_name": msg.sender_name,
            "received_at": msg.received_at,
            "media_type": msg.media_type,
            "source": "known",
            "status": "needs_action",
            "privacy_redacted": pg_result.redaction_applied or pg_result.media_blocked,
        }

        body_text = pg_result.body
        sender_display = msg.sender_name or msg.sender_number

        content = render_yaml_frontmatter(frontmatter)
        content += f"\n# WhatsApp Message\n\n"
        content += f"**From**: {sender_display} ({msg.sender_number})\n"
        content += f"**Received**: {msg.received_at}\n\n"
        content += body_text + "\n"

        # Step 4: Atomic write to vault (FR-003, FR-040)
        vault_file = needs_action_dir / filename
        atomic_write(vault_file, content)

        # Step 5: Privacy gate log (FR-039)
        log_entry = PrivacyLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            media_blocked=pg_result.media_blocked,
            redaction_applied=pg_result.redaction_applied,
            patterns_matched=pg_result.patterns_matched,
            source="whatsapp",
        )
        # Add message-specific fields
        log_dict = log_entry.to_dict()
        log_dict["message_id"] = msg.message_id
        log_dict["sender_number"] = msg.sender_number

        log_path = self.vault_path / "Logs" / "privacy_gate.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_dict) + "\n")

        # Step 6: Privacy alert if redaction occurred (FR-033)
        if pg_result.redaction_applied or pg_result.media_blocked:
            alert_msg = (
                f"⚠️ Private/sensitive content detected in message from "
                f"{sender_display}. Stored as REDACTED. "
                f"AI did NOT read or process this."
            )
            await self._send_privacy_alert(
                to=self._owner_number,
                body=alert_msg,
            )

    async def _send_privacy_alert(self, to: str, body: str) -> None:
        """Send a privacy alert via WhatsApp MCP send_message.

        This method is monkey-patched in tests to avoid real MCP calls.
        In production, it would call the WhatsApp MCP server.
        """
        try:
            client = await self._get_http_client()
            jid = to.lstrip("+") + "@s.whatsapp.net"
            await client.post(
                f"{self._bridge_url}/send",
                json={"to": jid, "body": body},
            )
        except Exception:
            # Log but don't fail the main process
            pass

    def validate_prerequisites(self) -> None:
        """Check OWNER_WHATSAPP_NUMBER is set."""
        owner = os.getenv("OWNER_WHATSAPP_NUMBER", "")
        if not owner:
            raise PrerequisiteError(
                "OWNER_WHATSAPP_NUMBER not set in environment. "
                "Add it to .env file in E.164 format (e.g., +15550001234).",
                ht_reference="HT-004",
            )
