# AGENTS.md

## Purpose

This project uses **Spec-Driven Development (SDD)** with **Spec-Kit Plus** and follows **AAIF (Agentic AI Foundation)** standards. All AI agents (Claude Code, Gemini CLI, Codex, Goose, etc.) MUST follow the **Spec-Kit lifecycle**:

> **Constitution → Specify → Plan → Tasks → Implement**

This prevents "vibe coding," ensures alignment across agents, and guarantees that every implementation step maps back to an explicit requirement.

---

## How Agents Must Work

Every agent in this project MUST obey these rules:

1. **Never generate code without a referenced Task ID.**
2. **Never modify architecture without updating `plan.md`.**
3. **Never propose features without updating `spec.md` (WHAT).**
4. **Never change principles without updating `constitution.md` (WHY).**
5. **Every code file must contain a comment linking it to the Task and Spec sections.**

If an agent cannot find the required spec, it must **stop and request it**, not improvise.

---

## Spec-Kit Plus Workflow (Source of Truth)

### 1. Constitution (WHY - Principles & Constraints)

**File**: `.specify/memory/constitution.md`

Defines the project's non-negotiables: architecture values, security rules, tech stack constraints, performance expectations, and patterns allowed.

Agents must check this before proposing solutions.

**Current Version**: 2.1.0

**Key Principles**:
- Spec-Driven Development (NON-NEGOTIABLE)
- Iterative Evolution (Brownfield Protocol)
- Test-First Mindset
- Smallest Viable Diff
- Intelligence Capture (PHR, ADR, Skills)
- AAIF Standards & Interoperability (MCP, AGENTS.md, Goose)
- Mandatory Clarification Gate (`/sp.clarify`)
- Process Failure Prevention (Phase 3 retrospective learnings)

---

### 2. Specify (WHAT - Requirements, Journeys & Acceptance Criteria)

**File**: `specs/<feature>/spec.md`

Contains:
- User journeys
- Requirements
- Acceptance criteria
- Domain rules
- Business constraints

Agents must not infer missing requirements - they must request clarification via `/sp.clarify` or propose specification updates.

**Command**: `/sp.specify`

---

### 3. Plan (HOW - Architecture, Components, Interfaces)

**File**: `specs/<feature>/plan.md`

Includes:
- Component breakdown
- APIs & schema diagrams
- Service boundaries
- System responsibilities
- High-level sequencing

All architectural output MUST be generated from the Specify file.

**Command**: `/sp.plan`

---

### 4. Tasks (BREAKDOWN - Atomic, Testable Work Units)

**File**: `specs/<feature>/tasks.md`

Each Task must contain:
- Task ID
- Clear description
- Preconditions
- Expected outputs
- Artifacts to modify
- Links back to Specify + Plan sections

Agents **implement only what these tasks define**.

**Command**: `/sp.tasks`

---

### 5. Implement (CODE - Write Only What the Tasks Authorize)

Agents now write code, but must:
- Reference Task IDs
- Follow the Plan exactly
- Not invent new features or flows
- Stop and request clarification if anything is underspecified

> The golden rule: **No task = No code.**

**Command**: `/sp.implement`

---

## Setup Commands

### Prerequisites

```bash
# Install UV (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (backend)
cd phase-3-chatbot/backend
uv sync

# Install dependencies (frontend)
cd phase-3-chatbot/frontend
pnpm install
```

### Development Servers

```bash
# Backend (FastAPI)
cd phase-3-chatbot/backend
uv run uvicorn app.main:app --reload --port 8000

# Frontend (Next.js)
cd phase-3-chatbot/frontend
pnpm dev
```

### Testing

```bash
# Backend tests (pytest)
cd phase-3-chatbot/backend
uv run pytest

# Frontend tests (Playwright)
cd phase-3-chatbot/frontend
pnpm test

# Linting
cd phase-3-chatbot/backend
uv run ruff check .

cd phase-3-chatbot/frontend
pnpm lint
```

### Environment Validation

```bash
# MANDATORY before every development session
./scripts/verify-env.sh
```

---

## Project Structure

```
Evolution-of-Todo/
├── .specify/                    # Spec-Kit Plus configuration
│   ├── memory/
│   │   └── constitution.md     # Project principles and governance
│   ├── templates/              # PHR, ADR, Spec, Plan, Tasks templates
│   └── scripts/
│       └── bash/
│           ├── create-phr.sh
│           └── verify-env.sh
├── ai-control/                  # Agent behavioral constitutions
│   ├── CLAUDE.md               # Claude execution law
│   ├── GEMINI.md               # Gemini research role
│   ├── CODEX.md                # Codex code generation
│   ├── SWARM.md                # Swarm parallel execution
│   ├── REGISTRY.md             # Agent governance registry
│   ├── SKILLS.md               # Reusable intelligence
│   ├── MCP.md                  # External integrations
│   └── LOOP.md                 # Spec-driven heartbeat
├── specs/                       # Specifications
│   ├── overview.md
│   ├── architecture.md
│   ├── features/               # Feature specs
│   ├── api/                    # API specs
│   ├── database/               # Schema specs
│   └── research/               # SDK/tool research docs
├── history/                     # Records
│   ├── prompts/                # PHR files
│   └── adr/                    # ADR files
├── phase-1-console/            # Phase I: Console App ✅
├── phase-2-web/                # Phase II: Full-Stack Web ✅
├── phase-3-chatbot/            # Phase III: AI Chatbot ⚠️
├── phase-4-k8s/ (future)       # Phase IV: Kubernetes
├── phase-5-cloud/ (future)     # Phase V: Cloud Deployment
├── scripts/
│   └── verify-env.sh           # Environment validation
├── AGENTS.md                   # THIS FILE
├── CLAUDE.md                   # @AGENTS.md + Claude-specific
└── README.md
```

---

## Code Style

### Backend (Python)

- **Version**: Python 3.13+
- **Type Hints**: Required (strict mode)
- **Linting**: Ruff
- **Formatting**: Black (via Ruff)
- **Testing**: pytest
- **Async**: Use async/await for I/O operations
- **Pydantic**: Strict mode (`model_config = ConfigDict(strict=True)`)

```python
# Example
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class Task(BaseModel):
    model_config = ConfigDict(strict=True)

    id: UUID  # Not str
    user_id: UUID  # Not str
    title: str
    completed: bool
```

### Frontend (TypeScript/React)

- **Version**: Next.js 16+ (App Router)
- **Type Safety**: TypeScript strict mode
- **Styling**: Tailwind CSS
- **Components**: Functional components with hooks
- **Linting**: ESLint
- **Formatting**: Prettier
- **Testing**: Playwright

```typescript
// tsconfig.json must have:
{
  "compilerOptions": {
    "strict": true,
    "strictNullChecks": true,
    "noImplicitAny": true
  }
}
```

---

## Git Workflow

### Branch Naming

- `00X-phase<N>-<description>` (e.g., `004-phase3-chatbot`)
- Feature branches within phase

### Commit Messages

**Format**: `<type>(<scope>): <subject>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `chore`: Maintenance tasks
- `refactor`: Code refactoring (no behavior change)
- `test`: Adding/updating tests

**Task Reference**: Every commit MUST reference Task ID in body

```bash
git commit -m "feat(chatkit): implement session creation endpoint

[Task]: T-003
[From]: spec.md section 2.1, plan.md section 3.4

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Pull Requests

Use `/sp.git.commit_pr` command to create PRs

**Requirements**:
- All tests passing
- qa-overseer certification
- ADR created for architectural decisions
- No dead code
- README updated

---

## Spec-Kit Plus Commands (Critical Workflow)

### `/sp.constitution`
Create or update the project constitution from interactive or provided principle inputs.

**When to Use**: Changing project principles, governance, or tech stack constraints.

---

### `/sp.specify`
Create or update the feature specification from a natural language feature description.

**When to Use**: BEFORE starting ANY new feature or modification.

---

### `/sp.clarify`
Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions.

**When to Use**:
- MANDATORY for unknowns (undocumented SDKs, new tech, ambiguous requirements)
- Before implementing ChatKit, OpenRouter, Kubernetes, or any new technology
- When encountering "SDK mysteries" or configuration unknowns

**CRITICAL**: Skipping this command caused 34-day Phase 3 overrun. NEVER skip.

---

### `/sp.plan`
Execute the implementation planning workflow using the plan template to generate design artifacts.

**When to Use**: After `/sp.specify` and `/sp.clarify` are complete.

---

### `/sp.tasks`
Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.

**When to Use**: After `/sp.plan` is complete.

---

### `/sp.implement`
Execute the implementation plan by processing and executing all tasks defined in tasks.md.

**When to Use**: ONLY after `/sp.tasks` is complete.

**Prerequisite Check**: loop-controller agent verifies spec.md exists. If missing, BLOCK and request specification.

---

### `/sp.git.commit_pr`
An autonomous Git agent that intelligently executes git workflows to commit the work and create PR.

**When to Use**: After implementation is COMPLETE (all tests passing, qa-overseer certified).

---

### `/sp.adr`
Review planning artifacts for architecturally significant decisions and create ADRs.

**When to Use**: After making architectural decisions (tech stack changes, framework choices, API contracts).

---

### `/sp.phr`
Record an AI exchange as a Prompt History Record (PHR) for learning and traceability.

**When to Use**: After EVERY implementation session (automatic).

---

### `/sp.checklist`
Generate a custom checklist for the current feature based on user requirements.

**When to Use**: Before claiming "implementation complete".

---

### `/sp.analyze`
Perform a non-destructive cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md.

**When to Use**: After task generation, before implementation begins.

---

### `/sp.taskstoissues`
Convert existing tasks into actionable, dependency-ordered GitHub issues for the feature.

**When to Use**: For project management tracking (optional but recommended).

---

## Agent Behavior Rules

### Mandatory Practices (DOs)

✅ **DO** write specs for emergency pivots
- Example: When Gemini failed, create `specs/features/llm-provider-fallback.md`

✅ **DO** create research documents for undocumented SDKs
- Example: `specs/research/chatkit-protocol.md` before ChatKit integration

✅ **DO** test in isolation before integration
- Example: Test ChatKit session creation with `curl` BEFORE backend integration

✅ **DO** maintain working baselines
- Git tag after each layer: `git tag -a "phase3-layer2-complete" -m "..."`

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

### Forbidden Practices (DON'Ts)

❌ **DON'T** declare "implementation complete" without passing tests
- "Complete" = "All tests green"

❌ **DON'T** skip clarification when encountering unknowns
- SDK mysteries are blockers, not optional research

❌ **DON'T** maintain parallel architectures "just in case"
- Single architecture rule

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

## Boundaries / Safety

Agents MUST NOT:

- Generate missing requirements (use `/sp.clarify` instead)
- Create tasks on their own (use `/sp.tasks`)
- Alter stack choices without justification (create ADR)
- Add endpoints, fields, or flows that aren't in the spec
- Ignore acceptance criteria
- Produce "creative" implementations that violate the plan
- Modify `constitution.md` without user approval
- Touch `.specify/` directory without explicit instruction
- Modify `ai-control/` directory without explicit instruction
- **Work in incorrect directory** (see Directory Safety Rule below)

### Phase Execution Gate (MANDATORY)

**Rule**: Phase transitions require EXPLICIT user approval. No agent may auto-execute the next phase.

**Operational Workflow**:

1. **Phase Completion**:
   - Complete all tasks for current phase
   - Mark all tasks as [X] in tasks.md
   - Run acceptance tests
   - Verify exit codes (0 = success)

2. **STOP and Report**:
   - Display: "Phase N Complete"
   - Show completion summary:
     ```
     Phase N: [Phase Name]
     Status: COMPLETE
     Tasks: [X/X completed]
     Acceptance Criteria: [X/X passing]
     Warnings: [list any issues]

     OPTIONS:
     A. Proceed to Phase N+1
     B. Pause and review

     What would you like to do?
     ```

3. **WAIT for User Input**:
   - DO NOT proceed until user responds
   - Valid proceed signals: "proceed", "A", "next", "continue", "yes"
   - Valid pause signals: "pause", "B", "review", "stop", "no"

4. **Execute User Decision**:
   - If proceed: Begin Phase N+1 workflow
   - If pause: End session, preserve state

**Example Violation**:
```
WRONG:
Phase 1 complete → Auto-start Phase 2

CORRECT:
Phase 1 complete → Report to user → Wait for approval → User says "proceed" → Start Phase 2
```

**Enforcement**: loop-controller validates phase transitions include user approval checkpoint.

---

### Specialized Agent Usage Enforcement (MANDATORY)

**Rule**: Domain-specific tasks MUST use appropriate specialized agents.

**Implementation Workflow**:

1. **Task Analysis**:
   - Identify task domain (backend, frontend, infra, etc.)
   - Match task to required specialist agent
   - Verify specialist agent available

2. **Delegation**:
   - Use Task tool to launch specialist agent
   - Provide complete context (spec, plan, tasks)
   - Specify expected deliverables

3. **Validation**:
   - Validator agent reviews output
   - Checks compliance with spec
   - Verifies code quality

4. **Certification**:
   - qa-overseer certifies if quality gate
   - User approves final deliverable

**Example Workflows**:

**Backend Implementation**:
```
loop-controller → backend-builder (implement) → qa-overseer (certify) → User (approve)
```

**File Creation**:
```
backend-builder (create file) → path-warden (verify placement) → loop-controller (validate)
```

**Architecture Decision**:
```
User (request) → lead-architect (design) → spec-architect (document) → User (approve)
```

**Enforcement**: If task executed without required specialist, loop-controller BLOCKS and requires review.

---

### Directory Safety Rule (MANDATORY)

**Working Directory Requirement**: ALL operations MUST be performed in:
```
E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo
```

**Validation Protocol**:
1. **Before ANY operation** (spec creation, file creation, task execution):
   - Verify current working directory matches the required path
   - If mismatch detected: STOP IMMEDIATELY (exit code 3)

2. **Error Response** (if wrong directory detected):
   ```
   ❌ WRONG DIRECTORY DETECTED

   Current:  [detected path]
   Required: E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo

   ACTION: Fix directory before proceeding.
   COMMAND: cd E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo

   [Exit code 3]
   ```

3. **Misplaced Files Recovery** (if specs/artifacts created in wrong location):
   - Detect misplaced files in parent directory (`E:\M.Y\GIAIC-Hackathons\`) or sibling directories
   - Move ALL project-related files to correct directory (`E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo\`)
   - Delete the wrong directory after successful move
   - Validate deletion completed successfully
   - Log recovery actions in PHR

4. **Phase Execution Integration**:
   - Validate directory BEFORE each phase starts
   - Re-validate directory after phase completion
   - If directory changed mid-phase: HALT, report violation
   - Phase transitions MUST occur in correct directory

5. **Integration Points**:
   - ALL automation scripts (`scripts/*.sh`, `scripts/*.py`) MUST include directory validation
   - Spec-Kit commands (`/sp.specify`, `/sp.plan`, `/sp.tasks`, `/sp.implement`) MUST validate directory first
   - File creation operations MUST verify correct directory before Write/Edit

**Exit Codes**:
- `0`: Success
- `1`: Warnings (non-critical)
- `2`: Environment validation failure
- `3`: Wrong directory detected
- `4`: (Reserved)
- `5`: Unauthorized phase progression (NEW)

If a conflict arises between spec files, the **Constitution > AGENTS.md > Specify > Plan > Tasks** hierarchy applies.

---

## AAIF Standards Compliance

This project follows Agentic AI Foundation (AAIF) standards:

### MCP (Model Context Protocol)

- All tool integrations use MCP servers (not direct API calls)
- Backend services exposed as MCP tools for multi-agent access
- MCP servers are stateless, no business logic embedded

**Active MCPs**:
- `filesystem` - File operations (always use)
- `github` - Issue/PR management (high priority)
- `postgres` - Neon database queries (always use)
- `context7` - Documentation lookup (always use)
- `code-search` - Codebase exploration (always use)
- `playwright` - UI testing (development phase)
- `vercel` - Deployment management (deployment phase)
- `docker` - Container operations (Phase IV+)

### AGENTS.md

- This file is the vendor-neutral canonical instructions
- CLAUDE.md references `@AGENTS.md` (thin wrapper pattern)
- GEMINI.md, CODEX.md, QWEN.md all reference `@AGENTS.md`
- Spec-Kit workflow documented here

### Goose Framework

- Use Goose as reference "agent OS" for multi-agent orchestration
- Goose recipes define subagent behaviors and coordination patterns
- Community governance ensures long-term stability

### Interoperability

- Tools exposed via MCP work with Claude Code, Gemini CLI, Goose, OpenAI Agents SDK
- No vendor lock-in; agents are swappable at UX layer
- Shared plumbing (MCP + AGENTS.md) across all AI tools

---

## Files Agents Should Read First

Before starting work, agents should read in this order:

1. **AGENTS.md** (this file) - Workflow and conventions
2. **.specify/memory/constitution.md** - Principles and constraints
3. **specs/<current-feature>/spec.md** - Requirements
4. **specs/<current-feature>/plan.md** - Architecture
5. **specs/<current-feature>/tasks.md** - Work breakdown
6. **PHASE_3_RETROSPECTIVE.md** - Lessons learned

---

## Developer-Agent Alignment

Humans and agents collaborate, but the **spec is the single source of truth**.

Before every session, agents should re-read:

1. `.specify/memory/constitution.md`
2. `specs/<current-feature>/spec.md`
3. `specs/<current-feature>/plan.md`
4. `specs/<current-feature>/tasks.md`

This ensures predictable, deterministic development.

---

## Current Feature Context

**Branch**: `004-phase3-chatbot`
**Phase**: Phase III - AI Chatbot (PAUSED at 31% completion)
**Status**: Blocked on HTTP 500 session creation error
**Spec**: `phase-3-chatbot/specs/phase-3-spec.md`
**Retrospective**: `PHASE_3_RETROSPECTIVE.md`

**Known Issues**:
- HTTP 500 session creation error (blocker)
- Missing `specs/api/mcp-tools.md`
- Missing ADR-013 (OpenRouter migration)
- Missing ADR-014 (Custom ChatKit server)
- README.md outdated (shows Phase 2)
- 0/5 E2E tests passing

**Next Steps**:
- Option A: Fix HTTP 500 blocker, complete Phase 3
- Option B: Freeze Phase 3, document technical debt, proceed to Phase 4

---

## Version History

**Version**: 1.1.0
**Created**: 2026-01-25
**Last Updated**: 2026-01-27
**Next Review**: Before Phase 4 kickoff

**Changelog**:
- 1.1.0 (2026-01-27): Added Phase Execution Gate, Specialized Agent Enforcement, Enhanced Directory Safety Rule, Exit Code 5
- 1.0.0 (2026-01-25): Initial release
