"""HITL Manager — vault-filesystem state machine for draft approval (T019).

Implements ADR-0011: HITLManager lifecycle controller.

State machine:
    pending → approved | rejected | awaiting_reminder | timed_out

Vault directories:
    vault/Pending_Approval/  — drafts awaiting owner decision
    vault/Approved/          — owner approved (Gmail MCP will send)
    vault/Rejected/          — owner rejected (not sent)
    vault/Logs/              — hitl_decisions.jsonl audit log

Draft ID format: <YYYYMMDD-HHMMSS>-<8-char-lowercase-hex>
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

# Priority emoji map (ADR-0011 §Batch Notification Protocol)
PRIORITY_EMOJI: dict[str, str] = {
    "HIGH": "\U0001f534",  # 🔴
    "MED":  "\U0001f7e1",  # 🟡
    "LOW":  "\U0001f7e2",  # 🟢
}


def _generate_draft_id() -> str:
    """Generate a collision-resistant draft ID.

    Format: <YYYYMMDD-HHMMSS>-<8-char-lowercase-hex>
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    suffix = secrets.token_hex(4)  # 8 hex chars
    return f"{ts}-{suffix}"


def _read_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter from a --- delimited markdown file."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 2:
            return yaml.safe_load(parts[1]) or {}
    return {}


def _read_body(path: Path) -> str:
    """Extract the body section (after second ---) of a frontmatter file."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


def _write_frontmatter_file(path: Path, frontmatter: dict, body: str = "") -> None:
    """Write a markdown file with YAML frontmatter."""
    content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{body}\n"
    path.write_text(content, encoding="utf-8")


def _update_frontmatter(path: Path, updates: dict) -> None:
    """Update specific keys in an existing frontmatter file (in-place)."""
    body = _read_body(path)
    fm = _read_frontmatter(path)
    fm.update(updates)
    _write_frontmatter_file(path, fm, body)


class HITLManager:
    """Human-in-the-Loop lifecycle controller for draft approval.

    Manages the vault-filesystem state machine:
        submit_draft → send_batch_notification → handle_owner_reply / check_timeouts

    Args:
        whatsapp_client: MCPClient with call_tool("send_message", ...) capability.
        gmail_client: MCPClient with call_tool("send_email", ...) capability.
        vault_path: Root vault directory (parent of Pending_Approval/, Approved/, etc.).
        owner_number: Owner's E.164 WhatsApp number for notifications.
        batch_delay_seconds: Seconds to accumulate drafts before notifying (0 = immediate).
        reminder_hours: Hours before sending a reminder (default 24).
        timeout_hours: Hours before marking draft timed_out (default 48).
        max_concurrent_drafts: Maximum drafts per batch notification.
    """

    def __init__(
        self,
        whatsapp_client: Any,
        gmail_client: Any,
        vault_path: Path,
        owner_number: str,
        batch_delay_seconds: int = 120,
        reminder_hours: int = 24,
        timeout_hours: int = 48,
        max_concurrent_drafts: int = 5,
    ) -> None:
        self._whatsapp = whatsapp_client
        self._gmail = gmail_client
        self._vault = Path(vault_path)
        self._owner_number = owner_number
        self._batch_delay = batch_delay_seconds
        self._reminder_hours = reminder_hours
        self._timeout_hours = timeout_hours
        self._max_drafts = max_concurrent_drafts

        # Vault sub-directories
        self._pending_dir = self._vault / "Pending_Approval"
        self._approved_dir = self._vault / "Approved"
        self._rejected_dir = self._vault / "Rejected"
        self._logs_dir = self._vault / "Logs"

        # Ensure directories exist
        for d in (self._pending_dir, self._approved_dir, self._rejected_dir, self._logs_dir):
            d.mkdir(parents=True, exist_ok=True)

        # In-memory notification queue (ADR-0011 §Concurrent Draft Handling)
        self._notification_queue: list[str] = []

    # -----------------------------------------------------------------------
    # T019-A: submit_draft — write draft to Pending_Approval/ with frontmatter
    # -----------------------------------------------------------------------

    async def submit_draft(
        self,
        recipient: str,
        subject: str,
        body: str,
        priority: str,
        risk_level: str = "low",
    ) -> str:
        """Write a draft to vault/Pending_Approval/ and queue for notification.

        Args:
            recipient: Target email address.
            subject: Email subject line.
            body: Draft email body text.
            priority: "HIGH" | "MED" | "LOW"
            risk_level: "low" | "medium" | "high"

        Returns:
            Unique draft_id (used for approve/reject commands).
        """
        draft_id = _generate_draft_id()

        # Collision guard — increment suffix until unique
        draft_path = self._pending_dir / f"{draft_id}.md"
        while draft_path.exists():
            draft_id = _generate_draft_id()
            draft_path = self._pending_dir / f"{draft_id}.md"

        now = datetime.now(timezone.utc).isoformat()
        frontmatter: dict = {
            "type": "approval_request",
            "status": "pending",
            "draft_id": draft_id,
            "recipient": recipient,
            "subject": subject,
            "priority": priority,
            "risk_level": risk_level,
            "reversible": False,
            "notified_at": None,
            "created_at": now,
        }
        _write_frontmatter_file(draft_path, frontmatter, body)

        # Queue for batch notification
        self._notification_queue.append(draft_id)
        return draft_id

    # -----------------------------------------------------------------------
    # T019-B: send_batch_notification — one WhatsApp summary for all pending
    # -----------------------------------------------------------------------

    async def send_batch_notification(self) -> None:
        """Send a single WhatsApp summary for all pending drafts.

        Format (ADR-0011):
            📋 N drafts pending:
            1. 🔴 [HIGH] <draft_id_short> — <recipient> — <subject>
            ...
            Reply: approve <draft_id> | reject <draft_id>
        """
        # Collect all pending drafts from filesystem
        pending = sorted(self._pending_dir.glob("*.md"))
        if not pending:
            return

        lines = [f"\U0001f4cb {len(pending)} draft(s) pending approval:\n"]
        now_iso = datetime.now(timezone.utc).isoformat()

        for i, path in enumerate(pending[: self._max_drafts], start=1):
            fm = _read_frontmatter(path)
            draft_id = fm.get("draft_id", path.stem)
            priority = fm.get("priority", "LOW")
            recipient = fm.get("recipient", "?")
            subject = fm.get("subject", "?")
            emoji = PRIORITY_EMOJI.get(priority, "\U0001f7e2")
            short_id = draft_id[-12:] if len(draft_id) > 12 else draft_id
            lines.append(f"{i}. {emoji} [{priority}] {short_id} — {recipient} — {subject}")

            # Update notified_at
            _update_frontmatter(path, {"notified_at": now_iso})

        lines.append(
            "\nReply: approve <draft_id> or reject <draft_id>"
        )

        message_body = "\n".join(lines)
        await self._whatsapp.call_tool(
            "send_message",
            {"to": self._owner_number, "body": message_body},
        )

        # Clear the queue after notification
        self._notification_queue.clear()

    # -----------------------------------------------------------------------
    # T019-C: handle_owner_reply — parse command and execute decision
    # -----------------------------------------------------------------------

    async def handle_owner_reply(self, message: str, sender: str) -> None:
        """Parse owner's WhatsApp reply and execute approve/reject/clarify.

        Commands (case-insensitive):
            approve <draft_id>  → send email + move to Approved/
            reject  <draft_id>  → skip email + move to Rejected/
            <anything else>     → send clarification message

        Args:
            message: Raw WhatsApp message text from owner.
            sender: E.164 sender number (used to verify owner).
        """
        text = message.strip().lower()

        if text.startswith("approve "):
            draft_id_fragment = message.strip().split(None, 1)[1].strip()
            await self._approve(draft_id_fragment, sender)

        elif text.startswith("reject "):
            draft_id_fragment = message.strip().split(None, 1)[1].strip()
            await self._reject(draft_id_fragment, sender)

        else:
            # Ambiguous reply — send clarification, no irreversible action
            await self._whatsapp.call_tool(
                "send_message",
                {
                    "to": self._owner_number,
                    "body": (
                        "I didn't understand that. Please reply:\n"
                        "  approve <draft_id>\n"
                        "  reject <draft_id>"
                    ),
                },
            )

    # -----------------------------------------------------------------------
    # T019-D: check_timeouts — 24h reminder / 48h timeout
    # -----------------------------------------------------------------------

    async def check_timeouts(self) -> None:
        """Check Pending_Approval/ for drafts past 24h / 48h thresholds.

        24h → status: awaiting_reminder, send WhatsApp reminder
        48h → status: timed_out (no email sent)
        """
        now = datetime.now(timezone.utc)
        reminder_delta = timedelta(hours=self._reminder_hours)
        timeout_delta = timedelta(hours=self._timeout_hours)

        for path in sorted(self._pending_dir.glob("*.md")):
            fm = _read_frontmatter(path)
            status = fm.get("status", "pending")
            created_at_str = fm.get("created_at")
            if not created_at_str:
                continue

            try:
                created_at = datetime.fromisoformat(created_at_str)
            except ValueError:
                continue

            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            age = now - created_at

            if age >= timeout_delta and status not in ("timed_out",):
                # 48h timeout — update status only, no email
                _update_frontmatter(path, {"status": "timed_out"})

            elif age >= reminder_delta and status == "pending":
                # 24h reminder — update status + send WhatsApp reminder
                _update_frontmatter(path, {"status": "awaiting_reminder"})
                draft_id = fm.get("draft_id", path.stem)
                subject = fm.get("subject", "?")
                await self._whatsapp.call_tool(
                    "send_message",
                    {
                        "to": self._owner_number,
                        "body": (
                            f"\U000023f0 Reminder: draft pending approval for 24+ hours.\n"
                            f"Draft: {draft_id}\nSubject: {subject}\n"
                            "Reply: approve <draft_id> or reject <draft_id>"
                        ),
                    },
                )

    # -----------------------------------------------------------------------
    # Internal: approve / reject actions
    # -----------------------------------------------------------------------

    async def _approve(self, draft_id: str, decided_by: str) -> None:
        """Approve a draft: send email via Gmail MCP + move to Approved/ + log."""
        draft_path = self._find_draft(draft_id)
        if draft_path is None:
            await self._whatsapp.call_tool(
                "send_message",
                {
                    "to": self._owner_number,
                    "body": f"Draft not found: {draft_id}. Please check the draft ID.",
                },
            )
            return

        fm = _read_frontmatter(draft_path)
        body = _read_body(draft_path)
        recipient = fm.get("recipient", "")
        subject = fm.get("subject", "")

        # Send email via Gmail MCP
        send_result = await self._gmail.call_tool(
            "send_email",
            {"to": recipient, "subject": subject, "body": body},
        )

        # Move to Approved/
        approved_path = self._approved_dir / draft_path.name
        _update_frontmatter(draft_path, {
            "status": "approved",
            "decided_at": datetime.now(timezone.utc).isoformat(),
            "decided_by": decided_by,
        })
        draft_path.rename(approved_path)

        # Audit log
        self._log_decision(
            draft_id=fm.get("draft_id", draft_path.stem),
            decision="approved",
            decided_by=decided_by,
            sent_at=send_result.get("sent_at") if isinstance(send_result, dict) else None,
        )

    async def _reject(self, draft_id: str, decided_by: str) -> None:
        """Reject a draft: move to Rejected/ + log (no email sent)."""
        draft_path = self._find_draft(draft_id)
        if draft_path is None:
            await self._whatsapp.call_tool(
                "send_message",
                {
                    "to": self._owner_number,
                    "body": f"Draft not found: {draft_id}. Please check the draft ID.",
                },
            )
            return

        fm = _read_frontmatter(draft_path)

        # Move to Rejected/
        rejected_path = self._rejected_dir / draft_path.name
        _update_frontmatter(draft_path, {
            "status": "rejected",
            "decided_at": datetime.now(timezone.utc).isoformat(),
            "decided_by": decided_by,
        })
        draft_path.rename(rejected_path)

        # Audit log (no email sent → sent_at is None)
        self._log_decision(
            draft_id=fm.get("draft_id", draft_path.stem),
            decision="rejected",
            decided_by=decided_by,
            sent_at=None,
        )

    def _find_draft(self, draft_id: str) -> Path | None:
        """Find a draft file in Pending_Approval/ matching draft_id (full or prefix).

        Supports:
        - Full draft_id match (filename stem)
        - Prefix match (first N chars of stem)
        - Frontmatter draft_id field match
        """
        # Exact filename match
        exact = self._pending_dir / f"{draft_id}.md"
        if exact.exists():
            return exact

        # Prefix / suffix match against filename stems
        draft_id_lower = draft_id.lower()
        for path in sorted(self._pending_dir.glob("*.md")):
            stem = path.stem.lower()
            if stem.startswith(draft_id_lower) or stem.endswith(draft_id_lower):
                return path
            # Check frontmatter draft_id field
            try:
                fm = _read_frontmatter(path)
                fid = (fm.get("draft_id") or "").lower()
                if fid == draft_id_lower or fid.startswith(draft_id_lower) or fid.endswith(draft_id_lower):
                    return path
            except Exception:
                continue

        return None

    def _log_decision(
        self,
        draft_id: str,
        decision: str,
        decided_by: str,
        sent_at: str | None,
    ) -> None:
        """Append a decision entry to vault/Logs/hitl_decisions.jsonl."""
        entry = {
            "draft_id": draft_id,
            "decision": decision,
            "decided_at": datetime.now(timezone.utc).isoformat(),
            "decided_by": decided_by,
            "sent_at": sent_at,
        }
        log_path = self._logs_dir / "hitl_decisions.jsonl"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
