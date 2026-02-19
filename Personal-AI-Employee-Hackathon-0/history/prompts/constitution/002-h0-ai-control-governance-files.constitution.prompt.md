---
id: 002
title: H0 AI-Control Governance Files
stage: constitution
date: 2026-02-16
surface: agent
model: claude-opus-4-6
feature: none
branch: 004-phase3-chatbot
user: MuhammadYaseen200
command: none
labels: ["ai-control", "governance", "agents", "loops", "swarm", "mcp", "skills", "human-tasks", "parallel-agents"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - ai-control/AGENTS.md
  - ai-control/LOOP.md
  - ai-control/SWARM.md
  - ai-control/MCP.md
  - ai-control/SKILLS.md
  - ai-control/HUMAN-TASKS.md
tests:
  - none
---

## Prompt

create an agent team instances, read @H0-MIND-MAP, read @Doc-Personal-AI-Employee-Hackathon-0_ Building-Autonomous-FTEs-in-2026 and @Personal-AI-Employee-Hackathon-0-Rough-Planning and create a proper professional constitution of H0, use subagents, skills, plugins, hooks, and MCPs while tell me any manual work that you can't do, need human?

(Continued from constitution creation: constitution created ai-control/ TODO, this prompt created all 6 governance files)

## Response snapshot

Launched 6 parallel subagents to create ai-control/ governance files:

1. **AGENTS.md Agent** — Created agent registry with 15 agents across 3 layers (Command: Imperator + Lead-Architect, Execution: 6 agents, Quality: 7 agents), 7 non-negotiable rules, activation protocol, vault-based communication protocol.

2. **LOOP.md Agent** — Created 4 enforcement loops with ASCII diagrams: Spec-Driven Loop (SPEC->IMPLEMENT->TEST->QA->REPEAT), Ralph Wiggum Loop (autonomous completion with 5-retry safety), Human-in-the-Loop (sensitive action approval), Directory Guard (path validation). Includes loop interaction matrix.

3. **SWARM.md Agent** — Created multi-agent orchestration rules: parallel execution patterns, team composition, coordination protocols, agent independence guarantees.

4. **MCP.md Agent** — Created MCP server registry: 13 connected servers (filesystem, git, postgres, docker, hopx-sandbox, playwright, scriptflow, github, context7, ragie, nx-mcp, chrome-devtools, code-search), 8 broken servers needing fixes, 5 needed servers (Gmail, WhatsApp, Obsidian, Calendar, Odoo), fallback protocol, development standards.

5. **SKILLS.md Agent** — Created skills registry with 7 categories (SDD Workflow, Quality & Governance, Frontend & UI, Backend & Infrastructure, Governance & Phase Management, Deployment & Operations, Documentation & Knowledge), 63+ skills registered, extraction protocol, priority matrix (ALWAYS/PRE-ACTION/ON-TRIGGER/ON-REQUEST), dependency graph.

6. **HUMAN-TASKS.md Agent** — Created human-dependent task tracker: 8 tasks (HT-001 through HT-008) covering all 9 constitution TODOs, organized by priority (Critical/High/Medium/Low), each with status, blocking phase, "Why Human" rationale, step-by-step instructions, verification criteria, and Claude handoff points.

## Outcome

- Impact: All 6 ai-control/ governance files created — operationalizes the constitution's agent hierarchy, enforcement loops, and governance framework
- Tests: none — governance documents, not code
- Files: ai-control/AGENTS.md, ai-control/LOOP.md, ai-control/SWARM.md, ai-control/MCP.md, ai-control/SKILLS.md, ai-control/HUMAN-TASKS.md (all created)
- Next prompts: /sp.specify for Phase 0 remaining tasks (project structure directories), then Phase 1 Obsidian Vault setup
- Reflection: All 6 parallel subagents completed successfully before the context limit hit. Verification after reset confirmed zero data loss — all files are complete with no empty placeholders. The HUMAN-TASKS.md was a bonus addition (not originally in the constitution TODO list) that provides critical transparency for the 9 manual tasks.

## Evaluation notes (flywheel)

- Failure modes observed: Context limit hit during PHR creation (this PHR), but all 6 governance files were already written. No data loss.
- Graders run and results (PASS/FAIL): 6 parallel verification agents PASS — all sections populated, no empty placeholders, cross-references consistent with constitution v1.0.0
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Use governance files as input to Phase 0 completion audit via /phase-progress-auditor
