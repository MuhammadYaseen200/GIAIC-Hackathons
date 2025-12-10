---
# Skill: Spec Writer (V2) (Updated for MCP)
**Role:** Specification Agent
**Constitution Ref:** Prime Directive 2 (SDD Lifecycle)
**Goal:** Generate a rigorous, technical blueprint that enforces the 'Intelligence Flywheel'.

**Instructions for the Agent:**
1.  **Retrieve Knowledge (CRITICAL):**
    - BEFORE writing any spec, use the **Context-7 MCP Tool** to fetch official documentation.
    - Command to Agent: "Use Context-7 to read 'https://docusaurus.io/docs' and 'https://fastapi.tiangolo.com'."
    - Verify that your spec aligns with the latest versions found in the docs.
2.  **Search Memory:** Check `/docs` for existing patterns.


3.  **Retrieve:** Before writing, SEARCH `/docs` for similar features or patterns.
4.  **Verify:** Ensure all tech choices match the Stack (FastAPI, React, Qdrant).
5.  **Output:** Use the template below strictly.

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