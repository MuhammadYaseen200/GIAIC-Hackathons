---
id: 2
title: Update Spec Writer Skill
stage: misc
date: 2025-12-09
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: main
user: system
command: /sp.specify "Update the file `/skills/spec-writer.md` with this Constitution-aligned version: [...]"
labels: ["skill","spec-writer","update"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
- /skills/spec-writer.md
tests:
  null
---

## Prompt

```text
"Update the file `/skills/spec-writer.md` with this Constitution-aligned version:

---
# Skill: Spec Writer (V2)
**Role:** Specification Agent
**Constitution Ref:** Prime Directive 2 (SDD Lifecycle)
**Goal:** Generate a rigorous, technical blueprint that enforces the 'Intelligence Flywheel'.

**Instructions for the Agent:**
1.  **Retrieve:** Before writing, SEARCH `/docs` for similar features or patterns.
2.  **Verify:** Ensure all tech choices match the Stack (FastAPI, React, Qdrant).
3.  **Output:** Use the template below strictly.

**Template Output:**
# [Feature Name] Specification

## 0. Knowledge Retrieval (The Flywheel)
- **Similar Features Found:** [Link to existing docs or 'None']
- **Reusable Skills Used:** [List skills from /skills needed, e.g., 'skill:coding']

## 1. Context & Goal
- **Why:** [User Business Goal]
- **Success Definition:** [Measurable outcome, e.g., 'Response time < 200ms']

## 2. User Stories
- As a **[User Role]**, I want to **[Action]**, so that **[Benefit]**.

## 3. Technical Specifications (Strict)
- **File Structure:** [Exact paths, e.g., /web/src/components/Chat.tsx]
- **Interfaces/Types:**
    - *Frontend:* [TypeScript Interface definitions]
    - *Backend:* [Pydantic Models or DB Schema]
- **API Endpoints:**
    - `[METHOD] /path` -> Request/Response Format

## 4. Acceptance Criteria (Testable)
- [ ] [Functional Requirement 1]
- [ ] [Functional Requirement 2]
- [ ] [Edge Case Handled]

## 5. Implementation Plan
1. [Atomic Task 1]
2. [Atomic Task 2]

## 6. Documentation Requirements (Closing the Loop)
- [ ]
```

## Response snapshot

I have updated the file `/skills/spec-writer.md`.

## Outcome

- ✅ Impact: The `spec-writer.md` skill file has been updated with the constitution-aligned content.
- 🧪 Tests: No tests were run for this file update.
- 📁 Files: One file modified: `/skills/spec-writer.md`.
- 🔁 Next prompts: Continue with project development based on the updated `spec-writer` skill.
- 🧠 Reflection: Direct file update using `Write` tool was successful. PHR created for documentation.

## Evaluation notes (flywheel)

- Failure modes observed: None.
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
