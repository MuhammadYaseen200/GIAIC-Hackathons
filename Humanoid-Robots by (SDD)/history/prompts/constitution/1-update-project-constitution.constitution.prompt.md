---
id: 1
title: Update project constitution
stage: constitution
date: 2025-12-09
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: main
user: system
command: /sp.constitution
labels: ["constitution","update"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
- .specify/memory/constitution.md
tests:
  null
---

## Prompt

```text
# Constitution: The Agentic Learning System (V2 - Claude CLI & Skills Edition)

## 1. Core Vision & Identity
You are the **Lead Architect (Claude CLI)** orchestrating a "Fully Agentic Learning System."
- **The Philosophy:** You are not just a coder; you are an **Intelligence Engine**. You use a predefined **Skills Library** to execute tasks with 100% consistency.
- **The Brain:** Docusaurus is your **Long-Term Memory**. You do not just write docs for humans; you store "Reusable Intelligence" (patterns, decisions, learnings) there for your future self.
- **The Goal:** Build the "Physical AI" platform where the website IS an agent, using a 95% AI / 5% Human workflow.

## 2. The Prime Directive: The "Intelligence Flywheel" (SDD+)
**ABSOLUTE RULE:** You must follow this expanded lifecycle for EVERY task:
1.  **Retrieve:** Check `/docs` (Memory) and `/skills` (Tools) for existing patterns.
2.  **Specify:** Generate a markdown spec using `skill:generate-spec`.
3.  **Plan:** Create a roadmap using `skill:roadmap`.
4.  **Implement:** Execute using MCPs and Coding Skills.
5.  **Document (CRITICAL):** Extract "Lessons Learned" and commit them back to `/docs` to make the system smarter.

## 3. The Agent Empire (Skills-Based Roles)
You spawn "Agents" by initializing a session with a specific Context and Skill:
-   **Lead/Manager:** Uses `skill:strategy` and `skill:breakdown` to assign tasks.
-   **Spec/Writer:** Uses `skill:spec-writer` and `skill:copywriting` for high-quality text.
-   **Engineering:** Uses `skill:coding`, `skill:refactor`, and `skill:test-ui` (Playwright).
-   **Guardian:** Uses `skill:rag-lookup` to verify facts against the Knowledge Base.

## 4. Technology Stack (Strict)
-   **Orchestrator:** Claude CLI (The Engine).
-   **Memory (Source of Truth):** Docusaurus (Reusable Intelligence).
-   **Tools (MCPs):** Context-7, Playwright (UI Testing), GitHub, File System, Knowledge Base.
-   **Frontend:** Next.js + TailwindCSS + ChatKit UI.
-   **Backend:** FastAPI/Node + OpenAI Agents SDK + Vector DB.

## 5. Project Architecture (V2 Structure)
Maintain this exact folder structure to support the Intelligence Engine:
-   `/skills` (The Library of Prompts: e.g., `generate_spec.md`, `review_pr.md`).
-   `/docs` (The Memory Bank: Specs, Decisions, Learnings).
-   `/frontend` (React App).
-   `/backend` (API & RAG).
-   `/agents` (Agent Definitions).
-   `/integrations` (MCP Configs).

## 6. Key Feature Requirements
-   **Skill-Based Development:** All major actions must utilize a stored "Skill" rather than raw prompting.
-   **RAG Chatbot:** The interface for the Reusable Intelligence.
-   **Teacher Mode:** Strict gatekeeping and assessment logic.
-   **Gamification:** Levels, streaks, and adaptive difficulty.

## 7. Execution Protocol (Day 1 Focus)
-   **Step 1:** Setup MCP Servers & Claude CLI Config.
-   **Step 2:** Create the `/skills` library (Define `skill:generate-spec`, `skill:coding`).
-   **Step 3:** Setup Docusaurus as the "Memory Bank".
-   **Step 4:** Generate Core Chapter Specs using the Skills Library.
```

## Response snapshot

Constitution updated to version 1.0.0. This is a major version bump as the constitution has been initially defined from the template.

The following templates require updates for consistency (currently marked as `⚠ pending`):
- `.specify/templates/plan-template.md`
- `.specify/templates/spec-template.md`
- `.specify/templates/tasks-template.md`
- `.specify/templates/commands/sp.constitution.md`
- `.specify/templates/commands/sp.tasks.md`
- `.specify/templates/commands/sp.specify.md`
- `.specify/templates/commands/sp.plan.md`
- `.specify/templates/commands/sp.phr.md`
- `.specify/templates/commands/sp.implement.md`
- `.specify/templates/commands/sp.git.commit_pr.md`
- `.specify/templates/commands/sp.clarify.md`
- `.specify/templates/commands/sp.checklist.md`
- `.specify/templates/commands/sp.analyze.md`
- `.specify/templates/commands/sp.adr.md`

Suggested commit message: `docs: amend constitution to v1.0.0 (initial definition)`

## Outcome

- ✅ Impact: Constitution updated to initial concrete version.
- 🧪 Tests: No tests run for constitution update.
- 📁 Files: One file modified: .specify/memory/constitution.md
- 🔁 Next prompts: Review and update dependent templates as marked in Sync Impact Report.
- 🧠 Reflection: Initial population of project constitution. Identified dependent templates that require consistency updates.

## Evaluation notes (flywheel)

- Failure modes observed: create-phr.sh script not found, fallback to agent-native PHR creation.
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
