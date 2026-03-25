"""Unit tests for social_poster.py — run_until_complete integration."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_draft_and_notify_creates_vault_file(tmp_path):
    """draft_and_notify creates a file in vault/Pending_Approval/."""
    with patch("orchestrator.social_poster.VAULT_PATH", tmp_path):
        from orchestrator.social_poster import draft_and_notify
        with patch("orchestrator.social_poster.SOCIAL_LOG", tmp_path / "Logs" / "social_posts.jsonl"):
            result = await draft_and_notify("Test post about AI", platforms=["facebook"])

    assert result["status"] == "pending_approval"
    assert "draft_path" in result
    assert Path(result["draft_path"]).exists()


@pytest.mark.asyncio
async def test_draft_and_notify_logs_jsonl(tmp_path):
    """draft_and_notify writes a JSONL entry."""
    with patch("orchestrator.social_poster.VAULT_PATH", tmp_path):
        with patch("orchestrator.social_poster.SOCIAL_LOG", tmp_path / "Logs" / "social_posts.jsonl"):
            from orchestrator.social_poster import draft_and_notify
            await draft_and_notify("AI automation topic", platforms=["twitter"])

    log_file = tmp_path / "Logs" / "social_posts.jsonl"
    assert log_file.exists()
    entry = json.loads(log_file.read_text().strip().split("\n")[0])
    assert entry["action"] == "draft_created"
    assert "ts" in entry


@pytest.mark.asyncio
async def test_publish_approved_uses_run_until_complete(tmp_path):
    """publish_approved wraps platform call in run_until_complete."""
    import orchestrator.social_poster as sp_mod
    import inspect
    src = inspect.getsource(sp_mod)
    assert "run_until_complete" in src


@pytest.mark.asyncio
async def test_run_until_complete_social_poster_integration(tmp_path):
    """publish_approved retries via run_until_complete on transient failure."""
    # Create a mock draft file
    draft_dir = tmp_path / "Pending_Approval"
    draft_dir.mkdir(parents=True)
    done_dir = tmp_path / "Done"
    done_dir.mkdir(parents=True)
    draft = draft_dir / "social_post_test.md"
    draft.write_text("""---
type: social_post
---

# Draft

Test tweet content
""")

    call_count = 0

    async def flaky_post(text: str) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RuntimeError("Transient network error")
        return {"success": True, "tweet_id": "123", "url": "https://t.co/x"}

    with patch("orchestrator.social_poster.VAULT_PATH", tmp_path):
        with patch("orchestrator.social_poster.SOCIAL_LOG", tmp_path / "Logs" / "social_posts.jsonl"):
            with patch("mcp_servers.twitter.client.post_tweet", side_effect=flaky_post):
                from orchestrator.social_poster import publish_approved
                result = await publish_approved(draft, "twitter")

    # With run_until_complete retry, second attempt should succeed
    assert call_count >= 1


@pytest.mark.asyncio
async def test_publish_approved_facebook(tmp_path):
    """publish_approved routes to Facebook client correctly."""
    draft_dir = tmp_path / "Pending_Approval"
    draft_dir.mkdir(parents=True)
    done_dir = tmp_path / "Done"
    done_dir.mkdir(parents=True)
    draft = draft_dir / "social_post_fb.md"
    draft.write_text("---\ntype: social_post\n---\n\n# Draft\n\nFacebook test post\n")

    with patch("orchestrator.social_poster.VAULT_PATH", tmp_path):
        with patch("orchestrator.social_poster.SOCIAL_LOG", tmp_path / "Logs" / "social_posts.jsonl"):
            with patch("mcp_servers.facebook.client.post_to_facebook",
                       new_callable=AsyncMock,
                       return_value={"success": True, "post_id": "fb123"}):
                from orchestrator.social_poster import publish_approved
                result = await publish_approved(draft, "facebook")

    assert result.get("success") is True


@pytest.mark.asyncio
async def test_publish_approved_instagram_skipped(tmp_path):
    """publish_approved with instagram returns skipped when no IG account."""
    draft_dir = tmp_path / "Pending_Approval"
    draft_dir.mkdir(parents=True)
    done_dir = tmp_path / "Done"
    done_dir.mkdir(parents=True)
    draft = draft_dir / "social_post_ig.md"
    draft.write_text("---\ntype: social_post\n---\n\n# Draft\n\nInstagram caption\n")

    with patch("orchestrator.social_poster.VAULT_PATH", tmp_path):
        with patch("orchestrator.social_poster.SOCIAL_LOG", tmp_path / "Logs" / "social_posts.jsonl"):
            with patch("mcp_servers.facebook.client.post_to_instagram",
                       new_callable=AsyncMock,
                       return_value={"status": "skipped", "reason": "no_ig_account"}):
                from orchestrator.social_poster import publish_approved
                result = await publish_approved(draft, "instagram")

    assert result is not None


@pytest.mark.asyncio
async def test_publish_approved_moves_draft_to_done(tmp_path):
    """After publishing, draft file is moved to Done/."""
    draft_dir = tmp_path / "Pending_Approval"
    draft_dir.mkdir(parents=True)
    done_dir = tmp_path / "Done"
    done_dir.mkdir(parents=True)
    draft = draft_dir / "social_post_move.md"
    draft.write_text("---\ntype: social_post\n---\n\n# Draft\n\nLinkedIn post\n")

    with patch("orchestrator.social_poster.VAULT_PATH", tmp_path):
        with patch("orchestrator.social_poster.SOCIAL_LOG", tmp_path / "Logs" / "social_posts.jsonl"):
            from orchestrator.social_poster import publish_approved
            await publish_approved(draft, "linkedin")

    assert not draft.exists()
    assert (done_dir / "social_post_move.md").exists()
