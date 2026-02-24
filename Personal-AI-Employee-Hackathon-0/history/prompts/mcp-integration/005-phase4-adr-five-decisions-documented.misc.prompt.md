---
id: "005"
title: Phase 4 ADR — Five Decisions Documented
stage: misc
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: mcp-integration
branch: 007-mcp-integration
user: MuhammadYaseen200
command: /sp.adr
labels: ["adr","mcp-integration","phase4","fastmcp","oauth2","fallback-protocol","error-contract","vault-ops"]
links:
  spec: specs/007-mcp-integration/spec.md
  ticket: "null"
  adr: history/adr/0005-mcp-server-framework-stack.md
  pr: "null"
files:
  - history/adr/0005-mcp-server-framework-stack.md
  - history/adr/0006-gmail-oauth2-architecture-mcp-context.md
  - history/adr/0007-mcp-fallback-protocol-orchestrator-wiring.md
  - history/adr/0008-typed-mcp-error-contract.md
  - history/adr/0009-vault-operations-reuse-strategy.md
  - history/prompts/mcp-integration/005-phase4-adr-five-decisions-documented.misc.prompt.md
tests:
  - "null"
---

## Prompt

/sp.adr

now read spec, plan, reseach, data moel, quick start, tasks, requirements and contracts to generate adr of phase 4 (MCP integration)

 you have constitution, spec, adr, plan, tasks, research and phr file for backup support and as resource and Reusable intelligence to start generating adr
- create claude agent team instance
- apply all governance and control, applied enforcement, rules, laws,   loops,   autionations, workflows
- use skills, sub-agents, mcps, plugins, hooks
### 3. AGENT STACK (Mobilized)
- **Command Team**: @qa-oversee, @loop-controller, @imperator, @path-warden.
- **Build Team**: @modular-ai-architect, @ux-frontend-developer, @spec-architect.

### 4. SKILLS & MCP REGISTRY
- **A. AI & MCP Construction**: building-mcp-servers, scaffolding-openai-agents, streaming-llm-responses, building-chat-interfaces.
- **B. Safety & Quality**: deployment-preflight-check, security-scan, env-validator, spec-driven-development, skill-creator.
- **Context**: Use `context7` MCP for documentation, framework, and package verification. Use `skill-creator` if a new ADR template pattern is needed.
- **Active MCPs**: context7, code-search, postgres.

## Response snapshot

Read all Phase 4 planning artifacts (spec, plan, research, data-model, quickstart, tasks, contracts/gmail-tools.json, contracts/obsidian-tools.json). Applied ADR clustering rules — grouped 8 research decisions into 5 architecturally significant decision clusters. Verified no conflicts with existing ADRs 0001–0004. create-adr.sh failed (template not found); used agent-native Write tool for all 5 ADRs.

**ADRs created:**

- **ADR-0005** (`0005-mcp-server-framework-stack.md`): FastMCP + Pydantic v2 + stdio transport for both MCP servers. Supersedes research.md D1 (low-level Server API). Alternatives: low-level Server (rejected — 2× boilerplate), FastAPI SSE (rejected — no streaming needed), TypeScript SDK (rejected — Python consistency + reuse constraint).

- **ADR-0006** (`0006-gmail-oauth2-architecture-mcp-context.md`): Gmail OAuth2 singleton pattern — `get_gmail_service()` adapted from `gmail_watcher.py:170-211`, no browser flow, `AuthRequiredError` if token missing. Alternatives: reimplement OAuth2 (rejected — spec FR-007), inherit GmailWatcher (rejected — wrong abstraction), per-call auth (rejected — ~200ms overhead), keychain (rejected — WSL2 unreliable).

- **ADR-0007** (`0007-mcp-fallback-protocol-orchestrator-wiring.md`): Dedicated `MCPClient` class in `orchestrator/mcp_client.py` — subprocess JSON-RPC → on failure log `mcp_fallback` JSONL → run fallback callable (vault_ops) → raise `MCPUnavailableError`. Alternatives: inline MCP calls (rejected — SRP), async ClientSession (rejected — instability), vault_ops direct (rejected — spec violation), MCP-only no fallback (rejected — Constitution X).

- **ADR-0008** (`0008-typed-mcp-error-contract.md`): `MCPErrorCode` Literal + `MCPError` Pydantic model; all tools return `json.dumps(...)` — never raw exceptions; 8 named error codes; orchestrator detects via `result.get("error")`. Alternatives: raise exceptions (rejected — no structured codes), HTTP status codes (rejected — MCP not HTTP), union type (rejected — complexity), isError flag only (rejected — insufficient for fallback discrimination).

- **ADR-0009** (`0009-vault-operations-reuse-strategy.md`): Direct import `atomic_write`, `render_yaml_frontmatter`, `sanitize_utf8` from `watchers/utils.py` via `sys.path.insert(0, project_root)` in server.py. Alternatives: reimplement (rejected — spec FR-010 + duplication), `shared/` package (rejected — 385 tests reference watchers.utils), pip install -e . (rejected — over-engineered), vault_ops import (rejected — cross-layer dependency).

**Referenced existing ADRs (no conflicts):**
- ADR-0001: BaseWatcher pattern (non-watcher MCP servers do NOT use BaseWatcher — confirmed)
- ADR-0002: Async SDK pattern (MCPClient uses asyncio.create_subprocess_exec — consistent)
- ADR-0003: JSONL logging + atomic write (mcp_fallback.jsonl follows same format — consistent)
- ADR-0004: LLM provider registry (no overlap — ADR-0007 covers MCP orchestrator wiring)

## Outcome

- ✅ Impact: 5 ADRs created covering all architecturally significant Phase 4 decisions; all spec FRs (FR-001–FR-016) traceable to at least one ADR; create-adr.sh failure handled gracefully via agent-native tools
- 🧪 Tests: No tests run (ADR generation phase — governance artifact, not implementation)
- 📁 Files: 5 ADR files created in history/adr/; PHR written to history/prompts/mcp-integration/
- 🔁 Next prompts: /sp.implement — begin T001–T031 from specs/007-mcp-integration/tasks.md; start with Phase 1+2 (T001–T010) then Phase 3 MVP (T011–T016)
- 🧠 Reflection: Clustering 8 research decisions into 5 ADRs (not 8 atomic records) was the right call — avoids over-granular ADRs for trivially related decisions; building-mcp-servers skill correctly identified FastMCP as the recommended framework, overriding the original D1 low-level Server API choice

## Evaluation notes (flywheel)

- Failure modes observed: create-adr.sh template not found — mitigated by agent-native Write tool; setup-plan.sh returned external path (parent dir) — mitigated by using project-local specs/ directory
- Graders run and results (PASS/FAIL): ADR clustering check PASS (all 5 ADRs have alternatives + tradeoffs + multi-component scope); significance test PASS (all 5 decisions are cross-cutting and will be revisited); conflict check PASS (no conflicts with ADR-0001–0004)
- Prompt variant (if applicable): sp.adr-v1
- Next experiment: Add `create-adr.sh` template repair script to `.specify/scripts/bash/` so agent-native fallback is not needed in future sessions
