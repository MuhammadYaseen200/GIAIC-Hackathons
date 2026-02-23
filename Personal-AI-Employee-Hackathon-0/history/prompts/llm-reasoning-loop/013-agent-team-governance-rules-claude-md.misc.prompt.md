---
id: "013"
title: Agent Team Governance Rules CLAUDE.md
stage: misc
date: 2026-02-23
surface: agent
model: claude-sonnet-4-6
feature: llm-reasoning-loop
branch: 006-llm-reasoning-loop
user: MuhammadYaseen200
command: /sp.implement (continuation)
labels: ["agent-team", "governance", "claude-md", "rules", "loop-controller", "qa-overseer", "path-warden", "imperator", "skills", "mcps", "orchestration"]
links:
  spec: specs/006-llm-reasoning-loop/spec.md
  ticket: null
  adr: specs/006-llm-reasoning-loop/plan.md#adr-0006
  pr: null
files:
  - CLAUDE.md (Agent Team Governance & Execution Protocol section added)
tests: []
---

## Prompt

first write them all as rule in claude.md file
in every execution:
- first identify the execution
- look if need to implement governance, rules, laws, automations, workflows, loop
- create agent team instance, dedicate tasks, load step related skills, mcps, plugins hooks, read task related files and orchestrate sub agents to manage sub tasks
- mention and explain, how or when to use them and where to use them

[followed by conversation summary request]

## Response snapshot

Added `## Agent Team Governance & Execution Protocol` section to CLAUDE.md (lines 120–411, ~290 lines). The section contains 6 mandatory steps:

**STEP 0 — Execution Identification**: Classify every request as `trivial | single-task | feature | phase | governance | qa | deploy`. Trivial/single-task allow direct execution; all others proceed through the full protocol.

**STEP 1 — Governance Gate**: `@loop-controller` is MANDATORY as FIRST action for all non-trivial requests. Enforces SPEC → CLARIFY → PLAN → TASKS → IMPLEMENT → TEST → QA → DEPLOY cycle. Blocking violations halt all other agents.

**STEP 2 — Governance Layers Check**: Table listing all 8 governance layers (loop-controller, imperator, spec-architect, path-warden, qa-overseer, security-scan, deployment-preflight-check, env-validator) with WHEN each is required and which agent/skill handles it.

**STEP 3 — Agent Team Instantiation**: Full Command Team (loop-controller, imperator, path-warden, qa-overseer) + Build Team (spec-architect, modular-ai-architect, backend-builder, ux-frontend-developer, enterprise-grade-validator) with WHEN/WHERE/HOW for each.

**STEP 4 — Skills, MCPs, Plugins & Hooks Loading**: Skills-by-phase table (Spec/Plan/Tasks/Implement/Test/QA/Deploy/Polish), MCP-by-task-type table (context7, code-search, postgres, git, filesystem, chrome-devtools, hopx-sandbox), hooks respect rules.

**STEP 5 — Task Delegation & Sub-Agent Orchestration**: 5 delegation rules + full orchestration template showing the correct phase execution sequence with parallel/sequential blocks.

**STEP 6 — How/When/Where Reference Card**: Quick-lookup tables + invocation syntax examples for agents, skills, and MCPs.

**Governance Checklist**: 12-item checklist that MUST be completed before marking any phase done. Failure = governance violation.

## Outcome

- ✅ Impact: CLAUDE.md now has binding, mandatory rules for agent team governance. Every future session operating on this project will have the protocol available as project instructions.
- 📁 Files: CLAUDE.md (506 lines total, up from ~210; new section ~290 lines)
- 🔁 Next prompts: Ready for PR creation (`/sp.git.commit_pr`) for the complete `006-llm-reasoning-loop` feature.
- 🧠 Reflection: The rules are written as imperative mandates ("MUST", "ALWAYS", "NEVER skip") rather than suggestions, so the protocol cannot be quietly defaulted around. The checklist format provides a concrete completion gate that can be verified.

## Evaluation notes (flywheel)

- Failure modes observed: Agent team governance protocol was missing from CLAUDE.md despite being specified in every /sp.implement prompt throughout all 9 phases of this feature.
- Root cause: No machine-enforceable rule existed — governance was advisory, not mandatory.
- Fix applied: Rules written as OVERRIDES with explicit blocking conditions (loop-controller blocks all others on violation; checklist must complete before phase marked done).
- Next experiment: Verify protocol is followed in the next feature's first phase.
