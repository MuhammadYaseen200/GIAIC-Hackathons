---
id: 004
title: Gmail Watcher Architecture ADRs
stage: plan
date: 2026-02-17
surface: agent
model: claude-opus-4-6
feature: gmail-watcher
branch: 005-gmail-watcher
user: MuhammadYaseen200
command: /sp.adr
labels: ["adr", "architecture", "gmail-watcher", "phase-2"]
links:
  spec: specs/005-gmail-watcher/spec.md
  ticket: null
  adr: history/adr/0001-watcher-base-class-design.md, history/adr/0002-async-integration-pattern-for-sync-sdks.md, history/adr/0003-local-file-based-data-persistence.md, history/adr/0004-keyword-heuristic-email-classification.md
  pr: null
files:
  - history/adr/0001-watcher-base-class-design.md
  - history/adr/0002-async-integration-pattern-for-sync-sdks.md
  - history/adr/0003-local-file-based-data-persistence.md
  - history/adr/0004-keyword-heuristic-email-classification.md
tests:
  - N/A (documentation-only task)
---

## Prompt

first run adr command then we proceed to tasks gmail-watcher-architecture-decisions to document the 4 ADRs
create claude agent team instance, use skills, sub-agents, mcps, plugins, hooks

## Response snapshot

Created 4 ADRs documenting the architecturally significant decisions from the Gmail Watcher plan:

1. **ADR-0001: Watcher Base Class Design** -- ABC over Protocol for shared lifecycle/retry/state/logging implementation. Alternatives: Protocol, duck typing, mixin pattern.
2. **ADR-0002: Async Integration Pattern for Sync SDKs** -- asyncio.to_thread() wraps sync google-api-python-client. Alternatives: synchronous, aiohttp raw REST, custom executor, subprocess.
3. **ADR-0003: Local File-Based Data Persistence** -- JSON state file + JSONL daily logs in vault/Logs/. Alternatives: SQLite, YAML/plaintext, single JSON file.
4. **ADR-0004: Keyword Heuristic Email Classification** -- Score dictionaries with default-to-actionable policy. Alternatives: LLM-based, ML model, regex-only, always-actionable.

All 4 passed the 3-part significance test (Impact + Alternatives + Cross-cutting). 5 raw decisions clustered into 4 ADRs. create-adr.sh failed due to git root mismatch (monorepo), fell back to agent-native file creation.

## Outcome

- ✅ Impact: 4 ADRs created, documenting all architectural decisions from plan.md before implementation begins
- 🧪 Tests: N/A (documentation-only task)
- 📁 Files: 4 ADR files in history/adr/
- 🔁 Next prompts: /sp.tasks to generate dependency-ordered tasks.md, then /sp.implement
- 🧠 Reflection: create-adr.sh assumes git root = project root, which fails in monorepo. Agent-native fallback worked correctly. ADR clustering reduced 5 raw decisions to 4 logical clusters.

## Evaluation notes (flywheel)

- Failure modes observed: create-adr.sh --json failed because git rev-parse --show-toplevel returns monorepo root, not project dir. Template not found at expected path.
- Graders run and results (PASS/FAIL): Significance test: 4/4 PASS. Clustering check: PASS (no over-granular ADRs). Alternatives check: PASS (3-4 alternatives per ADR).
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Fix create-adr.sh to accept --repo-root override, or set GIT_WORK_TREE for monorepo support.
