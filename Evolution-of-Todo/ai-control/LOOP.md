# SPEC-DRIVEN LOOP

The heartbeat that prevents 90% of failures in the Evolution of Todo project.

## MANDATORY LOOP

```
SPEC → IMPLEMENT → TEST → QA → FIX → REPEAT
```

This loop is **IMMUTABLE** and **NON-NEGOTIABLE**.

## LOOP STAGES

### Stage 1: SPEC (Define WHAT)

**Entry Condition**: User has a feature request or requirement

**Actions**:
1. Run `/sp.specify` to create `spec.md`
2. Run `/sp.clarify` to resolve unknowns (MANDATORY if any ambiguity)
3. Define acceptance criteria
4. Get user approval

**Exit Condition**: `spec.md` exists AND is approved by user AND (no unknowns OR `/sp.clarify` completed)

**Blocker**: If spec unclear or ambiguous, HALT at Stage 1 until clarified. If unknowns detected (undocumented SDKs, new tech, ambiguous requirements), `/sp.clarify` is MANDATORY before Stage 2

**Responsible Agent**: spec-architect

---

### Stage 2: IMPLEMENT (Define HOW + Write Code)

**Entry Condition**: Spec approved AND loop-controller verified spec exists

**Actions**:
1. Run `/sp.plan` to create `plan.md` (architecture)
2. Run `/sp.tasks` to create `tasks.md` (work breakdown)
3. Assign tasks to appropriate agents:
   - backend-builder (Python/FastAPI)
   - ux-frontend-developer (Next.js/React)
   - devops-rag-engineer (Docker/K8s)
4. Execute tasks with Task ID references
5. Log all external interactions
6. Enforce strict types (Pydantic/TypeScript)

**Exit Condition**: Code written, Task IDs referenced, no syntax errors

**Blocker**: If spec missing, loop-controller BLOCKS implementation

**Responsible Agents**: backend-builder, ux-frontend-developer, devops-rag-engineer (orchestrated by imperator)

---

### Stage 3: TEST (Verify Correctness)

**Entry Condition**: Code implementation complete

**Actions**:
1. Run unit tests (pytest for backend, Playwright for frontend)
2. Run integration tests
3. Run E2E tests (if applicable)
4. Capture test output
5. Fix any failing tests

**Exit Condition**: ALL tests passing (green)

**Blocker**: If ANY test fails, return to Stage 2 (FIX)

**Responsible Agents**: backend-builder (pytest), ux-frontend-developer (Playwright)

---

### Stage 4: QA (Certify Quality)

**Entry Condition**: All tests passing

**Actions**:
1. qa-overseer reviews:
   - Acceptance criteria met?
   - Tests cover all scenarios?
   - No blocker bugs?
   - Documentation updated?
   - Skills created for reusable patterns?
   - ADRs written for architectural decisions?
2. qa-overseer validates against checklist (use `/sp.checklist`)
3. qa-overseer certifies OR rejects

**Exit Condition**: qa-overseer certification obtained

**Blocker**: If qa-overseer rejects, return to Stage 2 (FIX) with feedback

**Responsible Agent**: qa-overseer

---

### Stage 5: FIX (Address Feedback)

**Entry Condition**: Tests failed OR qa-overseer rejected

**Actions**:
1. Analyze failure/rejection
2. Update code to address issues
3. Return to Stage 3 (TEST)

**Exit Condition**: Fixes applied, ready to test again

**Responsible Agents**: Same agent that did implementation (backend-builder, ux-frontend-developer, etc.)

---

### Stage 6: REPEAT (Next Task)

**Entry Condition**: qa-overseer certified current task

**Actions**:
1. Mark task as complete in `tasks.md`
2. Create PHR documenting work (use `/sp.phr`)
3. Move to next task in `tasks.md`
4. If all tasks complete, move to next feature

**Exit Condition**: All tasks in feature complete

**Responsible Agent**: imperator (orchestrator)

---

## ENFORCEMENT

### loop-controller Responsibilities

The `loop-controller` agent enforces this loop by:

1. **Blocking implementation** if spec.md does not exist
2. **Blocking deployment** if tests are not passing
3. **Blocking "complete" claims** if qa-overseer has not certified
4. **Blocking phase transition** if previous phase not 100% complete

### Violation Consequences

If an agent attempts to violate the loop (e.g., code without spec):

1. **HALT** - Stop execution immediately
2. **REPORT** - Log violation in PHR
3. **REDIRECT** - Send back to correct stage
4. **ESCALATE** - Notify imperator and user

## LOOP METRICS (Phase Tracking)

### Phase I (Console App)
- **Loop Compliance**: 90%+ (manual validation)
- **Violations**: Few (simple project)
- **Result**: ✅ COMPLETE

### Phase II (Full-Stack Web)
- **Loop Compliance**: 85%+ (documented in PHRs)
- **Violations**: Minor (skipped some ADRs)
- **Result**: ✅ COMPLETE

### Phase III (AI Chatbot)
- **Loop Compliance**: ~40% (CRITICAL FAILURE)
- **Violations**:
  - ❌ Never ran `/sp.clarify` for ChatKit (caused 14-day delay)
  - ❌ Declared "complete" without green tests (3 times)
  - ❌ Skipped environment validation (4 days wasted)
- **Result**: ⚠️ PAUSED at 31% (QA-verified)

### Phase IV (Local K8s)
- **Target Compliance**: 95%+
- **Required**: Strict loop enforcement with no exceptions

## LOOP VIOLATIONS (Phase 3 Retrospective)

### Violation 1: Skipped `/sp.clarify` for ChatKit SDK

**What Happened**: Encountered unknown SDK, guessed at implementation instead of clarifying

**Consequence**: 34-day overrun, HTTP 500 error still unresolved

**Prevention**: loop-controller now BLOCKS implementation if unknowns detected without `/sp.clarify`

---

### Violation 2: Premature "Complete" Claims

**What Happened**: Declared "Implementation Complete" (PHR-304) with 0 tests passing

**Consequence**: False confidence, found bugs later, wasted 4 days on rework

**Prevention**: qa-overseer now requires test output attachment to PHR before certifying

---

### Violation 3: Skipped Environment Validation

**What Happened**: Invalid `.env` values (e.g., `0.0.0.0.1`) not caught early

**Consequence**: 2 days debugging connection errors

**Prevention**: loop-controller now requires `scripts/verify-env.sh` to pass before Stage 2

---

## LOOP SHORTCUTS (FORBIDDEN)

These shortcuts are EXPLICITLY FORBIDDEN:

❌ "Just this once, let's skip the spec"
❌ "Tests are mostly passing, that's good enough"
❌ "I'll write the ADR later"
❌ "Environment validation can wait"
❌ "QA can happen after deployment"

If you find yourself saying ANY of these, **STOP** and return to the loop.

## LOOP OPTIMIZATION (Allowed)

These optimizations are ALLOWED:

✅ Parallel implementation (Swarm mode) for independent tasks
✅ Incremental testing (test as you code)
✅ Continuous deployment (after QA certification)
✅ Automated environment validation (scripts)

Optimization is about **SPEED**, not skipping steps.

## FAILURE MODE

If loop is broken at any stage:

1. **STOP** execution immediately
2. **IDENTIFY** which stage was violated
3. **REPORT** to imperator and user
4. **RETURN** to correct stage
5. **DOCUMENT** violation in PHR for learning

## VERSION

**Version**: 1.0.0
**Created**: 2026-01-25
**Last Updated**: 2026-01-25
**Based On**: Phase 3 Retrospective (34-day overrun analysis)
