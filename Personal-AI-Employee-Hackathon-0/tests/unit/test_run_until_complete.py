"""Unit tests for run_until_complete Ralph Wiggum loop. RED first."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


@pytest.mark.asyncio
async def test_all_steps_success():
    """run_until_complete returns status=complete when all steps succeed."""
    from orchestrator.run_until_complete import run_until_complete

    step1 = AsyncMock(return_value="ok1")
    step2 = AsyncMock(return_value="ok2")

    result = await run_until_complete(
        "test_workflow",
        [("step1", step1), ("step2", step2)],
    )

    assert result["status"] == "complete"
    assert "step1" in result["completed"]
    assert "step2" in result["completed"]


@pytest.mark.asyncio
async def test_single_step_fails_then_succeeds():
    """Step that fails once succeeds on retry."""
    from orchestrator.run_until_complete import run_until_complete

    call_count = 0

    async def flaky_step():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Temporary failure")
        return "ok"

    result = await run_until_complete(
        "test_workflow",
        [("flaky", flaky_step)],
        max_retries=3,
    )

    assert result["status"] == "complete"
    assert call_count == 2


@pytest.mark.asyncio
async def test_step_exhausts_retries_returns_failed():
    """Step that always fails returns status=failed after max_retries."""
    from orchestrator.run_until_complete import run_until_complete

    always_fails = AsyncMock(side_effect=RuntimeError("Always fails"))

    result = await run_until_complete(
        "test_workflow",
        [("bad_step", always_fails)],
        max_retries=3,
    )

    assert result["status"] == "failed"
    assert result["failed_step"] == "bad_step"
    assert always_fails.call_count == 3


@pytest.mark.asyncio
async def test_on_exhausted_callback_called():
    """on_exhausted callback is called when retries exhausted."""
    from orchestrator.run_until_complete import run_until_complete

    on_exhausted = AsyncMock()
    always_fails = AsyncMock(side_effect=RuntimeError("fail"))

    await run_until_complete(
        "test_wf",
        [("bad", always_fails)],
        max_retries=2,
        on_exhausted=on_exhausted,
    )

    on_exhausted.assert_called_once()
    args = on_exhausted.call_args[0]
    assert args[0] == "test_wf"  # workflow_name
    assert args[1] == "bad"  # step_name


@pytest.mark.asyncio
async def test_backoff_timing_increases():
    """Retry backoff follows 2^(attempt-1) pattern."""
    from orchestrator.run_until_complete import run_until_complete

    sleep_calls = []

    async def mock_sleep(seconds):
        sleep_calls.append(seconds)

    always_fails = AsyncMock(side_effect=RuntimeError("fail"))

    with patch("orchestrator.run_until_complete.asyncio.sleep", side_effect=mock_sleep):
        await run_until_complete(
            "test_wf",
            [("step", always_fails)],
            max_retries=3,
        )

    # Backoff: 1s after attempt 1, 2s after attempt 2 (no sleep after last)
    assert len(sleep_calls) == 2
    assert sleep_calls[0] == 1  # 2^(1-1) = 1
    assert sleep_calls[1] == 2  # 2^(2-1) = 2


@pytest.mark.asyncio
async def test_completed_steps_recorded():
    """Completed steps are recorded in result even on later failure."""
    from orchestrator.run_until_complete import run_until_complete

    step1 = AsyncMock(return_value="ok")
    step2 = AsyncMock(side_effect=RuntimeError("step2 fails"))

    result = await run_until_complete(
        "test_wf",
        [("step1", step1), ("step2", step2)],
        max_retries=1,
    )

    assert result["status"] == "failed"
    assert "step1" in result["completed"]
    assert result["failed_step"] == "step2"


@pytest.mark.asyncio
async def test_audit_log_written_per_attempt():
    """_log_audit is called for every attempt."""
    from orchestrator.run_until_complete import run_until_complete

    with patch("orchestrator.run_until_complete._log_audit") as mock_log:
        step = AsyncMock(return_value="ok")
        await run_until_complete("wf", [("s", step)], max_retries=3)

        # At least one log call for successful step
        assert mock_log.called


@pytest.mark.asyncio
async def test_previous_steps_not_retried_on_later_failure():
    """When step N fails, steps 0..N-1 are NOT retried."""
    from orchestrator.run_until_complete import run_until_complete

    step1 = AsyncMock(return_value="ok")
    step2 = AsyncMock(side_effect=RuntimeError("fail"))

    await run_until_complete(
        "wf",
        [("step1", step1), ("step2", step2)],
        max_retries=3,
    )

    # step1 called once (succeeds), step2 called 3 times (retried)
    assert step1.call_count == 1
    assert step2.call_count == 3


@pytest.mark.asyncio
async def test_run_until_complete_used_by_briefing():
    """run_until_complete is used inside run_daily_briefing."""
    with patch("orchestrator.run_until_complete.run_until_complete") as mock_ruc:
        mock_ruc.return_value = {"status": "complete", "completed": []}
        import orchestrator.ceo_briefing as briefing
        # Verify run_until_complete is importable from within ceo_briefing module
        import inspect
        src = inspect.getsource(briefing)
        assert "run_until_complete" in src


@pytest.mark.asyncio
async def test_run_until_complete_used_by_weekly_audit():
    """run_until_complete is used inside run_weekly_audit."""
    import orchestrator.weekly_audit as audit
    import inspect
    src = inspect.getsource(audit)
    assert "run_until_complete" in src


@pytest.mark.asyncio
async def test_every_step_logged_to_audit_jsonl(tmp_path):
    """Every step attempt is written to audit.jsonl."""
    import json
    from orchestrator.run_until_complete import run_until_complete, AUDIT_LOG
    import orchestrator.run_until_complete as ruc_mod

    audit_log = tmp_path / "audit.jsonl"
    original_log = ruc_mod.AUDIT_LOG
    ruc_mod.AUDIT_LOG = audit_log

    try:
        step1 = AsyncMock(return_value="ok")
        step2 = AsyncMock(side_effect=[RuntimeError("fail"), None])

        await run_until_complete(
            "test_wf",
            [("step1", step1), ("step2", step2)],
            max_retries=3,
        )

        lines = audit_log.read_text().strip().split("\n")
        entries = [json.loads(l) for l in lines]
        # step1 success + step2 fail + step2 success
        assert len(entries) >= 3
        assert all("ts" in e and "outcome" in e and "step" in e for e in entries)
        outcomes = [e["outcome"] for e in entries]
        assert "success" in outcomes
        assert "failed" in outcomes
    finally:
        ruc_mod.AUDIT_LOG = original_log


@pytest.mark.asyncio
async def test_on_exhausted_sends_whatsapp_notification():
    """on_exhausted callback fires when all retries fail; test with GoBridge mock."""
    from orchestrator.run_until_complete import run_until_complete

    whatsapp_messages = []

    async def mock_on_exhausted(workflow, step, exc):
        whatsapp_messages.append(f"{workflow}/{step}: {exc}")

    always_fails = AsyncMock(side_effect=RuntimeError("network down"))

    result = await run_until_complete(
        "briefing",
        [("collect_odoo", always_fails)],
        max_retries=2,
        on_exhausted=mock_on_exhausted,
    )

    assert result["status"] == "failed"
    assert len(whatsapp_messages) == 1
    assert "briefing" in whatsapp_messages[0]
    assert "collect_odoo" in whatsapp_messages[0]
