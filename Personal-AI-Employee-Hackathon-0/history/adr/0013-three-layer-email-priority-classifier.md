# ADR-0013: Three-Layer Email Priority Classifier

> **Scope**: Defines the tiered classification strategy for incoming emails — spanning spam filtering, keyword heuristics, and LLM fallback — and how the output drives HITL priority tagging, Calendar MCP invocation, and token cost management.

- **Status:** Accepted
- **Date:** 2026-03-02
- **Feature:** hitl-whatsapp-silver (008)
- **Context:** ADR-0004 (Phase 2) established a keyword heuristic email classifier for routing emails as actionable vs. informational. Phase 5 extends this with two critical additions: (1) a spam/auto-reply filter (Layer 1) that prevents draft creation for no-reply/newsletter emails entirely, and (2) an LLM classification fallback (Layer 3) for genuinely ambiguous emails where keywords are insufficient. The priority output (HIGH/MED/LOW) now directly drives HITL batch notification urgency tags (🔴/🟡/🟢) and triggers Calendar MCP queries. Token cost is a real concern — the owner explicitly noted that unnecessary LLM calls are costly and should be minimized. This requires a tiered approach rather than classifying all emails with LLM.

<!-- Significance checklist (ALL must be true to justify this ADR)
     1) Impact: Long-term consequence for architecture/platform/security? ✅ YES — affects token cost for every processed email; drives HITL UX; determines when Calendar MCP is invoked
     2) Alternatives: Multiple viable options considered with tradeoffs? ✅ YES — see Alternatives section
     3) Scope: Cross-cutting concern (not an isolated detail)? ✅ YES — orchestrator, HITL Manager, Calendar MCP, LLM provider all participate -->

## Decision

Implement a **three-layer tiered classifier** as `_classify_priority(subject, body) → PriorityClassification` in `orchestrator/orchestrator.py`:

### Layer 1 — Spam/Auto-reply Filter (zero tokens)
- **Trigger**: Pattern match on sender address and subject/body keywords
- **Patterns**: `noreply@`, `no-reply@`, `donotreply@`, `unsubscribe`, `newsletter`, `automated response`, `out of office`, `auto-reply`, `vacation notice`, `delivery status notification`, `mailer-daemon`
- **Action**: `priority = "SKIP"` → no draft created → email archived directly to vault/Done/
- **Token cost**: 0 (regex only)
- **Coverage estimate**: ~40-50% of raw email volume

### Layer 2 — Keyword Heuristic (zero tokens)
Extends ADR-0004 keyword approach; adds Calendar trigger:
- **HIGH keywords**: `urgent`, `asap`, `deadline`, `overdue`, `immediate`, `critical`, `emergency`
  → `priority = "HIGH"`, `trigger_calendar = False`
- **MED keywords**: `meeting`, `schedule`, `availability`, `call`, `appointment`, `calendar`, `reschedule`
  → `priority = "MED"`, `trigger_calendar = True` → Calendar MCP invoked before drafting
- **No match**: `priority = "AMBIGUOUS"` → Layer 3
- **Token cost**: 0 (keyword scan only)
- **Coverage estimate**: ~30-40% of non-spam emails

### Layer 3 — LLM Classification (AMBIGUOUS only)
- **Trigger**: Email passed Layers 1 and 2 with no keyword match
- **Implementation**: Single Claude API call with email subject + body snippet (≤500 chars)
- **Prompt**: Minimal — classify as HIGH / MED / LOW only; one-word response
- **Token estimate**: ~150-200 tokens per ambiguous email
- **Coverage estimate**: ~20-30% of non-spam emails (the genuinely ambiguous ones)
- **Output**: `priority = "HIGH" | "MED" | "LOW"`, `reasoning` (one sentence for PHR/debug)

### Priority-to-HITL Mapping
| Priority | Emoji | Urgency | Calendar Query |
|----------|-------|---------|----------------|
| HIGH     | 🔴   | Immediate review expected | No |
| MED      | 🟡   | Review within 24h | Yes (Layer 2 trigger) |
| LOW      | 🟢   | Review when convenient | No |
| SKIP     | —    | No draft; archived | No |

### Extends ADR-0004
ADR-0004 Layer 2 keyword heuristic is preserved unchanged. Phase 5 wraps it with Layers 1 (spam filter, new) and 3 (LLM fallback, new). The Layer 2 keyword lists are expanded with `schedule`, `reschedule`, `calendar` for Calendar MCP integration.

## Consequences

### Positive

- **Token efficiency**: ~70-80% of emails handled at zero LLM cost (Layers 1+2). LLM called only for genuinely ambiguous cases (~20-30%). At 100 emails/day, this reduces LLM calls from 100 to ~20-30.
- **Accuracy where it matters**: Layer 3 LLM classification is reserved for ambiguous emails where keyword matching would give wrong results. HIGH-priority emails are most likely to be caught by Layer 2 keywords; genuinely ambiguous ones get LLM attention.
- **Calendar MCP integration via Layer 2**: The `trigger_calendar` flag from Layer 2 MED classification cleanly separates "when to call Calendar MCP" from draft logic — no if/else chains in orchestrator.
- **Extensible**: Adding new HIGH/MED keywords requires editing one list in `orchestrator.py`. Adding a new classification tier (e.g., Layer 2.5 sender-reputation check) fits naturally between layers.
- **HITL UX driven by classification**: Priority emoji in batch notification gives owner immediate triage context — 🔴 emails get attention first.

### Negative

- **Layer 2 keyword false positives**: An email with "Urgent shipping update from your store" may be classified HIGH but is actually spam. Layer 1 should catch `noreply@` sender, but keyword spam emails from non-noreply senders slip through.
- **Layer 3 LLM latency**: LLM classification adds ~1-3s latency per ambiguous email. At 20-30 ambiguous emails/day, total added latency is 20-90s spread across the day — acceptable for async batch processing.
- **Layer 3 non-determinism**: LLM may classify the same email differently on different runs. Mitigated by single-word constrained output; cached per email (no re-classification of same message).
- **Layer 2 MED → Calendar MCP → latency**: Every MED email triggers a Calendar MCP call before drafting. At 5s Calendar MCP timeout and 20 MED emails/day, this adds ~100s of calendar latency across the day. Acceptable.

## Alternatives Considered

### Alternative A: Pure LLM classification (all emails) — rejected
Send all non-spam emails to LLM for HIGH/MED/LOW classification.
- **Pro**: Most accurate; no keyword maintenance; handles complex email content.
- **Con**: 100x higher token cost (100 LLM calls/day vs 20-30); owner explicitly noted this is "very costly"; adds 1-3s latency to every email. Rejected — token waste is unacceptable per owner's explicit preference.

### Alternative B: Pure rule-based (keyword only, no LLM) — rejected
Extend ADR-0004 keywords further; no LLM Layer 3.
- **Pro**: Zero token cost; deterministic; fast.
- **Con**: ~20-30% of emails are genuinely ambiguous — "Can we discuss this?" with no obvious keywords. These emails default to LOW, potentially missing important requests. Owner accuracy on ambiguous emails suffers. Rejected — LLM is the correct tool for ambiguous classification.

### Alternative C: Two-layer (spam filter + LLM, no keyword heuristic) — rejected
Skip keyword heuristic; route all non-spam to LLM.
- **Pro**: Simpler (no keyword lists to maintain); more accurate than keywords for MED detection.
- **Con**: ~70-80% of emails that keywords handle at zero cost now consume LLM tokens. Keyword heuristic is accurate for common cases (explicit HIGH/MED language). Rejected — wastes tokens on clear-cut cases.

### Alternative D: Sender reputation layer (email domain scoring) — deferred
Classify by sender domain reputation (known business domains = higher priority).
- **Pro**: Zero tokens; accurate for known senders.
- **Con**: Requires maintaining a sender reputation database; complex cold-start problem for new senders; adds Phase 6 complexity. Deferred to Phase 6 — may be added as Layer 1.5 if Layer 1 spam filter proves insufficient.

## References

- Feature Spec: `specs/008-hitl-whatsapp-silver/spec.md` (FR-025; SC-006)
- Implementation Plan: `specs/008-hitl-whatsapp-silver/plan.md` (Phase F — Orchestrator Integration)
- Research: `specs/008-hitl-whatsapp-silver/research.md` (Decision 5)
- Data Model: `specs/008-hitl-whatsapp-silver/data-model.md` (Section 6: PriorityClassification dataclass; Section 7: Email Priority Classification State Machine)
- Related ADRs: ADR-0004 (Phase 2 keyword heuristic — superseded at Layer 2; this ADR extends, not replaces, ADR-0004), ADR-0011 (HITL batch notification uses priority output), ADR-0012 (WhatsApp MCP sends batch notifications with priority emoji)
- Clarification Session: `history/prompts/hitl-whatsapp-silver/002-phase5-hitl-spec-clarification.spec.prompt.md` (Q5: owner left classifier design to agent; reasoning documented here)
- Evaluator Evidence: `history/prompts/hitl-whatsapp-silver/003-phase5-hitl-plan.plan.prompt.md`
