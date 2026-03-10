---
id: 001
title: LinkedIn Cron Silver Spec Creation
stage: spec
date: 2026-03-05
surface: agent
model: claude-sonnet-4-6
feature: linkedin-cron-silver
branch: 009-linkedin-cron-silver
user: owner
command: /sp.specify
labels: [spec,linkedin,cron,hitl,silver-tier,phase-5-5,mcp,privacy-gate]
links:
  spec: specs/009-linkedin-cron-silver/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/009-linkedin-cron-silver/spec.md
  - specs/009-linkedin-cron-silver/checklists/requirements.md
tests:
  - Checklist validation: all 12 items PASS
  - No [NEEDS CLARIFICATION] markers in spec
  - All mandatory spec sections present
---

## Prompt

/sp.specify Phase 5.5: LinkedIn Auto-Poster + Cron Scheduling (Silver Tier Completion)

Complete the two remaining Silver tier requirements:

1. LinkedIn Auto-Poster (LinkedIn MCP Server):
   - MCP server: mcp_servers/linkedin/server.py (follows same FastMCP + Pydantic v2 + stdio pattern as ADR-0005)
   - Tools: post_update(text, visibility), get_profile(), health_check()
   - OAuth2 Authorization Code flow: scripts/linkedin_auth.py generates linkedin_token.json
   - HITL approval: every post goes to vault/Pending_Approval/ before publishing (Loop 3, Constitution Principle III)
   - Privacy Gate: apply existing watchers/privacy_gate.py before drafting any post content
   - Post content: AI-drafted about owner's AI/web dev learning, projects, freelance work
   - Rate limit: max 1 post per day (LinkedIn API personal app constraint)
   - Vault logging: every post (approved or rejected) logged to vault/Logs/linkedin_posts.jsonl
   - Graceful degradation: if LinkedIn API unreachable, log warning and continue (Constitution Principle X)
   - Manual trigger: python orchestrator/linkedin_poster.py --draft "topic"
   - Watcher trigger: vault/Needs_Action/ items with type=linkedin_post or tag #linkedin

2. Cron Scheduling:
   - scripts/setup_cron.sh: installs cron entries with absolute paths
   - Orchestrator run every 15 minutes: process vault/Needs_Action/ items
   - LinkedIn post drafting: once per day at 9:00 AM (configurable via CRON_LINKEDIN_TIME in .env)
   - All cron output: >> vault/Logs/cron.log 2>&1
   - scripts/remove_cron.sh: clean uninstall of all project cron entries
   - Cron entries must source .env before running (export $(grep -v "^#" .env | xargs))

Reuse (do NOT reimplement):
   - watchers/privacy_gate.py — PrivacyGate class
   - orchestrator/hitl_manager.py — HITLManager class
   - mcp_servers/whatsapp/bridge.py — GoBridge for WhatsApp HITL notifications
   - mcp_servers/gmail/server.py — reference for MCP server structure

Constraints:
   - NEVER post to LinkedIn without explicit WhatsApp approval from owner (Loop 3)
   - No hardcoded credentials — all from .env: LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN
   - Post content: professional only (AI, web dev, freelance — no personal/sensitive content)
   - linkedin_token.json must be in .gitignore
   - All new MCP tools must have contract tests
   - Test coverage for critical paths must exceed 80% (Constitution Principle V)
   - Wrong directory = STOP. All work in /mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0

## Response snapshot

Created branch `009-linkedin-cron-silver` and wrote full spec to `specs/009-linkedin-cron-silver/spec.md` with:
- 4 User Stories (P1: HITL approval workflow, P2: daily auto-draft cron, P2: orchestrator cron every 15min, P3: vault-triggered posts)
- 8 edge cases (rate limit, bridge offline, token expiry, privacy gate redaction, empty post, cron overlap, idempotent setup, 24hr expiry)
- 16 Functional Requirements: FR-001–FR-010 (LinkedIn), FR-011–FR-016 (Cron)
- 10 Success Criteria: SC-001–SC-010 (all measurable, technology-agnostic)
- Key entities: LinkedInDraft, LinkedInPost, CronEntry, ApprovalRequest
- Assumptions, Out of Scope (Twitter/Facebook/Instagram, comment reading, image attachments), Dependencies

Checklist at `specs/009-linkedin-cron-silver/checklists/requirements.md` — all 12 items PASS.

## Outcome

- ✅ Impact: Complete Phase 5.5 spec ready for /sp.clarify or /sp.plan; Silver tier gap documented with full acceptance criteria
- 🧪 Tests: Checklist validation PASS (12/12); no [NEEDS CLARIFICATION] markers; all mandatory sections present
- 📁 Files: specs/009-linkedin-cron-silver/spec.md (created); specs/009-linkedin-cron-silver/checklists/requirements.md (created)
- 🔁 Next prompts: /sp.clarify (if owner wants to refine), /sp.adr linkedin-oauth2-token-strategy, /sp.plan (when ready for architecture), or Claude plan mode review
- 🧠 Reflection: LinkedIn API v2 uses UGC Posts endpoint (not Share API v1) — this distinction matters for plan phase. ADR-0014 should document the OAuth2 Authorization Code flow vs Gmail's approach.

## Evaluation notes (flywheel)

- Failure modes observed: None — spec creation clean; branch created successfully
- Graders run and results (PASS/FAIL): Checklist validation PASS (12/12 items)
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Consider adding a "Post Preview" acceptance scenario (owner sees formatted preview in WhatsApp before approving, not just raw text)
