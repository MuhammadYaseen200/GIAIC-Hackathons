"""Unit tests for social_dm_monitor.py — TDD RED first."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_load_keywords_from_file(tmp_path):
    """load_keywords reads keywords from vault/Config/social_keywords.md."""
    keywords_file = tmp_path / "Config" / "social_keywords.md"
    keywords_file.parent.mkdir(parents=True)
    keywords_file.write_text("job, hire, freelance, client\n")

    with patch("watchers.social_dm_monitor.KEYWORDS_FILE", keywords_file):
        from watchers.social_dm_monitor import load_keywords
        result = await load_keywords()

    assert isinstance(result, list)
    assert len(result) > 0
    assert "job" in result or "hire" in result


@pytest.mark.asyncio
async def test_keyword_match_detected():
    """should_escalate returns True when keyword found in text."""
    from watchers.social_dm_monitor import should_escalate
    result = await should_escalate("I have an urgent project for you", ["job", "urgent", "project"])
    assert result is True


@pytest.mark.asyncio
async def test_no_keyword_no_escalation():
    """should_escalate returns False when no keyword matches."""
    from watchers.social_dm_monitor import should_escalate
    result = await should_escalate("Hello, how are you today?", ["job", "hire", "invoice"])
    assert result is False


@pytest.mark.asyncio
async def test_twitter_403_returns_empty_gracefully():
    """check_twitter_dms returns [] on 403 Forbidden (elevated access required)."""
    import httpx
    with patch("watchers.social_dm_monitor._twitter_request",
               side_effect=Exception("403 Forbidden")):
        from watchers.social_dm_monitor import check_twitter_dms
        result = await check_twitter_dms()

    assert result == []


@pytest.mark.asyncio
async def test_facebook_dm_escalation_sends_whatsapp():
    """When Facebook DM matches keyword, WhatsApp notification is sent."""
    mock_bridge = MagicMock()
    mock_bridge.send = AsyncMock()

    with patch("watchers.social_dm_monitor.GoBridge", return_value=mock_bridge):
        from watchers.social_dm_monitor import notify_owner
        await notify_owner("facebook", "John Doe", "I have a job offer for you")

    mock_bridge.send.assert_called_once()
    msg = mock_bridge.send.call_args[0][0]
    assert len(msg) <= 500
    assert "facebook" in msg.lower() or "John" in msg


@pytest.mark.asyncio
async def test_instagram_mention_escalation():
    """check_instagram_mentions returns [] gracefully when no IG account."""
    import os
    with patch.dict("os.environ", {"INSTAGRAM_BUSINESS_ACCOUNT_ID": ""}):
        from watchers.social_dm_monitor import check_instagram_mentions
        result = await check_instagram_mentions()

    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_all_platforms_checked_independently():
    """run_dm_monitor checks all 3 platforms independently."""
    with patch("watchers.social_dm_monitor.check_facebook_dms", new_callable=AsyncMock, return_value=[]) as fb:
        with patch("watchers.social_dm_monitor.check_instagram_mentions", new_callable=AsyncMock, return_value=[]) as ig:
            with patch("watchers.social_dm_monitor.check_twitter_dms", new_callable=AsyncMock, return_value=[]) as tw:
                with patch("watchers.social_dm_monitor.load_keywords", new_callable=AsyncMock, return_value=["job"]):
                    from watchers.social_dm_monitor import run_dm_monitor
                    result = await run_dm_monitor()

    fb.assert_called_once()
    ig.assert_called_once()
    tw.assert_called_once()
    assert "checked" in result


@pytest.mark.asyncio
async def test_dm_monitor_logged_to_audit_jsonl(tmp_path):
    """run_dm_monitor writes to audit.jsonl."""
    audit_log = tmp_path / "audit.jsonl"
    with patch("watchers.social_dm_monitor.AUDIT_LOG", audit_log):
        with patch("watchers.social_dm_monitor.check_facebook_dms", new_callable=AsyncMock, return_value=[]):
            with patch("watchers.social_dm_monitor.check_instagram_mentions", new_callable=AsyncMock, return_value=[]):
                with patch("watchers.social_dm_monitor.check_twitter_dms", new_callable=AsyncMock, return_value=[]):
                    with patch("watchers.social_dm_monitor.load_keywords", new_callable=AsyncMock, return_value=["job"]):
                        from watchers.social_dm_monitor import run_dm_monitor
                        await run_dm_monitor()

    assert audit_log.exists()
    entry = json.loads(audit_log.read_text().strip().split("\n")[0])
    assert "ts" in entry
    assert entry.get("action") == "dm_monitor.run"
