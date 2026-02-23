---
id: 003
title: Phase 3 Plan Ralph Wiggum Orchestrator
stage: plan
date: 2026-02-23
surface: agent
model: claude-opus-4-6
feature: llm-reasoning-loop
branch: 006-llm-reasoning-loop
user: MuhammadYaseen200
command: /sp.plan
labels: ["plan","ralph-wiggum","orchestrator","multi-llm","provider-abstraction","openai-compatible"]
links:
  spec: specs/006-llm-reasoning-loop/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-llm-reasoning-loop/plan.md
  - specs/006-llm-reasoning-loop/research.md
tests:
  - none (plan phase, no code changes)
---

## Prompt

/sp.plan

you have constitution, spec, adr, plan, tasks and phr file for backup support and as resource and Reusable intelligence to start generate plan
- create claude agent team instance
- apply all governance and control, applied enforcement, rules, laws, loops, automations, workflows
- use skills, sub-agents, mcps, plugins, hooks

(Follow-up): you should use context 7 for openai agent sdk openai_compatible with other llms

## Response snapshot

Generated complete Phase 3 implementation plan via @modular-ai-architect (claude-opus-4-6) with parallel @loop-controller gate validation.

**Governance results**:
- @loop-controller: GATE CLEAR — 6/6 checkpoints passed (spec approved, /sp.clarify done, orchestrator/ empty, correct sequence, no tasks.md yet, correct branch)
- @path-warden: Not run (plan-only phase, no file placement violations expected)

**plan.md** (1253 lines) covers:
1. Context + Phase 3 entry criteria (all satisfied)
2. Technical context: runtime constraints, dependencies (anthropic, openai, pydantic)
3. Constitution compliance check: 10/10 principles
4. Three new ADRs: ADR-0005 (provider abstraction), ADR-0006 (structured output), ADR-0007 (base class)
5. Module design for 14 files across `orchestrator/` directory
6. Provider abstraction: 2 adapters decided — `AnthropicAdapter` + `OpenAICompatibleAdapter`
7. Data flow diagrams (poll cycle, LLM call, decision application, state machine)
8. Ralph Wiggum system prompt and JSON schema contract
9. Testing strategy: 12 test files, ~120 tests
10. Implementation order: 14 files in 7 dependency-ordered phases
11. Verification plan (unit → integration → e2e smoke test)
12. Appendices: FR coverage matrix, environment variable reference

**research.md** (329+ lines) covers 8 research areas:
1. Provider abstraction (OpenAI-compatible as de facto standard)
2. Why not litellm (large deps, black-box errors)
3. Structured output (Pydantic + prompt engineering)
4. Orchestrator base class (extend BaseWatcher)
5. YAML frontmatter parsing
6. Vault scanning
7. Atomic frontmatter update
8. OpenAI Agents SDK vs raw openai SDK (new: confirmed raw SDK is correct choice)

**OpenAI Agents SDK research**: User requested Context7 docs on openai_compatible patterns. Key finding: `openai-agents` uses `OpenAIChatCompletionsModel(openai_client=AsyncOpenAI(base_url=...))` internally — identical to our `OpenAICompatibleAdapter._client = AsyncOpenAI(base_url=...)`. Our direct SDK approach is confirmed correct. The `openai-agents` framework would add overhead without benefit for our use case (we are building the orchestrator, not using another framework's orchestrator).

## Outcome

- ✅ Impact: plan.md + research.md complete — Phase 3 architecture fully designed, 3 ADRs identified, 14-module dependency chain specified, 2-adapter provider architecture confirmed
- 🧪 Tests: No test changes (plan phase only)
- 📁 Files: specs/006-llm-reasoning-loop/plan.md (1253 lines), specs/006-llm-reasoning-loop/research.md (380 lines)
- 🔁 Next prompts: /sp.tasks — generate dependency-ordered tasks.md from plan.md; then /sp.adr for ADR-0005, ADR-0006, ADR-0007
- 🧠 Reflection: Agent hit Anthropic rate limit during PHR creation step, but both plan.md and research.md were written successfully before the limit. PHR created manually (this file). @loop-controller validated the gate cleanly 6/6 — spec-driven workflow compliance maintained.

## Evaluation notes (flywheel)

- Failure modes observed: Rate limit hit during PHR creation (cosmetic — deliverables written successfully); Context7 MCP not configured for this project (worked around with WebFetch)
- Graders run and results (PASS/FAIL): @loop-controller GATE CLEAR 6/6 PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Proceed to /sp.tasks
