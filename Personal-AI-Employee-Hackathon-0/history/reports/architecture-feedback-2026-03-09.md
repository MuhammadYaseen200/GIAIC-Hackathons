# Architecture Feedback — H0 Personal AI Employee
**Date**: 2026-03-09
**Author**: Architecture Reviewer (claude-sonnet-4-6)
**Scope**: Post-Phase 5.5 review, pre-Phase 6 (Gold) preparation
**Files Reviewed**: specs/overview.md, ai-control/AGENTS.md, ai-control/MCP.md, orchestrator/orchestrator.py, orchestrator/linkedin_poster.py, orchestrator/hitl_manager.py, orchestrator/mcp_client.py, orchestrator/vault_ops.py, mcp_servers/linkedin/server.py, mcp_servers/linkedin/auth.py, mcp_servers/linkedin/client.py, mcp_servers/whatsapp/bridge.py, watchers/privacy_gate.py, watchers/base_watcher.py, watchers/whatsapp_watcher.py

---

## Executive Summary

The H0 project has a well-governed, incrementally built architecture that has delivered Silver tier on schedule. The vault-as-message-bus pattern, MCP-first discipline, and HITL state machine are genuine architectural strengths. However, the transition from Silver (local, WSL2, single-user) to Gold (CEO Briefing, Odoo ERP, cloud-ready) exposes several structural limits. The most critical issues before Phase 6 begins are: duplicate frontmatter parsing across seven files, a subprocess-per-call MCP client that cannot sustain Odoo load, hardcoded absolute paths in linkedin_poster.py, and the absence of a unified HITL response dispatcher for the two parallel approval channels (email drafts vs. LinkedIn posts).

---

## STRENGTH — What Is Well-Designed

### S-001: BaseWatcher as a Shared Lifecycle Primitive
`watchers/base_watcher.py` cleanly enforces poll interval minimums, exponential backoff retries, structured JSONL logging, atomic state persistence, file-based locking, and graceful signal handling. Every watcher that extends it inherits these guarantees without re-implementation. The pattern is correctly applied across `GmailWatcher`, `WhatsAppWatcher`, and `RalphWiggumOrchestrator`.

### S-002: Privacy Gate as a Pure Function
`watchers/privacy_gate.py` is stateless, has no I/O, and is called consistently at the entry boundary of every data ingestion path (Gmail watcher, WhatsApp watcher, LinkedIn poster). The design is correct: sensitive content cannot flow downstream because it is redacted or blocked before any vault write. Coverage is reported at 95%. This is a strong privacy boundary.

### S-003: MCP Fallback Protocol
`orchestrator/mcp_client.py` implements a disciplined three-stage fallback (MCP attempt → fallback callable → MCPUnavailableError) that is logged at every stage. The pattern is applied uniformly across Gmail, Obsidian, Calendar, and WhatsApp MCPs inside the orchestrator. This prevents silent failures and gives operators visibility into degraded operation.

### S-004: HITL State Machine Clarity
`orchestrator/hitl_manager.py` implements a well-defined five-state machine (pending → approved | rejected | awaiting_reminder | timed_out) backed entirely by vault files. The state is durable: a process crash does not lose the decision context. The 24h reminder and 48h timeout are explicit and configurable via env vars. The `_find_draft()` method supports both exact and prefix matching, which handles the common case of a human typing a short ID.

### S-005: Vault as an Auditable Message Bus
Using markdown files with YAML frontmatter as the inter-process communication medium is unconventional but well-suited to a single-developer project where human readability and Obsidian compatibility are first-class concerns. Every decision, draft, and log entry is visible in the vault without any special tooling.

### S-006: SDD Governance Discipline
All phases have complete spec.md → plan.md → ADRs → tasks.md chains. The ADR record (0001–0015) is current and covers all significant decisions. The AGENTS.md governance layer and MCP.md registry are maintained. This is rare in hackathon projects and provides a solid foundation for onboarding Phase 6 contributors.

### S-007: Rate Limiting for External APIs
The LinkedIn poster checks `_count_today_posts()` before calling the LLM draft step, preventing wasted API tokens and avoiding LinkedIn rate limit violations. The fallback notifies the owner via WhatsApp rather than silently dropping the request.

---

## DEBT — Technical Debt (Ranked by Impact on Phase 6)

### D-001 [CRITICAL]: Subprocess-Per-Call MCP Client
**Location**: `orchestrator/mcp_client.py`, `_invoke_tool()`
**Impact**: Every MCP tool call spawns a new Python subprocess, performs an MCP initialize handshake, sends the tool call, and terminates. For low-frequency email triage, the overhead is acceptable. For Phase 6, the CEO Briefing will need to call Obsidian MCP (write summary), Gmail MCP (send briefing), and Calendar MCP (read events) in sequence within a tight window. The Odoo MCP will likely require batch reads. The per-call subprocess spawn latency (200–500ms startup + handshake) will multiply into unacceptable delays. A persistent subprocess pool or native Python library calls (bypassing MCP for internal servers) is needed before Odoo integration.

### D-002 [HIGH]: Duplicate Frontmatter Parsing
**Locations**:
- `orchestrator/vault_ops.py`: `_split_file()`, `_FRONTMATTER_RE`
- `orchestrator/hitl_manager.py`: `_read_frontmatter()`, `_read_body()`, `_write_frontmatter_file()`
- `orchestrator/linkedin_poster.py`: inline `content.split("---", 2)` in `check_pending_approvals()`, `publish_approved()`, `handle_rejected()`, `process_linkedin_vault_triggers()`
- `orchestrator/orchestrator.py`: inline `content.split("---", 2)` in `_scan_approved_drafts()`

There are at least four distinct implementations of the same "split markdown on --- delimiters and parse YAML" operation. The `vault_ops.py` version uses a compiled regex with proper dotall handling. The `hitl_manager.py` version uses a simpler split. The `linkedin_poster.py` version scans raw text lines for frontmatter fields rather than using YAML. These diverge in edge case handling (YAML values with colons, multiline strings, files not starting with ---). Any bug fix in one place will not propagate to the others. Phase 6 will add at least one more format (CEO Briefing notes, Odoo records) and will repeat this pattern again unless a single `parse_vault_file()` function is established in `orchestrator/vault_ops.py` and imported everywhere.

### D-003 [HIGH]: Hardcoded Absolute Path in linkedin_poster.py
**Location**: `orchestrator/linkedin_poster.py`, line 30–33
```python
REQUIRED_DIR = "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0"
if not str(PROJECT_ROOT).startswith(REQUIRED_DIR):
    print(f"WRONG DIRECTORY: {PROJECT_ROOT}\nRequired: {REQUIRED_DIR}\nSTOP.")
    sys.exit(1)
```
This guard will terminate the process on the Oracle VM (Phase 7) where the absolute path will be different. It will also break in any CI environment. The intent (preventing accidental execution from the wrong directory) is valid, but the implementation couples the code to a specific developer's filesystem. The pattern is not used in any other module. Should be removed before Phase 7 cloud deployment.

### D-004 [HIGH]: Two Parallel HITL Approval Channels With No Unified Dispatcher
The system now has two separate approval workflows:
1. Email draft approval: `HITLManager.handle_owner_reply()` in `orchestrator/hitl_manager.py` — parses "approve/reject \<draft_id\>" from the owner's WhatsApp reply.
2. LinkedIn post approval: `check_pending_approvals()` in `orchestrator/linkedin_poster.py` — reads `status` field in vault frontmatter (set manually or via external trigger).

These two channels are structurally disconnected. The LinkedIn approval flow does not parse WhatsApp replies — it polls the frontmatter status field. This means the owner cannot approve a LinkedIn post by replying "approve" to the WhatsApp notification the same way they approve email drafts. The HITL experience is inconsistent, and any Phase 6 approval surface (Odoo action, CEO Briefing send) will add a third divergent pattern unless a unified dispatcher is created.

### D-005 [MEDIUM]: In-Memory Notification Queue Not Durable
**Location**: `orchestrator/hitl_manager.py`, line 127: `self._notification_queue: list[str] = []`
The notification queue is a plain Python list on the `HITLManager` instance. If the orchestrator crashes between `submit_draft()` and `send_batch_notification()`, the queue is lost. The draft files exist in `vault/Pending_Approval/`, but the owner will not receive a WhatsApp notification. Drafts will silently accumulate until the next `check_timeouts()` sends a 24h reminder. For Phase 6, where CEO Briefing is time-sensitive, losing the notification is a material failure mode.

### D-006 [MEDIUM]: WhatsApp Health Check Uses a Probe Request Rather Than a Dedicated Endpoint
**Location**: `mcp_servers/whatsapp/bridge.py`, lines 42–48
```python
resp = await client.get(f"{BRIDGE_URL}/api/send")
alive = resp.status_code in (200, 405)
```
The health check sends a GET to the /api/send endpoint and infers health from receiving a 405. This is fragile: a future version of the Go bridge that changes routing or adds authentication to /api/send will break health detection without the health check returning an error. A dedicated `/health` endpoint on the Go bridge is the correct fix.

### D-007 [MEDIUM]: Rate Limit State Not Durable Across Restarts
**Location**: `orchestrator/linkedin_poster.py`, `_count_today_posts()`
The daily post count is derived by scanning `vault/Logs/linkedin_posts.jsonl` for today's published entries. This is correct and durable. However, the JSONL file is opened in append mode without any write lock. Under concurrent execution (e.g., two cron invocations running simultaneously before the ADR-0015 FileLock is acquired), two "published" entries could be written, or the count could be read before a concurrent write completes. The `POSTS_JSONL` file is opened with `open(..., "a")` directly rather than via `atomic_write`, making it the only log write in the system that bypasses atomic guarantees.

### D-008 [LOW]: LinkedIn linkedin_poster.py Bypasses MCP Layer for API Calls
**Location**: `orchestrator/linkedin_poster.py`, line 186: `return await post_to_linkedin(post_text, "PUBLIC")`
This calls the LinkedIn API client directly (module-level function) rather than through the LinkedIn MCP server. The MCP server (`mcp_servers/linkedin/server.py`) exists and wraps the same client, but the poster bypasses it. The MCP.md registry states "Direct API calls from agent code bypassing this registry are FORBIDDEN." This is an architectural violation. In practice it works because the MCP server is a thin wrapper, but it means the LinkedIn MCP tools (post_update, health_check) are never exercised in the live workflow.

### D-009 [LOW]: PywaStub Placeholder Left in Production Path
**Location**: `mcp_servers/whatsapp/bridge.py`, lines 58–65
`PywaStub` is referenced in `bridge.py` and represents an unimplemented backend. HT-012 was deferred. The stub raises `NotImplementedError` on any call, meaning any code that selects the wrong backend will fail at runtime with a confusing error. No code currently selects PywaStub, but the module-level dead code adds confusion and will not be removed naturally unless explicitly tracked.

---

## RISK — Top Risks With Mitigation

### R-001 [CRITICAL]: LinkedIn OAuth2 Token Expiry Breaks the Entire LinkedIn Workflow
**Risk**: The LinkedIn access token expires. The `_refresh_token()` function in `mcp_servers/linkedin/auth.py` calls the LinkedIn token endpoint synchronously using `httpx.post()` (blocking call inside an async context). If the refresh fails (network error, expired refresh token, LinkedIn app revoked), the entire `post_to_linkedin()` call chain raises `AuthRequiredError`, the draft is left in `vault/Pending_Approval/` with `status=auth_error`, and there is no automatic recovery or human escalation.
**Blast radius**: All LinkedIn posts silently fail until a human runs `scripts/linkedin_auth.py` again.
**Mitigation**: Add a vault alert file (`vault/Needs_Action/linkedin_auth_required.md`) when `AuthRequiredError` is raised, and add a WhatsApp notification to the owner. Also replace the synchronous `httpx.post()` in `_refresh_token()` with `httpx.AsyncClient` to avoid blocking the event loop.

### R-002 [HIGH]: No Concurrency Control Between Cron LinkedIn Trigger and Orchestrator Poll Cycle
**Risk**: ADR-0015 defines a FileLock at `/tmp/h0_orchestrator.lock` to prevent overlapping orchestrator runs. However, `linkedin_poster.py --check` can be called directly from cron without acquiring this lock (see the `__main__` block of orchestrator.py — `check_pending_approvals()` is called after `poll()` within the lock, but the standalone `--check` CLI path has no lock). If the cron schedule runs `--check` at a time when the orchestrator is mid-poll, two processes could attempt to rename the same draft file (in `_approve()` calling `draft_path.rename(approved_path)` and `_scan_approved_drafts()` in the orchestrator both acting on `vault/Approved/` simultaneously).
**Blast radius**: Silent file-not-found errors, possible duplicate LinkedIn posts if a draft is processed twice before the first rename completes.
**Mitigation**: Ensure all paths that modify `vault/Pending_Approval/` and `vault/Approved/` acquire the orchestrator FileLock before proceeding. The `--check` standalone CLI path is currently unguarded.

### R-003 [HIGH]: Vault File Count Growth Is Unbounded
**Risk**: Every email, WhatsApp message, LinkedIn draft, decision log entry, and MCP fallback log is written to the vault directory tree. There is no cleanup or archival policy. `vault/Done/` accumulates all processed emails indefinitely. `vault/Logs/` produces a new JSONL file per day per watcher name. The `state.processed_ids` list in `WatcherState` is pruned at 10,000 entries (`prune_processed_ids()`), but the actual vault files are never deleted. On the Oracle VM (Phase 7), a persistent disk with bounded capacity will eventually fill unless an archival job is implemented.
**Blast radius**: Disk full stops all vault writes (atomic_write will fail), which crashes the orchestrator.
**Mitigation**: Add a vault archival task to the Phase 7 scope (move Done/ files older than 30 days to a compressed archive). Add disk usage monitoring as a Phase 6 operational prerequisite.

---

## PHASE 6 PREP — Specific Actions Needed Before Gold Tier Begins

### P6-001 [BLOCKING]: Establish a Single vault_parse() Utility
Before writing any Phase 6 code (CEO Briefing generator, Odoo record writer), consolidate the four frontmatter parsing implementations into a single function in `orchestrator/vault_ops.py`. The function signature should be:
```python
def parse_vault_file(content: str) -> tuple[dict, str]: ...
def write_vault_file(frontmatter: dict, body: str) -> str: ...
```
All callers in `orchestrator/hitl_manager.py`, `orchestrator/linkedin_poster.py`, `orchestrator/orchestrator.py`, and the new Phase 6 modules must use this shared function. This prevents a fifth divergent implementation from being added.

### P6-002 [BLOCKING]: Remove Hardcoded Path Guard from linkedin_poster.py
The `REQUIRED_DIR` check at lines 30–33 of `orchestrator/linkedin_poster.py` must be removed before Phase 6 starts. If it is not removed, the CEO Briefing scheduler (which may import or call linkedin_poster functions) will break on any machine other than the current developer WSL2 instance.

### P6-003 [BLOCKING]: Design the Unified HITL Dispatcher
Phase 6 will add at least one new approval surface (CEO Briefing "approve to send" flow). Before implementing it, design and document a unified HITL dispatcher that routes incoming WhatsApp "approve/reject \<id\>" messages to the correct handler (email draft vs. LinkedIn post vs. CEO Briefing). The current architecture has two disconnected handlers and the problem will not self-resolve. A routing table keyed on draft file prefix or type frontmatter field is the minimal viable solution.

### P6-004 [REQUIRED]: Register Odoo MCP Before Implementation
Per MCP.md development standards, the Odoo MCP server must have a spec in `specs/odoo-mcp/spec.md` before any code is written. The MCP.md registry entry for "Odoo MCP" exists as a future item but has no spec, no fallback defined, and no env var documentation. HT-006 (install Odoo Community, create API user) must be completed before the spec can be written.

### P6-005 [REQUIRED]: Address Subprocess MCP Client Performance
For Phase 6, the CEO Briefing will need 3–5 MCP calls in sequence within a single orchestrator cycle. The current per-call subprocess spawn pattern is acceptable for the current load (1–5 emails per poll cycle) but will create observable latency for briefing generation. Before Phase 6 implementation, define whether to: (a) accept the latency and set a generous timeout, (b) switch the internal MCP servers to importable Python libraries called directly, or (c) implement a persistent subprocess connection pool. Document the decision as ADR-0016.

### P6-006 [OPERATIONAL]: Add Disk Usage and Token Budget Monitoring
The `OrchestratorState` tracks `total_tokens_used` but there is no alerting when it crosses a threshold. Phase 6 will add CEO Briefing (daily LLM call) and Odoo queries. Before Phase 6 starts, add: (a) a token budget check that sends a WhatsApp alert if weekly usage exceeds a configurable limit, (b) a vault size check (total MB in `vault/`) that alerts when approaching a configurable limit.

### P6-007 [RECOMMENDED]: Fix WhatsApp Health Check
Replace the /api/send 405 probe with a dedicated `/health` endpoint on the Go bridge, or use the GoBridge `health()` method to check for a response to `/messages` (which has defined behavior). Document the health check contract in `mcp_servers/whatsapp/bridge.py`.

---

## RECOMMENDATIONS — Prioritized List of Improvements

| # | Priority | Action | Effort | Impact |
|---|----------|--------|--------|--------|
| 1 | CRITICAL | Consolidate frontmatter parsing into vault_ops.py (P6-001) | Small (1–2h) | Prevents divergence in 4+ files |
| 2 | CRITICAL | Remove hardcoded REQUIRED_DIR path guard (P6-002, D-003) | Trivial (5 min) | Required for cloud deployment |
| 3 | HIGH | Design unified HITL dispatcher routing table (P6-003, D-004) | Medium (spec + ADR) | Prevents third divergent HITL channel in Phase 6 |
| 4 | HIGH | Add WhatsApp alert + vault file on AuthRequiredError for LinkedIn (R-001) | Small | Prevents silent workflow failure on token expiry |
| 5 | HIGH | Guard standalone `--check` CLI with FileLock (R-002) | Trivial | Prevents race condition on cron overlap |
| 6 | HIGH | Spec + register Odoo MCP before implementation (P6-004) | Medium | Required by MCP governance rules |
| 7 | MEDIUM | Make notification_queue durable (D-005) | Small | Prevents lost HITL notifications on crash |
| 8 | MEDIUM | Switch POSTS_JSONL writes to atomic_write (D-007) | Trivial | Consistency with rest of vault write pattern |
| 9 | MEDIUM | Decide MCP client strategy for Phase 6 load + ADR-0016 (P6-005) | Medium | Avoids performance surprise during briefing generation |
| 10 | MEDIUM | Add token budget + disk usage alerting (P6-006) | Small | Prevents silent cost overrun |
| 11 | LOW | Route LinkedIn poster through linkedin_mcp server (D-008) | Small | Restores MCP-first compliance |
| 12 | LOW | Remove PywaStub dead code (D-009) | Trivial | Reduces confusion |
| 13 | LOW | Fix WhatsApp health check endpoint (D-006, P6-007) | Small | Makes health monitoring reliable |

---

## Architecture Diagram — Current State (Post Phase 5.5)

```
External Sources                   Vault (Markdown Message Bus)            External Sinks
──────────────                     ────────────────────────────            ──────────────
Gmail API          ───poll───▶     vault/Needs_Action/                     Gmail API
                                         │                                 LinkedIn API
WhatsApp Go Bridge ───poll───▶           │                                 WhatsApp Go Bridge
                                         ▼
                              RalphWiggumOrchestrator
                              (poll cycle every 120s)
                                         │
                              ┌──────────┴──────────┐
                              │  3-Layer Classifier  │
                              │  (spam/keyword/LLM)  │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  LLM Decision Loop   │
                              │  (Claude, 5 retries) │
                              └──────────┬──────────┘
                                         │
                         ┌───────────────┼───────────────┐
                         ▼               ▼               ▼
                  vault/Drafts/   vault/Done/    vault/Needs_Action/
                                                 (updated status)
                         │
                  HITLManager
                  (WhatsApp notify)
                         │
                  vault/Pending_Approval/
                         │
                  ┌──────┴──────┐
                  ▼             ▼
            vault/Approved/  vault/Rejected/
                  │
            Gmail MCP → send email

LinkedIn path (parallel):
linkedin_poster.py ──▶ Privacy Gate ──▶ LLM draft ──▶ vault/Pending_Approval/
                                                              │
                                              WhatsApp notify (separate channel)
                                                              │
                                              check_pending_approvals() polls
                                                              │
                                              LinkedIn API (direct, bypasses MCP)
```

---

## What Must NOT Change (Preserve These)

1. The Privacy Gate as the first step in every ingest path — do not add any ingest that bypasses `run_privacy_gate()`.
2. Atomic writes for all vault file modifications — never replace `atomic_write()` with a direct `file.write()`.
3. The BaseWatcher exponential backoff and structured logging — do not bypass these by writing standalone scripts that call API directly.
4. ADR documentation for architectural decisions — every new Phase 6 service decision must produce an ADR.
5. The FileLock at `/tmp/h0_orchestrator.lock` — all paths that write to the vault must acquire this lock.

---

*Report generated: 2026-03-09 | Reviewer: claude-sonnet-4-6 | Branch: 009-linkedin-cron-silver*
