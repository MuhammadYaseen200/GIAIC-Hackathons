---
id: 004
title: LinkedIn Cron Silver Implementation Plan
stage: plan
date: 2026-03-05
surface: agent
model: claude-sonnet-4-6
feature: linkedin-cron-silver
branch: 009-linkedin-cron-silver
user: owner
command: /sp.plan
labels: [plan,linkedin,cron,mcp,oauth2,hitl,phase-5-5,silver-tier]
links:
  spec: specs/009-linkedin-cron-silver/spec.md
  ticket: null
  adr: history/adr/0014-linkedin-oauth2-token-lifecycle.md
  pr: null
files:
  - specs/009-linkedin-cron-silver/plan.md
  - specs/009-linkedin-cron-silver/research.md
  - specs/009-linkedin-cron-silver/data-model.md
  - specs/009-linkedin-cron-silver/quickstart.md
  - specs/009-linkedin-cron-silver/contracts/linkedin_mcp_tools.md
tests:
  - Constitution Check: all 9 principles PASS
  - Contract tests defined for all 3 MCP tools (13 test cases total)
  - Phase A-H acceptance gates defined
---

## Prompt

/sp.plan

## Response snapshot

Generated 5 planning artifacts for specs/009-linkedin-cron-silver/:

- research.md: 8 decisions (LinkedIn UGC Posts API, OAuth2 scopes, httpx, topic selection, lock file, cron format, HITL state transitions, rate limit strategy)
- data-model.md: 4 entities (LinkedInDraft, LinkedInPost, CronEntry, ApprovalRequest), full state machine diagram, file naming conventions
- contracts/linkedin_mcp_tools.md: 3 MCP tools (post_update, get_profile, health_check) with Pydantic models, all error paths, 13 contract test cases
- quickstart.md: 7-step setup walkthrough (OAuth2 → PERSON_URN → topic file → health check → manual test → cron install → verify)
- plan.md: 8 implementation phases (A-H), 32 tasks estimated, all 10 acceptance criteria mapped, 5 ADRs referenced

Constitution Check: 9/9 principles PASS.

## Outcome

- ✅ Impact: Phase 5.5 fully planned — ready for /sp.tasks to generate T001-T032 task list
- 🧪 Tests: Contract tests for all 3 MCP tools specified; Phase F targets SC-008 (>80% coverage)
- 📁 Files: 5 artifacts in specs/009-linkedin-cron-silver/ (plan.md, research.md, data-model.md, quickstart.md, contracts/linkedin_mcp_tools.md)
- 🔁 Next prompts: /sp.tasks (generate T001-T032), then /sp.implement
- 🧠 Reflection: LinkedIn UGC Posts API is simpler than expected — just one POST endpoint with a specific JSON structure. The OAuth2 offline_access scope is the key complexity. Setup_cron.sh idempotency via H0_CRON_MANAGED comment suffix is cleaner than grep-based duplicate detection.

## Evaluation notes (flywheel)

- Failure modes observed: plan-template.md has Option 1/2/3 placeholders that need manual cleanup — done correctly here
- Graders run and results (PASS/FAIL): Constitution Check PASS (9/9)
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Add a "cron test mode" to setup_cron.sh that sets LinkedIn drafter to run 2 minutes from now for smoke testing
