---
id: PHR-003
title: Phase 2 Architecture Decision Records
stage: plan
date: 2025-12-29
surface: Claude Code CLI
model: claude-opus-4-5-20251101
feature: phase-2-web
branch: phase-2-web-init
user: MuhammadYaseen200
command: /sp.adr
labels: [adr, architecture, phase-2, decisions]
links:
  spec: phase-2-web/specs/spec.md
  ticket: N/A
  adr: history/adr/ADR-004 to ADR-007
  pr: N/A
files:
  - history/adr/ADR-004-httponly-cookie-jwt-strategy.md (created)
  - history/adr/ADR-005-nextjs-server-actions-data-layer.md (created)
  - history/adr/ADR-006-sqlmodel-alembic-migrations.md (created)
  - history/adr/ADR-007-brownfield-isolation-strategy.md (created)
  - phase-2-web/specs/plan.md (updated with ADR references)
tests:
  - N/A (documentation phase)
---

## Prompt

```text
/sp.adr use agents @agent-lead-architect @agent-imperator @agent-qa-overseer @agent-path-warden
**Context:**
We have completed the Planning for **Phase 2: Full-Stack Web Application**.
* **Current Directory:** `phase-2-web/` (Strict Check).
* **Decisions Made:** CL-001 to CL-005 from the Clarification phase.
* **Goal:** Formalize these decisions into immutable ADRs (`history/adr/`) to prevent regression during implementation.

**Objective:**
Generate the **Architecture Decision Records (ADRs)** for Phase 2.

**Required ADRs:**
1. ADR-004: HTTP-Only Cookie Strategy for JWT
2. ADR-005: Next.js Server Actions as Data Layer
3. ADR-006: SQLModel with Alembic for Migrations
4. ADR-007: Brownfield Isolation Strategy
```

## Response snapshot

Generated 4 comprehensive Architecture Decision Records:

**ADR-004: HTTP-Only Cookie JWT Strategy**
- Context: SPA token storage security (XSS vulnerability in localStorage)
- Decision: httpOnly cookies + Next.js middleware extraction
- Alternatives considered: localStorage, server-side session, cookie-only

**ADR-005: Next.js Server Actions as Data Layer**
- Context: Next.js 15 data mutation patterns
- Decision: Server Actions for all mutations with revalidatePath
- Alternatives considered: API Routes (BFF), React Query client-side

**ADR-006: SQLModel with Alembic for Migrations**
- Context: Database schema evolution from nothing (Phase 1) to PostgreSQL
- Decision: Alembic migrations, no create_all() in production
- Alternatives considered: create_all(), Django-style, raw SQL (Flyway)

**ADR-007: Brownfield Isolation Strategy**
- Context: How Phase 2 relates to Phase 1 code
- Decision: Port logic, do not import from phase-1-console/
- Alternatives considered: direct imports, shared library, complete rewrite

Each ADR includes:
- Detailed context and constraints
- Decision with implementation patterns
- Consequences (positive/negative/risks)
- Alternatives considered with rejection rationale
- Implementation guidelines and forbidden patterns

Updated plan.md with ADR reference table linking to all 4 ADRs.

## Outcome

- Impact: Formalized 4 architectural decisions as immutable ADRs
- Tests: N/A (documentation)
- Files: 4 ADRs created, plan.md updated
- Next prompts: `/sp.implement` to begin implementation following tasks.md
- Reflection: ADR format with alternatives section provides strong documentation for future reference

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): ADR Checklist - PASS
  - Each ADR documents clustered decision (not atomic)
  - Each ADR lists at least one alternative
  - Each ADR includes pros/cons for chosen and alternatives
  - Each ADR is concise but sufficiently detailed
- Prompt variant (if applicable): Standard /sp.adr with agent orchestration
- Next experiment (smallest change to try): Consider generating ADR diagrams (Mermaid) for complex decisions
