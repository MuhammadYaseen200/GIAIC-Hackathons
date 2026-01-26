# SWARM EXECUTION RULES

Swarm mode enables parallel execution of independent tasks.

## ACTIVATION CONDITIONS

Swarm mode is enabled when:

1. **Tasks are independent** - No shared state dependencies
2. **Shared state is minimal** - Each task operates on isolated data
3. **Agents are available** - Multiple agents can work simultaneously
4. **User approves** - Parallel execution explicitly requested or beneficial

## RULES

### Task Isolation

- Each agent owns ONE task completely
- No cross-agent communication during execution
- No shared memory or state
- Results collected independently by orchestrator

### Agent Assignment

```
Task 1 → backend-builder (FastAPI endpoint)
Task 2 → ux-frontend-developer (React component)
Task 3 → devops-rag-engineer (Docker config)

All running in parallel, no dependencies.
```

### Result Collection

- All results go to imperator for aggregation
- qa-overseer validates EACH result independently
- Merge only when ALL tasks pass validation
- Rollback ALL if ANY task fails

## PARALLEL EXECUTION PATTERN

### Example: Phase 3 ChatKit Integration (3 Parallel Tracks)

**Track 1: Backend (backend-builder)**
- Task: Implement `/api/v1/chatkit/sessions` endpoint
- Files: `backend/app/api/v1/chatkit.py`
- Tests: `backend/tests/test_chatkit_crud.py`

**Track 2: Frontend (ux-frontend-developer)**
- Task: Create ChatKit UI component
- Files: `frontend/components/chat/ChatKit.tsx`
- Tests: `frontend/tests/chatkit.spec.ts`

**Track 3: Infrastructure (devops-rag-engineer)**
- Task: Configure CORS and proxy
- Files: `frontend/app/api/chatkit/[...path]/route.ts`
- Tests: Manual CORS validation

**Orchestrator (imperator)**:
1. Launch all 3 agents in parallel
2. Collect results independently
3. Validate with qa-overseer
4. Merge when all green
5. Rollback if any fail

## FORBIDDEN PATTERNS

❌ **NEVER**:
- Allow agents to communicate directly during execution
- Share context between parallel agents
- Merge results before qa-overseer validation
- Proceed if ANY agent fails
- Skip integration testing after merge

## COORDINATION PROTOCOL

### Before Swarm Launch

1. **imperator** verifies:
   - Tasks are truly independent
   - No shared state conflicts
   - All specs/plans available
   - Agents are ready

2. **imperator** assigns:
   - Task ID to each agent
   - File boundaries (no overlaps)
   - Success criteria
   - Timeout limits

### During Execution

- Agents work independently
- No inter-agent communication
- Each agent logs progress
- imperator monitors (read-only)

### After Completion

1. **imperator** collects results
2. **qa-overseer** validates EACH independently
3. **path-warden** validates file placements
4. **imperator** merges if all pass
5. **imperator** creates integration tests
6. **qa-overseer** validates integration

## FAILURE HANDLING

If ANY agent fails:

1. **STOP** all other agents
2. **ROLLBACK** all changes (use git tags)
3. **REPORT** failure to user
4. **FIX** the failed task
5. **RESTART** swarm from scratch (or sequential)

No partial merges. All-or-nothing.

## SWARM vs SEQUENTIAL DECISION

### Use Swarm When:
✅ Tasks are independent (backend + frontend + infra)
✅ No shared state
✅ Time-critical (deadline pressure)
✅ Clear boundaries (no file overlaps)

### Use Sequential When:
⚠️ Tasks have dependencies (A must complete before B)
⚠️ Shared state (multiple tasks modifying same file)
⚠️ Unclear boundaries
⚠️ High risk (production deployment)

## EXAMPLE SWARM SESSION

```
User: "Implement ChatKit integration: backend API, frontend UI, and proxy config"

imperator:
  ✓ Verified: 3 independent tasks
  ✓ No shared files
  ✓ All specs available
  → Launch swarm

Task 1 (backend-builder): [Task T-301] Backend API
Task 2 (ux-frontend-developer): [Task T-302] Frontend UI
Task 3 (devops-rag-engineer): [Task T-303] Proxy Config

[All agents execute in parallel]

backend-builder: ✅ Completed (10 min)
ux-frontend-developer: ✅ Completed (12 min)
devops-rag-engineer: ✅ Completed (8 min)

qa-overseer:
  ✓ Backend tests passing
  ✓ Frontend tests passing
  ✓ Proxy tests passing
  → Approve merge

imperator: ✅ Integration complete
```

## AAIF COMPLIANCE

Swarm operates under AAIF standards:
- Each agent uses MCP servers independently
- No vendor lock-in (agents are swappable)
- Shared AGENTS.md instructions
- Neutral orchestration (imperator)

## VERSION

**Version**: 1.0.0
**Created**: 2026-01-25
**Last Updated**: 2026-01-25
