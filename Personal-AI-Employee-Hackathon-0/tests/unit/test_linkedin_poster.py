"""Unit tests for linkedin_poster.py workflow.

Written RED before implementation — covers state transitions per spec.
"""
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("OWNER_WHATSAPP_NUMBER", "+921234567890")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


@pytest.mark.asyncio
async def test_draft_workflow_creates_vault_file(mock_env, tmp_path):
    """--draft creates vault file and sends WhatsApp notification."""
    from orchestrator.linkedin_poster import draft_and_notify

    with patch("orchestrator.linkedin_poster.run_privacy_gate") as pg:
        pg.return_value = MagicMock(media_blocked=False)
        with patch(
            "orchestrator.linkedin_poster._draft_post_content",
            new_callable=AsyncMock,
            return_value="AI is transforming development...",
        ):
            with patch(
                "orchestrator.linkedin_poster._send_hitl_notification",
                new_callable=AsyncMock,
            ):
                with patch(
                    "orchestrator.linkedin_poster._count_today_posts", return_value=0
                ):
                    with patch(
                        "orchestrator.linkedin_poster.VAULT_PENDING",
                        tmp_path / "Pending_Approval",
                    ):
                        (tmp_path / "Pending_Approval").mkdir(parents=True)
                        result = await draft_and_notify("test topic")
                        assert result["status"] == "drafted"
                        files = list(
                            (tmp_path / "Pending_Approval").glob("*_linkedin_*.md")
                        )
                        assert len(files) == 1


@pytest.mark.asyncio
async def test_privacy_gate_blocks_topic(mock_env):
    """PrivacyGate blocks sensitive topic → status=privacy_blocked, no vault file."""
    from orchestrator.linkedin_poster import draft_and_notify

    with patch("orchestrator.linkedin_poster.run_privacy_gate") as pg:
        pg.return_value = MagicMock(media_blocked=True)
        result = await draft_and_notify("my credit card number is 1234")
        assert result["status"] == "privacy_blocked"


@pytest.mark.asyncio
async def test_rate_limit_queues_for_tomorrow(mock_env):
    """Rate limit (>=1 post today) → status=rate_limited, no new draft."""
    from orchestrator.linkedin_poster import draft_and_notify

    with patch("orchestrator.linkedin_poster.run_privacy_gate") as pg:
        pg.return_value = MagicMock(media_blocked=False)
        with patch("orchestrator.linkedin_poster._count_today_posts", return_value=1):
            result = await draft_and_notify("AI topic")
            assert result["status"] == "rate_limited"


@pytest.mark.asyncio
async def test_publish_approved_post(mock_env, tmp_path):
    """Approved post → linkedin_mcp.post_update called → status=published, move_to_done called."""
    from orchestrator.linkedin_poster import publish_approved

    draft_path = tmp_path / "2026-03-05T090000_linkedin_test.md"
    draft_path.write_text("---\nstatus: approved\ntopic: test\n---\nHello LinkedIn\n")
    with patch(
        "orchestrator.linkedin_poster._call_post_update",
        new_callable=AsyncMock,
        return_value={"post_id": "urn:li:share:123"},
    ):
        with patch("orchestrator.linkedin_poster._log_event"):
            with patch("orchestrator.linkedin_poster.update_frontmatter"):
                with patch(
                    "orchestrator.linkedin_poster.move_to_done"
                ) as mock_move_done:
                    result = await publish_approved(draft_path)
                    assert result["status"] == "published"
                    mock_move_done.assert_called_once()


@pytest.mark.asyncio
async def test_rejected_post_moves_to_rejected(mock_env, tmp_path):
    """Rejected post → status=rejected, file moved to vault/Rejected/."""
    from orchestrator.linkedin_poster import handle_rejected

    draft_path = tmp_path / "2026-03-05T090000_linkedin_test.md"
    draft_path.write_text("---\nstatus: rejected\ntopic: test\n---\n")
    with patch("orchestrator.linkedin_poster._log_event"):
        with patch("orchestrator.linkedin_poster.update_frontmatter"):
            with patch(
                "orchestrator.linkedin_poster._move_to_rejected"
            ) as mock_rej:
                result = await handle_rejected(draft_path)
                assert result["status"] == "rejected"
                mock_rej.assert_called_once()


@pytest.mark.asyncio
async def test_auto_mode_picks_random_topic(mock_env):
    """--auto reads topic file and picks a random topic."""
    from orchestrator.linkedin_poster import run_auto_mode

    with patch(
        "orchestrator.linkedin_poster._load_topics",
        return_value=["Topic A", "Topic B", "Topic C"],
    ):
        with patch(
            "orchestrator.linkedin_poster.draft_and_notify",
            new_callable=AsyncMock,
            return_value={"status": "drafted"},
        ) as mock_draft:
            await run_auto_mode()
            assert mock_draft.called
            topic_used = mock_draft.call_args[0][0]
            assert topic_used in ["Topic A", "Topic B", "Topic C"]


@pytest.mark.asyncio
async def test_linkedin_api_error_graceful_degradation(mock_env, tmp_path):
    """LinkedIn API error on publish → status=api_error, draft not deleted."""
    from mcp_servers.linkedin.client import LinkedInAPIError
    from orchestrator.linkedin_poster import publish_approved

    draft_path = tmp_path / "2026-03-05T090000_linkedin_test.md"
    draft_path.write_text("---\nstatus: approved\ntopic: test\n---\nHello LinkedIn\n")
    with patch(
        "orchestrator.linkedin_poster._call_post_update",
        side_effect=LinkedInAPIError(503, "Service unavailable"),
    ):
        with patch("orchestrator.linkedin_poster._log_event"):
            with patch("orchestrator.linkedin_poster.update_frontmatter"):
                result = await publish_approved(draft_path)
                assert result["status"] == "api_error"
                assert draft_path.exists()  # Not deleted on error


@pytest.mark.asyncio
async def test_vault_item_type_linkedin_triggers_draft(mock_env, tmp_path):
    """Vault item with type=linkedin_post triggers draft; non-matching files are skipped (T029)."""
    from orchestrator.linkedin_poster import process_linkedin_vault_triggers

    needs_action = tmp_path / "Needs_Action"
    done_dir = tmp_path / "Done"
    needs_action.mkdir()
    done_dir.mkdir()

    # LinkedIn trigger
    trigger = needs_action / "2026-03-08T090000_linkedin_trigger.md"
    trigger.write_text(
        "---\ntype: linkedin_post\ntopic: milestone reached\nstatus: pending\n---\n"
    )
    # Non-matching item (should be skipped)
    other = needs_action / "2026-03-08T090001_email_task.md"
    other.write_text(
        "---\ntype: email_task\ntopic: some email\nstatus: pending\n---\n"
    )

    with patch(
        "orchestrator.linkedin_poster.draft_and_notify",
        new_callable=AsyncMock,
        return_value={"status": "drafted"},
    ) as mock_draft:
        await process_linkedin_vault_triggers(needs_action, done_dir)
        mock_draft.assert_called_once_with("milestone reached")
        # LinkedIn trigger moved to Done
        assert not trigger.exists()
        assert (done_dir / trigger.name).exists()
        # Non-matching file stays in Needs_Action
        assert other.exists()
        assert not (done_dir / other.name).exists()


@pytest.mark.asyncio
async def test_vault_item_hashtag_linkedin_triggers_draft(mock_env, tmp_path):
    """Vault item with #linkedin tag also triggers draft (T031)."""
    from orchestrator.linkedin_poster import process_linkedin_vault_triggers

    needs_action = tmp_path / "Needs_Action"
    done_dir = tmp_path / "Done"
    needs_action.mkdir()
    done_dir.mkdir()

    trigger = needs_action / "2026-03-08T090000_tagged_item.md"
    trigger.write_text(
        "---\ntype: task\ntags: ['#linkedin', '#automation']\ntopic: Python automation\nstatus: pending\n---\n"
    )

    with patch(
        "orchestrator.linkedin_poster.draft_and_notify",
        new_callable=AsyncMock,
        return_value={"status": "drafted"},
    ) as mock_draft:
        await process_linkedin_vault_triggers(needs_action, done_dir)
        mock_draft.assert_called_once_with("Python automation")
        assert not trigger.exists()


# ── NEW TESTS: check_pending_approvals() — previously zero coverage ─────────────


@pytest.mark.asyncio
async def test_check_pending_approvals_approved_post(tmp_path):
    """check_pending_approvals calls publish_approved for status=approved files."""
    from orchestrator.linkedin_poster import check_pending_approvals

    draft = tmp_path / "2026-03-09T090000_linkedin_test.md"
    draft.write_text("---\ntype: linkedin_post\nstatus: approved\ntopic: test\n---\nHello LinkedIn\n")

    with patch("orchestrator.linkedin_poster.VAULT_PENDING", tmp_path):
        with patch(
            "orchestrator.linkedin_poster.publish_approved",
            new_callable=AsyncMock,
            return_value={"status": "published"},
        ) as mock_pub:
            await check_pending_approvals()
            mock_pub.assert_called_once_with(draft)


@pytest.mark.asyncio
async def test_check_pending_approvals_rejected_post(tmp_path):
    """check_pending_approvals calls handle_rejected for status=rejected files."""
    from orchestrator.linkedin_poster import check_pending_approvals

    draft = tmp_path / "2026-03-09T090000_linkedin_test.md"
    draft.write_text("---\ntype: linkedin_post\nstatus: rejected\ntopic: test\n---\nHello\n")

    with patch("orchestrator.linkedin_poster.VAULT_PENDING", tmp_path):
        with patch(
            "orchestrator.linkedin_poster.handle_rejected",
            new_callable=AsyncMock,
            return_value={"status": "rejected"},
        ) as mock_rej:
            await check_pending_approvals()
            mock_rej.assert_called_once_with(draft)


@pytest.mark.asyncio
async def test_check_pending_approvals_expired_draft(tmp_path):
    """check_pending_approvals expires pending drafts past expires_at."""
    from orchestrator.linkedin_poster import check_pending_approvals

    expired_ts = time.time() - 100  # already expired
    draft = tmp_path / "2026-03-09T090000_linkedin_test.md"
    draft.write_text(
        f"---\ntype: linkedin_post\nstatus: pending_approval\ntopic: test\nexpires_at: {expired_ts}\n---\nHello\n"
    )

    with patch("orchestrator.linkedin_poster.VAULT_PENDING", tmp_path):
        with patch(
            "orchestrator.linkedin_poster.handle_rejected",
            new_callable=AsyncMock,
            return_value={"status": "rejected"},
        ) as mock_rej:
            with patch("orchestrator.linkedin_poster._log_event"):
                await check_pending_approvals()
                mock_rej.assert_called_once_with(draft)


@pytest.mark.asyncio
async def test_check_pending_approvals_not_yet_expired(tmp_path):
    """check_pending_approvals does NOT expire drafts that are still pending."""
    from orchestrator.linkedin_poster import check_pending_approvals

    future_ts = time.time() + 86400  # 24h from now
    draft = tmp_path / "2026-03-09T090000_linkedin_test.md"
    draft.write_text(
        f"---\ntype: linkedin_post\nstatus: pending_approval\ntopic: test\nexpires_at: {future_ts}\n---\nHello\n"
    )

    with patch("orchestrator.linkedin_poster.VAULT_PENDING", tmp_path):
        with patch(
            "orchestrator.linkedin_poster.publish_approved",
            new_callable=AsyncMock,
        ) as mock_pub:
            with patch(
                "orchestrator.linkedin_poster.handle_rejected",
                new_callable=AsyncMock,
            ) as mock_rej:
                await check_pending_approvals()
                mock_pub.assert_not_called()
                mock_rej.assert_not_called()


@pytest.mark.asyncio
async def test_check_pending_approvals_empty_dir(tmp_path):
    """check_pending_approvals handles empty vault gracefully."""
    from orchestrator.linkedin_poster import check_pending_approvals

    with patch("orchestrator.linkedin_poster.VAULT_PENDING", tmp_path):
        # Must not raise
        await check_pending_approvals()


@pytest.mark.asyncio
async def test_check_pending_approvals_missing_dir():
    """check_pending_approvals handles non-existent vault dir gracefully."""
    from orchestrator.linkedin_poster import check_pending_approvals

    nonexistent = Path("/tmp/nonexistent_vault_pending_xyz123")
    with patch("orchestrator.linkedin_poster.VAULT_PENDING", nonexistent):
        await check_pending_approvals()  # Must not raise


# ── NEW TESTS: publish_approved() — AuthRequiredError + file_not_found ──────────


@pytest.mark.asyncio
async def test_publish_approved_auth_required_error(mock_env, tmp_path):
    """publish_approved handles AuthRequiredError: updates frontmatter, logs, returns auth_error."""
    from mcp_servers.linkedin.auth import AuthRequiredError
    from orchestrator.linkedin_poster import publish_approved

    draft_path = tmp_path / "2026-03-09T090000_linkedin_test.md"
    draft_path.write_text("---\nstatus: approved\ntopic: test\n---\nHello LinkedIn\n")

    with patch(
        "orchestrator.linkedin_poster._call_post_update",
        side_effect=AuthRequiredError("Token expired"),
    ):
        with patch("orchestrator.linkedin_poster._log_event") as mock_log:
            with patch("orchestrator.linkedin_poster.update_frontmatter") as mock_fm:
                result = await publish_approved(draft_path)
                assert result["status"] == "auth_error"
                # frontmatter updated to auth_error
                mock_fm.assert_called_once()
                call_args = mock_fm.call_args[0]
                assert call_args[1].get("status") == "auth_error"
                # event logged
                mock_log.assert_called()


@pytest.mark.asyncio
async def test_publish_approved_file_not_found(mock_env, tmp_path):
    """publish_approved returns error status when draft file is missing."""
    from orchestrator.linkedin_poster import publish_approved

    missing_path = tmp_path / "nonexistent_linkedin_draft.md"
    result = await publish_approved(missing_path)
    assert result["status"] == "error"
    assert result["reason"] == "file_not_found"


# ── NEW TESTS: draft_and_notify() — LLM failure + content privacy gate ──────────


@pytest.mark.asyncio
async def test_draft_workflow_llm_failure_returns_error(mock_env, tmp_path):
    """LLM draft failure → status=error, no vault file created."""
    from orchestrator.linkedin_poster import draft_and_notify

    with patch("orchestrator.linkedin_poster.run_privacy_gate") as pg:
        pg.return_value = MagicMock(media_blocked=False)
        with patch("orchestrator.linkedin_poster._count_today_posts", return_value=0):
            with patch(
                "orchestrator.linkedin_poster._draft_post_content",
                new_callable=AsyncMock,
                side_effect=Exception("API credits exhausted"),
            ):
                with patch(
                    "orchestrator.linkedin_poster.VAULT_PENDING",
                    tmp_path / "Pending_Approval",
                ):
                    (tmp_path / "Pending_Approval").mkdir(parents=True)
                    result = await draft_and_notify("AI agents")
                    assert result["status"] == "error"
                    assert "LLM error" in result["reason"]
                    # No vault file should be created
                    files = list(
                        (tmp_path / "Pending_Approval").glob("*_linkedin_*.md")
                    )
                    assert len(files) == 0


@pytest.mark.asyncio
async def test_draft_workflow_privacy_gate_blocks_generated_content(mock_env, tmp_path):
    """Privacy gate blocks AI-generated content (Step 4) → privacy_blocked, no vault file."""
    from orchestrator.linkedin_poster import draft_and_notify

    call_count = 0

    def pg_side_effect(text, media_type):
        nonlocal call_count
        call_count += 1
        # First call (topic check) passes, second call (content check) blocks
        if call_count == 1:
            return MagicMock(media_blocked=False)
        return MagicMock(media_blocked=True)

    with patch("orchestrator.linkedin_poster.run_privacy_gate", side_effect=pg_side_effect):
        with patch("orchestrator.linkedin_poster._count_today_posts", return_value=0):
            with patch(
                "orchestrator.linkedin_poster._draft_post_content",
                new_callable=AsyncMock,
                return_value="My account number is 1234-5678",  # sensitive
            ):
                with patch(
                    "orchestrator.linkedin_poster.VAULT_PENDING",
                    tmp_path / "Pending_Approval",
                ):
                    (tmp_path / "Pending_Approval").mkdir(parents=True)
                    result = await draft_and_notify("safe topic")
                    assert result["status"] == "privacy_blocked"
                    assert result["reason"] == "content_blocked"
                    assert call_count == 2  # Both gates were called
                    # No vault file
                    files = list(
                        (tmp_path / "Pending_Approval").glob("*_linkedin_*.md")
                    )
                    assert len(files) == 0


# ── D-004: draft_id field + HITL routing fix ─────────────────────────────────


@pytest.mark.asyncio
async def test_write_draft_vault_file_includes_draft_id(tmp_path):
    """_write_draft_vault_file returns (path, draft_id) and frontmatter has draft_id field."""
    import yaml
    from orchestrator.linkedin_poster import _write_draft_vault_file

    pending = tmp_path / "Pending_Approval"
    pending.mkdir()

    with patch("orchestrator.linkedin_poster.VAULT_PENDING", pending):
        path, draft_id = _write_draft_vault_file("AI automation topic", "Post body content")
        assert path.exists()
        assert draft_id  # non-empty string
        text = path.read_text()
        parts = text.split("---", 2)
        fm = yaml.safe_load(parts[1])
        assert fm["draft_id"] == draft_id
        assert fm["type"] == "linkedin_post"


@pytest.mark.asyncio
async def test_draft_and_notify_returns_draft_id_in_log(mock_env, tmp_path):
    """draft_and_notify result includes draft_id in vault file frontmatter."""
    import yaml
    from orchestrator.linkedin_poster import draft_and_notify

    pending = tmp_path / "Pending_Approval"
    pending.mkdir()

    with patch("orchestrator.linkedin_poster.run_privacy_gate") as pg:
        pg.return_value = MagicMock(media_blocked=False)
        with patch(
            "orchestrator.linkedin_poster._draft_post_content",
            new_callable=AsyncMock,
            return_value="Test post content",
        ):
            with patch("orchestrator.linkedin_poster._send_hitl_notification", new_callable=AsyncMock):
                with patch("orchestrator.linkedin_poster._count_today_posts", return_value=0):
                    with patch("orchestrator.linkedin_poster.VAULT_PENDING", pending):
                        result = await draft_and_notify("AI topic")
                        assert result["status"] == "drafted"
                        files = list(pending.glob("*_linkedin_*.md"))
                        assert len(files) == 1
                        fm = yaml.safe_load(files[0].read_text().split("---", 2)[1])
                        assert "draft_id" in fm
                        assert fm["draft_id"]


@pytest.mark.asyncio
async def test_hitl_approve_linkedin_sets_approved_in_place(tmp_path):
    """HITLManager._approve() with type=linkedin_post sets status=approved in Pending_Approval/."""
    import yaml
    from orchestrator.hitl_manager import HITLManager, _generate_draft_id

    vault = tmp_path / "vault"
    pending = vault / "Pending_Approval"
    approved = vault / "Approved"
    rejected = vault / "Rejected"
    logs = vault / "Logs"
    for d in [pending, approved, rejected, logs]:
        d.mkdir(parents=True)

    # Write a linkedin_post draft with draft_id
    draft_id = _generate_draft_id()
    short_id = draft_id[-12:]
    draft_path = pending / f"2026-03-09T090000_linkedin_test.md"
    draft_path.write_text(
        f"---\ntype: linkedin_post\ndraft_id: {draft_id}\nstatus: pending_approval\ntopic: AI\n---\n\nPost body"
    )

    whatsapp = MagicMock()
    whatsapp.call_tool = AsyncMock()
    gmail = MagicMock()
    gmail.call_tool = AsyncMock()

    manager = HITLManager(whatsapp, gmail, vault, "+921234567890")
    await manager._approve(short_id, "+921234567890")

    # File stays in Pending_Approval/ (NOT moved to Approved/)
    assert draft_path.exists(), "LinkedIn draft must stay in Pending_Approval/ after approve"
    assert not (approved / draft_path.name).exists(), "File must NOT move to Approved/"
    fm = yaml.safe_load(draft_path.read_text().split("---", 2)[1])
    assert fm["status"] == "approved"
    # Gmail was NOT called
    gmail.call_tool.assert_not_called()
    # WhatsApp confirmation was sent
    whatsapp.call_tool.assert_called_once()


@pytest.mark.asyncio
async def test_hitl_reject_linkedin_sets_rejected_in_place(tmp_path):
    """HITLManager._reject() with type=linkedin_post sets status=rejected in Pending_Approval/."""
    import yaml
    from orchestrator.hitl_manager import HITLManager, _generate_draft_id

    vault = tmp_path / "vault"
    pending = vault / "Pending_Approval"
    rejected = vault / "Rejected"
    for d in [pending, vault / "Approved", rejected, vault / "Logs"]:
        d.mkdir(parents=True)

    draft_id = _generate_draft_id()
    draft_path = pending / f"2026-03-09T090000_linkedin_test.md"
    draft_path.write_text(
        f"---\ntype: linkedin_post\ndraft_id: {draft_id}\nstatus: pending_approval\ntopic: AI\n---\n\nPost body"
    )

    whatsapp = MagicMock()
    whatsapp.call_tool = AsyncMock()
    gmail = MagicMock()
    gmail.call_tool = AsyncMock()

    manager = HITLManager(whatsapp, gmail, vault, "+921234567890")
    await manager._reject(draft_id[-12:], "+921234567890")

    assert draft_path.exists(), "LinkedIn draft must stay in Pending_Approval/ after reject"
    assert not (rejected / draft_path.name).exists(), "File must NOT move to Rejected/"
    fm = yaml.safe_load(draft_path.read_text().split("---", 2)[1])
    assert fm["status"] == "rejected"
    gmail.call_tool.assert_not_called()


@pytest.mark.asyncio
async def test_hitl_approve_email_draft_unchanged(tmp_path):
    """HITLManager._approve() for type=approval_request still sends email + moves to Approved/."""
    from orchestrator.hitl_manager import HITLManager

    vault = tmp_path / "vault"
    pending = vault / "Pending_Approval"
    approved = vault / "Approved"
    for d in [pending, approved, vault / "Rejected", vault / "Logs"]:
        d.mkdir(parents=True)

    draft_id = await _create_email_draft(pending)

    whatsapp = MagicMock()
    whatsapp.call_tool = AsyncMock()
    gmail = MagicMock()
    gmail.call_tool = AsyncMock(return_value={"sent_at": "2026-03-09T09:00:00Z"})

    manager = HITLManager(whatsapp, gmail, vault, "+921234567890")
    await manager._approve(draft_id, "+921234567890")

    # Email draft moves to Approved/
    assert not (pending / f"{draft_id}.md").exists()
    assert (approved / f"{draft_id}.md").exists()
    gmail.call_tool.assert_called_once()  # Email was sent


async def _create_email_draft(pending: Path) -> str:
    """Helper: create an approval_request draft and return its draft_id."""
    import secrets
    from datetime import datetime, timezone

    draft_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(4)
    (pending / f"{draft_id}.md").write_text(
        f"---\ntype: approval_request\ndraft_id: {draft_id}\nstatus: pending\n"
        f"recipient: boss@co.com\nsubject: Test\npriority: MED\n---\n\nBody"
    )
    return draft_id


# ═══════════════════════════════════════════════════════════════════════════════
# COVERAGE EXPANSION: Missing paths in linkedin_poster.py
# Target: orchestrator/linkedin_poster.py from 76% → 80%+
# ═══════════════════════════════════════════════════════════════════════════════


# ── _count_today_posts() direct tests ─────────────────────────────────────────


def test_count_today_posts_with_published_entries(tmp_path):
    """_count_today_posts counts only published entries for today (UTC)."""
    import json
    from datetime import date
    from orchestrator.linkedin_poster import _count_today_posts

    posts_file = tmp_path / "linkedin_posts.jsonl"
    today = date.today().isoformat()
    entries = [
        {"ts": f"{today}T09:00:00Z", "event": "published", "status": "published"},
        {"ts": f"{today}T12:00:00Z", "event": "published", "status": "published"},
        {"ts": "2020-01-01T09:00:00Z", "event": "published", "status": "published"},  # old date
        {"ts": f"{today}T10:00:00Z", "event": "drafted", "status": "pending"},
    ]
    posts_file.write_text("\n".join(json.dumps(e) for e in entries))

    with patch("orchestrator.linkedin_poster.POSTS_JSONL", posts_file):
        assert _count_today_posts() == 2


def test_count_today_posts_with_malformed_line(tmp_path):
    """_count_today_posts skips malformed JSON lines gracefully."""
    from datetime import date
    from orchestrator.linkedin_poster import _count_today_posts

    posts_file = tmp_path / "linkedin_posts.jsonl"
    today = date.today().isoformat()
    content = (
        f'{{"ts": "{today}T09:00:00Z", "status": "published"}}\n'
        "NOT_VALID_JSON\n"
        f'{{"ts": "{today}T10:00:00Z", "status": "published"}}\n'
    )
    posts_file.write_text(content)

    with patch("orchestrator.linkedin_poster.POSTS_JSONL", posts_file):
        assert _count_today_posts() == 2


def test_count_today_posts_file_not_exists(tmp_path):
    """_count_today_posts returns 0 when JSONL file does not exist."""
    from orchestrator.linkedin_poster import _count_today_posts

    with patch("orchestrator.linkedin_poster.POSTS_JSONL", tmp_path / "nonexistent.jsonl"):
        assert _count_today_posts() == 0


# ── _load_topics() direct tests ────────────────────────────────────────────────


def test_load_topics_with_file(tmp_path):
    """_load_topics returns parsed topics from markdown file."""
    from orchestrator.linkedin_poster import _load_topics

    topics_file = tmp_path / "linkedin_topics.md"
    topics_file.write_text("# LinkedIn Post Topics\n\n- AI automation\n- Python projects\n- Hackathons\n")

    with patch("orchestrator.linkedin_poster.TOPICS_FILE", topics_file):
        topics = _load_topics()

    assert "AI automation" in topics
    assert "Python projects" in topics
    assert len(topics) == 3


def test_load_topics_file_missing(tmp_path):
    """_load_topics returns fallback list when topics file is missing."""
    from orchestrator.linkedin_poster import _load_topics

    with patch("orchestrator.linkedin_poster.TOPICS_FILE", tmp_path / "nonexistent.md"):
        topics = _load_topics()

    assert len(topics) >= 1
    assert isinstance(topics[0], str)


def test_load_topics_all_headers_returns_fallback(tmp_path):
    """_load_topics returns fallback when file has only comment/header lines."""
    from orchestrator.linkedin_poster import _load_topics

    topics_file = tmp_path / "linkedin_topics.md"
    topics_file.write_text("# Header\n# Another header\n")

    with patch("orchestrator.linkedin_poster.TOPICS_FILE", topics_file):
        topics = _load_topics()

    assert len(topics) >= 1


# ── _draft_post_content() direct test ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_draft_post_content_calls_anthropic(mock_env):
    """_draft_post_content calls Anthropic AsyncClient and returns stripped text."""
    from orchestrator.linkedin_poster import _draft_post_content

    mock_text_block = MagicMock()
    mock_text_block.text = "  Draft LinkedIn post about AI.  "
    mock_message = MagicMock()
    mock_message.content = [mock_text_block]

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)

    with patch("orchestrator.linkedin_poster.anthropic") as mock_anthropic_mod:
        mock_anthropic_mod.AsyncAnthropic.return_value = mock_client
        result = await _draft_post_content("AI automation")

    assert result == "Draft LinkedIn post about AI."
    mock_client.messages.create.assert_called_once()


# ── _send_hitl_notification() direct test ─────────────────────────────────────


@pytest.mark.asyncio
async def test_send_hitl_notification_sends_to_owner(tmp_path):
    """_send_hitl_notification calls GoBridge.send with correct content."""
    from orchestrator.linkedin_poster import _send_hitl_notification

    draft_path = tmp_path / "2026-03-09T090000_linkedin_test.md"

    mock_bridge = AsyncMock()
    with patch("orchestrator.linkedin_poster.OWNER_WA", "+921234567890"):
        with patch("orchestrator.linkedin_poster.GoBridge") as mock_bridge_cls:
            mock_bridge_cls.return_value = mock_bridge
            await _send_hitl_notification(
                "AI topic", "Post content here.", draft_path, "deadbeef123456"
            )

    mock_bridge.send.assert_called_once()
    _to, _msg = mock_bridge.send.call_args[0]
    assert _to == "+921234567890"
    assert "AI topic" in _msg
    assert "ef123456" in _msg  # last 12 chars of draft_id


@pytest.mark.asyncio
async def test_send_hitl_notification_truncates_long_post(tmp_path):
    """_send_hitl_notification truncates post preview to 300 chars with ellipsis."""
    from orchestrator.linkedin_poster import _send_hitl_notification

    draft_path = tmp_path / "2026-03-09T090000_linkedin_test.md"
    long_post = "x" * 500

    mock_bridge = AsyncMock()
    with patch("orchestrator.linkedin_poster.OWNER_WA", "+92123"):
        with patch("orchestrator.linkedin_poster.GoBridge") as mock_bridge_cls:
            mock_bridge_cls.return_value = mock_bridge
            await _send_hitl_notification("topic", long_post, draft_path, "abc12345678901")

    _to, _msg = mock_bridge.send.call_args[0]
    assert "..." in _msg


# ── _move_to_rejected() direct test ──────────────────────────────────────────


def test_move_to_rejected_moves_file(tmp_path):
    """_move_to_rejected actually renames file into VAULT_REJECTED directory."""
    from orchestrator.linkedin_poster import _move_to_rejected

    rejected_dir = tmp_path / "Rejected"
    draft = tmp_path / "2026-03-09T090000_linkedin_test.md"
    draft.write_text("draft content")

    with patch("orchestrator.linkedin_poster.VAULT_REJECTED", rejected_dir):
        _move_to_rejected(draft)

    assert not draft.exists()
    assert (rejected_dir / draft.name).exists()
    assert (rejected_dir / draft.name).read_text() == "draft content"


# ── _call_post_update() direct test ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_call_post_update_delegates_to_post_to_linkedin():
    """_call_post_update calls post_to_linkedin with text and PUBLIC visibility."""
    from orchestrator.linkedin_poster import _call_post_update

    with patch(
        "orchestrator.linkedin_poster.post_to_linkedin",
        new_callable=AsyncMock,
        return_value={"post_id": "urn:li:share:test999"},
    ) as mock_post:
        result = await _call_post_update("Test LinkedIn post")

    mock_post.assert_called_once_with("Test LinkedIn post", "PUBLIC")
    assert result["post_id"] == "urn:li:share:test999"


# ── draft_and_notify: WhatsApp notification failure (non-fatal) ───────────────


@pytest.mark.asyncio
async def test_draft_whatsapp_failure_still_returns_drafted(mock_env, tmp_path):
    """WhatsApp notification failure is non-fatal — draft status is still 'drafted'."""
    from orchestrator.linkedin_poster import draft_and_notify

    pending = tmp_path / "Pending_Approval"
    pending.mkdir()

    with patch("orchestrator.linkedin_poster.run_privacy_gate") as pg:
        pg.return_value = MagicMock(media_blocked=False)
        with patch(
            "orchestrator.linkedin_poster._draft_post_content",
            new_callable=AsyncMock,
            return_value="Test content",
        ):
            with patch(
                "orchestrator.linkedin_poster._send_hitl_notification",
                new_callable=AsyncMock,
                side_effect=Exception("WhatsApp bridge unavailable"),
            ):
                with patch("orchestrator.linkedin_poster._count_today_posts", return_value=0):
                    with patch("orchestrator.linkedin_poster.VAULT_PENDING", pending):
                        with patch("orchestrator.linkedin_poster._log_event"):
                            result = await draft_and_notify("AI topic")

    assert result["status"] == "drafted"
    files = list(pending.glob("*_linkedin_*.md"))
    assert len(files) == 1  # vault file still created


# ── check_pending_approvals edge cases ───────────────────────────────────────


@pytest.mark.asyncio
async def test_check_pending_approvals_malformed_file(tmp_path):
    """check_pending_approvals skips files without proper YAML frontmatter."""
    from orchestrator.linkedin_poster import check_pending_approvals

    draft = tmp_path / "2026-03-09T090000_linkedin_test.md"
    draft.write_text("No frontmatter separators here at all")

    with patch("orchestrator.linkedin_poster.VAULT_PENDING", tmp_path):
        with patch(
            "orchestrator.linkedin_poster.publish_approved", new_callable=AsyncMock
        ) as mock_pub:
            await check_pending_approvals()
            mock_pub.assert_not_called()


@pytest.mark.asyncio
async def test_check_pending_approvals_invalid_expires_at(tmp_path):
    """check_pending_approvals handles non-float expires_at without crashing."""
    from orchestrator.linkedin_poster import check_pending_approvals

    draft = tmp_path / "2026-03-09T090000_linkedin_test.md"
    draft.write_text(
        "---\ntype: linkedin_post\nstatus: pending_approval\nexpires_at: not_a_float\n---\nContent\n"
    )

    with patch("orchestrator.linkedin_poster.VAULT_PENDING", tmp_path):
        with patch(
            "orchestrator.linkedin_poster.handle_rejected", new_callable=AsyncMock
        ) as mock_rej:
            with patch(
                "orchestrator.linkedin_poster.publish_approved", new_callable=AsyncMock
            ) as mock_pub:
                await check_pending_approvals()
                # Invalid expires_at → no expiry, no action
                mock_rej.assert_not_called()
                mock_pub.assert_not_called()


# ── process_linkedin_vault_triggers edge cases ───────────────────────────────


@pytest.mark.asyncio
async def test_process_vault_triggers_nonexistent_dir(tmp_path):
    """process_linkedin_vault_triggers returns gracefully if needs_action dir missing."""
    from orchestrator.linkedin_poster import process_linkedin_vault_triggers

    nonexistent = tmp_path / "Needs_Action"
    done = tmp_path / "Done"
    # Must not raise
    await process_linkedin_vault_triggers(nonexistent, done)


@pytest.mark.asyncio
async def test_process_vault_triggers_malformed_file(tmp_path):
    """process_linkedin_vault_triggers skips files with no frontmatter."""
    from orchestrator.linkedin_poster import process_linkedin_vault_triggers

    needs_action = tmp_path / "Needs_Action"
    done = tmp_path / "Done"
    needs_action.mkdir()
    done.mkdir()

    bad_file = needs_action / "2026-03-09T090000_bad.md"
    bad_file.write_text("No frontmatter separators")

    with patch(
        "orchestrator.linkedin_poster.draft_and_notify", new_callable=AsyncMock
    ) as mock_draft:
        await process_linkedin_vault_triggers(needs_action, done)
        mock_draft.assert_not_called()


@pytest.mark.asyncio
async def test_process_vault_triggers_empty_topic_fallback(tmp_path):
    """Vault trigger with no topic field uses 'LinkedIn post' as fallback."""
    from orchestrator.linkedin_poster import process_linkedin_vault_triggers

    needs_action = tmp_path / "Needs_Action"
    done = tmp_path / "Done"
    needs_action.mkdir()
    done.mkdir()

    trigger = needs_action / "2026-03-09T090000_linkedin_notopic.md"
    trigger.write_text("---\ntype: linkedin_post\nstatus: pending\n---\n")

    with patch(
        "orchestrator.linkedin_poster.draft_and_notify",
        new_callable=AsyncMock,
        return_value={"status": "drafted"},
    ) as mock_draft:
        await process_linkedin_vault_triggers(needs_action, done)
        mock_draft.assert_called_once_with("LinkedIn post")


@pytest.mark.asyncio
async def test_process_vault_triggers_exception_continues(tmp_path):
    """Exception during one vault trigger is caught; subsequent files are still processed."""
    from orchestrator.linkedin_poster import process_linkedin_vault_triggers

    needs_action = tmp_path / "Needs_Action"
    done = tmp_path / "Done"
    needs_action.mkdir()
    done.mkdir()

    f1 = needs_action / "2026-03-09T090000_linkedin_a.md"
    f1.write_text("---\ntype: linkedin_post\ntopic: topic a\n---\n")
    f2 = needs_action / "2026-03-09T090001_linkedin_b.md"
    f2.write_text("---\ntype: linkedin_post\ntopic: topic b\n---\n")

    call_count = 0

    async def mock_draft(topic):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Simulated draft failure")
        return {"status": "drafted"}

    with patch("orchestrator.linkedin_poster.draft_and_notify", side_effect=mock_draft):
        await process_linkedin_vault_triggers(needs_action, done)

    assert call_count == 2


# ── main() CLI dispatch tests ─────────────────────────────────────────────────


def _run_and_close(coro):
    """Close the coroutine to prevent 'never awaited' warning."""
    coro.close()


def test_main_draft_arg(mock_env):
    """main() --draft arg calls asyncio.run(draft_and_notify(...))."""
    from orchestrator.linkedin_poster import main

    with patch("sys.argv", ["linkedin_poster.py", "--draft", "AI automation"]):
        with patch("orchestrator.linkedin_poster.asyncio.run", side_effect=_run_and_close) as mock_run:
            main()
            mock_run.assert_called_once()


def test_main_auto_arg(mock_env):
    """main() --auto arg calls asyncio.run(run_auto_mode())."""
    from orchestrator.linkedin_poster import main

    with patch("sys.argv", ["linkedin_poster.py", "--auto"]):
        with patch("orchestrator.linkedin_poster.asyncio.run", side_effect=_run_and_close) as mock_run:
            main()
            mock_run.assert_called_once()


def test_main_check_arg(mock_env):
    """main() --check arg calls asyncio.run(check_pending_approvals())."""
    from orchestrator.linkedin_poster import main

    with patch("sys.argv", ["linkedin_poster.py", "--check"]):
        with patch("orchestrator.linkedin_poster.asyncio.run", side_effect=_run_and_close) as mock_run:
            main()
            mock_run.assert_called_once()
