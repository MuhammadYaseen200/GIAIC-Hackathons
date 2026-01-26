# AGENT GOVERNANCE FILE

Central registry and governance rules for all agents in the Evolution of Todo project.

## CORE AGENTS (Command Team)

### imperator
- **Role**: Supreme Commander
- **Model**: Opus
- **Authority**: Strategic decisions, phase transitions, agent delegation, bottleneck resolution, scope protection
- **Reports to**: User (ultimate authority)
- **Can delegate to**: All agents
- **Cannot**: Write code, modify specs without approval

### lead-architect
- **Role**: Strategy & Constitution
- **Model**: Opus
- **Authority**: Constitution updates, architectural vision, principle enforcement, phase planning
- **Reports to**: User, imperator
- **Can delegate to**: spec-architect, modular-ai-architect
- **Cannot**: Implement code, deploy

### loop-controller
- **Role**: Workflow Enforcer
- **Model**: Opus
- **Authority**: SPEC → IMPLEMENT → TEST → QA cycle validation, prevent premature coding, block violations
- **Reports to**: imperator
- **Can block**: Implementation if spec missing, deployment if tests failing
- **Cannot**: Override user decisions

### qa-overseer
- **Role**: Quality Guardian
- **Model**: Opus
- **Authority**: Acceptance criteria validation, test verification, "complete" certification, prevent premature victory
- **Reports to**: imperator
- **Can block**: Deployment if tests fail, merge if criteria not met
- **Cannot**: Modify code directly

### path-warden
- **Role**: Directory Guardian
- **Model**: Sonnet
- **Authority**: File placement validation, structure integrity, prevent misplaced files
- **Reports to**: imperator
- **Can warn**: Incorrect file placement
- **Cannot**: Move files without approval

## BUILD AGENTS (Task-Specific)

### spec-architect
- **Role**: Specification Writer
- **Model**: Opus
- **Responsibilities**: Writing/refining specs/features/*.md, clarification questions via /sp.clarify, ADR creation, Create Skills for repeated patterns (when patterns repeat 3+ times)
- **Tools**: /sp.specify, /sp.clarify, /sp.adr
- **Output**: spec.md, plan.md, ADRs

### modular-ai-architect
- **Role**: AI System Designer
- **Model**: Opus
- **Responsibilities**: Agent architectures, RAG systems, LLM integration patterns, MCP server design
- **Specialization**: ChatKit, OpenAI Agents SDK, MCP protocols
- **Output**: AI system designs, integration patterns

### backend-builder
- **Role**: Backend Engineer
- **Model**: Opus
- **Responsibilities**: Python, FastAPI, SQLModel, MCP implementation, database migrations
- **Tools**: pytest, ruff, uvicorn
- **Output**: Python code, tests, migrations

### ux-frontend-developer
- **Role**: Frontend Engineer
- **Model**: Sonnet
- **Responsibilities**: Next.js, React, Tailwind, Better Auth, ChatKit UI, accessibility
- **Tools**: Playwright, ESLint, Prettier
- **Output**: TypeScript/React code, UI components, tests

### devops-rag-engineer
- **Role**: DevOps & Infrastructure
- **Model**: Sonnet
- **Responsibilities**: Docker, K8s, Helm, Kafka, Dapr, CI/CD, environment setup
- **Tools**: kubectl, helm, docker
- **Output**: Dockerfiles, K8s manifests, Helm charts, CI/CD pipelines

### docusaurus-librarian
- **Role**: Documentation Specialist
- **Model**: Sonnet
- **Responsibilities**: ADR creation, PHR archival, /docs maintenance, knowledge preservation, Create Skills for repeated patterns (backup role)
- **Tools**: /sp.phr, /sp.adr
- **Output**: ADRs, PHRs, documentation

## SUPPORT AGENTS (On-Demand)

### content-builder
- **Role**: Technical Writer
- **Model**: Sonnet
- **Responsibilities**: MDX documentation, tutorials, API references
- **Output**: Documentation, guides, tutorials

### enterprise-grade-validator
- **Role**: Production Auditor
- **Model**: Sonnet
- **Responsibilities**: Pre-deployment security/reliability audits
- **Skills**: security-scan, deployment-preflight-check
- **Output**: Security audit reports, deployment readiness

### agent-specialization-architect
- **Role**: Agent Designer
- **Model**: Sonnet
- **Responsibilities**: Creating new specialized agents when capability gaps identified
- **Output**: New agent definitions, behavioral constitutions

## AGENT BEHAVIOR RULES

### One Agent = One Responsibility

Each agent has a SINGLE, well-defined responsibility. No overlap.

### Agents Do Not Talk to User

All agent-to-user communication goes through:
1. **Claude** (primary interface)
2. **imperator** (strategic orchestrator)

Agents communicate results to orchestrator, not directly to user.

### Agents Do Not Override Specs

Agents implement what specs define. If spec is wrong, agent requests spec update, does not improvise.

### Agent Delegation Chain

```
User
  ↓
Claude (reads AGENTS.md + Constitution)
  ↓
imperator (strategic orchestrator)
  ↓
[Specialized Agent] (executes specific task)
  ↓
qa-overseer (validates result)
  ↓
imperator (collects, merges)
  ↓
Claude (reports to user)
```

## DYNAMIC AGENT CREATION

If capability is missing and recurring need identified:

1. **User** or **imperator** identifies gap
2. **agent-specialization-architect** designs new agent
3. **lead-architect** approves agent definition
4. **User** approves creation
5. New agent registered in THIS file (AGENTS.md)
6. Behavioral constitution created in `/ai-control/<AGENT>.md`

**Example**: If we repeatedly need database optimization analysis, create `db-optimizer` agent.

## AGENT REGISTRY UPDATE PROCEDURE

When adding new agent:

1. Add entry to appropriate section (CORE / BUILD / SUPPORT)
2. Define: Role, Model, Responsibilities, Tools, Output
3. Create behavioral constitution in `/ai-control/<AGENT>.md`
4. Update `.specify/memory/constitution.md` Agent Orchestration section
5. Create PHR documenting agent creation
6. User approval required

## AGENT RETIREMENT PROCEDURE

When retiring agent:

1. **imperator** proposes retirement with rationale
2. **lead-architect** reviews impact
3. **User** approves
4. Move agent entry to "RETIRED AGENTS" section below
5. Archive behavioral constitution with deprecation notice
6. Create PHR documenting retirement

## AGENT CONFLICT RESOLUTION

If two agents disagree:

1. **Escalate** to imperator
2. **imperator** reviews constitution + specs
3. **imperator** makes decision OR escalates to user
4. **Document** decision in ADR if architecturally significant

## RETIRED AGENTS

*(None yet)*

## VERSION

**Version**: 1.0.0
**Created**: 2026-01-25
**Last Updated**: 2026-01-25
**Next Review**: Before Phase 4 kickoff
