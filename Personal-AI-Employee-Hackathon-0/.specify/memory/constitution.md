<!--
  SYNC IMPACT REPORT
  ==================
  Version change: 0.0.0 (template) -> 1.0.0 (initial ratification)
  Bump rationale: MAJOR - first concrete constitution replacing template

  Modified principles: N/A (all new)
  Added sections:
    - 10 Core Principles (I through X)
    - Tech Stack Constraints
    - Agent Governance & Enforcement Loops
    - Development Workflow
    - Governance (amendment procedure, versioning, compliance)

  Removed sections:
    - All template placeholders replaced

  Templates requiring updates:
    - .specify/templates/plan-template.md: ✅ Compatible (Constitution Check section aligns)
    - .specify/templates/spec-template.md: ✅ Compatible (User Stories + Requirements align)
    - .specify/templates/tasks-template.md: ✅ Compatible (Phase-gated structure aligns)
    - .specify/templates/phr-template.prompt.md: ✅ Compatible (no changes needed)

  Follow-up TODOs:
    - DONE(AI_CONTROL_FILES): ✅ Created ai-control/ with AGENTS.md, LOOP.md, SWARM.md, MCP.md, SKILLS.md, HUMAN-TASKS.md (2026-02-16)
    - TODO(GMAIL_OAUTH): Human MUST set up Gmail API OAuth credentials manually
    - TODO(WHATSAPP_SESSION): Human MUST authenticate WhatsApp Web session manually
    - TODO(OBSIDIAN_VAULT): Human MUST create Obsidian vault and folder structure manually
    - TODO(NEON_DB): Human MUST provision Neon PostgreSQL and provide connection string
    - TODO(ODOO_INSTALL): Human MUST install Odoo Community Edition locally (Gold tier)
    - TODO(MCP_FIX): Human MUST fix broken MCPs: Neon, gemini-cli, git, n8n-local, codex-cli
    - TODO(MCP_ADD): Human MUST add Gmail MCP, WhatsApp MCP, Obsidian MCP configs
    - TODO(ORACLE_VM): Human MUST provision Oracle Cloud VM for Platinum tier
-->

# H0: Personal AI Employee Constitution

## Core Principles

### I. Spec-Driven Development (NON-NEGOTIABLE)

Every feature, watcher, MCP server, and integration MUST begin with a
specification before any code is written. The mandatory workflow is:

- SPEC -> IMPLEMENT -> TEST -> QA -> FIX -> REPEAT
- No implementation without an approved `spec.md` in `specs/<feature>/`
- No deployment without QA-overseer sign-off
- Violation of this loop MUST halt execution immediately
- All specifications MUST use Given-When-Then acceptance scenarios
- The `/sp.specify` command is the sole entry point for new work

**Rationale:** Evolution-of-Todo proved that unspec'd code leads to
rework, scope creep, and untestable outputs. 13 ADRs and 37+ PHRs
from EoT were produced by strictly following this discipline.

### II. Local-First Privacy

All data MUST reside locally by default. The Obsidian vault is the
single source of truth for the AI Employee's state and memory.

- Secrets (API keys, OAuth tokens, session files) MUST never leave
  the local machine or be committed to version control
- Cloud sync (Platinum tier) MUST sync only markdown/state files;
  secrets MUST be excluded via `.gitignore` and sync-ignore rules
- No third-party SaaS MUST store user personal data unless the user
  explicitly opts in and the action is logged in `/Logs/`
- `.env` files MUST be used for all credentials; hardcoding is forbidden

**Rationale:** The hackathon blueprint mandates privacy-focused,
local-first architecture. Personal affairs (Gmail, WhatsApp, banking)
contain sensitive data that MUST remain under user control.

### III. Human-in-the-Loop for Sensitive Actions

Any action that sends data externally, spends money, or modifies
third-party state MUST require explicit human approval.

- Sensitive actions MUST create an approval file in `/Pending_Approval/`
- Execution proceeds ONLY after the file is moved to `/Approved/`
- Categories requiring approval: email sending, financial transactions,
  social media posting, account modifications, payments
- Approval thresholds MUST be configurable in `Company_Handbook.md`
- All approved actions MUST be logged in `/Logs/` with timestamp,
  action type, and outcome

**Rationale:** Autonomous agents operating on personal and business
data without guardrails create unacceptable risk. The HITL pattern
prevents irreversible mistakes while preserving automation speed for
non-sensitive operations.

### IV. MCP-First External Actions

All interactions with external systems MUST be routed through Model
Context Protocol (MCP) servers. Direct API calls from agent code
are forbidden.

- Each external service MUST have a dedicated MCP server wrapper
- MCP servers MUST be stateless; state lives in the Obsidian vault
- MCP servers MUST expose typed tool definitions with input validation
- Fallback behavior MUST be defined for each MCP (graceful degradation)
- New MCP servers MUST be registered in `ai-control/MCP.md`

**Rationale:** ADR-010 from Evolution-of-Todo proved that MCP wrapping
standardizes tool access, enables testing via mock servers, and
prevents vendor lock-in.

### V. Test-Driven Quality

All code MUST be validated through automated tests before merging.

- Watchers MUST have integration tests (mock data in -> action file out)
- MCP servers MUST have contract tests (input -> expected output)
- Orchestrator loops MUST have state-transition tests
- E2E tests via Playwright MUST verify critical user journeys
- The `/security-scan` skill MUST run before every `git push`
- Tests MUST be written FIRST, verified to fail, then implementation
  proceeds (Red-Green-Refactor)
- Test coverage for critical paths (watchers, MCP tools, approval
  workflow) MUST exceed 80%

**Rationale:** The EoT project documented HTTP 500 root cause analyses
and regression bugs that escaped due to insufficient test coverage.
TDD prevents these failures.

### VI. Watcher Architecture (Perception Layer)

The AI Employee's sensory system MUST follow the BaseWatcher pattern
for all external input sources.

- All watchers MUST inherit from a common `BaseWatcher` class
- Watchers MUST be idempotent (processing the same input twice
  produces the same result without side effects)
- Watchers MUST write structured markdown files to `/Needs_Action/`
  with YAML frontmatter (type, from, subject, priority, status)
- Watchers MUST handle their own errors and log failures without
  crashing the main process
- Watchers MUST run in persistent sessions (tmux/systemd) with
  automatic restart on failure
- Check intervals MUST be configurable per watcher type

**Rationale:** The hackathon blueprint defines watchers as the core
perception mechanism. Demo Day showcased that watcher reliability
directly determines overall system reliability.

### VII. Phase-Gated Delivery

Development MUST proceed through defined phases. Each phase has
explicit entry criteria, deliverables, and exit criteria.

- Phase transitions MUST be validated by `/phase-execution-controller`
- No phase N+1 work MUST begin until phase N exit criteria are met
- Environment validation MUST pass before any phase execution
  (fail-fast strategy from ADR-013)
- Each phase MUST produce a testable, demonstrable increment
- Phase status MUST be tracked in `specs/overview.md`

**Phase Definitions:**
- Phase 0: Foundation & Governance (constitution, project structure)
- Phase 1: Obsidian Vault (folder taxonomy, templates, Dashboard.md)
- Phase 2: First Watcher - Bronze (Gmail or filesystem watcher)
- Phase 3: Claude Reasoning Loop (Ralph Wiggum pattern)
- Phase 4: MCP Integration (Gmail send, browser, file system)
- Phase 5: HITL Approval + WhatsApp - Silver
- Phase 6: CEO Briefing + Odoo - Gold
- Phase 7: Always-On Cloud - Platinum
- Phase 8: Polish, Testing & Demo

**Rationale:** EoT demonstrated that phase isolation prevents
cross-contamination of concerns and enables incremental delivery.

### VIII. Reusable Intelligence

Every decision, solution, and failure MUST be documented for reuse.

- Prompt History Records (PHRs) MUST be created for every user prompt
  in `history/prompts/` (constitution, feature, or general subdirs)
- Architecture Decision Records (ADRs) MUST be created for significant
  decisions (Impact + Alternatives + Scope test, all true = suggest)
- ADRs MUST never be auto-created; user consent is required
- Skills MUST be extracted when a pattern repeats 3+ times
- The `docs/` directory serves as the system's long-term memory
- Session state MUST be persisted to enable resume across sessions
  via `/session-state-manager`

**Rationale:** The "Flywheel" concept: Claude CLI executes, skills
ensure consistency, reusable intelligence means solving each problem
only once. EoT's 37+ PHRs and 13 ADRs prove this approach works.

### IX. Security by Default

Security MUST be built into every layer, not bolted on afterward.

- Secrets MUST use `.env` files; never hardcoded, never committed
- Authentication MUST use JWT + HTTPOnly cookies (ADR-004 pattern)
- All API endpoints MUST have rate limiting
- Input validation MUST occur at system boundaries (user input,
  external APIs, watcher data)
- The `/security-scan` skill MUST run pre-push
- OWASP Top 10 vulnerabilities MUST be actively prevented
- Audit logging MUST capture: who, what, when, outcome
- Banking and payment credentials MUST never sync to cloud

**Rationale:** The AI Employee handles email, WhatsApp, banking,
and social media. A security breach in any domain has cascading
real-world consequences.

### X. Graceful Degradation

The system MUST continue functioning when components fail.

- Each watcher MUST operate independently; one watcher's failure
  MUST NOT affect others
- MCP server failures MUST trigger fallback behavior, not crashes
- The Ralph Wiggum loop MUST have a maximum retry count to prevent
  infinite loops (configurable, default: 5)
- Network failures MUST be handled with exponential backoff
- All errors MUST be logged to `/Logs/` with structured format
- The system MUST recover automatically after transient failures
- Health checks MUST monitor all running components
- Dashboard.md MUST reflect current system health status

**Rationale:** Demo Day revealed that process death and API failures
are the most common production issues. Self-healing patterns
(Junaid's "self-healing loop") solve this.

## Tech Stack Constraints

| Component | Required Version | Purpose |
|-----------|-----------------|---------|
| Claude Code | Active subscription (Pro) | Reasoning engine + orchestrator |
| Obsidian | v1.10.6+ | Knowledge base + dashboard |
| Python | 3.13+ | Watchers, orchestrator, MCP servers |
| Node.js | v24+ LTS | MCP servers + automation |
| Git + GitHub | Latest | Version control, PRs, issues |
| Playwright | Latest | Browser automation + E2E testing |
| SQLite | Bundled with Python | Development database |
| Neon PostgreSQL | Latest (Gold tier) | Production persistence |
| FastAPI | Latest | REST API framework |
| SQLModel + Alembic | Latest | ORM + migrations |
| Odoo Community | v19+ (Gold tier) | ERP / accounting integration |

**Prohibited:**
- No direct database queries; use SQLModel ORM
- No synchronous blocking I/O in watchers; use async
- No frontend frameworks unless explicitly spec'd for a feature
- No cloud services for data storage without user opt-in

## Agent Governance & Enforcement Loops

### Agent Hierarchy

All agents MUST operate within their defined authority:

- **Imperator** (Opus): Strategic decisions, scope protection, delegation
- **Lead-Architect** (Opus): Specs, plans, ADRs, phase transitions
- **Spec-Architect** (Opus): Rigorous specifications before code
- **Backend-Builder** (Opus): FastAPI, database, MCP servers, watchers
- **UX-Frontend-Developer** (Sonnet): UI components, accessibility
- **DevOps-RAG-Engineer** (Sonnet): Docker, deployment, RAG pipelines
- **Task-Orchestrator** (Sonnet): Parallel work coordination
- **Modular-AI-Architect** (Opus): Agent design, memory systems
- **QA-Overseer** (Opus): Final verification before "Done"
- **Loop-Controller** (Opus): Enforce SPEC->IMPL->TEST->QA cycle
- **Path-Warden** (Sonnet): File placement validation
- **Enterprise-Grade-Validator** (Sonnet): Production readiness

### Enforcement Loops

1. **Spec-Driven Loop**: SPEC -> IMPLEMENT -> TEST -> QA -> REPEAT.
   Violation = STOP immediately.
2. **Ralph Wiggum Loop**: Create state -> Claude works -> Try exit ->
   Check /Done? -> NO: re-inject, YES: allow exit.
3. **Human-in-the-Loop**: Detect sensitive -> /Pending_Approval/ ->
   Human reviews -> /Approved/ -> MCP executes -> /Logs/.
4. **Directory Guard**: Wrong directory = STOP immediately. Move
   everything to correct path before resuming.

### Agent Rules

- One agent = one responsibility; no cross-domain execution
- Agents MUST NOT override specifications
- Agents MUST NOT communicate directly; use vault files as message bus
- New agents MUST be registered in `ai-control/AGENTS.md`
- Agent failures MUST be logged with root cause analysis

## Development Workflow

### SDD Command Sequence

```
/sp.specify  -> specs/<feature>/spec.md
/sp.clarify  -> Resolve unknowns (2-3 targeted questions)
/sp.plan     -> specs/<feature>/plan.md + research.md + data-model.md
/sp.adr      -> history/adr/ADR-NNN.md (if significant decision)
/sp.tasks    -> specs/<feature>/tasks.md
/sp.taskstoissues -> GitHub Issues (optional)
/sp.implement -> Code changes (smallest viable diff)
/sp.git.commit_pr -> Git commit + PR
/sp.phr      -> history/prompts/<feature>/NNN-slug.prompt.md
```

### Quality Gates

- **Pre-implementation**: Spec approved, plan reviewed, tasks broken down
- **Pre-commit**: Tests pass, `/code-cleanliness` skill passes
- **Pre-push**: `/security-scan` passes, no secrets in staged files
- **Pre-merge**: QA-overseer verification, Playwright E2E passes
- **Pre-deploy**: `/deployment-preflight-check` passes

### Directory Structure (Canonical)

```
Personal-AI-Employee-Hackathon-0/
├── .specify/           # SpecKit Plus (templates, scripts, constitution)
├── .claude/commands/   # SDD commands
├── ai-control/         # Governance files (AGENTS, LOOP, SWARM, MCP, SKILLS)
├── specs/              # Feature specifications
├── history/            # ADRs + PHRs
├── vault/              # Obsidian Vault (AI dashboard)
├── watchers/           # Python watcher scripts
├── mcp-servers/        # Custom MCP server implementations
├── orchestrator/       # Ralph Wiggum loop + task runner
├── tests/              # All test suites
├── scripts/            # Utility scripts
└── docs/               # Reusable Intelligence / long-term memory
```

## Governance

### Amendment Procedure

1. Any team member or agent MAY propose an amendment
2. Amendments MUST be documented with rationale and impact analysis
3. Amendments MUST be reviewed by the Lead-Architect agent
4. Breaking changes (principle removal/redefinition) require human approval
5. All amendments MUST update the version number per semantic versioning
6. The Sync Impact Report (HTML comment at top of this file) MUST be
   updated with every amendment

### Versioning Policy

- **MAJOR**: Backward-incompatible governance/principle changes
- **MINOR**: New principle/section added or materially expanded
- **PATCH**: Clarifications, wording, typo fixes, non-semantic changes

### Compliance Review

- Every PR MUST verify compliance with this constitution
- The Loop-Controller agent MUST enforce the spec-driven loop
- The QA-Overseer MUST verify deliverables against acceptance criteria
- Phase transitions MUST be validated by `/phase-execution-controller`
- Quarterly review of constitution relevance (or after each major phase)

### Authoritative Source Mandate

Agents MUST prioritize MCP tools and CLI commands for all information
gathering and task execution. Internal knowledge MUST NOT be assumed;
all methods require external verification via authoritative sources.

**Version**: 1.0.0 | **Ratified**: 2026-02-16 | **Last Amended**: 2026-02-16
