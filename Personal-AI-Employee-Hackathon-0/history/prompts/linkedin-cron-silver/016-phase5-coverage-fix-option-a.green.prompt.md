---
id: "016"
title: Phase 5 Coverage Fix Option A
stage: green
date: 2026-03-10
surface: agent
model: claude-sonnet-4-6
feature: hitl-whatsapp-silver
branch: 009-linkedin-cron-silver
user: m-y-j
command: sp.implement
labels: ["coverage","phase-5","whatsapp","hitl","agent-team","warnings","utcnow"]
links:
  spec: specs/008-hitl-whatsapp-silver/spec.md
  ticket: specs/008-hitl-whatsapp-silver/tasks.md
  adr: history/adr/0012-whatsapp-backend-selection.md
  pr: null
files:
  - tests/unit/test_whatsapp_watcher.py
  - tests/unit/test_whatsapp_bridge_server.py
  - tests/unit/test_hitl_manager.py
  - orchestrator/linkedin_poster.py
  - tests/unit/test_linkedin_poster.py
tests:
  - tests/unit/test_whatsapp_watcher.py (all pass)
  - tests/unit/test_whatsapp_bridge_server.py (14 new tests, all pass)
  - tests/unit/test_hitl_manager.py (12 new tests, all pass)
  - tests/unit/test_linkedin_poster.py (87 pass, 0 warnings)
  - 142 total tests, 0 failures, -W error::DeprecationWarning -W error::RuntimeWarning PASS
---

## Prompt

option: A (recommended)
Read Constitution, specs, clarify, plan, adr, requirements, checklists, contracts, and overview files
create claude agent team instance, specify the to use sub-agents, skills, Context7, and Mcps, divide task among
instance and deploy specialist sub-agents and must skills

[Fix all 3 gaps from Phase 5 Silver: WhatsApp coverage gaps, HITL manager coverage, trivial warnings]

## Response snapshot

Created 3-agent team `phase5-coverage-fixes` with parallel execution:

**wa-coverage-writer**: Added 8 tests to test_whatsapp_watcher.py + created test_whatsapp_bridge_server.py (14 tests):
- TestGetHttpClient: singleton pattern coverage
- TestPoll: returns messages, since param, JID stripping, empty response, HTTP error
- TestDeduplication: skips existing message_id file
- TestGoBridgeSend: success (200), failure (500 → ValueError), _to_jid helper
- TestGoBridgeHealth: healthy on 405, healthy on 200, unhealthy on ConnectError
- TestPywaStub: send/health both raise NotImplementedError
- TestServerSendMessage: success path, error path
- TestServerHealthCheck: success path, error path
- TestGetBridge: go_bridge/pywa/unknown backends
Result: whatsapp_watcher.py 71%→100%, bridge.py 55%→100%, server.py 0%→97%

**hitl-coverage-writer**: Added 12 tests to test_hitl_manager.py:
- Draft ID collision guard (while-loop body)
- Empty send_batch_notification early return
- Approve/reject "draft not found" error paths
- LinkedIn post approve/reject HITL paths (type=linkedin_post)
- check_timeouts: no created_at, invalid date, naive datetime, 48h timed_out, 24h reminder
Result: hitl_manager.py 80%→96%

**trivial-fixes**: Two source file changes:
- orchestrator/linkedin_poster.py: `datetime.utcnow()` → `datetime.now(timezone.utc)` in 3 places; added `timezone` to import
- tests/unit/test_linkedin_poster.py: replaced whole-asyncio mock with `asyncio.run` + `_run_and_close` helper in test_main_draft_arg/auto_arg/check_arg
Result: Zero DeprecationWarning, zero RuntimeWarning

**Final verification (142 tests, -W error flags):**
```
mcp_servers/whatsapp/bridge.py    100%
mcp_servers/whatsapp/server.py     97%   (line 55: mcp.run() in __main__)
mcp_servers/whatsapp/models.py    100%
watchers/whatsapp_watcher.py      100%
orchestrator/hitl_manager.py       99%   (lines 472-473: rare exception fallback)
orchestrator/linkedin_poster.py    99%   (lines 32-33, 457: untestable sys.exit + __main__)
142 passed, 0 failed, 0 DeprecationWarning, 0 RuntimeWarning
```

## Outcome

- ✅ Impact: Phase 5 Silver coverage gaps fully closed. All Phase 5+5.5 modules now ≥97%. SC-008 gate met on all Silver tier files.
- 🧪 Tests: 142 total passing. +22 tests added (8 watcher + 14 bridge/server + 12 hitl_manager). Zero warnings.
- 📁 Files: tests/unit/test_whatsapp_watcher.py, tests/unit/test_whatsapp_bridge_server.py (new), tests/unit/test_hitl_manager.py, orchestrator/linkedin_poster.py, tests/unit/test_linkedin_poster.py
- 🔁 Next prompts: Phase 6 Gold — CEO Briefing + Odoo spec
- 🧠 Reflection: The GoBridge uses `async with httpx.AsyncClient` context manager — tests must patch both `__aenter__` and `__aexit__` on the mock. PywaStub is sync class with async methods — can test without event loop tricks. Module-level `WHATSAPP_BACKEND` binding means `importlib.reload()` is needed for env-var-dependent _get_bridge tests.

## Evaluation notes (flywheel)

- Failure modes observed: Coverage flags with file path syntax (watchers/whatsapp_watcher.py) silently exclude files — always use directory path (watchers) or dotted module notation
- Graders run and results (PASS/FAIL): 142/142 PASS; -W error::DeprecationWarning PASS; -W error::RuntimeWarning PASS
- Prompt variant (if applicable): 3-agent parallel team (independent files, no conflicts)
- Next experiment (smallest change to try): Add subprocess test for lines 32-33 (sys.exit guard) and 55 (__main__ mcp.run) to push remaining files to 100%
