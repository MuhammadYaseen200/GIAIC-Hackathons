# ADR-0018: Ralph Wiggum Loop Implementation Pattern

- **Status:** Accepted
- **Date:** 2026-03-11
- **Feature:** ceo-briefing-odoo-gold (Phase 6)
- **Context:** The Gold Tier specification requires a "Ralph Wiggum loop for autonomous
  multi-step task completion" (Section 2D of the hackathon document). The project already has
  a 15-minute orchestrator polling loop (Phase 3, `orchestrator/orchestrator.py`) which
  constitutes the outer Ralph Wiggum loop. Phase 6 needs per-workflow-step retry logic
  (collect data, draft briefing, write vault, send notification) so that transient errors
  in one step do not abort the entire workflow. Multiple implementation strategies exist for
  this inner retry loop.

## Decision

Implement a **new `run_until_complete()` async utility** in `orchestrator/run_until_complete.py`
that wraps any sequence of workflow steps with per-step retry and exponential backoff:

```python
async def run_until_complete(
    workflow_name: str,
    steps: list[tuple[str, Callable[[], Awaitable[Any]]]],
    max_retries: int = 3,
    on_exhausted: Callable[[str, str, Exception], Awaitable[None]] | None = None,
) -> dict:
```

- Each step is retried independently up to `max_retries=3` times
- Backoff: `2^(attempt-1)` seconds (1s, 2s, 4s between retries)
- On exhaustion: calls `on_exhausted` callback (HITL WhatsApp notification) then returns `{"status": "failed"}`
- On success: logs to `vault/Logs/audit.jsonl` and continues to next step
- The existing 15-min orchestrator polling loop (outer Ralph Wiggum) remains unchanged

This utility is NOT a general workflow engine — it is a minimal, purpose-built retry wrapper
scoped to H0 workflows (briefing, audit, social posting).

## Consequences

### Positive

- **Separation of concerns**: Each workflow step function stays clean and throwable; `run_until_complete` owns all retry/backoff logic
- **Reusable across workflows**: `ceo_briefing.py`, `weekly_audit.py`, and `social_poster.py` all share the same retry primitive — consistent behavior
- **Audit log built-in**: Every step attempt (success or failure) is logged to `audit.jsonl` without callers needing to remember to log
- **HITL escalation on exhaustion**: Meets FR-029/FR-030: autonomous retry first, human escalation only when retries exhausted
- **Testable in isolation**: `test_run_until_complete.py` can test the retry logic with mock step functions without needing real MCP servers
- **Minimal code**: ~60 lines — no external workflow library required

### Negative

- Steps are strictly sequential; no parallel step execution within a workflow (acceptable: briefing steps are data-dependent)
- No persistent state across process restarts — if orchestrator process dies mid-workflow, recovery requires re-running from step 1 (acceptable for daily briefing cadence)
- Max retries is hardcoded at call sites; different workflows cannot yet dynamically adjust retry count (mitigated: `max_retries` is a parameter)
- Exponential backoff adds up to 7s overhead on full 3-retry exhaustion (1+2+4) — within SC-001 60s budget for most steps

## Alternatives Considered

**Alternative A: Extend existing 15-min orchestrator polling as the only retry mechanism**
- Allow the orchestrator's next 15-min cycle to retry a failed briefing step
- Rejected: 15-minute retry interval violates SC-001 (briefing must complete ≤60s). A network
  hiccup on Odoo query would delay the entire daily briefing by 15 minutes minimum.

**Alternative B: External workflow engine (Celery, Temporal, Prefect)**
- Production-grade workflow orchestration with persistent task queues, distributed retry, and visibility dashboards
- Rejected: Massive dependency overhead for a single-owner local system; requires Redis/RabbitMQ broker;
  violates ADR-0003 (local-first, no cloud dependencies). Gold Tier target is Oracle VM (Phase 7), not
  a distributed Kubernetes cluster.

**Alternative C: `tenacity` library retry decorator**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def collect_odoo_section(): ...
```
- Cleaner decorator syntax; well-tested library
- Rejected: Decorators on individual step functions scatter retry config across the codebase;
  HITL escalation callback pattern not natively supported by tenacity; audit logging requires
  additional before/after hooks. The custom `run_until_complete()` keeps all cross-cutting
  concerns (logging, escalation) in one place.

**Alternative D: Recursive self-calling ("true Ralph Wiggum")**
- Each step function calls itself recursively on failure until a "done" condition
- Rejected: Stack depth unbounded; harder to unit test; harder to reason about backoff timing;
  `run_until_complete()` achieves the same semantic with a simple loop.

## References

- Feature Spec: `specs/010-ceo-briefing-odoo-gold/spec.md` (FR-029, FR-030, Section 2D)
- Implementation Plan: `specs/010-ceo-briefing-odoo-gold/plan.md` (Phase F, T059–T065)
- Related ADRs: ADR-0002 (async integration pattern), ADR-0007 (MCP fallback protocol — graceful degradation extended here), ADR-0011 (HITL workflow — escalation on exhaustion)
- Evaluator Evidence: `history/prompts/ceo-briefing-odoo-gold/002-phase6-gold-clarify-social-ralph.clarify.prompt.md` (Q3: run_until_complete wrapper confirmed)
