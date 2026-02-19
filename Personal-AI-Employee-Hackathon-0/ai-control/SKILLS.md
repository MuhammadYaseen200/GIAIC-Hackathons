# H0 Skills Registry

## Purpose
This file is the authoritative registry of all reusable skills available to Claude Code agents on the H0 project. Per Constitution Principle VIII (Reusable Intelligence), skills MUST be extracted when a pattern repeats 3+ times. Every skill used in the project MUST be registered here.

## Skill Categories

### Category 1: Core Development (SDD Workflow)

| Skill | Trigger | Purpose | Phase |
|-------|---------|---------|-------|
| `/sp.specify` | New feature request | Generate spec.md with Given-When-Then scenarios | All |
| `/sp.clarify` | Ambiguity in spec | Ask 2-5 targeted clarification questions | All |
| `/sp.plan` | Spec approved | Generate plan.md + research.md + data-model.md | All |
| `/sp.adr` | Significant decision detected | Create Architecture Decision Record | All |
| `/sp.tasks` | Plan approved | Generate dependency-ordered tasks.md | All |
| `/sp.taskstoissues` | Tasks approved | Convert tasks to GitHub Issues | All |
| `/sp.implement` | Tasks ready | Execute implementation plan | All |
| `/sp.git.commit_pr` | Implementation done | Git commit + PR creation | All |
| `/sp.phr` | Any prompt completed | Create Prompt History Record | All |
| `/sp.constitution` | Governance change | Create/update project constitution | Phase 0 |
| `/sp.analyze` | After task generation | Cross-artifact consistency check | All |
| `/sp.checklist` | Before implementation | Custom verification checklist | All |
| `/sp.reverse-engineer` | Existing codebase | Reverse into SDD artifacts | As needed |

### Category 2: Quality & Governance

| Skill | Trigger | Purpose | Phase |
|-------|---------|---------|-------|
| `/spec-driven-development` | Any coding attempt | Enforce spec-first workflow | All |
| `/spec-architect` | Feature request | Generate rigorous technical specification | All |
| `/code-cleanliness` | Before commit | Style enforcement, debug cleanup | All |
| `/security-scan` | Before git push | Vulnerability detection, secret scanning | All |
| `/env-validator` | Project init, start failures | Validate .env and environment setup | All |
| `/systematic-debugging` | Bug encountered | Root cause analysis methodology | All |
| `/qa-overseer` | Feature complete claim | Final validation against spec | All |
| `/review-and-judge` | Submission review | Hackathon rubric compliance check | Phase 8 |
| `/hackathon-rules` | Scope decisions | Enforce H0 hackathon constraints | All |

### Category 3: Frontend & UI

| Skill | Trigger | Purpose | Phase |
|-------|---------|---------|-------|
| `/frontend-design` | UI implementation | Production-grade interface design | Phase 5+ |
| `/styling-with-shadcn` | Component creation | Accessible shadcn/ui components | Phase 5+ |
| `/building-chat-interfaces` | Chat UI needed | Auth + context-injected chat | Phase 3+ |
| `/building-chat-widgets` | Interactive UI needed | Agentic UIs with widgets | Phase 5+ |
| `/webapp-testing` | After UI changes | Playwright E2E testing | Phase 4+ |
| `/test-ui` | UI verification | Screenshot-based verification | Phase 4+ |
| `/browsing-with-playwright` | Browser automation | Navigate, fill forms, click | Phase 4+ |

### Category 4: Backend & Infrastructure

| Skill | Trigger | Purpose | Phase |
|-------|---------|---------|-------|
| `/scaffolding-fastapi-dapr` | API implementation | FastAPI + SQLModel scaffolding | Phase 2+ |
| `/building-rag-systems` | Knowledge base | RAG pipeline with vector DB | Phase 6 |
| `/building-mcp-servers` | New MCP needed | MCP server creation guide | Phase 4+ |
| `/mcp-builder` | MCP development | MCP server implementation | Phase 4+ |
| `/configuring-better-auth` | Auth setup | OAuth/JWT authentication | Phase 5+ |
| `/memory-systems` | Agent memory design | State persistence architecture | Phase 3+ |

### Category 5: Governance & Phase Management

| Skill | Trigger | Purpose | Phase |
|-------|---------|---------|-------|
| `/phase-execution-controller` | Phase transition | Validate runtime behavior, safe transition | All |
| `/phase-progress-auditor` | Phase status check | Detect completed/partial/missing artifacts | All |
| `/session-state-manager` | Session start/resume | Persist state for cross-session resume | All |
| `/command-orchestration` | SDD command usage | Ensure correct command ordering | All |
| `/template-selector` | New artifact creation | Auto-select correct template | All |
| `/creating-skills` | Pattern repeated 3+ times | Extract new reusable skill | All |
| `/project-context` | Any project task | Load H0 project context | All |
| `/todo-domain-expert` | Task management logic | Domain knowledge for task systems | All |

### Category 6: Deployment & Operations

| Skill | Trigger | Purpose | Phase |
|-------|---------|---------|-------|
| `/deployment-preflight-check` | Before deploy | Build integrity verification | Phase 7+ |
| `/deployment-stability` | After deploy | Smoke tests and stability checks | Phase 7+ |
| `/containerizing-applications` | Docker setup | Dockerfile and compose generation | Phase 7+ |
| `/operating-production-services` | SRE patterns | SLOs, error budgets, runbooks | Phase 7+ |

### Category 7: Documentation & Knowledge

| Skill | Trigger | Purpose | Phase |
|-------|---------|---------|-------|
| `/doc-coauthoring` | Documentation needed | Structured doc co-authoring | All |
| `/fetching-library-docs` | Library API lookup | Token-efficient doc fetching via Context7 | All |
| `/researching-with-deepwiki` | Repo exploration | GitHub/GitLab repo research | As needed |

## Skill Extraction Protocol

Per Constitution Principle VIII:

```
1. Pattern detected (same approach used 3+ times)
2. Candidate skill identified
3. Extract into /creating-skills format:
   - Name, trigger, purpose
   - Input/output contract
   - Example invocations
   - Edge cases
4. Register in this file
5. Test skill in isolation
6. Announce to team via /Logs/
```

## Skill Priority Matrix

| Priority | When to Use | Examples |
|----------|------------|---------|
| **ALWAYS** | Every operation, no exceptions | /spec-driven-development, /sp.phr, /session-state-manager |
| **PRE-ACTION** | Before specific actions | /security-scan (pre-push), /code-cleanliness (pre-commit), /env-validator (pre-start) |
| **ON-TRIGGER** | When specific condition met | /systematic-debugging (bug), /spec-architect (feature), /phase-execution-controller (phase change) |
| **ON-REQUEST** | When user explicitly asks | /sp.adr, /review-and-judge, /containerizing-applications |

## Skill Dependencies

```
/sp.specify ──► /sp.clarify ──► /sp.plan ──► /sp.tasks ──► /sp.implement ──► /sp.git.commit_pr
                                    │                                               │
                                    ▼                                               ▼
                                /sp.adr                                         /sp.phr
                              (if significant)                               (always)
```

---
*Governed by: .specify/memory/constitution.md (Principle VIII: Reusable Intelligence)*
*See also: AGENTS.md (which agents use which skills), LOOP.md (skill enforcement)*
*Version: 1.0.0 | Date: 2026-02-16*
