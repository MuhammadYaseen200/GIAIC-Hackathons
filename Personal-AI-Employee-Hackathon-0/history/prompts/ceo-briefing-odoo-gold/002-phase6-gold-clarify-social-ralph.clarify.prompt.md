---
id: "002"
title: Phase 6 Gold Clarify Social Ralph Loop
stage: clarify
date: 2026-03-11
surface: agent
model: claude-sonnet-4-6
feature: ceo-briefing-odoo-gold
branch: 010-ceo-briefing-odoo-gold
user: m-y-j
command: sp.clarify
labels: ["phase-6","gold","clarify","social-media","ralph-wiggum","facebook","instagram","twitter","dm-monitoring","mcp"]
links:
  spec: specs/010-ceo-briefing-odoo-gold/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/010-ceo-briefing-odoo-gold/spec.md
tests:
  - Spec quality checklist: all clarification markers resolved; 3/3 interactive Q&A answered
---

## Prompt

one thing i'm clarifying is that, it must should cover all from given below, its all from document file:
Gold Tier: Autonomous Employee
Estimated time: 40+ hours
All Silver requirements plus:
Full cross-domain integration (Personal + Business)
Create an accounting system for your business in Odoo Community (self-hosted, local) and integrate it via an MCP server using Odoo's JSON-RPC APIs (Odoo 19+).
Integrate Facebook and Instagram and post messages and generate summary
Integrate Twitter (X) and post messages and generate summary
Multiple MCP servers for different action types
Weekly Business and Accounting Audit with CEO Briefing generation
Error recovery and graceful degradation
Comprehensive audit logging
Ralph Wiggum loop for autonomous multi-step task completion (see Section 2D)

Documentation of your architecture and lessons learned
All AI functionality should be implemented as Agent Skills

another thing is, also explain me what we are going to achieve in this phase, to understand and clear if i have any question,

also add those problems mistakes, that we face till now, like: remain to add, edit, change, update, weaknesses, leaks, loose, tests, latency, majors, minors, small, big, risk, medium, low, high, flows, scripts problem, ensure no name user name, email, real phone number, any path, directory, key word, address all gitignore, nothing expose

[Q1 answer] B Recommended,
and i do not even know about what mcp will be official, safe, authenticate, and perfect for our development and for future,
when you want to add mcp for (Facebook, Instagram, Twitter/X,) go at:
https://github.com/modelcontextprotocol/servers
or
https://modelcontextprotocol.io/docs/getting-started/intro
add appropriate mcp for them
note: i will use all automated social media for my career perspective, personal branding, clients, job
keep in mind that for personal DM, comments, so you have to notify me if for serious, sensitive, job and client related reply or need human approval,

[Q2 answer] Recommended: Option A

[Q3 answer] yes recommended

## Response snapshot

Ran `/sp.clarify` for `010-ceo-briefing-odoo-gold`. Full spec rewrite incorporating all Gold Tier official requirements (previous session), then conducted 3-question interactive Q&A:

**Q1 — Social media credentials status:**
- Answer: None exist yet (Option B)
- Action: HT-014 (Facebook Page + App), HT-015 (Instagram Business Account), HT-016 (Twitter/X developer app) to be added to HUMAN-TASKS.md
- Official MCP registry checked — no Facebook/Instagram/Twitter MCPs found; custom FastMCP servers will be built following project pattern
- Additional scope from Q1: DM/comment monitoring with HITL escalation for job/client keywords added as FR-028 (P3)

**Q2 — Facebook/Instagram account type:**
- Answer: Facebook Page + Instagram Business Account linked to it (Option A)
- Action: FR-016 updated to specify Meta Graph API + Page Access Token; HT-014/HT-015 updated
- Out of Scope updated: "Autonomous replies to DMs" (monitoring still in scope)

**Q3 — Ralph Wiggum loop implementation:**
- Answer: New `run_until_complete()` wrapper (Option B)
- Action: FR-029 (run_until_complete utility) + FR-030 (atomic step design) added
- Each workflow step retries up to N times with exponential backoff; escalates to HITL after exhausting retries

**Final spec state:**
- 8 User Stories (US1–US8)
- 30 Functional Requirements (FR-001–FR-030)
- 12 Success Criteria (SC-001–SC-012)
- Clarifications section: 7 bullets (4 from initial rewrite + 3 from Q&A)

## Outcome

- ✅ Impact: All 3 interactive Q&A questions answered; spec fully resolved with 0 [NEEDS CLARIFICATION] markers. Ralph Wiggum loop defined as run_until_complete() wrapper (FR-029/FR-030). DM monitoring added as FR-028. Social MCP account type locked in (Facebook Page + Instagram Business). Custom MCPs confirmed for all 3 platforms.
- 🧪 Tests: Spec quality checklist — all clarification markers resolved; 3 interactive questions answered and encoded into spec
- 📁 Files: specs/010-ceo-briefing-odoo-gold/spec.md (updated — Clarifications, FR-028, FR-029, FR-030, Out of Scope, Assumptions)
- 🔁 Next prompts: /sp.plan for Phase 6 Gold; then add HT-014/HT-015/HT-016 to ai-control/HUMAN-TASKS.md
- 🧠 Reflection: Official MCP registry has no social media MCPs for Facebook/Instagram/Twitter — all must be custom-built. This is architecturally consistent with project pattern (FastMCP for everything) but means 3 new MCP servers in Phase 6. Ralph Wiggum loop is a genuinely new architectural component, not covered by existing orchestrator polling.

## Evaluation notes (flywheel)

- Failure modes observed: Official MCP registry search returned no social media results — always check registry before assuming coverage exists; custom build is the fallback for H0
- Graders run and results (PASS/FAIL): 3/3 Q&A questions answered; spec quality checklist PASS (0 markers remaining)
- Prompt variant (if applicable): Resumed from context limit with prior spec rewrite already done; interactive Q&A continued cleanly
- Next experiment (smallest change to try): Add HT-014/HT-015/HT-016 to HUMAN-TASKS.md, then run /sp.plan
