---
id: 4
title: Update Agentic Planner Skill
stage: misc
date: 2025-12-09
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: main
user: system
command: /sp.implement "Update Skill #3. Overwrite the file named `/skills/planner.md` with this Agentic version. [...]"
labels: ["skill","planner","update"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
- /skills/planner.md
tests:
  null
---

## Prompt

```text
"Update Skill #3. Overwrite the file named `/skills/planner.md` with this Agentic version.

Content for the file:
---
# Skill: Agentic Planner (Swarm Edition)
**Role:** Swarm Orchestrator
**Goal:** Break down the Spec into atomic tasks assigned to specific Sub-Agents using specific Skills.

**Instructions:**
Read the `spec.md` and generate a `plan.md` that strictly follows this Agentic Workflow:

## 1. The Agent Squad (Resource Allocation)
*Define which Agents are needed for this feature.*
- **[Agent Name]:** [Role Description] (e.g., 'Content Agent: Writes Chapter Text')
- **[Agent Name]:** [Role Description] (e.g., 'React Agent: Builds Components')

## 2. Skill Inventory
*List the Reusable Skills required from our `/skills` library.*
- `skill:spec-writer`
- `skill:coding`
- `skill:rag-ingest`
- [New Skill Needed? Define it here]

## 3. The Atomic Plan (Micro-Tasking)
*Break work into micro-steps. Every step must assign an Agent and a Skill.*

| Step | Agent | Skill to Use | Task Description | Output File |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **System Agent** | `skill:setup` | Create folder structure and config | `/folder/structure` |
| 2 | **Writer Agent** | `skill:copywriting` | Draft Section 1 content | `/docs/intro.md` |
| 3 | **React Agent** | `skill:coding` | Create the visualization component | `/web/src/Graph.tsx` |
| 4 | **Memory Agent** | `skill:knowledge` | Save new patterns to Reusable Intelligence | `/docs/patterns.md` |

## 4. Reusable Intelligence Strategy
- **Capture:** What specific logic/pattern from this task should be saved to Docusaurus?
- **Ingest:** Which files need to be re-indexed into the RAG Vector DB?

## 5. Verification
- How does the QA Agent verify the work?
---
"
```

## Response snapshot

I have updated the file `/skills/planner.md`.

## Outcome

- ✅ Impact: The `planner.md` skill file has been updated with the agentic version.
- 🧪 Tests: No tests were run for this file update.
- 📁 Files: One file modified: `/skills/planner.md`.
- 🔁 Next prompts: Continue with project development based on the updated `planner` skill.
- 🧠 Reflection: Direct file update using `Write` tool was successful. PHR created for documentation.

## Evaluation notes (flywheel)

- Failure modes observed: None.
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
