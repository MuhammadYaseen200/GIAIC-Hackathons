---
id: "013"
title: Fix D-004 LinkedIn HITL Approval Routing
stage: green
date: 2026-03-09
surface: agent
model: claude-sonnet-4-6
feature: linkedin-cron-silver
branch: 009-linkedin-cron-silver
user: m-y-j
command: manual (context resumed)
labels: ["bug-fix","hitl","whatsapp","linkedin","d-004","routing"]
links:
  spec: specs/009-linkedin-cron-silver/spec.md
  ticket: specs/009-linkedin-cron-silver/tasks.md
  adr: history/adr/0014-linkedin-oauth2-token-lifecycle.md
  pr: null
files:
  - orchestrator/linkedin_poster.py
  - orchestrator/hitl_manager.py
  - tests/unit/test_linkedin_poster.py
tests:
  - tests/unit/test_linkedin_poster.py (69 tests, all PASS)
  - tests/unit/test_hitl_manager.py (included in 69 total)
---

## Prompt

let's start fix D-004 LinkedIn HITL approval

## Response snapshot

Fixed D-004: LinkedIn HITL approval was broken — WhatsApp "approve <id>" replies could not route to LinkedIn drafts.

**Root cause (2-part)**:
1. `_write_draft_vault_file()` wrote no `draft_id:` frontmatter field → `HITLManager._find_draft()` couldn't match
2. Even if found, `HITLManager._approve()` would send email instead of publishing to LinkedIn

**3 files changed:**

**`orchestrator/linkedin_poster.py`**:
- Added `from orchestrator.hitl_manager import _generate_draft_id` import
- `_write_draft_vault_file()`: now calls `_generate_draft_id()`, adds `draft_id:` to frontmatter, returns `tuple[Path, str]`
- `_send_hitl_notification()`: added `draft_id: str` param, shows `short_id` (last 12 chars) in WA message with explicit approve/reject commands
- `draft_and_notify()`: unpacks `(draft_path, draft_id)` tuple, passes `draft_id` to notification + log

**`orchestrator/hitl_manager.py`**:
- `_approve()`: reads `fm.get("type")` — if `linkedin_post`: sets `status=approved` in place (stays in Pending_Approval/), skips Gmail, sends WA confirmation; if `approval_request`: original email flow unchanged
- `_reject()`: same dispatch — linkedin_post stays in place with `status=rejected`; email flow unchanged

**5 new tests in test_linkedin_poster.py**:
- `test_write_draft_vault_file_includes_draft_id` — verifies frontmatter has draft_id
- `test_draft_and_notify_returns_draft_id_in_log` — e2e draft_id in vault file
- `test_hitl_approve_linkedin_sets_approved_in_place` — status=approved in Pending_Approval/, NOT in Approved/, Gmail NOT called
- `test_hitl_reject_linkedin_sets_rejected_in_place` — status=rejected in place, Gmail NOT called
- `test_hitl_approve_email_draft_unchanged` — approval_request flow still sends email + moves to Approved/

## Outcome

- ✅ Impact: D-004 FIXED — WhatsApp "approve <id>" now routes correctly to LinkedIn drafts; check_pending_approvals() picks up status=approved and publishes; email drafts unaffected
- 🧪 Tests: 69 passed, 0 failed (was 64 before; +5 D-004 tests)
- 📁 Files: orchestrator/linkedin_poster.py, orchestrator/hitl_manager.py, tests/unit/test_linkedin_poster.py
- 🔁 Next prompts: Phase 6 prep (Odoo Gold tier spec); D-003 (remove REQUIRED_DIR hardcode); D-002 (unify frontmatter parsers)
- 🧠 Reflection: The fix intentionally leaves LinkedIn drafts IN Pending_Approval/ after approve (not moving to Approved/) so check_pending_approvals()'s glob pattern `*_linkedin_*.md` continues to find them. Keeping the two approval flows (email vs LinkedIn) decoupled via type-dispatch avoids coupling HITLManager to LinkedIn business logic.

## Evaluation notes (flywheel)

- Failure modes observed: none — all 69 tests green on first run after changes
- Graders run and results (PASS/FAIL): 69/69 PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Test D-003 fix (remove REQUIRED_DIR guard) — make linkedin_poster.py portable across machines
