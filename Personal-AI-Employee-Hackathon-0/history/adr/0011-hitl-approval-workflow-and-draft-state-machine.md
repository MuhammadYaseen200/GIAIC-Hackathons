# ADR-0011: HITL Approval Workflow and Draft State Machine

> **Scope**: Defines the complete Human-in-the-Loop approval architecture for Phase 5 Silver tier — vault-based state machine, draft ID scheme, batch notification strategy, command protocol, timeout lifecycle, and audit logging.

- **Status:** Accepted
- **Date:** 2026-03-02
- **Feature:** hitl-whatsapp-silver (008)
- **Context:** Constitution Principle III mandates that any action sending data externally (email send) requires explicit human approval via `vault/Pending_Approval/` → `vault/Approved/` flow. Phase 5 makes this concrete: the orchestrator drafts email replies, which must be reviewed by the owner via WhatsApp before Gmail MCP sends them. The HITL system must handle concurrent drafts (multiple emails drafted in the same poll cycle), notification delivery, owner command parsing, 24h/48h timeouts, and an audit trail — all without a database (Neon is Phase 6+).

<!-- Significance checklist (ALL must be true to justify this ADR)
     1) Impact: Long-term consequence for architecture/platform/security? ✅ YES — defines the approval contract for the entire Silver tier; all future approval flows reuse this pattern
     2) Alternatives: Multiple viable options considered with tradeoffs? ✅ YES — see Alternatives section
     3) Scope: Cross-cutting concern (not an isolated detail)? ✅ YES — orchestrator, vault, WhatsApp MCP, Gmail MCP all participate -->

## Decision

Build the HITL workflow as a **vault-filesystem state machine** with `HITLManager` as the lifecycle controller:

### State Machine
- **States**: `pending` → `approved` | `rejected` | `awaiting_reminder` | `timed_out`
- **State store**: YAML frontmatter in vault files (human-readable in Obsidian; no DB required)
- **Transitions as file moves**: `vault/Pending_Approval/` → `vault/Approved/` (on approve), `vault/Rejected/` (on reject)
- **In-place state updates**: `awaiting_reminder` and `timed_out` update frontmatter in-place (file stays in `Pending_Approval/`)

### Draft ID Format
- Pattern: `<YYYYMMDD-HHMMSS>-<8-char-lowercase-hex>` (e.g., `20260302-143022-a1b2c3d4`)
- Collision probability: ~1/65536 per second — negligible; increment suffix on rare collision
- Embeds timestamp in ID — enables age-based timeout scanning without reading full frontmatter

### Batch Notification Protocol
- Owner receives ONE WhatsApp summary message per batch window (default: 120s after first new draft)
- Message format: `📋 N drafts pending:\n1. 🔴 [HIGH] <draft_id_short> — <recipient> — <subject>\n...`
- Priority emoji: 🔴 HIGH / 🟡 MED / 🟢 LOW (driven by tiered classifier in ADR-0013)
- Maximum 5 drafts per batch; overflow held in in-memory queue for next batch
- On update within batch window: updated message sent (not duplicate)

### Command Protocol
- Accept: `approve <draft_id>` or `reject <draft_id>` (case-insensitive; first 8 hex chars sufficient)
- Ambiguous reply → clarification message sent; no irreversible action taken
- Unknown draft ID → error message; no irreversible action taken

### Timeout Lifecycle
- 24h with no response: status → `awaiting_reminder`; send WhatsApp reminder; no email sent
- 48h with no response: status → `timed_out`; no email sent; draft stays in `Pending_Approval/`

### Audit Log
- `vault/Logs/hitl_decisions.jsonl`: `{draft_id, decision, decided_at, decided_by, sent_at}` — append-only

### Concurrent Draft Handling
- `HITLManager` maintains in-memory `_pending_notification_queue`
- Each draft identified by unique `draft_id` — concurrent operations are independent
- File lock not needed: `atomic_write` + unique filenames prevent collision

## Consequences

### Positive

- **No database required for Phase 5**: vault filesystem is sufficient for state management at current scale (~10 concurrent drafts max).
- **Human-readable state**: Owner can open `vault/Pending_Approval/` in Obsidian and see full draft context, status, and history.
- **Audit trail built-in**: YAML frontmatter tracks `decided_at` + JSONL log provides structured audit for all decisions.
- **HITL invariant enforced**: `reversible: false` in frontmatter + code path that blocks email send unless status == "approved" satisfies Constitution Principle III.
- **Batch notification reduces notification fatigue**: Single message per polling window vs N individual pings on busy email days.
- **Reusable pattern**: Future HITL flows (WhatsApp replies, Odoo actions in Phase 6) follow the same `Pending_Approval/` → `Approved/` file-move pattern.

### Negative

- **No real-time push**: Timeout checks run on poll cycle intervals — a 48h draft may sit until the next `check_timeouts()` poll. Acceptable given batch polling architecture.
- **In-memory notification queue is ephemeral**: If orchestrator crashes between draft write and batch notification, queue is lost — draft stays in `Pending_Approval/` but no notification is sent. Owner can still see draft in Obsidian. Mitigated by `notified_at=null` check on restart.
- **Single approver**: Architecture assumes one owner; no multi-approval or delegation in Phase 5.
- **Vault scale limit**: Hundreds of drafts in `Pending_Approval/` would require vault scan on each poll. At 100 emails/day and 24h retention, worst-case is ~100 files — acceptable without indexing.

## Alternatives Considered

### Alternative A: SQLite/Neon DB state machine (rejected for Phase 5)
Store draft state in a database table with proper foreign keys and transactions.
- **Pro**: ACID guarantees; proper concurrent access; queryable.
- **Con**: Neon is Phase 6+ dependency; SQLite adds a new tech component; vault is already the system's source of truth per Constitution Principle V; database migration complexity for such simple state. Rejected for Phase 5 — may revisit in Phase 6 when Neon is introduced.

### Alternative B: Email-based approval (rejected)
Send approval requests to owner's email; owner replies to approve/reject.
- **Pro**: No WhatsApp dependency for approval; fallback if WhatsApp is down.
- **Con**: Slower UX (email requires opening app, reading email, replying); harder to parse structured commands in email replies; defeats the purpose of WhatsApp-centric Silver tier. Rejected.

### Alternative C: Individual notifications per draft (rejected)
Send a separate WhatsApp message for each draft as soon as it's created.
- **Pro**: Immediate notification; simpler implementation (no batch queue).
- **Con**: Notification flood on busy email days (e.g., 20 emails processed → 20 WhatsApp pings); degrades UX; owner explicitly requested batch approach. Rejected per clarification session 2026-03-02.

### Alternative D: Telegram/Signal for approval channel (rejected)
Use a different messaging platform for HITL notifications.
- **Pro**: May have better bot API; no Meta dependency.
- **Con**: Owner is on WhatsApp (HT-004 done); introducing a second messaging platform adds HT tasks and UX friction. Rejected — WhatsApp is the chosen owner communication channel.

## References

- Feature Spec: `specs/008-hitl-whatsapp-silver/spec.md` (FR-012 through FR-020, FR-040, FR-041; SC-002 through SC-005)
- Implementation Plan: `specs/008-hitl-whatsapp-silver/plan.md` (Phase D — HITL Manager)
- Research: `specs/008-hitl-whatsapp-silver/research.md` (Decision 2, Decision 4)
- Data Model: `specs/008-hitl-whatsapp-silver/data-model.md` (Section 4: HITL Manager models; Section 7: State Transitions)
- Related ADRs: ADR-0003 (JSONL audit log pattern), ADR-0007 (MCPClient used by HITLManager to call Gmail MCP and WhatsApp MCP), ADR-0008 (error codes for HITL send failures)
- Loop.md: `ai-control/LOOP.md` (Loop 3: Human-in-the-Loop)
- Evaluator Evidence: `history/prompts/hitl-whatsapp-silver/003-phase5-hitl-plan.plan.prompt.md`
