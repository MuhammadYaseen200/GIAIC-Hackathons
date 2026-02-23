---
id: 001
title: "LLM Reasoning Loop Spec Creation"
stage: spec
date: 2026-02-22
surface: agent
model: claude-opus-4-6
feature: llm-reasoning-loop
branch: 005-gmail-watcher
user: MuhammadYaseen200
command: /sp.specify
labels: ["phase3", "reasoning-loop", "ralph-wiggum", "multi-llm", "specification"]
links:
  spec: specs/006-llm-reasoning-loop/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-llm-reasoning-loop/spec.md
tests:
  - null
---

## Prompt

You are writing the Phase 3 specification for the Personal AI Employee project.

PROJECT CONTEXT (read these files for full understanding):
- Constitution: .specify/memory/constitution.md
- Phase overview: specs/overview.md
- Phase 2 spec (completed): specs/005-gmail-watcher/spec.md
- ADRs: history/adr/
- AI control: ai-control/LOOP.md
- Spec template: .specify/templates/spec-template.md

PHASE 2 OUTPUT (what exists in vault now):
- vault/Needs_Action/ -- markdown files with status: pending (actionable emails)
- vault/Inbox/ -- markdown files (informational emails)
- Each file has YAML frontmatter: type, status, source, message_id, from, subject, date_received, classification, priority, watcher

FEATURE TO SPECIFY:
Phase 3 -- Multi-LLM Reasoning Loop (Ralph Wiggum Orchestrator)

Core requirements from user:
1. Multi-LLM provider abstraction layer -- Claude is DEFAULT, but can switch to OpenAI, Gemini, OpenRouter, Qwen, GLM, Goose via .env config WITHOUT changing code
2. Ralph Wiggum loop -- reads vault/Needs_Action/ files with status: pending, sends to LLM, gets decision
3. LLM decisions: draft_reply | needs_info | archive | urgent | delegate
4. Draft writer -- writes suggested reply to vault/Drafts/ (does NOT send)
5. Status updates -- updates YAML frontmatter: pending -> pending_approval | needs_info | done
6. HITL (Human in the Loop) -- NEVER sends email without human approval (approval is Phase 4)
7. Runs as separate process alongside Gmail Watcher
8. Structured prompting -- Ralph Wiggum principle: clear, simple, deterministic instructions to LLM
9. Audit trail -- every decision logged to vault/Logs/

## Response snapshot

Generated complete Phase 3 specification at specs/006-llm-reasoning-loop/spec.md including:
- Governance alignment table mapping to all relevant constitution principles and control documents
- Phase 3 entry criteria (all met from Phase 2) and exit criteria (12 items)
- Constraints-first section: 11 NOT-supported items, performance limits, security boundaries, technical debt
- HT-009 new human task for LLM API key configuration with privacy notice
- 6 prioritized user stories (P1-P6) with 35 Given-When-Then acceptance scenarios
- 14 edge cases with specific recovery behavior
- 24 functional requirements (FR-001 through FR-024)
- 7 key entities with detailed descriptions
- Complete data contracts: LLMDecision schema, updated email frontmatter, draft reply schema, decision log entry schema, orchestrator state schema, supported providers registry table
- 10 measurable success criteria (SC-001 through SC-010)
- Non-functional requirements: performance, scalability, security, observability
- Enforcement loop integration for all 4 loops (Spec-Driven, Ralph Wiggum, HITL, Directory Guard)
- State machine definition with 5 states and transition triggers
- 3 ADR suggestions for significant architectural decisions
- In-scope / out-of-scope boundary definition
- Upstream and downstream dependency mapping

## Outcome

- Impact: Complete Phase 3 specification produced, ready for /sp.clarify and /sp.plan
- Tests: No tests yet (spec phase -- tests come during implementation)
- Files: 1 file created (specs/006-llm-reasoning-loop/spec.md)
- Next prompts: /sp.clarify on spec, then /sp.plan for architecture, then /sp.adr for the 3 suggested ADRs
- Reflection: Spec is comprehensive -- 24 FRs, 35 acceptance scenarios, 14 edge cases. The provider abstraction design and structured output enforcement are the two highest-risk architectural decisions that need ADRs before implementation.

## Evaluation notes (flywheel)

- Failure modes observed: None during spec creation. Potential risk: spec may over-specify implementation details (e.g., specific SDK names in provider registry). This is acceptable for a spec that must be implementable without questions.
- Graders run and results (PASS/FAIL): N/A (spec phase)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Run /sp.clarify to identify any ambiguities, then proceed to /sp.plan
