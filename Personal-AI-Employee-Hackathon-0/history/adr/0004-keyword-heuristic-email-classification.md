# ADR-0004: Keyword Heuristic Email Classification

> **Scope**: Defines the email classification strategy for Phase 2 -- keyword/pattern scoring to route emails as actionable vs. informational.

- **Status:** Accepted
- **Date:** 2026-02-17
- **Feature:** gmail-watcher (005)
- **Context:** The GmailWatcher must classify each email as "actionable" (routes to `vault/Needs_Action/`) or "informational" (routes to `vault/Inbox/`). The spec explicitly constrains Phase 2 to keyword/heuristic analysis -- LLM-based classification is deferred to Phase 3 when the Ralph Wiggum reasoning loop is available. The target accuracy is 80%+ (SC-005). The system must default to actionable (safer to surface than miss).

## Decision

Use **keyword score dictionaries** applied to sender, subject, and first 500 characters of body text, with a **default-to-actionable** policy.

Components:
- **ACTIONABLE_KEYWORDS**: Dictionary of keywords/phrases with positive scores (e.g., "urgent": 3, "action required": 5, "deadline": 3, "please review": 4, "approve": 4, "meeting": 2, "invoice": 3)
- **INFORMATIONAL_KEYWORDS**: Dictionary with positive scores (e.g., "newsletter": 5, "unsubscribe": 4, "no-reply": 3, "digest": 3, "automated": 3, "notification": 2)
- **INFORMATIONAL_SENDER_PATTERNS**: Regex patterns for known informational senders (e.g., `noreply@`, `notifications@`, `newsletter@`, `*@github.com` notifications)
- **Scoring algorithm**: Sum actionable score and informational score across sender+subject+body(500 chars). If informational_score > actionable_score by a configurable threshold (default: 2), classify as informational. Otherwise, classify as actionable (default-to-actionable policy).
- **Case-insensitive matching**: All comparisons lowercased
- **Phase 3 migration**: The `_classify_email()` method is isolated and can be replaced with an LLM call without changing the watcher lifecycle

## Consequences

### Positive

- Zero external dependencies -- pure Python string matching, no ML libraries, no API calls
- Deterministic and fast -- classification completes in microseconds, well within the 500ms poll overhead budget
- Transparent -- users can inspect and modify keyword lists; no black-box model behavior
- Default-to-actionable is the safer policy -- missing an actionable email is worse than surfacing an informational one
- Isolated method design enables clean Phase 3 swap to LLM classification without touching any other code
- Testable -- keyword lists can be unit-tested with known inputs/outputs

### Negative

- Lower accuracy than LLM-based classification -- expected 80%+ but will misclassify nuanced emails (e.g., an "urgent" newsletter, a casual email about a real deadline)
- Keyword lists require manual curation -- new patterns (e.g., a new automated sender) need list updates
- No learning -- classification doesn't improve over time (unlike ML approaches)
- Language-dependent -- English keywords only; multilingual inboxes will have lower accuracy
- Threshold tuning is manual -- the informational_score > actionable_score + 2 threshold is a guess, needs real-world calibration

## Alternatives Considered

**Alternative A: LLM-based classification (Claude API call per email)**
- Pros: High accuracy (95%+), handles nuance, multilingual, learns from context
- Cons: Spec explicitly prohibits in Phase 2; adds latency (1-3s per email); costs money per classification; requires API key management; Phase 3 dependency
- Rejected: Explicitly out of scope per spec constraints; deferred to Phase 3

**Alternative B: Pre-trained ML model (scikit-learn, spaCy)**
- Pros: Better accuracy than keywords (~90%), offline, no API costs
- Cons: Requires training data we don't have; adds heavy dependencies (numpy, scipy, sklearn); model maintenance burden; overkill for Phase 2 scope
- Rejected: No training data available; dependency weight disproportionate to Phase 2 scope

**Alternative C: Regex-only classification (no scoring)**
- Pros: Simpler than keyword scoring; well-understood pattern matching
- Cons: Binary match (no weighting); hard to express "newsletter with urgent language should still be informational"; no graceful degradation between categories
- Rejected: Scoring provides nuance that pure regex lacks; keyword dictionaries are barely more complex than regex lists

**Alternative D: Always actionable (no classification)**
- Pros: Zero implementation; guaranteed not to miss anything
- Cons: Floods `vault/Needs_Action/` with newsletters and notifications; makes the folder useless for prioritization; defeats the purpose of the watcher
- Rejected: Provides no value beyond basic email fetching

## References

- Feature Spec: `specs/005-gmail-watcher/spec.md` (FR-004, FR-006, SC-005, Edge Cases)
- Implementation Plan: `specs/005-gmail-watcher/plan.md`
- Related ADRs: ADR-0001 (BaseWatcher calls `process_item()` which triggers classification)
- Constitution: `.specify/memory/constitution.md` Principle VII (Phase-Gated -- no LLM in Phase 2)
