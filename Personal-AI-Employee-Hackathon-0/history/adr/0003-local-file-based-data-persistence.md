# ADR-0003: Local File-Based Data Persistence

> **Scope**: Defines the storage format for watcher state and operational logs -- JSON for state, JSONL for daily logs.

- **Status:** Accepted
- **Date:** 2026-02-17
- **Feature:** gmail-watcher (005)
- **Context:** Watchers need two kinds of persistent data: (1) operational state (processed IDs, last poll time, error counts) that survives restarts, and (2) activity logs (events, errors, metrics) for observability. Constitution Principle II mandates local-first storage. The spec names `vault/Logs/gmail_watcher_state.json` explicitly. The Obsidian vault with Dataview plugin is the primary UI for monitoring. Phase 6 (Gold tier) will migrate state to Neon PostgreSQL.

## Decision

Use **JSON files for watcher state** and **JSONL (JSON Lines) for daily activity logs**, both stored in `vault/Logs/`.

Components:
- **State file**: `vault/Logs/gmail_watcher_state.json` -- single JSON object with `last_poll_timestamp`, `processed_ids` (list), `error_count`, `total_emails_processed`, `uptime_start`
- **Log files**: `vault/Logs/gmail_watcher_YYYY-MM-DD.log` -- one JSON object per line, appended per event. Fields: `timestamp`, `watcher_name`, `event`, `severity`, `details`
- **Atomic writes**: State file writes use temp file + `os.replace()` to prevent corruption (FR-017)
- **Corrupt recovery**: If state file is invalid JSON on load, log warning, reset to clean state, continue (accept brief re-processing window)
- **FIFO pruning**: When `processed_ids` exceeds 100,000 entries, prune oldest to keep state file under ~10MB
- **File rotation**: One log file per day, naturally bounded (~500KB/day at 60s polls)

## Consequences

### Positive

- Human-readable in Obsidian -- users can inspect state and logs directly in their vault
- Dataview-parseable -- JSONL lines can be queried by the Obsidian Dataview plugin for Dashboard.md integration (SC-009)
- Zero additional dependencies -- JSON is stdlib, no database driver needed
- Atomic writes via `os.replace()` prevent corrupt partial state on crash or power loss
- `grep`-friendly -- JSONL logs are trivially searchable from the command line
- Natural daily rotation -- no log management daemon needed
- Spec-compliant -- names match `vault/Logs/gmail_watcher_state.json` exactly

### Negative

- No concurrent write safety beyond file locking -- two processes writing the same state file would corrupt it (mitigated by FileLock in ADR-0001's BaseWatcher)
- Processed-ID list grows linearly -- 100k IDs at ~20 bytes each = ~2MB, acceptable but requires FIFO pruning
- No indexing -- searching processed IDs is O(n) on the list (acceptable at 100k scale, not at 1M+)
- Phase 6 migration to PostgreSQL requires a data migration script (known technical debt, documented in spec)
- JSONL is append-only -- no in-place updates, which is correct for logs but means no log rotation/compaction

## Alternatives Considered

**Alternative A: SQLite for state + logs**
- Pros: ACID transactions, indexing, SQL queries, concurrent read safety
- Cons: Not human-readable in Obsidian (binary file); extra dependency management; Dataview can't query it; overkill for a single-watcher process; Python's sqlite3 has WAL mode complexities
- Rejected: Breaks Obsidian-native observability; adds complexity without proportional benefit at Phase 2 scale

**Alternative B: YAML for state + plain text logs**
- Pros: YAML is very Obsidian-friendly; plain text logs are universal
- Cons: YAML serialization has edge cases (strings that look like bools/numbers); plain text logs aren't structured (no Dataview queries); YAML write performance is worse than JSON
- Rejected: Structured logs are a requirement (SC-009); YAML's type coercion bugs are a known pitfall

**Alternative C: Single JSON file for everything (state + log entries)**
- Pros: One file to manage; atomic reads/writes
- Cons: File grows unbounded; must rewrite entire file on every log append; no daily rotation; slow I/O for frequent appends
- Rejected: Append-heavy workload doesn't suit single-file JSON

## References

- Feature Spec: `specs/005-gmail-watcher/spec.md` (FR-007, FR-009, FR-017, SC-009, NFR Observability)
- Implementation Plan: `specs/005-gmail-watcher/plan.md`
- Related ADRs: ADR-0001 (BaseWatcher manages state load/save and FileLock)
- Constitution: `.specify/memory/constitution.md` Principle II (Local-First Privacy), Principle X (Graceful Degradation)
