---
id: "009"
title: T020-T022 US4 Retry Financial Normalization Green
stage: green
date: 2026-02-23
surface: agent
model: claude-sonnet-4-6
feature: llm-reasoning-loop
branch: 006-llm-reasoning-loop
user: MuhammadYaseen200
command: /sp.implement
labels: ["us4", "ralph-wiggum", "retry-loop", "financial-safety", "provider-normalization", "green"]
links:
  spec: specs/006-llm-reasoning-loop/spec.md
  ticket: null
  adr: specs/006-llm-reasoning-loop/plan.md#adr-0006
  pr: null
files:
  - tests/unit/test_ralph_wiggum_retry.py
  - tests/unit/test_financial_safety.py
  - tests/unit/test_provider_normalization.py
  - orchestrator/orchestrator.py (fix: record_error on MaxIterationsExceeded)
  - specs/006-llm-reasoning-loop/tasks.md (T020-T022 marked [X])
tests:
  - tests/unit/test_ralph_wiggum_retry.py (11 tests — 11 passed)
  - tests/unit/test_financial_safety.py (7 tests — 7 passed)
  - tests/unit/test_provider_normalization.py (10 tests — 10 passed)
  - tests/unit/ full suite (313 tests — 313 passed, 0 regressions)
---

## Prompt

T020–T022 (Phase 6: US4 — Ralph Wiggum retry loop, financial safety, cross-provider normalization tests)

you have constitution, spec, adr, plan, tasks, research and phr file for backup support and as resource and Reusable intelligence to start implementation
- create claude agent team instance
- apply all governance and control, applied enforcement, rules, laws, loops, automations, workflows
- use skills, sub-agents, mcps, plugins, hooks

when complete then we move to next phase, if found bug and error or if work in wrong directory instead of
/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0, stop and get the correct directory and then continue
Wrong Directory = no work, stop immediately, or get right directory move everything related to project in correct directory

AGENT STACK (Mobilized):
- Command Team: @qa-overseer, @loop-controller, @imperator, @path-warden.
- Build Team: @modular-ai-architect, @ux-frontend-developer, @spec-architect.

SKILLS & MCP REGISTRY:
- AI & MCP Construction: building-mcp-servers, scaffolding-openai-agents, streaming-llm-responses, building-chat-interfaces.
- Safety & Quality: deployment-preflight-check, security-scan, env-validator, spec-driven-development, skill-creator.
- Intelligence: Use `skill-creator` if the decision application patterns can be further modularized. Use `context7` MCP for any specific frontmatter or YAML parsing documentation.
- MCP Servers: context7, code-search, postgres.

## Response snapshot

Implemented T020–T022 (Phase 6: US4 Structured Prompting tests):

**Bug fix** — `orchestrator/orchestrator.py`:
- Added `self._orch_state.record_error("MaxIterationsExceeded")` + `self._save_orch_state()` to the MaxIterationsExceeded handler. Previously OrchestratorState.error_counts was never incremented on retry exhaustion.

**T020** — `tests/unit/test_ralph_wiggum_retry.py` (11 tests):
- `_SequentialMockProvider`: returns a different canned response on each call, tracks all (system_prompt, user_message) pairs for assertion
- `TestCorrectionPromptOnRetry`: provider called twice on invalid JSON; 2nd call receives correction prompt; correction prompt embeds original bad response (first 500 chars)
- `TestAllIterationsExhausted`: email status=failed after 3 bad responses (max_iterations=3); message_id tracked in processed_ids; error_counts["MaxIterationsExceeded"]=1; exactly 3 provider calls made
- `TestSuccessOnRetry`: iteration_count=2 in frontmatter when valid JSON on 2nd attempt; decision correctly applied
- `TestPydanticValidationRetry`: decision="maybe" triggers Pydantic error → retry; confidence=2.5 triggers field_validator error → retry

Fix: Tests where archive would move the source file used `needs_info` (keeps file in place) or checked Done/ instead.

**T021** — `tests/unit/test_financial_safety.py` (7 tests):
- `TestFinancialSafetyKeywords`: 4 tests — payment, invoice, billing, subscription all in system prompt
- `TestFinancialSafetyNeverArchive`: 3 tests — NEVER+archive present; urgent/needs_info mentioned as alternatives; all 4 financial terms verified together

**T022** — `tests/unit/test_provider_normalization.py` (10 tests):
- `TestReturnTupleShape`: Both adapters return `(str, int, int)` shape with correct types (mocked SDKs)
- `TestOutputParsesIntoLLMDecision`: Both adapters' output parses into valid LLMDecision
- `TestProviderIdentityDoesNotLeakKeys`: provider_name()/model_name() on both adapters don't contain API key text
- `TestCorrectSdkMethodsCalled`: Anthropic passes system_prompt as dedicated `system=` kwarg; OpenAI passes as system-role message in messages array

**Test results**: 28 new tests (28 passed). Full suite: 313/313 passed.

## Outcome

- ✅ Impact: US4 complete — Ralph Wiggum retry loop fully validated. Financial safety constraint verified. Cross-provider interface normalization confirmed. Error count tracking now actually works.
- 🧪 Tests: 28 new tests (11 retry + 7 financial + 10 normalization). 313/313 full suite. 0 regressions.
- 📁 Files: 3 new test files + 1 bug fix in orchestrator.py + tasks.md updated (T020-T022 marked [X])
- 🔁 Next prompts: T023–T026 (Phase 7: US5 Audit Trail & Observability — logging + state persistence tests + verify_llm_provider.py script)
- 🧠 Reflection: The _SequentialMockProvider pattern (return different response per call, track all calls) is now the standard pattern for testing the retry loop. The archive-moves-file problem in tests is a recurring concern — solution is to use needs_info for tests that need to read the original file after processing.

## Evaluation notes (flywheel)

- Failure modes observed: (1) Two tests tried to read `mock_email_file` after archive decision had moved it — fixed by using needs_info decision or reading from Done/. (2) `_orch_state.record_error()` was never called on MaxIterationsExceeded — added the call + save.
- Graders run and results (PASS/FAIL): `pytest tests/unit/test_ralph_wiggum_retry.py tests/unit/test_financial_safety.py tests/unit/test_provider_normalization.py -v --asyncio-mode=auto` → 28 PASSED. Full: 313 PASSED.
- Prompt variant (if applicable): sp.implement T020-T022 Phase 6 US4
- Next experiment: T023–T026 (Phase 7: logging format tests, state persistence, verify_llm_provider.py script)
