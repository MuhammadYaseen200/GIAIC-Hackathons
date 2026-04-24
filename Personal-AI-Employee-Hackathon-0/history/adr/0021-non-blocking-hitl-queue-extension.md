# ADR-0021: Non-Blocking HITL Queue Extension

- **Status:** Accepted
- **Date:** 2026-04-11
- **Feature:** full-comms-automation (Phase 6.5)
- **Context:** ADR-0011 defined the HITL approval workflow for Phase 5 as a vault-filesystem
  state machine with hard timeouts: 24h reminder, 48h timeout-and-cancel. This design made
  sense for Phase 5's single use case (email draft approval) where a stale approval after
  48h was legitimately expired. Phase 6.5 introduces HITL across 5 platforms with a much
  higher volume of approval requests (WhatsApp media sends, LinkedIn reactions, calendar
  creates, social posts, Gmail drafts). The owner explicitly clarified (sp.clarify Q1):
  "when agent leave a mesg, it should not wait — just leave and when I get the mesg and
  free to reply, I'll, then agent wakeup and start proceeding."
  Two problems with the current `hitl_manager.py`:
  1. The in-memory notification queue (`self._notification_queue: list[str]`) is lost on
     process restart — any pending approvals are permanently lost if the process restarts.
  2. Hard 48h timeout cancels actions the owner may still want to approve later (e.g., a
     WhatsApp message drafted while travelling and approved 3 days later).
  A new queue behavior is needed: fire-and-forget, indefinitely persistent, with briefing
  reminders rather than hard timeouts.

## Decision

**Extend `orchestrator/hitl_manager.py` with a SQLite persistence layer. Change the timeout
behavior from hard-cancel to soft-reminder.** Do NOT rebuild the state machine — preserve
the vault-filesystem draft format and file-move state transitions from ADR-0011.

### Non-Blocking Behavior (new in Phase 6.5)
- `submit_draft()` enqueues and returns immediately — no waiting for owner response
- Calling code does NOT await approval before proceeding to the next task
- Approved actions are executed by a separate `execute_approved()` sweep (called by watchers
  and at briefing generation time)

### Persistence Layer (new in Phase 6.5)
- New file: `orchestrator/hitl_queue.py` — thin SQLite wrapper
- Database: `vault/hitl_queue.db` (WAL mode, local-first per ADR-0003)
- `CommunicationAction` table: id, platform, action_type, summary, content_ref, status,
  sent_at, responded_at, executed_at, retry_count, error_msg
- `hitl_manager.submit_draft()` writes to BOTH vault file (ADR-0011 state machine, preserved
  for human readability in Obsidian) AND SQLite queue (for cross-restart durability)
- On startup: scan `vault/Pending_Approval/` → sync any vault files not in SQLite queue

### Timeout Behavior Change (Phase 5 → Phase 6.5)
- **REMOVE** hard 24h reminder / 48h cancel enforcement
- **REPLACE** with: pending actions surface in daily CEO briefing as reminders (no deadline)
- Actions remain `pending` indefinitely until owner approves or explicitly declines
- `hitl_manager.get_pending_for_briefing()` returns all pending items for briefing section

### New Action Types Supported (Phase 6.5)
Extend `ActionType` enum: `whatsapp_text`, `whatsapp_media`, `whatsapp_group_create`,
`whatsapp_status`, `linkedin_post`, `linkedin_react`, `linkedin_comment`, `linkedin_connect`,
`facebook_post`, `facebook_reply`, `twitter_post`, `twitter_reply`, `calendar_create`,
`calendar_delete`, `gmail_draft_send` (was `email_send` in Phase 5)

## Consequences

### Positive
- **Never lose a pending approval**: SQLite persistence means process restart does not lose
  the queue — all pending items resume on next run
- **Owner-friendly**: No artificial deadlines on approvals; owner approves when ready
- **Briefing-driven reminders**: Pending actions surface naturally in daily briefing (SC-010)
  without aggressive re-notifications that cause WhatsApp notification fatigue
- **Backward compatible**: Vault file format (YAML frontmatter, file-move transitions) from
  ADR-0011 is fully preserved — Obsidian dashboard view works unchanged
- **Testable in isolation**: `hitl_queue.py` (SQLite layer) is independently testable without
  needing vault filesystem or WhatsApp bridge

### Negative
- **Two sources of truth during transition**: Vault files + SQLite both track state during
  Phase 6.5. If they diverge (e.g., owner manually moves a vault file), sync logic must
  reconcile. Mitigation: startup sync scan; vault file is authoritative for manual moves.
- **Indefinite queue can grow**: If owner never responds to low-priority items, queue grows
  unbounded. Mitigation: briefing reminders make all pending items visible; owner can
  explicitly decline to clear items.
- **No hard deadline means no guaranteed delivery SLA**: An action approved 7 days later may
  have stale content (e.g., "reply to Ahmed's WhatsApp" drafted for context that changed).
  Mitigation: `ContentDraft.drafted_at` timestamp shown in HITL summary; owner sees age.
- **Removes 48h auto-cancel safety valve**: Some actions (e.g., a LinkedIn post on a
  trending topic) lose relevance after 48h. Mitigation: summary text includes `drafted_at`;
  owner can decline stale items; future phase may add per-action-type soft expiry config.

## Alternatives Considered

**Alternative A: Keep existing 48h timeout, accept lost approvals on restart**
- Preserve ADR-0011 behavior exactly; lose in-memory queue on restart; 48h auto-cancel
- Rejected: Owner explicitly stated they want fire-and-forget behavior (sp.clarify Q1).
  48h deadline creates pressure and causes actions to be lost while travelling/busy.

**Alternative B: Rebuild HITL as pure SQLite state machine (remove vault files)**
- Single source of truth in SQLite; no vault file dependency
- Rejected: Vault files are human-readable in Obsidian dashboard — CEO can see pending
  approvals without running any code. Removing vault files breaks the Obsidian visibility
  that ADR-0003 and ADR-0011 deliberately designed for. Dual-state is worth the complexity.

**Alternative C: External message queue (Redis, RabbitMQ)**
- Production-grade queue with delivery guarantees
- Rejected: Violates ADR-0003 (local-first, minimal infrastructure). Single-user system
  does not need distributed queue semantics. SQLite WAL mode provides sufficient
  concurrency for one CEO's approval volume.

**Alternative D: File-lock + atomic JSON as persistence (no SQLite)**
- Append-only JSON file per action, file-lock for concurrent writes
- Rejected: JSON has race conditions under concurrent writes. SQLite WAL is purpose-built
  for this access pattern. Also: SQLite supports structured queries for `get_pending_for_briefing()`
  without scanning all files.

## References

- Feature Spec: `specs/011-full-comms-automation/spec.md` (FR-038, Clarification Q1)
- Implementation Plan: `specs/011-full-comms-automation/plan.md` (Phase A)
- Data Model: `specs/011-full-comms-automation/data-model.md` (CommunicationAction table)
- Superseded behavior: ADR-0011 §Timeout Lifecycle (24h/48h timeouts removed in Phase 6.5)
- Related ADRs: ADR-0011 (original HITL state machine — preserved), ADR-0003 (local-first persistence), ADR-0018 (Ralph Wiggum loop — execute_approved() follows same retry pattern)
