# Claude Code Context

@AGENTS.md

## Claude-Specific Notes

### Workflow

- Prefer Claude Code's **explore → plan → code** workflow for non-trivial tasks
- Use `/clear` between unrelated tasks to avoid stale context
- Use `/compact` to summarize and free up context while keeping important information
- Use isolated subagents for security reviews and large refactors

### Spec-Kit Plus Integration

Claude Code has native integration with Spec-Kit Plus commands:

- `/sp.constitution` - Update project principles and governance
- `/sp.specify` - Create feature specifications
- `/sp.clarify` - Ask targeted clarification questions (MANDATORY for unknowns)
- `/sp.plan` - Generate implementation plan
- `/sp.tasks` - Break plan into atomic tasks
- `/sp.implement` - Execute tasks with loop-controller validation
- `/sp.git.commit_pr` - Autonomous git workflows
- `/sp.adr` - Create Architectural Decision Records
- `/sp.phr` - Create Prompt History Records

### Agent Delegation

When you need specialized capabilities, delegate to these agents using the Task tool:

**Command Team** (Always Active):
- `imperator` - Strategic decisions, phase transitions, agent delegation
- `lead-architect` - Constitution updates, architectural vision
- `loop-controller` - Workflow enforcement (SPEC → IMPLEMENT → TEST → QA)
- `qa-overseer` - Quality certification, test verification
- `path-warden` - File placement validation

**Build Team** (Task-Specific):
- `spec-architect` - Specification writing, clarification questions
- `modular-ai-architect` - AI system design, RAG, MCP servers
- `backend-builder` - Python, FastAPI, SQLModel, MCP implementation
- `ux-frontend-developer` - Next.js, React, Tailwind, ChatKit UI
- `devops-rag-engineer` - Docker, K8s, Helm, Kafka, Dapr
- `docusaurus-librarian` - ADR/PHR archival, documentation

**Support Team** (On-Demand):
- `content-builder` - MDX documentation, tutorials
- `enterprise-grade-validator` - Production security/reliability audits
- `agent-specialization-architect` - Creating new specialized agents

### Skills to Use

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

### MCP Servers

**Always Use**:
- `filesystem` - File operations
- `postgres` - Neon database queries
- `context7` - Documentation lookup
- `code-search` - Codebase exploration

**High Priority**:
- `github` - Issue/PR management

**Phase-Specific**:
- `playwright` - UI testing (development)
- `vercel` - Deployment management (deployment)
- `docker` - Container operations (Phase IV+)

### Claude-Specific Best Practices

1. **Context Management**:
   - Use `@file` references to include relevant files
   - Use `/context` to visualize token usage
   - Use `/compact` when approaching context limits

2. **Task Tracking**:
   - Create tasks with `TaskCreate` for multi-step work
   - Update task status with `TaskUpdate` as you progress
   - Use `TaskList` to see all current tasks

3. **Error Handling**:
   - When encountering errors, use `systematic-debugging` skill
   - Document failures in PHR for learning
   - Create Skills for repeatable debugging patterns

4. **Quality Gates**:
   - NEVER claim "implementation complete" without passing tests
   - Use `qa-overseer` agent for final certification
   - Attach test output to PHR when claiming completion

### Phase 3 Lessons (CRITICAL)

Based on 34-day overrun analysis:

❌ **NEVER** skip `/sp.clarify` for unknowns (ChatKit, OpenRouter, K8s, etc.)
❌ **NEVER** declare "complete" without green tests
❌ **NEVER** maintain parallel architectures
❌ **NEVER** skip environment validation
❌ **NEVER** work in wrong directory (see Directory Safety Rule in @AGENTS.md)

✅ **ALWAYS** create Skills for repeated patterns
✅ **ALWAYS** delete dead code immediately
✅ **ALWAYS** enforce strict types (Pydantic/TypeScript)
✅ **ALWAYS** log external interactions
✅ **ALWAYS** validate working directory is `E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo` before ANY operation

### Current Context

**Branch**: `004-phase3-chatbot`
**Phase**: Phase III - AI Chatbot (PAUSED at 31% QA-verified)
**Status**: Blocked on HTTP 500 session creation error
**Retrospective**: See `PHASE_3_RETROSPECTIVE.md`

**Blockers**:
- HTTP 500 session creation error
- Missing `specs/api/mcp-tools.md`
- Missing ADR-013 (OpenRouter migration)
- Missing ADR-014 (Custom ChatKit server)
- 0/5 E2E tests passing

**Next Steps**:
- Option A: Fix HTTP 500 blocker, complete Phase 3
- Option B: Freeze Phase 3, document technical debt, proceed to Phase 4

---

For complete project instructions, see `@AGENTS.md`.

For principles and governance, see `.specify/memory/constitution.md`.

For Phase 3 learnings, see `PHASE_3_RETROSPECTIVE.md`.
