"""Ralph Wiggum Loop — run_until_complete utility.

Per ADR-0018: per-step retry with exponential backoff, HITL escalation on exhaustion.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

VAULT_PATH = Path(os.getenv("VAULT_PATH", "vault"))
AUDIT_LOG = VAULT_PATH / "Logs" / "audit.jsonl"

BACKOFF_BASE = 2  # ADR-0018: exponential backoff base (1s, 2s, 4s)


def _log_audit(workflow: str, step: str, attempt: int, outcome: str, error: str = "", duration_ms: int = 0) -> None:
    """Write one audit log entry to vault/Logs/audit.jsonl."""
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "workflow": workflow,
            "step": step,
            "attempt": attempt,
            "outcome": outcome,
            "error": error,
            "duration_ms": duration_ms,
        }
        with AUDIT_LOG.open("a") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception as e:
        logger.warning(f"_log_audit failed: {e}")


async def run_until_complete(
    workflow_name: str,
    steps: list[tuple[str, Callable[[], Awaitable[Any]]]],
    max_retries: int = 3,
    on_exhausted: Callable[[str, str, Exception], Awaitable[None]] | None = None,
) -> dict:
    """Execute steps with per-step retry and exponential backoff.

    Args:
        workflow_name: Name for audit logging.
        steps: List of (step_name, async_callable) tuples.
        max_retries: Max attempts per step (default: 3).
        on_exhausted: Async callback(workflow, step, exception) on exhaustion.

    Returns:
        {"status": "complete", "completed": [...]} on success.
        {"status": "failed", "failed_step": ..., "completed": [...], "error": ...} on failure.
    """
    if not steps:
        logger.warning(f"run_until_complete called with 0 steps for workflow '{workflow_name}' — nothing to do")
        return {"status": "complete", "completed": [], "workflow": workflow_name}

    completed: list[str] = []

    for step_name, step_fn in steps:
        last_exception: Exception | None = None

        for attempt in range(1, max_retries + 1):
            try:
                step_start = time.monotonic()
                await step_fn()
                duration_ms = round((time.monotonic() - step_start) * 1000)
                _log_audit(workflow_name, step_name, attempt, "success", duration_ms=duration_ms)
                completed.append(step_name)
                break
            except Exception as e:
                duration_ms = round((time.monotonic() - step_start) * 1000)
                last_exception = e
                _log_audit(workflow_name, step_name, attempt, "failed", str(e), duration_ms=duration_ms)
                logger.warning(
                    f"[{workflow_name}] step={step_name} attempt={attempt}/{max_retries} error={e}"
                )

                if attempt < max_retries:
                    backoff = BACKOFF_BASE ** (attempt - 1)  # 1s, 2s, 4s
                    await asyncio.sleep(backoff)
                else:
                    # Exhausted
                    if on_exhausted:
                        try:
                            await on_exhausted(workflow_name, step_name, e)
                        except Exception as cb_err:
                            logger.error(f"on_exhausted callback failed: {cb_err}")

                    return {
                        "status": "failed",
                        "failed_step": step_name,
                        "completed": completed,
                        "error": str(last_exception),
                    }

    return {"status": "complete", "completed": completed}
