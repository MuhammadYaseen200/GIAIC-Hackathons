# ADR-0010: Privacy Gate — Mandatory Pre-Processing Layer

> **Scope**: Defines the architecture and enforcement mechanism for the Privacy Gate — a mandatory pre-processing layer that intercepts all incoming content before any vault write or LLM call in the AI Employee system.

- **Status:** Accepted
- **Date:** 2026-03-02
- **Feature:** hitl-whatsapp-silver (008)
- **Context:** The owner has a non-negotiable privacy requirement that sensitive text (passwords, OTPs, PINs, card numbers, secrets) and all media content (images, video, audio) must NEVER be stored, processed by AI, or forwarded — even accidentally. Phase 5 introduces WhatsApp message ingestion, creating a new attack surface for sensitive content entering the vault. The existing Gmail watcher also has no protection. Any future watcher (WhatsApp, SMS, filesystem) faces the same risk. A security/privacy policy applied inconsistently per-watcher would be brittle and error-prone.

<!-- Significance checklist (ALL must be true to justify this ADR)
     1) Impact: Long-term consequence for architecture/platform/security? ✅ YES — applies to all future watchers; religious obligation
     2) Alternatives: Multiple viable options considered with tradeoffs? ✅ YES — see Alternatives section
     3) Scope: Cross-cutting concern (not an isolated detail)? ✅ YES — pre-empts vault writes and LLM calls system-wide -->

## Decision

Build the Privacy Gate as a **shared standalone pure-function utility module** (`watchers/privacy_gate.py`) with the following design:

- **Position**: Layer 0 — the FIRST step of `process_item()` in every watcher, before any vault write, LLM call, or HITL notification.
- **Sensitive text redaction**: Regex-based scan replaces matched sensitive patterns with `[REDACTED-*]` tokens. Patterns cover: passwords, PINs, OTPs (including bare 6-digit codes), card numbers (13-19 digits), CVV/CVC, API keys/secrets/tokens.
- **Media absolute block**: If `media_type != "text"`, the message body is unconditionally replaced with `"[MEDIA — content not stored]"`. No binary content ever reaches vault or LLM. This is unconditional — no exceptions regardless of caption context.
- **Implementation**: `run_privacy_gate(body, media_type, caption) → PrivacyGateResult` — pure function with zero side effects. No I/O, no imports from watchers or orchestrator (zero circular dependency risk).
- **Privacy alert**: When redaction occurs, a WhatsApp alert is sent to `OWNER_WHATSAPP_NUMBER` via WhatsApp MCP. Alert contains NO portion of the original content.
- **Audit log**: `vault/Logs/privacy_gate.jsonl` — presence flags only (`redaction_applied`, `media_blocked`, `timestamp`). No original content in log.
- **Retrofit**: Privacy Gate is applied to Gmail watcher (`watchers/gmail_watcher.py`) as a one-line change: import + call in `process_item()` before `atomic_write`.
- **New watchers**: Constitution mandate — every future watcher MUST call `run_privacy_gate()` as Layer 0 in `process_item()`.

## Consequences

### Positive

- **Religious compliance guaranteed**: Sensitive content can never reach the vault, LLM, or any external API — even if a message contains OTPs or private images.
- **Security hardening system-wide**: Even non-religious users benefit — passwords sent via WhatsApp or Gmail attachments never persist in plaintext.
- **Independently testable**: Pure function with no I/O enables comprehensive unit testing with 100% coverage of all regex patterns without live watchers.
- **Zero circular dependencies**: Module imports only `re`, `dataclasses`, `datetime` from stdlib. Safe to import from any watcher.
- **One-line Gmail retrofit**: Existing Phase 2/3 tests are unaffected because fixture emails contain no sensitive patterns. If they did, asserting `[REDACTED]` is the correct test behavior.
- **Extensible**: Adding a new sensitive pattern requires changing one list in `privacy_gate.py`; all watchers automatically benefit.

### Negative

- **False positive risk**: 6-digit order numbers, postal codes, or product codes may be flagged as OTPs. Owner sees `[REDACTED]` in vault and must check phone for original. This is an acceptable tradeoff — errs on the side of privacy.
- **Privacy alert noise**: Redaction events trigger WhatsApp alerts; on high-volume days with many 6-digit codes, this could generate alert noise. Mitigation: batch privacy alerts (future enhancement).
- **Regex limitation**: Sophisticated attackers or unusual formats may evade pattern matching. Mitigation: patterns are conservative (broad matching preferred over narrow).
- **No audit of original content**: By design, original sensitive content is never logged. This means post-incident forensics cannot recover original messages. Acceptable given privacy mandate.

## Alternatives Considered

### Alternative A: Per-watcher inline redaction (rejected)
Each watcher implements its own privacy filtering.
- **Pro**: No shared dependency; each watcher fully self-contained.
- **Con**: Privacy invariant duplicated across 3+ watchers; inconsistent patterns; easy to forget in new watchers; divergent behavior over time. Rejected — violates DRY and makes privacy a watcher-implementation detail rather than a system guarantee.

### Alternative B: Post-write vault scanner (rejected)
Write raw content to vault first, then scan and redact asynchronously.
- **Pro**: Simpler watcher code; scanning can be retried.
- **Con**: Raw sensitive content briefly on disk (window of exposure); LLM may see it during the gap; violates the "never on disk" requirement. Rejected — creates race condition and violates the privacy contract.

### Alternative C: Cloud content moderation API (e.g., Google Cloud DLP) (rejected)
Route all content through a cloud API for sensitive data detection.
- **Pro**: More accurate than regex; handles unstructured sensitive data.
- **Con**: Requires sending content to cloud (violates Constitution Principle II — Local-First Privacy); adds latency; costs money; requires internet. Fundamentally incompatible with local-first mandate. Rejected.

### Alternative D: LLM-based privacy detection (rejected)
Ask the LLM to detect and redact sensitive content before vault write.
- **Pro**: Handles complex/unstructured sensitive patterns.
- **Con**: Sends sensitive content to LLM API before deciding to redact — circular problem. LLM tokens consumed per message. Non-deterministic behavior. Rejected — you cannot use the LLM to decide if content is safe to send to the LLM.

## References

- Feature Spec: `specs/008-hitl-whatsapp-silver/spec.md` (FR-031 through FR-039; SC-009, SC-010)
- Implementation Plan: `specs/008-hitl-whatsapp-silver/plan.md` (Phase A)
- Research: `specs/008-hitl-whatsapp-silver/research.md` (Decision 3)
- Data Model: `specs/008-hitl-whatsapp-silver/data-model.md` (Section 1: Privacy Gate models)
- Related ADRs: ADR-0001 (BaseWatcher ABC — Privacy Gate runs inside process_item()), ADR-0003 (JSONL logging pattern used by privacy_gate.jsonl)
- Evaluator Evidence: `history/prompts/hitl-whatsapp-silver/002-phase5-hitl-spec-clarification.spec.prompt.md`
