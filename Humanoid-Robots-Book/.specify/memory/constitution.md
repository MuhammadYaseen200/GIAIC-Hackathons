<!--
SYNC IMPACT REPORT
Version Change: N/A → 1.0.0
Modified Principles: N/A (Initial constitution)
Added Sections:
  - Core Principles (7 principles)
  - Technology Stack Requirements
  - Development Workflow
  - Quality Gates
  - Governance
Removed Sections: None
Templates Requiring Updates:
  ✅ plan-template.md - Constitution Check section will reference these principles
  ✅ spec-template.md - User stories align with reusable intelligence principle
  ✅ tasks-template.md - Task organization reflects spec-driven development
Follow-up TODOs: None - all placeholders filled
-->

# Physical AI & Humanoid Robotics Textbook Constitution

## Core Principles

### I. Spec-Driven Development (SDD)

Every feature MUST follow the Constitution → Specification → Planning → Tasks → Implementation → Documentation workflow. No implementation begins without an approved specification. All work MUST be traceable to a spec document in `specs/<feature-name>/`.

**Rationale**: Prevents scope drift, ensures clarity before coding, and creates reusable documentation for future agents and human learners.

### II. Reusable Intelligence

Every design decision, solution pattern, and lesson learned MUST be captured in Docusaurus markdown under `/docs`. This documentation serves dual purposes: (1) educational content for learners, (2) long-term memory for AI agents. Before solving any problem, agents MUST query existing documentation to avoid redundant work.

**Rationale**: Creates a flywheel where the project becomes smarter over time. Documentation is not an afterthought but the primary knowledge base that powers both human learning and AI agent effectiveness.

### III. Agent-First Architecture

The system MUST be designed as a network of specialized Claude Code agents coordinated through slash commands and skills. Each agent has a clearly defined role (Writer, Planner, Implementer, QA, etc.) and operates through the Spec-Kit Plus workflow. Human involvement is reserved for strategic decisions, clarifications, and approvals.

**Rationale**: Enables 95% AI execution / 5% human oversight ratio. Agents working with predefined skills and specifications produce consistent, high-quality output faster than manual development.

### IV. Independent Testability

Every user story in specifications MUST be independently testable and deliverable as a viable MVP increment. Features are prioritized (P1, P2, P3...) and each can be developed, tested, and deployed without dependencies on lower-priority stories.

**Rationale**: Enables incremental delivery, parallel development by multiple agents, and early validation of core functionality. If only User Story 1 is implemented, the system should still provide tangible value.

### V. RAG-Native Learning Experience

The textbook MUST embed a RAG chatbot powered by OpenAI Agents/ChatKit SDK, FastAPI, Neon Serverless Postgres, and Qdrant Cloud. The chatbot MUST answer questions about full-chapter content AND user-selected text snippets. All book content MUST be ingested into vector embeddings for semantic retrieval.

**Rationale**: Transforms passive reading into interactive learning. Students can query concepts, get clarifications on complex topics (ROS 2, Isaac Sim, humanoid kinematics), and receive personalized explanations based on their background.

### VI. Personalization & Accessibility

The system MUST implement Better Auth for signup/signin and collect user background (software/hardware experience) at registration. Logged-in users MUST be able to: (1) personalize content difficulty per chapter via button, (2) translate content to Urdu per chapter via button. Personalization adjusts technical depth based on user profile.

**Rationale**: Accommodates diverse learner backgrounds (beginners to advanced). Urdu translation supports Pakistan-based Panaversity students. Personalization ensures content matches skill level, preventing frustration or boredom.

### VII. Hackathon Scoring Optimization

Development priorities MUST align with hackathon point allocation: (1) Base book + RAG chatbot = 100 points, (2) Reusable intelligence via subagents/skills = +50 bonus, (3) Better Auth + background collection = +50 bonus, (4) Content personalization = +50 bonus, (5) Urdu translation = +50 bonus. Maximum achievable score: 300 points.

**Rationale**: Focuses effort on high-value features. Base functionality ensures qualification; bonus features demonstrate advanced capabilities that differentiate top submissions and showcase industrial-grade agent workflows.

## Technology Stack Requirements

**Frontend**: Docusaurus v3.x for book hosting, React.js + Tailwind CSS for interactive components, Better Auth for authentication.

**Backend**: FastAPI (Python 3.11+) for RAG API, OpenAI Agents SDK / ChatKit SDK for conversational AI, Neon Serverless Postgres for user data and chat history, Qdrant Cloud (Free Tier) for vector embeddings.

**Deployment**: GitHub Pages or Vercel for static site, FastAPI backend on cloud provider with Neon/Qdrant integration.

**Development Tools**: Claude Code CLI as primary orchestrator, Spec-Kit Plus for SDD workflow, MCP servers (Context-7, File System, GitHub, Knowledge Base) for agent capabilities.

**AI Models**: Claude Sonnet 4.5 for spec/plan/task generation, OpenAI GPT-4 for chatbot and content personalization, OpenAI Whisper (referenced in course material, not implemented in book directly).

**Constraints**:
- All API keys stored in `.env` (never committed)
- Qdrant limited to 1GB free tier - chunk strategy required
- Neon Serverless Postgres 0.5GB free tier - efficient schema design mandatory
- Demo video MUST be under 90 seconds for hackathon submission

## Development Workflow

### Phase 1: Specification
1. Run `/sp.specify "<feature-description>"` to generate `specs/<feature>/spec.md`
2. Review user stories, acceptance criteria, and functional requirements
3. Run `/sp.clarify` if requirements are ambiguous
4. Obtain human approval before proceeding

### Phase 2: Planning
1. Run `/sp.plan` to generate `specs/<feature>/plan.md` with technical architecture
2. Verify Constitution Check passes or document complexity justifications
3. Generate data models, API contracts, and project structure
4. Run `/sp.adr` for architecturally significant decisions (e.g., RAG architecture, auth strategy)
5. Obtain human approval before proceeding

### Phase 3: Task Generation
1. Run `/sp.tasks` to generate `specs/<feature>/tasks.md` from approved plan
2. Tasks MUST be organized by user story with priority labels (P1, P2, P3)
3. Each task includes exact file paths and dependency markers `[P]` for parallel execution
4. Foundational tasks (database, auth, base models) MUST be in Phase 2 - blocking all user stories

### Phase 4: Implementation
1. Run `/sp.implement` to execute tasks from `tasks.md`
2. Agents work in priority order: Setup → Foundational → User Story 1 → User Story 2...
3. After each user story phase, validate independent functionality
4. Commit incrementally with PHR documentation via `/sp.phr`

### Phase 5: Review & Deployment
1. Run `/sp.analyze` for cross-artifact consistency check (spec, plan, tasks)
2. Run `/sp.git.commit_pr` to commit changes and create pull request
3. Deploy to GitHub Pages/Vercel
4. Generate demo video (under 90 seconds) showing: (a) book navigation, (b) RAG chatbot interaction, (c) personalization/translation features

## Quality Gates

### Specification Gate (Before Planning)
- [ ] All user stories have acceptance criteria in Given/When/Then format
- [ ] Each user story marked with priority (P1, P2, P3...)
- [ ] Functional requirements numbered (FR-001, FR-002...) and testable
- [ ] Success criteria measurable and technology-agnostic
- [ ] Edge cases documented

### Planning Gate (Before Task Generation)
- [ ] Constitution Check completed - all violations justified
- [ ] Technical context fully specified (no `NEEDS CLARIFICATION`)
- [ ] Project structure selected and documented
- [ ] API contracts defined in `contracts/` folder
- [ ] Data model documented with entities and relationships
- [ ] Quickstart instructions drafted for developers

### Task Gate (Before Implementation)
- [ ] Tasks organized by user story with phase labels
- [ ] Foundational phase clearly marked as blocking
- [ ] Dependencies explicit (no hidden prerequisites)
- [ ] Parallel opportunities marked with `[P]`
- [ ] Each task includes exact file path

### Implementation Gate (Per User Story)
- [ ] User story independently testable and demonstrates value
- [ ] Code follows project structure from plan.md
- [ ] Errors logged, sensitive data protected (no secrets in code)
- [ ] Changes committed with descriptive message and PHR
- [ ] Documentation updated in `/docs` (Reusable Intelligence)

### Deployment Gate (Final)
- [ ] Base functionality: Book deployed, RAG chatbot functional
- [ ] RAG chatbot answers questions on full chapters AND selected text
- [ ] Better Auth implemented with user background collection (if bonus pursued)
- [ ] Personalization per chapter functional (if bonus pursued)
- [ ] Urdu translation per chapter functional (if bonus pursued)
- [ ] Demo video under 90 seconds
- [ ] GitHub repo public with clear README
- [ ] All secrets in `.env.example` (not `.env`)

## Governance

This constitution supersedes all other development practices and style guides. All agents, slash commands, and human contributors MUST verify compliance with these principles before completing work.

### Amendment Procedure
1. Proposed changes documented in new spec under `specs/constitution-update/`
2. Run `/sp.constitution` with updated requirements
3. Version incremented per semantic versioning:
   - **MAJOR**: Backward-incompatible principle removals or redefinitions
   - **MINOR**: New principle added or materially expanded guidance
   - **PATCH**: Clarifications, wording fixes, non-semantic refinements
4. All dependent templates (plan, spec, tasks, command files) updated for consistency
5. Changes merged only after human approval

### Compliance Review
- Every `/sp.plan` execution MUST include Constitution Check section
- Every `/sp.analyze` execution verifies spec/plan/tasks alignment with constitution
- Complexity violations (e.g., exceeding Qdrant free tier, overly complex architecture) MUST be justified in Complexity Tracking table

### Conflict Resolution
If constitution conflicts with external requirements (hackathon rules, API limitations, deployment constraints), constitution takes precedence unless explicitly amended. Document conflicts as ADRs using `/sp.adr`.

**Version**: 1.0.0 | **Ratified**: 2025-12-12 | **Last Amended**: 2025-12-12
