# ADR-0015: Cron Scheduling Strategy

> **Scope**: Defines how the H0 AI Employee runs recurring tasks — orchestrator polling every 15 minutes and daily LinkedIn post drafting — without requiring a running Python process or external service.

- **Status:** Accepted
- **Date:** 2026-03-05
- **Feature:** linkedin-cron-silver (009)
- **Context:** Phase 5.5 requires two recurring operations: (1) orchestrator processing `vault/Needs_Action/` every 15 minutes, (2) LinkedIn post drafting once daily at 09:00. The system runs on a local WSL2 Ubuntu environment. The cron daemon is confirmed running (PID 1076, system audit 2026-03-05). The spec explicitly excludes "n8n or external workflow orchestration" and specifies "cron-native only for this phase" (Out of Scope, specs/009-linkedin-cron-silver/spec.md). Two approaches were considered: system cron (installed via crontab) and in-process Python scheduling (APScheduler).

## Decision

Use **system cron** via `scripts/setup_cron.sh` and `scripts/remove_cron.sh` with:

- **Orchestrator entry**: `*/15 * * * * source /abs/path/.env && python3 /abs/path/orchestrator/main.py >> /abs/path/vault/Logs/cron.log 2>&1`
- **LinkedIn drafter entry**: `<CRON_LINKEDIN_TIME> * * * source /abs/path/.env && python3 /abs/path/orchestrator/linkedin_poster.py --auto >> /abs/path/vault/Logs/cron.log 2>&1`  (time configurable via `CRON_LINKEDIN_TIME` in `.env`, default `0 9`)
- **Idempotency**: `setup_cron.sh` checks for existing entries (grep match) before adding — running 3 times produces exactly 2 entries (SC-007)
- **Lock file**: `orchestrator/main.py` creates `/tmp/h0_orchestrator.lock` on entry, removes on exit; new invocations detect lock and exit cleanly (prevents duplicate processing when cron fires during long run)
- **Env sourcing**: `export $(grep -v "^#" .env | xargs)` before each invocation — credentials available without modifying system environment
- **Absolute paths**: All paths hardcoded as absolute in crontab to avoid `$HOME` or `$PATH` issues in cron's minimal environment
- **Log format**: All stdout+stderr appended to `vault/Logs/cron.log` with timestamps added by prepending `date "+%Y-%m-%dT%H:%M:%S"` in the wrapper

## Consequences

### Positive

- **No running process required**: Cron survives reboots and terminal closes without a daemon process; system cron handles scheduling natively
- **Zero new dependencies**: No additional Python libraries required; `scripts/setup_cron.sh` is pure bash
- **Simple install/uninstall**: SC-006 (setup completes in <5s) and SC-007 (idempotent) trivially satisfied by bash grep+append
- **Debuggable**: `vault/Logs/cron.log` centralizes all cron output; `crontab -l` shows exactly what is scheduled at any time
- **Survives Python process failure**: If `orchestrator/main.py` crashes, cron retries on next interval automatically — no process manager needed
- **Lock file prevents overlap**: Simple `/tmp/*.lock` pattern prevents duplicate orchestrator runs without needing process manager or message queue

### Negative

- **WSL2 cron reliability**: System cron in WSL2 requires WSL2 to be running — if Windows suspends WSL2, cron does not fire. For local dev this is acceptable; for Phase 7 (Always-On Cloud VM), cron runs natively on Linux with no WSL2 concern
- **No missed-job recovery**: If WSL2 is offline during a scheduled time, that cron run is skipped silently — no catch-up mechanism. Mitigated by 15-minute interval (short enough that a missed run is rarely consequential) and daily LinkedIn draft (single missed day is acceptable)
- **Crontab is user-specific**: Cron entries live in the current user's crontab — not system-wide. If deploying to a different user on Oracle VM (Phase 7), `setup_cron.sh` must be re-run as the correct user
- **No built-in monitoring**: Cron does not alert on job failure; failure is only detectable by scanning `cron.log`. Future phases should add log-based alerting

## Alternatives Considered

**Alternative A: APScheduler (in-process Python scheduler)**
- Mechanism: `from apscheduler.schedulers.blocking import BlockingScheduler` in a long-running `scheduler.py` process; `@scheduler.scheduled_job("interval", minutes=15)` for orchestrator; `@scheduler.scheduled_job("cron", hour=9)` for LinkedIn
- Pros: Pure Python; timezone-aware; missed job handling built-in; easier to test (mock `datetime.now()`)
- Cons: Requires a permanent running process — if the process dies (crash, reboot, terminal close), scheduling stops; needs process manager (systemd/supervisor) to restart it, adding infrastructure; spec out-of-scope explicitly says "cron-native only"
- Rejected: Spec constraint (Out of Scope); requires additional process management infrastructure not present in Phase 5.5

**Alternative B: n8n workflow automation**
- Mechanism: n8n Docker container with HTTP webhook triggers for orchestrator + LinkedIn drafter
- Pros: Visual workflow editor; built-in retry logic; webhook-based triggering
- Cons: Entire n8n infrastructure (Docker, n8n container, PostgreSQL for n8n state) required; massively over-engineered for 2 cron jobs; spec explicitly excludes "n8n or external workflow orchestration"
- Rejected: Spec constraint (Out of Scope); disproportionate complexity

**Alternative C: systemd timer units**
- Mechanism: `.service` + `.timer` unit files in `~/.config/systemd/user/`
- Pros: More reliable than cron in modern Linux; supports `OnCalendar=`, missed job tracking via `Persistent=true`
- Cons: systemd user units require `loginctl enable-linger` in WSL2; WSL2 systemd support varies by version; adds complexity vs simple crontab; not universally available
- Rejected: WSL2 systemd reliability concerns; cron is universally available and already confirmed running

## References

- Feature Spec: `specs/009-linkedin-cron-silver/spec.md` (FR-011–FR-016, SC-005–SC-007, Out of Scope)
- System Audit: Cron daemon PID 1076 confirmed 2026-03-05
- Related ADRs: ADR-0003 (local file-based persistence — vault/Logs/ output target), ADR-0007 (MCP fallback protocol — cron runs main orchestrator which uses MCP-first)
