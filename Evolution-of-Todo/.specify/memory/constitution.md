<!--
SYNC IMPACT REPORT - Constitution Update
Version Change: 1.1.0 → 2.0.0 (MAJOR)
Date: 2026-01-25
Updated By: lead-architect, loop-controller, imperator

BREAKING CHANGES:
- Added Principle VI: AAIF Standards & Interoperability (mandatory MCP/AGENTS.md/Goose alignment)
- Added Principle VII: Mandatory Clarification Gate (enforces /sp.clarify workflow)
- Added Principle VIII: Process Failure Prevention (Phase 3 retrospective learnings)
- Restructured Agent Orchestration into Command Team vs Build Team
- Added Reusable Intelligence Framework (Skills/MCPs/Commands tracking)
- Added AI Control Directory Structure (/ai-control/ behavioral constitutions)

MODIFIED PRINCIPLES:
- Principle I: Spec-Driven Development → Added explicit violation detection system
- Principle V: Intelligence Capture → Expanded to include Skills creation mandate

ADDED SECTIONS:
- AAIF Compliance Layer (MCP, Goose, AGENTS.md integration)
- Skills & MCPs Registry (always-use + optional lists)
- Agent Roles & Responsibilities (detailed function mapping)
- Process Failure Safeguards (environment validation, rollback points, type safety)
- Phase 3 Lessons Learned (concrete DOs/DON'Ts)

REMOVED SECTIONS:
- None (purely additive changes)

TEMPLATES REQUIRING UPDATES:
⚠ PENDING: .specify/templates/plan-template.md (add AAIF compliance checks)
⚠ PENDING: .specify/templates/spec-template.md (add Skills creation requirement)
⚠ PENDING: .specify/templates/tasks-template.md (add environment validation task type)
✅ UPDATED: AGENTS.md (created at root)
✅ UPDATED: CLAUDE.md (references @AGENTS.md)

FOLLOW-UP TODOs:
1. Create /ai-control/ directory with 8 governance files (CLAUDE.md, GEMINI.md, CODEX.md, SWARM.md, AGENTS.md, SKILLS.md, MCP.md, LOOP.md)
2. Generate agent workflow diagrams (Mermaid: hierarchy, flow, mindmap)
3. Create environment validation script (scripts/verify-env.sh)
4. Document Skills creation workflow
5. Set up MCP auto-discovery system
-->

# Evolution of Todo Constitution

## Project Overview

**Mission**: Master Spec-Driven Development & Cloud-Native AI through iterative evolution from a Python console app to a fully-featured, Kubernetes-deployed AI chatbot, demonstrating AAIF (Agentic AI Foundation) standards and enterprise-grade multi-agent orchestration.

**Constraint**: No manual code writing. All code must be generated via Claude Code from approved specifications following strict agent governance protocols.

**Governance Model**: AAIF-aligned (MCP + Goose + AGENTS.md), Linux Foundation-style neutrality, multi-agent orchestration with behavioral constitutions.

---

## Core Principles

### I. Spec-Driven Development (NON-NEGOTIABLE)

Every line of code must trace back to an approved specification. The workflow is immutable:

1. **Constitution** → Define WHY (principles, constraints, governance)
2. **Specify** → Define WHAT (requirements, journeys, acceptance criteria)
3. **Plan** → Define HOW (architecture, components, interfaces)
4. **Tasks** → Break into ATOMIC, testable work units
5. **Implement** → Generate code ONLY for approved tasks

**Violation Response**: If code is proposed without a referenced Task ID, HALT and request specification.

**Violation Detection System**:
- loop-controller agent MUST verify spec.md exists before allowing implementation
- Every code commit MUST reference Task ID in commit message
- qa-overseer agent rejects PRs without spec traceability

**Evidence Required**:
- All implementations MUST link to Task ID + Spec section
- Example: `[Task]: T-003 [From]: spec.md section 2.1, plan.md section 3.4`

### II. Iterative Evolution (The Brownfield Protocol)

Each phase builds on the previous. We evolve, not rewrite.

- **Phase I → II**: In-memory logic moves to `backend/app/services/`
- **Phase II → III**: REST API becomes MCP Tool provider
- **Phase III → IV**: App containerized, Helm charts created
- **Phase IV → V**: Monolith decoupled via Kafka/Dapr events

**Pre-Phase Checklist**:
- [ ] Backup `CLAUDE.md` and current specs
- [ ] Verify previous phase acceptance criteria pass (QA-verified, not self-assessed)
- [ ] Create migration spec before touching code
- [ ] Run environment validation script (`scripts/verify-env.sh`)
- [ ] Establish git rollback point (tag with tests passing)

### III. Test-First Mindset

While not enforcing strict TDD, every feature must have:

1. **Acceptance Criteria** defined in spec BEFORE implementation
2. **Verification Steps** documented for manual testing
3. **Automated Tests** where tooling permits (pytest, Jest, Playwright)

**"Complete" Definition**: ALL acceptance tests passing (green), not "code exists".

**Premature Victory Prevention**: No PHR may claim "Implementation Complete" or "Gold Master" without attached test output showing PASS results.

### IV. Smallest Viable Diff

- Implement ONLY what the task specifies
- No "while I'm here" refactoring
- No premature optimization
- No feature creep within phases

**Single Architecture Rule**: When choosing between architectures (A vs B), DELETE the rejected one immediately. No parallel implementations "just in case".

### V. Intelligence Capture (PHR, ADR, Skills)

Every significant interaction is recorded:

- **PHR (Prompt History Record)**: Created after EVERY implementation session
- **ADR (Architectural Decision Record)**: Created for decisions with long-term impact (framework choices, data models, API contracts)
- **Skills**: Created when logic repeats 3+ times or solves a reusable pattern

**Reusable Intelligence Mandate**:
- If a problem is solved more than twice, create a Skill
- If an SDK/tool is integrated, document in `specs/research/<sdk-name>-protocol.md`
- If an agent workflow proves effective, formalize in `.claude/skills/`

**Skill Creation Triggers**:
- ChatKit integration patterns
- OpenRouter fallback configuration
- SSE streaming debugging
- Environment validation workflows
- Type safety enforcement patterns

### VI. AAIF Standards & Interoperability (NEW)

This project aligns with Agentic AI Foundation (AAIF) standards:

**MCP (Model Context Protocol)**:
- All tool integrations MUST use MCP servers (not direct API calls)
- Expose backend services as MCP tools for multi-agent access
- MCP servers are stateless, no business logic embedded

**AGENTS.md**:
- Root AGENTS.md defines vendor-neutral project instructions
- CLAUDE.md references `@AGENTS.md` (thin wrapper pattern)
- GEMINI.md, CODEX.md, QWEN.md all reference `@AGENTS.md`
- Spec-Kit workflow MUST be documented in AGENTS.md

**Goose Framework**:
- Use Goose as reference "agent OS" for multi-agent orchestration
- Goose recipes define subagent behaviors and coordination patterns
- Community governance ensures long-term stability

**Interoperability Commitment**:
- Tools exposed via MCP work with Claude Code, Gemini CLI, Goose, OpenAI Agents SDK
- No vendor lock-in; agents are swappable at UX layer
- Shared plumbing (MCP + AGENTS.md) across all AI tools

### VII. Mandatory Clarification Gate (Phase 3 Learning)

**Rule**: Before ANY implementation involving unknowns, run `/sp.clarify`.

**What Constitutes an "Unknown"**:
- Undocumented SDK behavior (e.g., ChatKit session creation protocol)
- New technology integration (e.g., OpenRouter, Kubernetes networking)
- Ambiguous requirements (e.g., "make it faster" without metrics)
- Tech stack deviations (e.g., swapping OpenAI Agents SDK for OpenRouter)

**Enforcement**:
- `/sp.implement` command MUST check for corresponding clarification PHR
- If missing, BLOCK execution and prompt: "Run /sp.clarify first"
- loop-controller agent validates clarification before green-lighting implementation

**Example Workflow**:
```
User: "We're implementing ChatKit integration"
Claude: Running /sp.clarify...

Q1: What is the exact ChatKit session creation request format?
Q2: What SSE event format does ChatKit expect?
Q3: How does ChatKit handle authentication (cookies vs headers)?
Q4: What is ChatKit's error response format?

[Research answers in specs/research/chatkit-protocol.md]
[THEN proceed to implementation]
```

### VIII. Process Failure Prevention (Phase 3 Retrospective)

Based on 34-day Phase 3 overrun analysis, these safeguards are MANDATORY:

**Environment Validation**:
- Day 1 of each phase: Create `scripts/verify-env.sh`
- Check ALL required env vars before ANY development session
- Validate: no extra characters (e.g., `0.0.0.0.1`), no concatenation, proper formatting

**Rollback Points**:
- Git tag before every major change: `git tag -a "phase<N>-layer<M>-complete" -m "..."`
- Tag ONLY when tests are passing
- Always have a "last known good" state to return to

**Type Safety Enforcement**:
- Pydantic strict mode (`model_config = ConfigDict(strict=True)`)
- TypeScript strict mode (`"strict": true` in tsconfig.json)
- No type coercion; reject at compile/runtime early

**Comprehensive Logging**:
- Log EVERY external interaction (API calls, SDK calls, tool invocations)
- Format: `logger.info(f"<Tool> request: {details}")` BEFORE call
- Format: `logger.info(f"<Tool> response: {status}, {summary}")` AFTER call

**Cache Management**:
- Clear Next.js `.next` folder before reporting "build broken"
- Document cache-clearing in development workflows
- Automate in `package.json` scripts where possible

**Dead Code Deletion**:
- When choosing Architecture A over B, delete B immediately
- No orphan components, endpoints, or schemas
- Commit message: `chore: remove <rejected-option> (ADR-<N>)`

---

## Technology Stack (Immutable)

### Phase I: Console App
| Layer | Technology |
|-------|------------|
| Runtime | Python 3.13+ |
| Package Manager | UV |
| AI Tooling | Claude Code, Spec-Kit Plus |

### Phase II: Full-Stack Web
| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16+ (App Router) |
| Backend | Python FastAPI |
| ORM | SQLModel |
| Database | Neon Serverless PostgreSQL |
| Authentication | Better Auth (JWT) |

### Phase III: AI Chatbot
| Layer | Technology |
|-------|------------|
| Chat UI | OpenAI ChatKit |
| AI Framework | OpenAI Agents SDK / OpenRouter (ADR-013) |
| MCP Server | Official MCP SDK (Python) / Custom ChatKit (ADR-014) |
| State | Stateless API + DB persistence |

### Phase IV: Local Kubernetes
| Layer | Technology |
|-------|------------|
| Containers | Docker (Docker Desktop) |
| Orchestration | Kubernetes (Minikube) |
| Package Manager | Helm Charts |
| AIOps | kubectl-ai, Kagent, Gordon (Docker AI) |

### Phase V: Cloud Deployment
| Layer | Technology |
|-------|------------|
| Cloud Platform | DigitalOcean DOKS / Azure AKS / GCP GKE |
| Event Streaming | Kafka (Redpanda/Strimzi) |
| Distributed Runtime | Dapr |
| CI/CD | GitHub Actions |

---

## AAIF Compliance Layer

### MCP Servers (Active)
| MCP | Purpose | Always Use? |
|-----|---------|-------------|
| filesystem | File operations | ✅ YES |
| github | Issue/PR management | ⚠️ HIGH PRIORITY |
| postgres | Neon database queries | ✅ YES |
| context7 | Documentation lookup | ✅ YES |
| code-search | Codebase exploration | ✅ YES |
| playwright | UI testing | ⚠️ Development phase |
| vercel | Deployment management | ⚠️ Deployment phase |
| docker | Container operations | ⚠️ Phase IV+ |

### Skills Registry (Reusable Intelligence)

**Always Use (A-Priority)**:
- `building-mcp-servers` - MCP construction patterns
- `scaffolding-openai-agents` - Agent SDK integration
- `streaming-llm-responses` - SSE/streaming patterns
- `building-chat-interfaces` - ChatKit/chat UI patterns
- `deployment-preflight-check` - Pre-deployment validation
- `security-scan` - Static security analysis
- `env-validator` - Environment variable validation
- `spec-driven-development` - SDD workflow enforcement

**Situational Use (B-Priority)**:
- `skill-creator` - When creating new reusable patterns
- `systematic-debugging` - When encountering complex bugs
- `configuring-better-auth` - Auth setup/modifications
- `scaffolding-fastapi-dapr` - Backend microservice setup
- `deploying-cloud-k8s` - Phase V deployment
- `containerizing-applications` - Phase IV Docker/K8s

### AGENTS.md Integration

**File Structure**:
```
/
├── AGENTS.md (vendor-neutral canonical instructions)
├── CLAUDE.md (@AGENTS.md + Claude-specific notes)
├── ai-control/ (behavioral constitutions)
│   ├── CLAUDE.md (execution law)
│   ├── GEMINI.md (research role)
│   ├── CODEX.md (code generation)
│   ├── SWARM.md (parallel execution)
│   ├── REGISTRY.md (agent governance registry)
│   ├── SKILLS.md (reusable intelligence)
│   ├── MCP.md (external integrations)
│   └── LOOP.md (spec-driven heartbeat)
```

**AGENTS.md Content Requirements**:
- Setup commands (install deps, start servers)
- Testing (how to run tests, linters, type-checkers)
- Project structure (monorepo layout, phase folders)
- Code style (Python strict types, TypeScript strict mode)
- Git workflow (branch naming, PR rules, /sp.git.commit_pr)
- Boundaries (don't modify infra/, k8s/ without spec)
- Spec-Kit workflow (Specify → Plan → Tasks → Implement)
- Tools specification (which MCPs/Skills for what tasks)

---

## Agent Orchestration

### Command Team (Always Active)

| Agent | Role | Model | Responsibilities |
|-------|------|-------|------------------|
| **imperator** | Supreme Commander | Opus | Strategic decisions, phase transitions, agent delegation, bottleneck resolution, scope protection |
| **lead-architect** | Strategy & Constitution | Opus | Constitution updates, architectural vision, principle enforcement, phase planning |
| **loop-controller** | Workflow Enforcer | Opus | SPEC → IMPLEMENT → TEST → QA cycle validation, prevents premature coding, blocks violations |
| **qa-overseer** | Quality Guardian | Opus | Acceptance criteria validation, test verification, "complete" certification, prevents premature victory |
| **path-warden** | Directory Guardian | Sonnet | File placement validation, structure integrity, prevents misplaced files |

**Command Team Workflow**:
1. User request → imperator evaluates against master-plan.md
2. imperator delegates to lead-architect (strategy) or loop-controller (workflow check)
3. loop-controller verifies spec exists before allowing implementation
4. qa-overseer certifies completion only when tests pass
5. path-warden validates file placements after creation/modification

### Build Team (Task-Specific)

| Agent | Role | Model | Responsibilities |
|-------|------|-------|------------------|
| **spec-architect** | Specification Writer | Opus | Writing/refining specs/features/*.md, clarification questions, ADR creation |
| **modular-ai-architect** | AI System Designer | Opus | Agent architectures, RAG systems, LLM integration patterns, MCP server design |
| **backend-builder** | Backend Engineer | Opus | Python, FastAPI, SQLModel, MCP implementation, database migrations |
| **ux-frontend-developer** | Frontend Engineer | Sonnet | Next.js, React, Tailwind, Better Auth, ChatKit UI, accessibility |
| **devops-rag-engineer** | DevOps & Infrastructure | Sonnet | Docker, K8s, Helm, Kafka, Dapr, CI/CD, environment setup |
| **docusaurus-librarian** | Documentation Specialist | Sonnet | ADR creation, PHR archival, /docs maintenance, knowledge preservation |

### Support Team (On-Demand)

| Agent | Role | Model | When to Use |
|-------|------|-------|-------------|
| **content-builder** | Technical Writer | Sonnet | MDX documentation, tutorials, API references |
| **enterprise-grade-validator** | Production Auditor | Sonnet | Pre-deployment security/reliability audits |
| **agent-specialization-architect** | Agent Designer | Sonnet | Creating new specialized agents when capability gaps identified |

### Agent Roles Answer Matrix

**Human/User Authority**: You (the user) are the ultimate authority. All agents serve you.

**After User, Who Leads?**: imperator (Opus) - The strategic orchestrator with delegation authority.

**Agent Responsibilities**:

| Responsibility | Primary Agent | Backup Agent |
|----------------|---------------|--------------|
| Create Constitution | lead-architect | imperator |
| Create Specs | spec-architect | modular-ai-architect (for AI features) |
| Create Plan | spec-architect | backend-builder / ux-frontend-developer (domain-specific) |
| Create and Break Tasks | spec-architect (via /sp.tasks) | task-orchestrator |
| Implement | backend-builder (backend), ux-frontend-developer (frontend) | devops-rag-engineer (infra) |
| Orchestrate | imperator | lead-architect |
| Engineer | backend-builder, ux-frontend-developer, devops-rag-engineer | modular-ai-architect (AI systems) |
| Architect | lead-architect (strategic), modular-ai-architect (AI) | spec-architect (feature-level) |
| Analyze | qa-overseer (quality), enterprise-grade-validator (production) | general-purpose |
| Debug | backend-builder, ux-frontend-developer (use systematic-debugging skill) | devops-rag-engineer |
| Remove Duplicate/Unnecessary | path-warden (files), backend-builder (code) | qa-overseer (review) |
| Security | enterprise-grade-validator (use security-scan skill) | backend-builder |
| Cleanness | path-warden (structure), backend-builder (code quality) | ux-frontend-developer |
| Performance | backend-builder (API), ux-frontend-developer (UI) | devops-rag-engineer (infra) |
| Requirements/Weakness/Loopholes | qa-overseer (testing), spec-architect (clarification) | imperator (strategic gaps) |
| Summary | docusaurus-librarian (PHR/ADR), lead-architect (retrospectives) | general-purpose |
| Explain | docusaurus-librarian (docs), content-builder (tutorials) | general-purpose |
| Solve | backend-builder, ux-frontend-developer (domain-specific) | general-purpose |
| Ask When/What/Why/Where/Which/How | spec-architect (via /sp.clarify) | imperator (strategic questions) |
| Feedbacks | qa-overseer (quality feedback), lead-architect (process feedback) | user (ultimate feedback) |
| Customer Support | docusaurus-librarian (docs), ux-frontend-developer (UX issues) | general-purpose |
| Inquirer | spec-architect (/sp.clarify), imperator (strategic probing) | general-purpose |
| Tests | qa-overseer (validation), backend-builder (pytest), ux-frontend-developer (Playwright) | enterprise-grade-validator |
| Review | qa-overseer (acceptance criteria), enterprise-grade-validator (production readiness) | lead-architect |
| CheckList | qa-overseer (use /sp.checklist), spec-architect | enterprise-grade-validator |
| PHR | docusaurus-librarian (archival), any agent (creation via /sp.phr) | general-purpose |
| ADR | docusaurus-librarian (use /sp.adr), lead-architect (strategic ADRs) | spec-architect |
| Approve | qa-overseer (quality gate), imperator (strategic decisions), **USER (ultimate approval)** | lead-architect |

---

## Feature Progression (Scope Boundaries)

### Basic Level (Phases I-III Core)
- [x] Add Task
- [x] Delete Task
- [x] Update Task
- [x] View Task List
- [x] Mark as Complete

### Intermediate Level (Phase V)
- [ ] Priorities (high/medium/low)
- [ ] Tags/Categories
- [ ] Search & Filter
- [ ] Sort Tasks

### Advanced Level (Phase V)
- [ ] Recurring Tasks
- [ ] Due Dates & Time Reminders

### Bonus Features
- [ ] Multi-language Support (Urdu)
- [ ] Voice Commands
- [ ] Reusable Intelligence (Subagents/Skills)
- [ ] Cloud-Native Blueprints

---

## API Design Principles

### REST Endpoints (Phase II+)
```
GET    /api/{user_id}/tasks           → List all tasks
POST   /api/{user_id}/tasks           → Create task
GET    /api/{user_id}/tasks/{id}      → Get task details
PUT    /api/{user_id}/tasks/{id}      → Update task
DELETE /api/{user_id}/tasks/{id}      → Delete task
PATCH  /api/{user_id}/tasks/{id}/complete → Toggle completion
```

### MCP Tools (Phase III+)
```
add_task(user_id, title, description?) → {task_id, status, title}
list_tasks(user_id, status?) → [{id, title, completed, ...}]
complete_task(user_id, task_id) → {task_id, status, title}
delete_task(user_id, task_id) → {task_id, status, title}
update_task(user_id, task_id, title?, description?) → {task_id, status, title}
```

### Chat Endpoint (Phase III+)
```
POST /api/{user_id}/chat
  Body: { conversation_id?, message }
  Response: { conversation_id, response, tool_calls[] }
```

---

## Security Principles

1. **No Hardcoded Secrets**: All credentials via `.env` files
2. **JWT Verification**: Backend validates Better Auth tokens
3. **User Isolation**: All queries scoped to authenticated `user_id`
4. **HTTPS Only**: Production endpoints must use TLS
5. **Environment Validation**: Run `scripts/verify-env.sh` before EVERY session
6. **Secret Management**: Never commit `.env`, use `.env.example` templates
7. **Security Scans**: Run security-scan skill before deployment

---

## Monorepo Structure

```
Evolution-of-Todo/
├── .specify/                    # Spec-Kit Plus configuration
│   ├── memory/
│   │   └── constitution.md     # THIS FILE
│   ├── templates/              # PHR, ADR, Spec, Plan, Tasks templates
│   └── scripts/
│       └── bash/
│           ├── create-phr.sh
│           └── verify-env.sh (NEW)
├── ai-control/ (NEW)            # Agent behavioral constitutions
│   ├── CLAUDE.md
│   ├── GEMINI.md
│   ├── CODEX.md
│   ├── SWARM.md
│   ├── REGISTRY.md
│   ├── SKILLS.md
│   ├── MCP.md
│   └── LOOP.md
├── specs/                       # Specifications
│   ├── overview.md
│   ├── architecture.md
│   ├── features/               # Feature specs
│   ├── api/                    # API specs
│   ├── database/               # Schema specs
│   └── research/ (NEW)          # SDK/tool research docs
│       └── chatkit-protocol.md (example)
├── history/                     # Records
│   ├── prompts/                # PHR files
│   │   ├── constitution/
│   │   ├── general/
│   │   └── <feature-name>/
│   └── adr/                    # ADR files
├── phase-1-console/            # Phase I: Console App
├── phase-2-web/                # Phase II: Full-Stack Web
│   ├── frontend/
│   └── backend/
├── phase-3-chatbot/            # Phase III: AI Chatbot
│   ├── frontend/
│   ├── backend/
│   └── specs/
├── phase-4-k8s/ (future)       # Phase IV: Kubernetes
├── phase-5-cloud/ (future)     # Phase V: Cloud Deployment
├── scripts/ (NEW)
│   └── verify-env.sh
├── AGENTS.md (NEW)             # Vendor-neutral agent instructions
├── CLAUDE.md                   # @AGENTS.md + Claude-specific
├── PHASE_3_RETROSPECTIVE.md    # Lessons learned
└── README.md
```

---

## Quality Gates

### Per-Phase Acceptance
| Phase | Gate |
|-------|------|
| I | All 5 basic features work in console |
| II | REST API returns correct data; Auth works |
| III | Chatbot executes MCP tools; State persists; ALL E2E tests passing |
| IV | Helm charts deploy successfully on Minikube; health checks pass |
| V | Full system runs on DOKS with Kafka/Dapr; production monitoring active |

### Per-Feature Acceptance
- [ ] Spec exists in `specs/features/`
- [ ] Plan exists with architectural decisions
- [ ] Tasks exist with atomic steps
- [ ] Implementation matches spec exactly
- [ ] Manual verification steps pass
- [ ] **ALL automated tests passing (green)** ← Phase 3 addition
- [ ] Skills created for reusable patterns ← Phase 3 addition
- [ ] ADRs written for architectural decisions ← Phase 3 addition
- [ ] Environment validation passing ← Phase 3 addition
- [ ] No dead code remaining ← Phase 3 addition

### "Complete" Definition (Phase 3 Learning)

A task/feature/phase is "complete" ONLY when:
1. All acceptance criteria met
2. All automated tests passing (green output attached to PHR)
3. qa-overseer certification obtained
4. No blocker bugs remaining
5. Documentation updated (README, specs, ADRs)

"Complete" does NOT mean:
- ❌ "Code exists"
- ❌ "Mostly working"
- ❌ "85% done"
- ❌ "Manual testing looks good"

---

## Process Failure Safeguards (Phase 3 Learnings)

### DOs (Mandatory Practices)

✅ **DO** write specs for emergency pivots
- Example: When Gemini failed, MUST create `specs/features/llm-provider-fallback.md`

✅ **DO** create research documents for undocumented SDKs
- Example: `specs/research/chatkit-protocol.md` before ChatKit integration

✅ **DO** test in isolation before integration
- Example: Test ChatKit session creation with `curl` BEFORE backend integration

✅ **DO** maintain working baselines
- Git tag after each layer: `git tag -a "phase3-layer2-complete" -m "Layer 2: Backend complete, tests passing"`

✅ **DO** delete dead code immediately
- When switching architectures, delete rejected option in same commit

✅ **DO** use `/sp.clarify` when encountering unknowns
- Don't guess, research, and document

✅ **DO** create Skills for repeatable patterns
- If solved same problem 2+ times, create Skill

✅ **DO** enforce strict types from Day 1
- Pydantic strict mode, TypeScript strict mode

✅ **DO** log every external interaction
- API calls, SDK calls, tool invocations with request/response details

✅ **DO** run environment validation before every session
- `./scripts/verify-env.sh` mandatory

✅ **DO** validate working directory before ANY operation
- Required directory: `E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo`
- If wrong directory detected: STOP immediately (exit code 3)
- If specs/artifacts created in wrong location: move to correct directory, delete wrong folder, validate deletion
- See AGENTS.md "Directory Safety Rule" for full protocol

### DON'Ts (Forbidden Practices)

❌ **DON'T** declare "implementation complete" without passing tests
- "Complete" = "All tests green" (see Quality Gates)

❌ **DON'T** skip clarification when encountering unknowns
- SDK mysteries are blockers, not optional research

❌ **DON'T** maintain parallel architectures "just in case"
- Single architecture rule (Principle IV)

❌ **DON'T** debug production while development is broken
- Fix local first, then deploy

❌ **DON'T** create test files that never pass
- Tests MUST pass before claiming completion

❌ **DON'T** assume bytes are strings (or vice versa)
- Always explicit `.decode()` when needed

❌ **DON'T** paste environment variables without validation
- Run `scripts/verify-env.sh` immediately

❌ **DON'T** trust cache (Next.js `.next` folder)
- Clear cache when debugging: `rm -rf .next`

❌ **DON'T** write ADRs "later"
- Write ADR when making decision, not retroactively

❌ **DON'T** use "Gold Master" before qa-overseer validation
- Only qa-overseer can certify completion

---

## Governance

1. **Constitution Supremacy**: This document supersedes all other practices
2. **Amendments**: Require documented rationale, PHR creation, and explicit user approval
3. **Spec Hierarchy**: Constitution > AGENTS.md > Specify > Plan > Tasks
4. **Backtracking**: Moving to a previous phase requires a new spec iteration
5. **Version Control**: Semantic versioning (MAJOR.MINOR.PATCH) enforced
6. **Agent Authority**: imperator delegates, user approves; no agent acts unilaterally
7. **Compliance Review**: lead-architect reviews constitution alignment monthly
8. **AAIF Alignment**: Maintain compatibility with MCP, Goose, AGENTS.md standards

**Amendment Procedure**:
1. Propose change with rationale (via lead-architect or user)
2. Document in PHR (use /sp.phr)
3. Update constitution version (semantic versioning)
4. Propagate changes to dependent templates
5. Create Sync Impact Report (HTML comment at file top)
6. User approval required for MAJOR/MINOR changes
7. Commit with message: `docs: amend constitution to vX.Y.Z (change summary)`

---

## Deadlines

| Phase | Due Date | Status |
|-------|----------|--------|
| Phase I | Dec 7, 2025 | ✅ COMPLETE |
| Phase II | Dec 14, 2025 | ✅ COMPLETE |
| Phase III | Dec 21, 2025 | ⚠️ PAUSED (31% verified) |
| Phase IV | Jan 4, 2026 | PENDING |
| Phase V | Jan 18, 2026 | PENDING |

**Timeline Estimation Policy (Phase 3 Learning)**:
- Constitution estimate = X days
- Realistic estimate = 2X days (unknown unknowns buffer)
- Phase 4 estimate: 14 days (constitution) → 28-30 days (realistic)

---

## Phase Completion Log

### Phase I: Console App ✅
- **Completed**: Dec 7, 2025
- **Deliverables**: Python CLI with in-memory task storage
- **Location**: `phase-1-console/`

### Phase II: Full-Stack Web ✅
- **Completed**: Dec 31, 2025
- **Deliverables**:
  - FastAPI backend with JWT auth (`phase-2-web/backend/`)
  - Next.js 15 frontend with App Router (`phase-2-web/frontend/`)
  - SQLite database (dev), PostgreSQL ready (prod)
  - 7 User Stories implemented (Register, Login, Add/View/Update/Delete/Complete Tasks)
  - Toast notifications, loading states, error boundaries
- **ADRs**: ADR-004 to ADR-007
- **Tasks**: 80 tasks, all complete

### Phase III: AI Chatbot ⚠️
- **Status**: PAUSED - Partially Complete (31% QA-verified)
- **Timeline**: 34-day overrun (Dec 21 → Jan 24, 2026)
- **Deliverables Completed**:
  - ChatKit UI (202 lines ChatKit.tsx, 35 lines page.tsx)
  - FastAPI backend with OpenRouter (not Agents SDK)
  - Custom ChatKit MCP server (not Official MCP SDK)
  - Database migrations (conversations, priority/tags)
- **Deliverables Missing**:
  - `specs/api/mcp-tools.md` (specification)
  - ADR-013 (OpenRouter migration)
  - README.md update (still shows Phase 2)
  - E2E tests passing (0/5 functional tests green)
- **Blockers**: HTTP 500 session creation error
- **Root Causes**: Skipped `/sp.clarify`, no environment validation, premature "complete" claims
- **Lessons Learned**: See PHASE_3_RETROSPECTIVE.md and Process Failure Safeguards section
- **Skills Created**: ZERO (should have created 3: chatkit-integration, openrouter-provider, sse-stream-debugger)
- **Path Forward**: Option A (fix HTTP 500 blocker) or Option B (freeze and document)

### Phase IV: Local Kubernetes (NEXT)
- **Estimated Timeline**: 28-30 days (NOT 14 days)
- **Prerequisites**:
  - Phase 3 completion OR documented technical debt freeze
  - Environment validation script created
  - Skills created for Phase 3 learnings
  - Process improvements from retrospective implemented
  - `/sp.clarify` workflow enforced
  - Rollback points strategy defined

---

**Version**: 2.0.0
**Ratified**: 2025-12-27
**Last Amended**: 2026-01-25
**Next Review**: Before Phase 4 kickoff (Q1 2026)
