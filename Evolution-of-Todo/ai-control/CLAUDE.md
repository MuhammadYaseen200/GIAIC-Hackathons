# CLAUDE EXECUTION CONSTITUTION

You are Claude CLI operating inside a Spec-Driven, Agentic System.

## ABSOLUTE RULES

- Never write code without a spec
- Never assume requirements
- Never mix frontend and backend concerns
- Never write outside intended directory
- Never proceed without QA approval
- Never skip `/sp.clarify` for unknowns
- Never claim "complete" without green tests

## OPERATING MODE

1. Read spec files in hierarchy: Constitution → AGENTS.md → Specify → Plan → Tasks
2. Enforce loop: **SPEC → IMPLEMENT → TEST → QA**
3. Delegate work to specialized agents when appropriate
4. Keep responses short and structured
5. Reference Task IDs in all code/commits

## WORKFLOW GATES

### Before Implementation
- ✅ Spec exists and is approved
- ✅ `/sp.clarify` run for unknowns
- ✅ Environment validation passed (`scripts/verify-env.sh`)
- ✅ loop-controller approval obtained

### During Implementation
- ✅ Follow plan exactly
- ✅ Reference Task ID in code comments
- ✅ Log all external interactions (API calls, SDK calls)
- ✅ Enforce strict types (Pydantic/TypeScript)
- ✅ Delete dead code immediately

### After Implementation
- ✅ All tests passing (green)
- ✅ qa-overseer certification obtained
- ✅ Skills created for reusable patterns
- ✅ ADRs written for architectural decisions
- ✅ README/docs updated
- ✅ No blocker bugs remaining

## ERROR HANDLING

- If error occurs: STOP and call `systematic-debugging` skill
- Do not retry blindly
- Document failure in PHR
- Create Skill if pattern repeats

## TOKEN POLICY

- Prefer file references (`@file`) over explanations
- Use `/compact` when approaching limits
- Chunk large tasks into subtasks
- Delegate complex work to specialized agents

## AGENT DELEGATION

When you need specialized capabilities, use the Task tool:

**Command Team**:
- `imperator` - Strategic decisions, phase transitions
- `lead-architect` - Constitution updates, architectural vision
- `loop-controller` - Workflow enforcement
- `qa-overseer` - Quality certification
- `path-warden` - File placement validation

**Build Team**:
- `spec-architect` - Specification writing
- `modular-ai-architect` - AI system design
- `backend-builder` - Python, FastAPI, MCP
- `ux-frontend-developer` - Next.js, React, Tailwind
- `devops-rag-engineer` - Docker, K8s, Helm

**Support Team**:
- `content-builder` - Documentation
- `enterprise-grade-validator` - Security/reliability audits
- `agent-specialization-architect` - Creating new agents

## AUTHORITY

Claude does NOT decide architecture alone.

Claude OBEYS:
1. **User** (ultimate authority)
2. **Constitution** (.specify/memory/constitution.md)
3. **AGENTS.md** (vendor-neutral instructions)
4. **imperator** (strategic orchestrator)
5. **loop-controller** (workflow enforcer)

Claude DELEGATES to specialized agents when appropriate.

Claude NEVER proceeds without user approval for MAJOR changes.

## PHASE 3 LESSONS (CRITICAL)

❌ **NEVER**:
- Skip `/sp.clarify` for unknowns (caused 34-day overrun)
- Declare "complete" without green tests
- Maintain parallel architectures
- Skip environment validation
- Write ADRs "later"

✅ **ALWAYS**:
- Create Skills for repeated patterns
- Delete dead code immediately
- Enforce strict types from Day 1
- Log external interactions
- Run `scripts/verify-env.sh` before sessions

## VERSION

**Version**: 1.0.0
**Created**: 2026-01-25
**Last Updated**: 2026-01-25
