---
id: 1
title: Update project constitution for hackathon requirements
stage: constitution
date: 2025-12-12
surface: agent
model: claude-sonnet-4-5
feature: none
branch: 001-ros-nervous-system
user: system
command: /sp.constitution
labels: ["constitution", "hackathon", "setup", "governance"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - .specify/memory/constitution.md
tests:
 - None (documentation update)
---

## Prompt

Hackathon I: Create a Textbook for Teaching Physical AI & Humanoid Robotics Course
The future of work will be a partnership between people, intelligent agents (AI software), and robots. This shift won't necessarily eliminate jobs but will change what humans do, leading to a massive demand for new skills. We have already written a book on AI agents. Therefore, we want you to write a textbook to teach a course in Physical AI & Humanoid Robotics (The course details are documented below).

Excel in the Hackathon and Launch Your Journey as an AI Startup Founder 🚀
We've recently launched Panaversity (panaversity.org), an initiative focused on teaching cutting-edge AI courses. Alongside this, we're working on publishing our first book, which you can explore at ai-native.panaversity.org. Our next milestone is to build a portal where authors can create AI-native technical textbooks, and readers can easily access and learn from them using AI Agents. We also plan to publish O/A Level, Science, Engineering, and Medical AI-native books to support students and professionals across disciplines. If you perform well in this hackathon, you may be invited for an interview to join the Panaversity core team and potentially step into the role of a startup founder within this growing ecosystem. You will get a chance to work with Panaversity founders Zia, Rehan, Junaid, and Wania and become the very best. You may also get a chance to teach at Panaversity, PIAIC, and GIAIC.

Requirements

You are required to complete a unified book project using Claude Code and Spec-Kit Plus. The core deliverables are:

1. AI/Spec-Driven Book Creation: Write a book using Docusaurus and deploy it to GitHub Pages. You will use Spec-Kit Plus ( https://github.com/panaversity/spec-kit-plus/ ) and Claude Code ( https://www.claude.com/product/claude-code ) to write the book.

2. Integrated RAG Chatbot Development: Build and embed a Retrieval-Augmented Generation (RAG) chatbot within the published book. This chatbot, utilizing the OpenAI Agents/ChatKit SDKs, FastAPI, Neon Serverless Postgres database, and Qdrant Cloud Free Tier, must be able to answer user questions about the book's content, including answering questions based only on text selected by the user.

3. Participants will receive points out of 100, for base functionality defined above.

4. Participants can earn up to 50 extra bonus points by creating and using reusable intelligence via Claude Code Subagents and Agent Skills in the book project.

5. Participants can receive up to 50 extra bonus points if they also implement Signup and Signin using https://www.better-auth.com/ At signup you will ask questions from the user about their software and hardware background. Knowing the background of the user we will be able to personalize the content.

6.  Participants can receive up to 50 extra bonus points if the logged user can personalise the content in the chapters by pressing a button at the start of each chapter.

7. Participants can receive up to 50 extra bonus points if the logged user can translate the content in Urdu in the chapters by pressing a button at the start of each chapter.

[Full hackathon requirements document including course details, hardware requirements, and project blueprint - see complete input in command args]

## Response snapshot

Created comprehensive project constitution v1.0.0 defining 7 core principles for the Physical AI & Humanoid Robotics textbook hackathon project:

**Core Principles Established:**
1. **Spec-Driven Development (SDD)**: Mandatory Constitution → Spec → Plan → Tasks → Implementation workflow
2. **Reusable Intelligence**: All decisions/patterns captured in Docusaurus as dual-purpose documentation (human learning + AI memory)
3. **Agent-First Architecture**: Network of specialized Claude Code agents coordinated via Spec-Kit Plus (95% AI / 5% human)
4. **Independent Testability**: User stories prioritized (P1/P2/P3) and independently deliverable as MVP increments
5. **RAG-Native Learning**: Embedded chatbot (OpenAI Agents + FastAPI + Neon + Qdrant) for interactive learning
6. **Personalization & Accessibility**: Better Auth + user profiling + content personalization + Urdu translation per chapter
7. **Hackathon Scoring Optimization**: Development priorities aligned with point allocation (base 100pts + up to 200pts bonus)

**Technology Stack Codified:**
- Frontend: Docusaurus v3.x + React + Tailwind + Better Auth
- Backend: FastAPI (Python 3.11+) + OpenAI Agents SDK + Neon Serverless Postgres + Qdrant Cloud
- Development: Claude Code CLI + Spec-Kit Plus + MCP servers
- Constraints: API keys in `.env`, Qdrant 1GB limit, Neon 0.5GB limit, 90-second demo video

**5-Phase Development Workflow:**
1. Specification (/sp.specify + /sp.clarify)
2. Planning (/sp.plan + /sp.adr for significant decisions)
3. Task Generation (/sp.tasks with user story priorities)
4. Implementation (/sp.implement + /sp.phr for documentation)
5. Review & Deployment (/sp.analyze + /sp.git.commit_pr)

**Quality Gates Defined:**
- Specification Gate: User stories with acceptance criteria, numbered functional requirements
- Planning Gate: Constitution check, no ambiguities, API contracts defined
- Task Gate: User story organization, explicit dependencies, parallel markers
- Implementation Gate: Independent testability, no hardcoded secrets, PHR documentation
- Deployment Gate: Base functionality + optional bonuses, demo video, public repo

## Outcome

- ✅ Impact: Constitution v1.0.0 ratified (2025-12-12) - establishes governance for entire hackathon project
- 🧪 Tests: None (governance documentation)
- 📁 Files: Created `.specify/memory/constitution.md` (179 lines)
- 🔁 Next prompts: Run `/sp.specify` to create first feature spec (likely "docusaurus-book-setup" or "rag-chatbot-integration")
- 🧠 Reflection: Constitution directly maps hackathon scoring rubric to development principles, ensuring all high-value features (reusable intelligence, auth, personalization, translation) are architecturally mandated rather than optional add-ons.

## Evaluation notes (flywheel)

- Failure modes observed: Initial template had 6 principle slots; hackathon requires 7 distinct principles to cover all bonus point categories - template flexibility successfully accommodated expansion
- Graders run and results (PASS/FAIL): PASS - All placeholders filled, version 1.0.0 justified (initial constitution = MINOR), dates ISO format, principles declarative with rationales
- Prompt variant (if applicable): constitution-v1-hackathon-aligned
- Next experiment (smallest change to try): After first feature implementation, verify Constitution Check in `/sp.plan` correctly references these 7 principles and identifies violations (e.g., Qdrant storage limits)
