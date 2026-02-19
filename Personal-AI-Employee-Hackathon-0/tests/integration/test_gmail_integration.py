"""Integration tests for the full Gmail watcher pipeline -- T097-T102.

Tests the full email-to-vault cycle: fetch → parse → classify → route.
All Gmail API calls are mocked; real filesystem, classification, and
state management run against a temporary vault.
"""

from __future__ import annotations

import asyncio
import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from watchers.gmail_watcher import GmailWatcher
from watchers.models import Classification


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_raw_email(
    msg_id: str,
    subject: str,
    sender: str,
    body: str,
    date: str = "Mon, 17 Feb 2026 10:00:00 +0000",
) -> dict:
    """Build a minimal raw Gmail API message dict (single text/plain part)."""
    encoded = base64.urlsafe_b64encode(body.encode()).decode()
    return {
        "id": msg_id,
        "threadId": f"thread_{msg_id}",
        "labelIds": ["INBOX", "UNREAD"],
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": sender},
                {"name": "To", "value": "me@example.com"},
                {"name": "Subject", "value": subject},
                {"name": "Date", "value": date},
            ],
            "body": {"data": encoded, "size": len(body)},
        },
        "sizeEstimate": len(body),
    }


def _vault_files(vault: Path) -> tuple[list[Path], list[Path]]:
    """Return (needs_action_files, inbox_files)."""
    na = list((vault / "Needs_Action").glob("*.md"))
    inbox = list((vault / "Inbox").glob("*.md"))
    return na, inbox


def _make_watcher(tmp_vault, mock_env) -> GmailWatcher:
    """Instantiate a GmailWatcher with temp paths."""
    return GmailWatcher(
        vault_path=str(tmp_vault),
        credentials_path=str(mock_env["credentials_path"]),
        token_path=str(mock_env["token_path"]),
    )


# ── T097 [P]: Full email cycle ────────────────────────────────────────────────


class TestFullEmailCycle:
    """T097: Mock Gmail returns 3 emails (2 actionable, 1 informational).
    Run full poll+process cycle. Verify 2 files in Needs_Action/, 1 in Inbox/,
    all with correct YAML frontmatter."""

    @pytest.mark.asyncio
    async def test_full_cycle_routes_and_formats_correctly(
        self, tmp_vault, mock_env
    ):
        raw_messages = [
            _make_raw_email(
                "full_001",
                "Action Required: Please Review Contract",
                "boss@company.com",
                "Please review the attached contract ASAP.",
            ),
            _make_raw_email(
                "full_002",
                "Urgent: Invoice Payment Due",
                "billing@vendor.com",
                "Invoice payment due tomorrow. Please approve.",
            ),
            _make_raw_email(
                "full_003",
                "Weekly Newsletter - Tech Digest",
                "noreply@newsletter.com",
                "This week in tech news. Unsubscribe here.",
            ),
        ]

        watcher = _make_watcher(tmp_vault, mock_env)
        watcher._fetch_unread_emails = AsyncMock(return_value=raw_messages)

        items = await watcher.poll()
        assert len(items) == 3

        for item in items:
            await watcher.process_item(item)

        na_files, inbox_files = _vault_files(tmp_vault)
        assert len(na_files) == 2, f"Expected 2 actionable files, got {len(na_files)}"
        assert len(inbox_files) == 1, f"Expected 1 informational file, got {len(inbox_files)}"

        # Verify YAML frontmatter on all files
        for filepath in na_files + inbox_files:
            content = filepath.read_text()
            parts = content.split("---\n", 2)
            assert len(parts) >= 3, f"Missing frontmatter in {filepath.name}"
            fm = yaml.safe_load(parts[1])

            assert fm["type"] == "email"
            assert fm["status"] == "pending"
            assert fm["source"] == "gmail"
            assert fm["watcher"] == "gmail_watcher"
            assert fm["priority"] == "standard"
            assert "message_id" in fm
            assert "classification" in fm


# ── T098 [P]: Duplicate prevention ───────────────────────────────────────────


class TestDuplicatePreventionAcrossCycles:
    """T098: Mock Gmail returns same 3 emails across 5 poll cycles.
    Verify exactly 3 files created total -- zero duplicates."""

    @pytest.mark.asyncio
    async def test_no_duplicates_over_five_cycles(self, tmp_vault, mock_env):
        raw_messages = [
            _make_raw_email(
                "dup_001",
                "Urgent: Approve Project Budget",
                "finance@company.com",
                "Please approve the budget ASAP.",
            ),
            _make_raw_email(
                "dup_002",
                "Please Review Legal Document",
                "legal@company.com",
                "Review and sign required.",
            ),
            _make_raw_email(
                "dup_003",
                "Monthly Newsletter - Platform Updates",
                "noreply@platform.com",
                "Monthly automated digest. Unsubscribe.",
            ),
        ]

        watcher = _make_watcher(tmp_vault, mock_env)
        watcher._fetch_unread_emails = AsyncMock(return_value=raw_messages)

        for cycle in range(5):
            items = await watcher.poll()
            for item in items:
                await watcher.process_item(item)

        na_files, inbox_files = _vault_files(tmp_vault)
        total = len(na_files) + len(inbox_files)
        assert total == 3, (
            f"Expected exactly 3 files after 5 cycles, got {total} "
            f"(duplicates present)"
        )

        # processed_ids should contain exactly 3 entries
        assert len(watcher.state.processed_ids) == 3


# ── T099 [P]: State persistence across restart ───────────────────────────────


class TestStatePersistenceAcrossRestart:
    """T099: Process emails, save state, create new watcher instance,
    load state, poll same emails -- verify zero new files created."""

    @pytest.mark.asyncio
    async def test_no_reprocessing_after_restart(self, tmp_vault, mock_env):
        raw_messages = [
            _make_raw_email(
                "persist_001",
                "Action Required: Sign the Form",
                "hr@company.com",
                "Please sign and submit ASAP.",
            ),
            _make_raw_email(
                "persist_002",
                "Automated Daily Digest",
                "digest@service.com",
                "Your daily digest. Unsubscribe.",
            ),
        ]

        # Instance 1: process emails and save state
        watcher1 = _make_watcher(tmp_vault, mock_env)
        watcher1._fetch_unread_emails = AsyncMock(return_value=raw_messages)

        items1 = await watcher1.poll()
        for item in items1:
            await watcher1.process_item(item)
        watcher1._save_state()

        na_before, inbox_before = _vault_files(tmp_vault)
        total_before = len(na_before) + len(inbox_before)
        assert total_before == 2  # both emails processed

        # Instance 2: simulates restart -- loads saved state
        watcher2 = _make_watcher(tmp_vault, mock_env)
        watcher2._load_state()
        watcher2._fetch_unread_emails = AsyncMock(return_value=raw_messages)

        items2 = await watcher2.poll()
        assert len(items2) == 0, (
            f"Expected 0 items after restart (all already processed), "
            f"got {len(items2)}"
        )

        na_after, inbox_after = _vault_files(tmp_vault)
        total_after = len(na_after) + len(inbox_after)
        assert total_after == total_before, (
            "No new files should be created after restart with same emails"
        )


# ── T100 [P]: Classification routing accuracy ─────────────────────────────────


class TestClassificationRoutingAccuracy:
    """T100: 10 test emails (5 clearly actionable, 5 clearly informational).
    Verify correct routing for all 10 (>=80% accuracy per SC-005)."""

    @pytest.mark.asyncio
    async def test_ten_email_routing_accuracy(self, tmp_vault, mock_env):
        actionable_raw = [
            _make_raw_email(
                "act_001",
                "Action Required: Approve Q1 Budget",
                "cfo@company.com",
                "Please approve the Q1 budget by the deadline.",
            ),
            _make_raw_email(
                "act_002",
                "Urgent: Invoice Payment Overdue",
                "billing@vendor.com",
                "Invoice payment is overdue. Please respond ASAP.",
            ),
            _make_raw_email(
                "act_003",
                "Please Review and Sign Contract",
                "legal@company.com",
                "Sign and return the attached contract.",
            ),
            _make_raw_email(
                "act_004",
                "Follow Up: Meeting Confirmation Required",
                "assistant@company.com",
                "Please confirm the meeting schedule.",
            ),
            _make_raw_email(
                "act_005",
                "Submit Expense Report by Friday Deadline",
                "finance@company.com",
                "Submit your expense report urgently.",
            ),
        ]
        informational_raw = [
            _make_raw_email(
                "inf_001",
                "Weekly Newsletter - Tech Industry Digest",
                "noreply@techdigest.com",
                "This week's tech news digest. Unsubscribe here.",
            ),
            _make_raw_email(
                "inf_002",
                "Monthly Summary: Platform Update Notification",
                "noreply@platform.com",
                "Automated monthly notification. No reply needed.",
            ),
            _make_raw_email(
                "inf_003",
                "Daily Digest: Morning News Roundup",
                "digest@newsfeed.com",
                "Your automated daily digest. Unsubscribe.",
            ),
            _make_raw_email(
                "inf_004",
                "Automated Alert: Scheduled Report Generated",
                "notifications@analytics.com",
                "Your automated weekly report is ready.",
            ),
            _make_raw_email(
                "inf_005",
                "Newsletter: Monthly Product Updates",
                "newsletter@product.com",
                "Monthly newsletter. Do not reply. Unsubscribe below.",
            ),
        ]

        watcher = _make_watcher(tmp_vault, mock_env)
        watcher._fetch_unread_emails = AsyncMock(
            return_value=actionable_raw + informational_raw
        )

        items = await watcher.poll()
        assert len(items) == 10, f"Expected 10 items, got {len(items)}"

        for item in items:
            await watcher.process_item(item)

        na_files, inbox_files = _vault_files(tmp_vault)
        total = len(na_files) + len(inbox_files)
        assert total == 10, f"Expected 10 files total, got {total}"

        # >=80% accuracy target (SC-005): at least 4/5 each
        assert len(na_files) >= 4, (
            f"Expected >=4 actionable in Needs_Action/, got {len(na_files)}"
        )
        assert len(inbox_files) >= 4, (
            f"Expected >=4 informational in Inbox/, got {len(inbox_files)}"
        )


# ── T101: Error recovery mid-cycle ───────────────────────────────────────────


class TestErrorRecoveryMidCycle:
    """T101: process_item fails for 2nd email of 5. Verify: 1st email processed,
    2nd not in processed_ids (retry-exhausted), 3rd-5th processed, error logged."""

    @pytest.mark.asyncio
    async def test_continues_after_process_item_failure(
        self, tmp_vault, mock_env
    ):
        raw_messages = [
            _make_raw_email("err_001", "Action Required: Approve Budget", "cfo@co.com", "Please approve."),
            _make_raw_email("err_002", "Urgent: Sign the Contract", "legal@co.com", "Sign now."),
            _make_raw_email("err_003", "Follow Up: Meeting Confirmation", "hr@co.com", "Confirm meeting."),
            _make_raw_email("err_004", "Submit Report by Deadline", "mgr@co.com", "Submit report."),
            _make_raw_email("err_005", "Please Review Invoice", "billing@co.com", "Review invoice."),
        ]

        watcher = _make_watcher(tmp_vault, mock_env)
        watcher._fetch_unread_emails = AsyncMock(return_value=raw_messages)

        # Replace process_item to always fail for err_002
        original_process = watcher.process_item.__func__  # unbound method

        async def failing_process_item(item):
            if item.message_id == "err_002":
                raise IOError("Simulated disk failure on 2nd email")
            return await original_process(watcher, item)

        watcher.process_item = failing_process_item

        with patch("watchers.base_watcher.asyncio.sleep", new_callable=AsyncMock):
            await watcher._run_poll_cycle()

        na_files, inbox_files = _vault_files(tmp_vault)
        total_files = len(na_files) + len(inbox_files)

        # 4 emails succeeded (1 failed), loop continues per base_watcher design
        assert total_files == 4, (
            f"Expected 4 files (1 failure), got {total_files}"
        )

        # Failed email NOT in processed_ids (not added since process_item raised)
        assert "err_002" not in watcher.state.processed_ids, (
            "Failed email should not be in processed_ids"
        )

        # Error was counted in state
        assert watcher.state.error_count >= 1

        # process_error was logged
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = tmp_vault / "Logs" / f"gmail_watcher_{today}.log"
        assert log_path.exists(), "Log file should exist after error"
        log_content = log_path.read_text()
        assert "process_error" in log_content


# ── T102: Concurrent lock prevention ──────────────────────────────────────────


class TestConcurrentLockPrevention:
    """T102: First watcher acquires lock, second watcher raises RuntimeError
    when attempting to acquire the same lock."""

    def test_second_instance_raises_on_lock_contention(
        self, tmp_vault, mock_env
    ):
        watcher1 = _make_watcher(tmp_vault, mock_env)
        watcher2 = _make_watcher(tmp_vault, mock_env)

        # First watcher acquires the vault lock
        watcher1._acquire_lock()

        try:
            # Second watcher must fail to acquire the same lock
            with pytest.raises(RuntimeError, match="[Ll]ock"):
                watcher2._acquire_lock()
        finally:
            # Always release so cleanup succeeds
            watcher1._release_lock()
