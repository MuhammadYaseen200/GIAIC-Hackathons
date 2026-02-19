---
id: 009
title: Phase 3 BaseWatcher Lifecycle Implementation
stage: green
date: 2026-02-18
surface: agent
model: claude-opus-4-6
feature: gmail-watcher
branch: 005-gmail-watcher
user: MuhammadYaseen200
command: /sp.implement
labels: ["phase-3", "base-watcher", "lifecycle", "tdd", "green", "abc"]
links:
  spec: specs/005-gmail-watcher/spec.md
  ticket: null
  adr: history/adr/0001-watcher-base-class-design.md, history/adr/0003-local-file-based-data-persistence.md
  pr: null
files:
  - watchers/base_watcher.py
  - tests/unit/test_base_watcher.py
  - specs/005-gmail-watcher/tasks.md
tests:
  - tests/unit/test_base_watcher.py (26 tests PASS)
  - tests/ (83 total tests PASS, 0 regressions)
---

## Prompt

Phase 3 (US2: BaseWatcher lifecycle -- T030-T051) whenever you want to proceed. You have constitution, spec, adr, plan, and tasks file for backup support and as resource to start implementation. Create claude agent team instance, apply all governance and control, applied enforcement, rules, laws, loops, automations, workflows, use skills, sub-agents, mcps, plugins, hooks. When complete then we move to next phase, if found bug and error or if work in wrong directory instead of /mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0, stop and get the correct directory and then continue.

## Response snapshot

Completed Phase 3 (US2: BaseWatcher lifecycle, T030-T051, 22 tasks):

1. Implemented `watchers/base_watcher.py` -- Full BaseWatcher ABC with:
   - `__init__()` with poll_interval >= 30 validation, path setup, WatcherState init
   - `async start()` with prerequisites, state load, lock acquire, signal handlers, poll loop
   - `async stop()` with state save, lock release, shutdown log
   - `async _run_poll_cycle()` with retry-wrapped poll/process, state update, cycle summary log
   - `async _retry_with_backoff()` with exponential backoff (2s, 4s, 8s), logging, re-raise
   - `_load_state()/_save_state()` JSON round-trip with corrupt-state recovery
   - `_log()` JSONL append to daily log file via WatcherLogEntry
   - `_acquire_lock()/_release_lock()` FileLock wrapper
   - `health_check()` status dict (name, status, last_poll, error_count, total_processed, uptime_start)
   - Abstract methods: poll(), process_item(), validate_prerequisites()

2. Wrote `tests/unit/test_base_watcher.py` -- 26 tests covering:
   - MockWatcher concrete subclass (T030)
   - Prerequisites validation (T031)
   - State load/create (T032)
   - Stop saves state & releases lock (T033)
   - Poll cycle processes items, updates timestamp, handles empty (T034)
   - Retry succeeds on 3rd attempt, succeeds first try (T035)
   - Retry exhausted raises (T036)
   - Corrupt state recovery + warning log (T037)
   - JSONL log creation, valid JSON entries, multiple appends (T038)
   - Poll interval validation: rejects <30, accepts 30, accepts 60 (T039)
   - Health check: status dict, ok when running, stopped when not (T040)
   - Abstract method enforcement: cannot instantiate base, incomplete subclass raises
   - State persistence round-trip

3. All 83 tests pass (26 base_watcher + 19 models + 38 utils), 0 regressions.

## Outcome

- Impact: Phase 3 complete -- BaseWatcher ABC fully functional with lifecycle, retry, state, logging, locking. Phase 4 (OAuth2) can begin.
- Tests: 83 passed, 0 failed (26 new base_watcher tests + 57 existing)
- Files: 2 files created, 1 file updated (tasks.md)
- Next prompts: /sp.implement Phase 4 (US3: OAuth2 Authentication -- T052-T063)
- Reflection: BaseWatcher design cleanly separates framework concerns from concrete watcher logic. MockWatcher pattern enables testing without external dependencies. All ADR-0001 design goals achieved.

## Evaluation notes (flywheel)

- Failure modes observed: None -- implementation and tests aligned on first pass. Context window compacted mid-session but state was preserved via summary.
- Graders run and results (PASS/FAIL): pytest 83/83 PASS. Full regression suite PASS. tasks.md updated PASS.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Phase 4 OAuth2 can reuse the retry_with_backoff pattern for token refresh. Consider testing token expiry edge case in isolation.
