# ADR-0019: CEO Briefing LLM Fallback Strategy

- **Status:** Accepted
- **Date:** 2026-03-11
- **Feature:** ceo-briefing-odoo-gold (Phase 6)
- **Context:** The CEO daily briefing (FR-005) uses Claude (Anthropic SDK) to draft a
  natural-language narrative from structured data sections (email summary, Odoo financials,
  calendar, social media activity). However, Anthropic API credits can be zero at any point
  (confirmed as a current constraint during Phase 6 planning — user must top up manually).
  The briefing must still be delivered reliably every day regardless of credit status.
  A fallback strategy is required so that `ceo_briefing.py` does not hard-fail when the
  LLM is unavailable.

## Decision

Implement a **two-tier briefing generation** strategy in `orchestrator/ceo_briefing.py`:

**Tier 1 (primary):** LLM-assisted narrative via Anthropic SDK (`claude-sonnet-4-6`)
- Collects all data sections → passes structured dict to LLM prompt → returns full narrative
- Used when: `ANTHROPIC_API_KEY` is set AND credits are available (API returns 2xx)

**Tier 2 (fallback):** Template-based structured report
- Same data sections → rendered into a fixed markdown template with section headers and bullet lists
- Activated when: `anthropic.APIStatusError` (402/credit) or `anthropic.AuthenticationError` or any API exception
- Output is functionally complete (all data present) but stylistically structured rather than narrative

```python
async def draft_briefing(sections: dict, period: str) -> str:
    try:
        return await _llm_draft(sections, period)
    except Exception as e:
        logger.warning(f"LLM unavailable ({e}); using template fallback.")
        _log_audit("draft_briefing", "llm_fallback", 1, "fallback", str(e))
        return _template_draft(sections, period)
```

The fallback is **not** a degraded experience — it delivers the same data; only the prose
style changes. The WhatsApp HITL notification includes a flag `[TEMPLATE MODE]` so the owner
knows the narrative was not LLM-assisted.

## Consequences

### Positive

- **Briefing always delivered**: SC-001 (daily briefing ≤60s) and SC-003 (WhatsApp notification ≤90s) are met regardless of Anthropic credits status
- **Data collection fully independent of LLM**: Odoo, Calendar, Email, Social sections are collected before the draft step; a LLM failure does not re-run expensive data fetches
- **Transparent to owner**: `[TEMPLATE MODE]` flag in WhatsApp notification is honest about fallback state
- **Testable without API credits**: Unit tests can mock the Anthropic SDK and test both code paths; no live API calls required for CI
- **Zero additional dependencies**: Template rendering uses Python f-strings; no Jinja2 or additional library

### Negative

- Two code paths to maintain (LLM prompt + template); when adding new briefing sections, both paths must be updated
- Template output is less readable than LLM narrative (no synthesis, no trend analysis, no natural language interpretation)
- `[TEMPLATE MODE]` notifications may cause alarm fatigue if credits are empty for extended periods (mitigation: HT-013: top-up reminder task)
- LLM errors other than credit exhaustion (rate limit, model unavailable) also trigger template fallback — some of those errors might be transient and retryable (mitigated: `run_until_complete` handles transient errors with retry before reaching draft step)

## Alternatives Considered

**Alternative A: Hard-fail when LLM unavailable**
- Raise exception → `run_until_complete` exhausts retries → HITL escalation → no briefing delivered
- Rejected: Violates SC-001/SC-003 (briefing must be available). Credit exhaustion is a predictable
  operational condition, not an exceptional error; failing the entire workflow is disproportionate.

**Alternative B: Cache last LLM-generated briefing as fallback**
- Store most recent LLM narrative; on credit failure, deliver yesterday's briefing with a date stamp
- Rejected: Stale data is actively misleading (yesterday's overdue invoices presented as today's).
  Template fallback with today's real data is always more accurate than yesterday's narrative.

**Alternative C: Switch to local LLM (Ollama/Mistral) as secondary LLM**
- Run a local open-source model as fallback when Anthropic credits = 0
- Rejected: Requires GPU or significant RAM (8GB+ for smallest useful model); WSL2 environment
  may not have GPU passthrough configured; setup complexity violates ADR-0003 (local-first, minimal
  infrastructure). Phase 7 (Oracle VM) could revisit this.

**Alternative D: Separate daily briefing into two commands — data-only vs narrative**
- `--collect` always runs (data only); `--narrate` adds LLM (optional)
- Rejected: Operational complexity for a 1-person system; cron would need to chain two commands;
  the template fallback achieves the same separation internally with zero UX change.

## References

- Feature Spec: `specs/010-ceo-briefing-odoo-gold/spec.md` (FR-005, SC-001, SC-003, SC-005)
- Implementation Plan: `specs/010-ceo-briefing-odoo-gold/plan.md` (Phase E, T043 — `draft_briefing()` with template fallback)
- Related ADRs: ADR-0007 (MCP fallback protocol — graceful degradation pattern extended to LLM), ADR-0018 (Ralph Wiggum loop — `run_until_complete` retries before reaching fallback)
- Evaluator Evidence: `history/prompts/ceo-briefing-odoo-gold/001-phase6-gold-spec.spec.prompt.md` (Anthropic credits = 0 noted as known constraint)
