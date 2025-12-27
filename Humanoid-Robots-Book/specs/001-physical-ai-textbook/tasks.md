---
description: "Task list for Physical AI & Humanoid Robotics Interactive Textbook"
---

# Tasks: Physical AI & Humanoid Robotics Interactive Textbook

**Input**: Design documents from `/specs/001-physical-ai-textbook/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are OPTIONAL for this feature (not explicitly requested in specification)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Hybrid project**: Frontend `docs/`, `src/` at repository root; Backend `backend/src/`
- **Agent infrastructure**: `skills/`, `agents/` at repository root
- Paths shown below follow hybrid architecture per plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure per implementation plan (frontend root, backend/, skills/, agents/)
- [x] T002 Initialize Node.js project with Docusaurus 3.x dependencies in package.json
- [x] T003 [P] Initialize Python project with FastAPI dependencies in backend/requirements.txt
- [x] T004 [P] Create .env.example file at repository root with API key placeholders
- [ ] T005 [P] Configure linting and formatting tools (ESLint for TypeScript, Black for Python)
- [ ] T006 [P] Setup GitHub Actions CI/CD workflow in .github/workflows/ci.yml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create Docusaurus configuration in docusaurus.config.js with site metadata and GitHub Pages deployment
- [ ] T008 Create sidebar navigation structure in sidebars.js for 4 modules
- [ ] T009 [P] Setup Neon Serverless Postgres database schema in backend/src/db/migrations/001_initial_schema.sql
- [ ] T010 [P] Implement Neon database connection client in backend/src/db/neon_client.py with async connection pooling
- [ ] T011 [P] Setup Qdrant Cloud collection in backend/src/db/qdrant_setup.py with 1536-dim vectors and metadata schema
- [ ] T012 [P] Implement FastAPI application entry point in backend/src/main.py with CORS middleware
- [ ] T013 [P] Create environment configuration loader in backend/src/config.py for API keys and database URLs
- [ ] T014 [P] Setup Alembic for database migrations in backend/src/db/migrations/

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Browse Core Technical Content (Priority: P1) 🎯 MVP

**Goal**: Deploy static Docusaurus site with 13+ chapters covering 4 modules (ROS 2, Gazebo, Isaac, VLA)

**Independent Test**: Visit deployed site, navigate through all 13 chapters, verify mobile responsiveness and search functionality

### Implementation for User Story 1

- [ ] T015 [P] [US1] Create landing page content in docs/intro.md with course overview and module links
- [ ] T016 [P] [US1] Create Module 1 directory structure docs/module1-ros2/ with week3, week4, week5 markdown files
- [ ] T017 [P] [US1] Create Module 2 directory structure docs/module2-digital-twin/ with week6, week7 markdown files
- [ ] T018 [P] [US1] Create Module 3 directory structure docs/module3-isaac/ with week8, week9, week10 markdown files
- [ ] T019 [P] [US1] Create Module 4 directory structure docs/module4-vla/ with week11, week12, week13 markdown files
- [ ] T020 [US1] Generate Week 3 content in docs/module1-ros2/week3-nodes.md covering ROS 2 Nodes and Topics (1500+ words, code examples)
- [ ] T021 [US1] Generate Week 4 content in docs/module1-ros2/week4-topics-services.md covering Topics vs Services (1500+ words)
- [ ] T022 [US1] Generate Week 5 content in docs/module1-ros2/week5-urdf.md covering URDF format for humanoids (1500+ words)
- [ ] T023 [US1] Generate Week 6 content in docs/module2-digital-twin/week6-gazebo.md covering Gazebo simulation (1500+ words)
- [ ] T024 [US1] Generate Week 7 content in docs/module2-digital-twin/week7-unity.md covering Unity rendering (1500+ words)
- [ ] T025 [US1] Generate Week 8 content in docs/module3-isaac/week8-isaac-sim.md covering NVIDIA Isaac Sim (1500+ words)
- [ ] T026 [US1] Generate Week 9 content in docs/module3-isaac/week9-isaac-ros.md covering Isaac ROS integration (1500+ words)
- [ ] T027 [US1] Generate Week 10 content in docs/module3-isaac/week10-nav2.md covering Nav2 path planning (1500+ words)
- [ ] T028 [US1] Generate Week 11 content in docs/module4-vla/week11-humanoid-kinematics.md covering bipedal locomotion (1500+ words)
- [ ] T029 [US1] Generate Week 12 content in docs/module4-vla/week12-manipulation.md covering humanoid grasping (1500+ words)
- [ ] T030 [US1] Generate Week 13 content in docs/module4-vla/week13-conversational.md covering GPT integration (1500+ words)
- [ ] T031 [US1] Add code examples and diagrams to all 13 chapters (minimum 2 code blocks per chapter)
- [ ] T032 [US1] Configure Docusaurus search plugin in docusaurus.config.js (local search or Algolia)
- [ ] T033 [US1] Create custom homepage React component in src/pages/index.tsx with hero section and module cards
- [ ] T034 [US1] Setup Tailwind CSS configuration in src/css/custom.css for styling
- [ ] T035 [US1] Test mobile responsiveness for all chapters on Chrome/Firefox/Safari mobile browsers
- [ ] T036 [US1] Deploy static site to GitHub Pages using npm run deploy command
- [ ] T037 [US1] Verify all chapter navigation links work correctly (previous/next buttons)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (MVP complete, base 50 points)

---

## Phase 4: User Story 2 - Interactive RAG Chatbot (Priority: P2)

**Goal**: Embed functional RAG chatbot widget on every chapter page with Qdrant retrieval

**Independent Test**: Open any chapter, ask "How do ROS 2 topics work?", verify chatbot retrieves context and answers within 10 seconds

### Implementation for User Story 2

- [ ] T038 [P] [US2] Implement text chunking script in backend/scripts/chunk_chapters.py using 512-token chunks with 50-token overlap
- [ ] T039 [US2] Generate OpenAI embeddings for all 13 chapters and upload to Qdrant collection using backend/scripts/ingest_chapters.py
- [ ] T040 [P] [US2] Create ChatSession model in backend/src/chat/models.py with SQLAlchemy ORM (session_id, user_id, chapter_context)
- [ ] T041 [P] [US2] Create Message model in backend/src/chat/models.py (message_id, session_id, role, content, retrieved_chunks)
- [ ] T042 [US2] Implement RAG engine in backend/src/chat/rag_engine.py with Qdrant semantic search (top 5 chunks, score threshold 0.7)
- [ ] T043 [US2] Implement /chat POST endpoint in backend/src/chat/routes.py with question, session_id, chapter_context parameters
- [ ] T044 [US2] Integrate OpenAI GPT-4 completion in backend/src/chat/rag_engine.py to generate answers from retrieved chunks
- [ ] T045 [US2] Implement chat history storage in Neon database within /chat endpoint
- [ ] T046 [P] [US2] Create ChatbotWidget React component in src/components/ChatbotWidget.tsx with text input and message display
- [ ] T047 [US2] Implement "Ask about selection" feature in ChatbotWidget.tsx using window.getSelection() API
- [ ] T048 [US2] Connect ChatbotWidget to FastAPI /chat endpoint using fetch() with error handling
- [ ] T049 [US2] Embed ChatbotWidget in Docusaurus layout template to appear on every chapter page
- [ ] T050 [US2] Implement out-of-scope question handling in backend/src/chat/rag_engine.py (detect low similarity scores)
- [ ] T051 [US2] Add citation display in ChatbotWidget.tsx showing chapter_id and heading from retrieved chunks
- [ ] T052 [US2] Test chatbot with 10 ground-truth Q&A pairs and verify 90% accuracy
- [ ] T053 [US2] Verify chatbot response time is under 10 seconds for 50 concurrent users using k6 load test

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (base 100 points complete)

---

## Phase 5: User Story 5 - Reusable Intelligence via Subagents (Priority: P5)

**Goal**: Document agent skills library and demonstrate agentic workflow in demo video

**Independent Test**: Judges inspect /skills directory, agents/definitions.yaml, and history/prompts/ to verify 5+ skills and PHRs

**Note**: This phase moved before US3/US4 because skills infrastructure supports content generation workflow

### Implementation for User Story 5

- [ ] T054 [P] [US5] Create generate-chapter skill documentation in skills/generate-chapter.md with purpose, inputs, outputs, example usage
- [ ] T055 [P] [US5] Create create-rag-embedding skill documentation in skills/create-rag-embedding.md
- [ ] T056 [P] [US5] Create review-content skill documentation in skills/review-content.md for QA agent
- [ ] T057 [P] [US5] Create personalize-content skill documentation in skills/personalize-content.md
- [ ] T058 [P] [US5] Create translate-to-urdu skill documentation in skills/translate-to-urdu.md
- [ ] T059 [US5] Create agents/definitions.yaml file defining Writer Agent, RAG Indexer Agent, QA Agent, Personalizer Agent, Translator Agent with role descriptions and skill mappings
- [ ] T060 [US5] Verify at least 10 PHR files exist in history/prompts/001-physical-ai-textbook/ documenting spec, plan, tasks, and implementation decisions
- [ ] T061 [US5] Record 20-second demo video segment showing agent generating new chapter autonomously using /sp.specify workflow
- [ ] T062 [US5] Add README.md section explaining agent skills and reusable intelligence architecture for judges

**Checkpoint**: Agent skills documented, demo video recorded (+50 bonus points)

---

## Phase 6: User Story 3 - Personalized Learning Experience (Priority: P3)

**Goal**: Implement Better Auth signup with background questionnaire and per-chapter personalization

**Independent Test**: Create beginner and advanced accounts, personalize same chapter, verify distinct content variations

### Implementation for User Story 3

- [ ] T063 [P] [US3] Create User model in backend/src/auth/models.py with SQLAlchemy ORM (user_id, email, hashed_password, software_level, hardware_level, robotics_background)
- [ ] T064 [P] [US3] Implement password hashing utility in backend/src/auth/utils.py using bcrypt
- [ ] T065 [US3] Implement /auth/signup POST endpoint in backend/src/auth/routes.py with email, password, profile fields validation
- [ ] T066 [US3] Implement /auth/signin POST endpoint in backend/src/auth/routes.py with JWT token generation
- [ ] T067 [US3] Implement JWT authentication middleware in backend/src/auth/middleware.py for protected endpoints
- [ ] T068 [P] [US3] Create AuthModal React component in src/components/AuthModal.tsx with signup and signin forms using Better Auth UI components
- [ ] T069 [US3] Integrate Better Auth form validation in AuthModal.tsx (email format, password strength)
- [ ] T070 [US3] Connect AuthModal to FastAPI /auth/signup and /auth/signin endpoints with httpOnly cookie handling
- [ ] T071 [US3] Implement user profile context in React using Context API to store authentication state globally
- [ ] T072 [US3] Create prompt templates in backend/src/personalize/prompt_builder.py for beginner, intermediate, advanced skill levels
- [ ] T073 [US3] Implement /personalize POST endpoint in backend/src/personalize/routes.py with chapter_id, user_profile parameters (requires JWT auth)
- [ ] T074 [US3] Integrate OpenAI GPT-4 in backend/src/personalize/prompt_builder.py to generate personalized markdown variations
- [ ] T075 [US3] Implement session-based caching in /personalize endpoint with 1-hour TTL to reduce API costs
- [ ] T076 [P] [US3] Create PersonalizeButton React component in src/components/PersonalizeButton.tsx visible only to logged-in users
- [ ] T077 [US3] Connect PersonalizeButton to FastAPI /personalize endpoint and replace chapter content dynamically
- [ ] T078 [US3] Implement per-chapter personalization reset (navigating away reverts to default content)
- [ ] T079 [US3] Test with beginner profile: verify content is 30% longer with simplified vocabulary using readability scores
- [ ] T080 [US3] Test with advanced profile: verify content is condensed with source code references
- [ ] T081 [US3] Verify anonymous users can read content without signup

**Checkpoint**: Authentication and personalization functional (+50 bonus points, total 150 points)

---

## Phase 7: User Story 4 - Urdu Translation Access (Priority: P4)

**Goal**: One-click Urdu translation preserving code blocks and technical terms

**Independent Test**: Log in, navigate to chapter, click "Translate to Urdu," verify 95% of natural language translated while code preserved

### Implementation for User Story 4

- [ ] T082 [P] [US4] Create translation prompt template in backend/src/translate/urdu_translator.py preserving code blocks, math notation, and acronyms
- [ ] T083 [US4] Implement /translate POST endpoint in backend/src/translate/routes.py with chapter_id, original_content parameters (requires JWT auth)
- [ ] T084 [US4] Integrate OpenAI GPT-4 in backend/src/translate/urdu_translator.py to translate natural language text to Urdu
- [ ] T085 [US4] Implement code block detection and preservation logic in urdu_translator.py using markdown parsing
- [ ] T086 [US4] Implement technical term detection (URDF, VSLAM, etc.) with English preservation and Urdu explanations in parentheses
- [ ] T087 [P] [US4] Create TranslateButton React component in src/components/TranslateButton.tsx with "Translate to Urdu" and "Show Original" toggle
- [ ] T088 [US4] Connect TranslateButton to FastAPI /translate endpoint and replace chapter content with translated version
- [ ] T089 [US4] Implement session-based translation state (translation resets on page reload) in TranslateButton.tsx using React state
- [ ] T090 [US4] Restrict translation feature to logged-in users only (redirect to AuthModal if not authenticated)
- [ ] T091 [US4] Test with 5 randomly selected chapters to verify 95% translation coverage and code preservation
- [ ] T092 [US4] Verify translation completes within 3 seconds for average chapter (1500 words)

**Checkpoint**: Urdu translation functional (+50 bonus points, total 200 points)

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final deployment

- [ ] T093 [P] Install broken-link-checker npm package and create link-check script in package.json
- [ ] T094 [P] Run broken-link-checker on deployed site and fix any broken external links in chapters
- [ ] T095 [P] Create pytest test suite in backend/tests/test_chat.py for RAG accuracy with 10 ground-truth Q&A pairs
- [ ] T096 [P] Create Playwright E2E test in tests/e2e/personalization.spec.ts validating beginner vs advanced content differences
- [ ] T097 [P] Run k6 load test script tests/load/chatbot-load.js to verify 50 concurrent users handled without degradation
- [ ] T098 [P] Optimize Docusaurus bundle size by lazy-loading ChatbotWidget component
- [ ] T099 [P] Run Lighthouse audit on deployed site to verify <3s page load time
- [ ] T100 [P] Create deployment documentation in specs/001-physical-ai-textbook/deployment.md with GitHub Pages and Railway instructions
- [ ] T101 Setup Railway deployment for FastAPI backend with environment variables configuration
- [ ] T102 Deploy FastAPI backend to Railway and verify CORS configuration allows GitHub Pages origin
- [ ] T103 Update frontend ChatbotWidget.tsx to use production backend URL from environment variable
- [ ] T104 Record full demo video (<90 seconds) showing: content browsing, chatbot interaction, personalization, translation, agent workflow
- [ ] T105 Create GitHub repository README.md with project overview, setup instructions, and demo video link
- [ ] T106 Verify all API keys are in .env (not committed) and .env.example template is complete
- [ ] T107 Final QA: Test all 5 user stories end-to-end on production deployment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational (Phase 2) - No dependencies on other stories
  - User Story 2 (P2): Requires User Story 1 content to exist for RAG ingestion (depends on T020-T030)
  - User Story 5 (P5): Can start after Foundational (independent of other stories) - Moved before US3/US4 for workflow clarity
  - User Story 3 (P3): Can start after Foundational (independent of US1/US2)
  - User Story 4 (P4): Requires User Story 3 authentication (depends on T063-T071)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Independently testable as static site
- **User Story 2 (P2)**: Depends on US1 content generation (T020-T030) for RAG ingestion - Independently testable with chatbot widget
- **User Story 5 (P5)**: Can start after Foundational - Independent of all other stories
- **User Story 3 (P3)**: Can start after Foundational - Independent but required for US4
- **User Story 4 (P4)**: Depends on US3 authentication (T063-T071) - Translation requires logged-in users

### Within Each User Story

- **User Story 1**: Content generation (T020-T030) before deployment (T036)
- **User Story 2**: Chunking and ingestion (T038-T039) before RAG engine (T042-T044)
- **User Story 5**: Skills documentation (T054-T058) before agents definition (T059)
- **User Story 3**: Auth models/endpoints (T063-T067) before personalization (T072-T075)
- **User Story 4**: Auth dependency (US3) before translation endpoints (T082-T086)

### Parallel Opportunities

- **Setup phase**: All tasks marked [P] can run in parallel (T002-T006)
- **Foundational phase**: All tasks marked [P] can run in parallel (T009-T014)
- **User Story 1**: Content generation (T015-T019 directory setup, T020-T030 individual chapters) can run in parallel
- **User Story 2**: Models (T040-T041), frontend (T046-T047) can run in parallel after ingestion (T038-T039) completes
- **User Story 5**: All skills documentation (T054-T058) can run in parallel
- **User Story 3**: Auth models (T063-T064), frontend components (T068-T069) can run in parallel
- **User Story 4**: Frontend component (T087) can run in parallel with backend implementation (T082-T086)
- **Polish phase**: Testing (T093-T099), documentation (T100), deployment (T101-T103) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all module directory creation together:
Task: "Create Module 1 directory structure docs/module1-ros2/"
Task: "Create Module 2 directory structure docs/module2-digital-twin/"
Task: "Create Module 3 directory structure docs/module3-isaac/"
Task: "Create Module 4 directory structure docs/module4-vla/"

# Launch all chapter content generation together (after directories exist):
Task: "Generate Week 3 content in docs/module1-ros2/week3-nodes.md"
Task: "Generate Week 4 content in docs/module1-ros2/week4-topics-services.md"
Task: "Generate Week 5 content in docs/module1-ros2/week5-urdf.md"
# ... (all 13 chapters can be generated in parallel)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (static site with 13 chapters)
4. **STOP and VALIDATE**: Deploy to GitHub Pages, verify all chapters navigable, mobile responsive, search works
5. Demo/submit if time-constrained (base 50 points)

### Incremental Delivery (Recommended for Hackathon)

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy (MVP - base 50 points)
3. Add User Story 2 → Test independently → Deploy (base 100 points)
4. Add User Story 5 → Test independently (bonus +50 points, total 150)
5. Add User Story 3 → Test independently (bonus +50 points, total 200)
6. Add User Story 4 → Test independently (bonus +50 points, total 250)
7. Complete Polish phase → Final deployment (total 300 points max)

### Parallel Team Strategy

With multiple developers or agents:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Agent/Developer A: User Story 1 (content generation)
   - Agent/Developer B: User Story 5 (skills documentation)
   - Agent/Developer C: User Story 3 (authentication infrastructure)
3. After US1 completes:
   - Agent/Developer A moves to User Story 2 (RAG chatbot, depends on US1 content)
4. After US3 completes:
   - Agent/Developer C moves to User Story 4 (translation, depends on US3 auth)
5. Polish phase: All agents collaborate on testing, deployment, demo video

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

## Task Count Summary

- **Phase 1 (Setup)**: 6 tasks
- **Phase 2 (Foundational)**: 8 tasks (BLOCKING)
- **Phase 3 (US1 - Browse Content)**: 23 tasks
- **Phase 4 (US2 - RAG Chatbot)**: 16 tasks
- **Phase 5 (US5 - Reusable Intelligence)**: 9 tasks
- **Phase 6 (US3 - Personalization)**: 19 tasks
- **Phase 7 (US4 - Urdu Translation)**: 11 tasks
- **Phase 8 (Polish)**: 15 tasks

**Total**: 107 tasks

**Parallel Opportunities**: 42 tasks marked [P] can run concurrently after dependencies met

**Independent Test Criteria**:
- US1: Static site deployed, 13 chapters navigable, mobile responsive
- US2: Chatbot answers questions within 10s, retrieves context from Qdrant
- US5: 5+ skills documented, agents/definitions.yaml complete, 10+ PHRs exist
- US3: Beginner vs advanced personalization produces distinct content
- US4: Urdu translation preserves code, completes in <3s

**Suggested MVP Scope**: Complete Phases 1-3 (Setup + Foundational + US1) for base 50 points, demonstrable static textbook site.
