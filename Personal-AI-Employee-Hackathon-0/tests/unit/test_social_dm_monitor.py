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


# -- ADDITIONAL COVERAGE TESTS -------------------------------------------------


@pytest.mark.asyncio
async def test_load_keywords_missing_file_returns_defaults():
    """load_keywords returns default keyword list when file doesn't exist."""
    from watchers.social_dm_monitor import load_keywords

    with patch("watchers.social_dm_monitor.KEYWORDS_FILE", Path("/nonexistent/path/keywords.md")):
        result = await load_keywords()

    assert isinstance(result, list)
    assert len(result) > 0  # Default keywords should be returned
    assert "job" in result
    assert "hire" in result


@pytest.mark.asyncio
async def test_should_escalate_case_insensitive():
    """should_escalate matches keywords case-insensitively."""
    from watchers.social_dm_monitor import should_escalate
    result = await should_escalate("I have a JOB OFFER for you", ["job", "hire"])
    assert result is True


@pytest.mark.asyncio
async def test_should_escalate_empty_text():
    """should_escalate returns False for empty text."""
    from watchers.social_dm_monitor import should_escalate
    result = await should_escalate("", ["job", "hire"])
    assert result is False


@pytest.mark.asyncio
async def test_check_facebook_dms_no_credentials():
    """check_facebook_dms returns [] when no page ID or token set."""
    with patch.dict("os.environ", {"FACEBOOK_PAGE_ID": "", "FACEBOOK_PAGE_ACCESS_TOKEN": ""}):
        from watchers.social_dm_monitor import check_facebook_dms
        result = await check_facebook_dms()
    assert result == []


@pytest.mark.asyncio
async def test_check_facebook_dms_success():
    """check_facebook_dms returns conversation data on success."""
    import httpx

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": [{"id": "conv-1", "snippet": "Hello I have a job for you",
                  "participants": {"data": [{"name": "Alice"}]}}]
    }

    with patch.dict("os.environ", {"FACEBOOK_PAGE_ID": "page-123",
                                    "FACEBOOK_PAGE_ACCESS_TOKEN": "tok-abc"}):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_inst = AsyncMock()
            mock_client_inst.get.return_value = mock_response
            mock_client_inst.__aenter__ = AsyncMock(return_value=mock_client_inst)
            mock_client_inst.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_inst

            from watchers.social_dm_monitor import check_facebook_dms
            result = await check_facebook_dms()

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["snippet"] == "Hello I have a job for you"


@pytest.mark.asyncio
async def test_check_facebook_dms_exception_returns_empty():
    """check_facebook_dms returns [] on any exception."""
    with patch.dict("os.environ", {"FACEBOOK_PAGE_ID": "page-123",
                                    "FACEBOOK_PAGE_ACCESS_TOKEN": "tok-abc"}):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_inst = AsyncMock()
            mock_client_inst.get.side_effect = Exception("Network error")
            mock_client_inst.__aenter__ = AsyncMock(return_value=mock_client_inst)
            mock_client_inst.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_inst

            from watchers.social_dm_monitor import check_facebook_dms
            result = await check_facebook_dms()

    assert result == []


@pytest.mark.asyncio
async def test_check_instagram_mentions_with_account_set():
    """check_instagram_mentions returns data when IG_ACCOUNT_ID is set."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"data": [{"text": "hey", "from": {"username": "bob"}}]}

    with patch.dict("os.environ", {"INSTAGRAM_BUSINESS_ACCOUNT_ID": "ig-123",
                                    "FACEBOOK_PAGE_ACCESS_TOKEN": "tok-abc"}):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_inst = AsyncMock()
            mock_client_inst.get.return_value = mock_response
            mock_client_inst.__aenter__ = AsyncMock(return_value=mock_client_inst)
            mock_client_inst.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_inst

            from watchers.social_dm_monitor import check_instagram_mentions
            result = await check_instagram_mentions()

    assert isinstance(result, list)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_check_instagram_mentions_exception():
    """check_instagram_mentions returns [] on exception."""
    with patch.dict("os.environ", {"INSTAGRAM_BUSINESS_ACCOUNT_ID": "ig-123",
                                    "FACEBOOK_PAGE_ACCESS_TOKEN": "tok-abc"}):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_inst = AsyncMock()
            mock_client_inst.get.side_effect = Exception("IG down")
            mock_client_inst.__aenter__ = AsyncMock(return_value=mock_client_inst)
            mock_client_inst.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_inst

            from watchers.social_dm_monitor import check_instagram_mentions
            result = await check_instagram_mentions()

    assert result == []


@pytest.mark.asyncio
async def test_check_twitter_dms_success():
    """check_twitter_dms returns DM events on success."""
    with patch("watchers.social_dm_monitor._twitter_request",
               new_callable=AsyncMock,
               return_value=[{"text": "job offer", "sender_id": "123"}]):
        from watchers.social_dm_monitor import check_twitter_dms
        result = await check_twitter_dms()

    assert isinstance(result, list)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_twitter_request_no_bearer_token():
    """_twitter_request raises when no bearer token set."""
    with patch.dict("os.environ", {"TWITTER_BEARER_TOKEN": ""}):
        from watchers.social_dm_monitor import _twitter_request
        with pytest.raises(Exception, match="No TWITTER_BEARER_TOKEN"):
            await _twitter_request("dm_events")


@pytest.mark.asyncio
async def test_twitter_request_403_raises():
    """_twitter_request raises on 403 Forbidden."""
    mock_response = MagicMock()
    mock_response.status_code = 403

    with patch.dict("os.environ", {"TWITTER_BEARER_TOKEN": "test-bearer"}):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_inst = AsyncMock()
            mock_client_inst.get.return_value = mock_response
            mock_client_inst.__aenter__ = AsyncMock(return_value=mock_client_inst)
            mock_client_inst.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_inst

            from watchers.social_dm_monitor import _twitter_request
            with pytest.raises(Exception, match="403"):
                await _twitter_request("dm_events")


@pytest.mark.asyncio
async def test_run_dm_monitor_with_escalation(tmp_path):
    """run_dm_monitor escalates when a DM matches a keyword."""
    audit_log = tmp_path / "audit.jsonl"
    fb_dm = {"snippet": "I have an urgent job offer",
             "participants": {"data": [{"name": "Bob"}]}}

    with patch("watchers.social_dm_monitor.AUDIT_LOG", audit_log), \
         patch("watchers.social_dm_monitor.check_facebook_dms",
               new_callable=AsyncMock, return_value=[fb_dm]), \
         patch("watchers.social_dm_monitor.check_instagram_mentions",
               new_callable=AsyncMock, return_value=[]), \
         patch("watchers.social_dm_monitor.check_twitter_dms",
               new_callable=AsyncMock, return_value=[]), \
         patch("watchers.social_dm_monitor.load_keywords",
               new_callable=AsyncMock, return_value=["job", "urgent"]), \
         patch("watchers.social_dm_monitor.notify_owner",
               new_callable=AsyncMock) as mock_notify:
        from watchers.social_dm_monitor import run_dm_monitor
        result = await run_dm_monitor()

    assert isinstance(result, dict)
    assert result["escalated"] >= 1
    mock_notify.assert_called_once()
    # Verify platform and sender passed correctly
    call_args = mock_notify.call_args[0]
    assert call_args[0] == "facebook"
    assert call_args[1] == "Bob"


@pytest.mark.asyncio
async def test_run_dm_monitor_instagram_escalation(tmp_path):
    """run_dm_monitor escalates Instagram mentions with keyword match."""
    audit_log = tmp_path / "audit.jsonl"
    ig_mention = {"text": "urgent project inquiry",
                  "from": {"username": "charlie_ig"}}

    with patch("watchers.social_dm_monitor.AUDIT_LOG", audit_log), \
         patch("watchers.social_dm_monitor.check_facebook_dms",
               new_callable=AsyncMock, return_value=[]), \
         patch("watchers.social_dm_monitor.check_instagram_mentions",
               new_callable=AsyncMock, return_value=[ig_mention]), \
         patch("watchers.social_dm_monitor.check_twitter_dms",
               new_callable=AsyncMock, return_value=[]), \
         patch("watchers.social_dm_monitor.load_keywords",
               new_callable=AsyncMock, return_value=["urgent", "project"]), \
         patch("watchers.social_dm_monitor.notify_owner",
               new_callable=AsyncMock) as mock_notify:
        from watchers.social_dm_monitor import run_dm_monitor
        result = await run_dm_monitor()

    assert result["escalated"] >= 1
    call_args = mock_notify.call_args[0]
    assert call_args[0] == "instagram"
    assert call_args[1] == "charlie_ig"


@pytest.mark.asyncio
async def test_run_dm_monitor_twitter_escalation(tmp_path):
    """run_dm_monitor escalates Twitter DMs with keyword match."""
    audit_log = tmp_path / "audit.jsonl"
    tw_dm = {"text": "contract opportunity", "sender_id": "tw-456"}

    with patch("watchers.social_dm_monitor.AUDIT_LOG", audit_log), \
         patch("watchers.social_dm_monitor.check_facebook_dms",
               new_callable=AsyncMock, return_value=[]), \
         patch("watchers.social_dm_monitor.check_instagram_mentions",
               new_callable=AsyncMock, return_value=[]), \
         patch("watchers.social_dm_monitor.check_twitter_dms",
               new_callable=AsyncMock, return_value=[tw_dm]), \
         patch("watchers.social_dm_monitor.load_keywords",
               new_callable=AsyncMock, return_value=["contract"]), \
         patch("watchers.social_dm_monitor.notify_owner",
               new_callable=AsyncMock) as mock_notify:
        from watchers.social_dm_monitor import run_dm_monitor
        result = await run_dm_monitor()

    assert result["escalated"] >= 1
    call_args = mock_notify.call_args[0]
    assert call_args[0] == "twitter"
    assert call_args[1] == "tw-456"


@pytest.mark.asyncio
async def test_notify_owner_gobridge_none():
    """notify_owner logs warning when GoBridge is None."""
    with patch("watchers.social_dm_monitor.GoBridge", None):
        from watchers.social_dm_monitor import notify_owner
        # Should not raise
        await notify_owner("twitter", "Charlie", "urgent job opportunity")


@pytest.mark.asyncio
async def test_notify_owner_bridge_exception():
    """notify_owner handles GoBridge.send exception gracefully."""
    mock_bridge = MagicMock()
    mock_bridge.send = AsyncMock(side_effect=Exception("Bridge down"))

    with patch("watchers.social_dm_monitor.GoBridge", return_value=mock_bridge):
        from watchers.social_dm_monitor import notify_owner
        # Should not raise
        await notify_owner("facebook", "Eve", "payment discussion")


@pytest.mark.asyncio
async def test_notify_owner_truncates_long_snippet():
    """notify_owner message is capped at 500 chars per SC-003."""
    mock_bridge = MagicMock()
    mock_bridge.send = AsyncMock()

    long_snippet = "A" * 600
    with patch("watchers.social_dm_monitor.GoBridge", return_value=mock_bridge):
        from watchers.social_dm_monitor import notify_owner
        await notify_owner("facebook", "Dave", long_snippet)

    msg = mock_bridge.send.call_args[0][0]
    assert len(msg) <= 500


def test_log_audit_writes_entry(tmp_path):
    """_log_audit writes a JSON entry to audit log."""
    audit_log = tmp_path / "audit.jsonl"

    with patch("watchers.social_dm_monitor.AUDIT_LOG", audit_log):
        from watchers.social_dm_monitor import _log_audit
        _log_audit("test.action", "success")

    assert audit_log.exists()
    entry = json.loads(audit_log.read_text().strip())
    assert entry["action"] == "test.action"
    assert entry["outcome"] == "success"
    assert entry["agent"] == "social_dm_monitor"
    assert "ts" in entry


def test_log_audit_with_error_field(tmp_path):
    """_log_audit includes error field when provided."""
    audit_log = tmp_path / "audit.jsonl"

    with patch("watchers.social_dm_monitor.AUDIT_LOG", audit_log):
        from watchers.social_dm_monitor import _log_audit
        _log_audit("test.fail", "failure", error="something went wrong")

    entry = json.loads(audit_log.read_text().strip())
    assert entry["error"] == "something went wrong"


def test_log_audit_handles_write_error():
    """_log_audit doesn't raise when log write fails."""
    with patch("watchers.social_dm_monitor.AUDIT_LOG") as mock_path:
        mock_path.parent.mkdir.side_effect = PermissionError("no access")
        from watchers.social_dm_monitor import _log_audit
        # Should not raise
        _log_audit("test.action", "success")
