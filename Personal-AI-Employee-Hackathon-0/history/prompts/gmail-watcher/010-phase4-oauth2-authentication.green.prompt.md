---
id: 010
title: Phase 4 OAuth2 Authentication Implementation
stage: green
date: 2026-02-18
surface: agent
model: claude-opus-4-6
feature: gmail-watcher
branch: 005-gmail-watcher
user: MuhammadYaseen200
command: /sp.implement
labels: ["phase-4", "oauth2", "authentication", "gmail", "tdd", "green"]
links:
  spec: specs/005-gmail-watcher/spec.md
  ticket: null
  adr: history/adr/0002-async-integration-pattern-for-sync-sdks.md
  pr: null
files:
  - watchers/gmail_watcher.py
  - scripts/gmail_auth.py
  - tests/unit/test_gmail_watcher.py
  - specs/005-gmail-watcher/tasks.md
tests:
  - tests/unit/test_gmail_watcher.py (8 tests PASS)
  - tests/ (91 total tests PASS, 0 regressions)
---

## Prompt

Phase 4 -- OAuth2 Authentication (T052-T063). This implements scripts/gmail_auth.py and GmailWatcher's _authenticate() method. You have constitution, spec, adr, plan, and tasks file for backup support and as resource to start implementation. Create claude agent team instance, apply all governance and control.

## Response snapshot

Completed Phase 4 (US3: OAuth2 Authentication, T052-T063, 12 tasks):

1. Wrote `tests/unit/test_gmail_watcher.py` with 8 test cases:
   - T052: New token triggers browser flow (InstalledAppFlow)
   - T053: Existing valid token skips browser flow
   - T054: Expired token triggers creds.refresh(), saves updated token
   - T055: Corrupt token deletes and re-auths via browser flow
   - T056: Missing credentials.json raises PrerequisiteError(HT-002)
   - T057: Missing vault dirs raises PrerequisiteError(HT-001)
   - T058: Missing env vars raises PrerequisiteError
   - Additional: All prerequisites present passes validation

2. Implemented `watchers/gmail_watcher.py`:
   - GmailWatcher.__init__() with credentials/token path resolution from .env
   - validate_prerequisites() checks vault dirs (HT-001), credentials.json (HT-002), .env vars
   - _authenticate() with 4-path flow: load existing, refresh expired, browser flow, corrupt recovery
   - _save_token() via atomic_write for crash safety
   - All 3 Gmail scopes (readonly, send, modify) for future-proofing
   - Stub poll()/process_item() for Phase 5

3. Implemented `scripts/gmail_auth.py`:
   - Standalone CLI with --credentials and --token flags
   - Falls back to .env for paths
   - Handles existing valid, expired-refresh, and new-flow scenarios
   - Verifies with getProfile(), prints authenticated email address

4. Fixed T058 test isolation: patched load_dotenv to prevent project .env leaking into test.

## Outcome

- Impact: Phase 4 complete -- OAuth2 authentication fully implemented with all token lifecycle paths tested. Phase 5 (Email-to-Vault MVP) can begin.
- Tests: 91 passed, 0 failed (8 new gmail_watcher tests + 83 existing)
- Files: 3 files created, 1 file updated (tasks.md)
- Next prompts: /sp.implement Phase 5 (US1: Email-to-Action Item MVP -- T064-T087)
- Reflection: Mocking google-auth libraries requires careful attention to the credential lifecycle (valid/expired/refresh_token). The corrupt token test needed explicit ValueError side_effect on from_authorized_user_file.

## Evaluation notes (flywheel)

- Failure modes observed: T058 initially failed because load_dotenv() picked up the project's .env file during testing. Fixed by patching load_dotenv in the test.
- Graders run and results (PASS/FAIL): pytest 91/91 PASS. Full regression suite PASS. tasks.md updated PASS.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Phase 5 will test _parse_email with the sample_raw_gmail_message fixture from conftest.py. Ensure fixture matches real Gmail API response format.
