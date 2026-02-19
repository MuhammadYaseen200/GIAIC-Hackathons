---
id: 011
title: Phase 5 Email-to-Vault MVP Implementation
stage: green
date: 2026-02-18
surface: agent
model: claude-sonnet-4-6
feature: gmail-watcher
branch: 005-gmail-watcher
user: MuhammadYaseen200
command: /sp.implement
labels: ["phase-5", "email-parsing", "classification", "vault-routing", "tdd", "green", "mvp"]
links:
  spec: specs/005-gmail-watcher/spec.md
  ticket: null
  adr: history/adr/0004-keyword-heuristic-email-classification.md
  pr: null
files:
  - watchers/gmail_watcher.py
  - tests/unit/test_gmail_watcher.py
  - specs/005-gmail-watcher/tasks.md
tests:
  - tests/unit/test_gmail_watcher.py (21 tests PASS)
  - tests/ (104 total tests PASS, 0 regressions)
---

## Prompt

Phase 5 -- Email-to-Action Item MVP (T064-T087). Implements GmailWatcher core: email parsing, keyword classification, filename generation, markdown rendering, vault routing, and poll/process_item pipeline. You have constitution, spec, adr, plan, and tasks file for backup support and as resource. Create claude agent team instance, apply all governance and control.

## Response snapshot

Completed Phase 5 (US1: Email-to-Vault MVP, T064-T087, 24 tasks):

1. Wrote 13 new test cases in `tests/unit/test_gmail_watcher.py`:
   - T064: TestParseEmailFullMessage -- headers/body/attachments parsed correctly
   - T065: TestParseEmailNoBody -- missing body returns "No email body content."
   - T066: TestParseEmailNonUtf8 -- non-UTF8 chars sanitized via sanitize_utf8()
   - T067: TestClassifyActionable -- "Urgent: Please review" → ACTIONABLE
   - T068: TestClassifyInformational -- noreply@/newsletter → INFORMATIONAL
   - T069: TestClassifyDefaultActionable -- ambiguous email → ACTIONABLE (default policy)
   - T070: TestGenerateFilenameNormal -- YYYY-MM-DD-HHmm-subject.md pattern
   - T071: TestGenerateFilenameCollision -- duplicate file → -001 suffix
   - T072: TestRenderMarkdown -- YAML frontmatter with all 12 required fields
   - T073: TestProcessItemActionableRoutesToNeedsAction -- ACTIONABLE → vault/Needs_Action/
   - T074: TestProcessItemInformationalRoutesToInbox -- INFORMATIONAL → vault/Inbox/
   - T075: TestPollFiltersAlreadyProcessed -- processed_ids filter prevents duplicates
   - T076: TestFetchUnreadEmailsWrapsInThread -- asyncio.to_thread() verified (ADR-0002)

2. Rewrote `watchers/gmail_watcher.py` with all Phase 5 implementation:
   - ACTIONABLE_KEYWORDS dict (18 keywords with weights 2-5)
   - INFORMATIONAL_KEYWORDS dict (15 keywords with weights 1-5)
   - INFORMATIONAL_SENDER_PATTERNS regex list (8 patterns: noreply@, newsletter@, etc.)
   - _CLASSIFICATION_THRESHOLD = 2 (default-to-actionable policy per ADR-0004)
   - _classify_email(): scorer over sender+subject+body[:500], returns ACTIONABLE/INFORMATIONAL
   - _parse_email(): extracts headers, decodes base64url body, HTML stripping, attachment detection
   - _extract_body_and_attachments(): recursive multipart traversal, prefers text/plain
   - _decode_body(): base64url decode with UTF-8 errors='replace'
   - _strip_html(): <br>→\n, tag removal, entity decoding (&nbsp; &amp; &lt; &gt;)
   - _fetch_unread_emails(): async wrapper over sync Gmail API (asyncio.to_thread)
   - _fetch_unread_emails_sync(): messages.list(q="is:unread in:inbox", maxResults=50) + per-message get
   - poll(): filter processed_ids, parse, classify, return list[EmailItem]
   - _generate_filename(): YYYY-MM-DD-HHmm-sanitized-subject.md with -001/-002 collision suffix
   - _render_markdown(): YAML frontmatter (12 fields) + email body
   - _get_vault_target_dir(): ACTIONABLE→Needs_Action/, INFORMATIONAL→Inbox/
   - process_item(): generate filename, render markdown, atomic_write, append processed_ids, log
   - __main__ block: argparse with --poll-interval and --vault-path

3. Updated tasks.md: T064-T087 all marked [x]

## Outcome

- Impact: MVP complete -- full email-to-vault pipeline functional. Emails fetched from Gmail API, classified by keyword heuristics (default-to-actionable), written as structured markdown to correct vault directory. Zero-duplicate guarantee via processed_ids filter.
- Tests: 104 passed, 0 failed (13 new Phase 5 tests + 91 existing)
- Files: gmail_watcher.py rewritten, test_gmail_watcher.py updated, tasks.md updated
- Next prompts: /sp.implement Phase 6 (US4: Routing & Ralph Wiggum Compatibility -- T088-T091)
- Reflection: HTML body parsing required careful MIME type traversal through nested multipart/* parts. Date parsing in filename generation uses datetime.fromisoformat() with .replace("Z", "+00:00") for RFC date strings.

## Evaluation notes (flywheel)

- Failure modes observed: None in Phase 5 -- tests were written to match exact API behavior
- Graders run and results (PASS/FAIL): pytest 104/104 PASS. Full regression suite PASS. tasks.md updated PASS.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Phase 6 verifies YAML frontmatter is parseable and compatible with Ralph Wiggum schema. Use yaml.safe_load to parse frontmatter sections in tests.
