# Feature Specification: RAG Chatbot (Physical AI Tutor)

**Feature Branch**: `002-rag-chatbot`
**Created**: 2025-12-13
**Status**: Draft
**Input**: User description: "Create the RAG Chatbot Architecture. Context: We need a 'Physical AI Tutor' chatbot. Assign the Backend work to @Backend-Engineer and Frontend work to @Frontend-Architect. Requirements: Frontend: A React component (`<ChatWidget />`) integrated into Docusaurus. Backend: FastAPI service (`backend/src/api.py`) connecting to Qdrant. Data: Ingestion script for markdown files."

## User Scenarios & Testing

### User Story 1 - Ask Questions About Current Chapter (Priority: P1)

A student reading Chapter 3 about ROS 2 Topics can click the chat widget, ask "How do I create a subscriber?", and receive an answer with code examples extracted from that chapter plus citations.

**Why this priority**: This is the core MVP—enabling contextual help without leaving the page. Delivers immediate value and proves the RAG pipeline works end-to-end.

**Independent Test**: Open Chapter 3, click chat widget, type "What is a subscriber?", verify response contains relevant code from Chapter 3 with citation link.

**Acceptance Scenarios**:

1. **Given** a student is on Chapter 3 (Topics & Services), **When** they ask "Show me subscriber code", **Then** the chatbot returns the `CameraSubscriber` class from Chapter 3 with a link to that section
2. **Given** a student asks "What message types can I subscribe to?", **When** the chatbot retrieves content, **Then** it responds with `sensor_msgs/Image`, `std_msgs/String`, etc. from Module 1 chapters
3. **Given** a student clicks a citation link in the response, **When** the link is clicked, **Then** the browser navigates to the exact chapter section

---

### User Story 2 - Multi-Chapter Knowledge Synthesis (Priority: P2)

Students can ask questions that require synthesizing information from multiple chapters (e.g., "How do I simulate a robot?"), and the chatbot combines knowledge from URDF (Chapter 6) + Gazebo (Chapter 7).

**Why this priority**: Demonstrates advanced RAG capability (retrieval from multiple sources). Helps students connect concepts across modules.

**Independent Test**: Ask "What's the full workflow from URDF to Gazebo?", verify response mentions both Chapter 6 (URDF creation) and Chapter 7 (Gazebo launch).

**Acceptance Scenarios**:

1. **Given** a student asks "How do I go from URDF to simulation?", **When** the chatbot searches all chapters, **Then** it synthesizes steps from Chapters 4, 6, and 7 with citations
2. **Given** a student asks "What hardware do I need for this book?", **When** the chatbot aggregates hardware requirements, **Then** it lists laptop (Modules 1-2), RTX 4070 Ti (Module 3), Jetson Orin (deployment)

---

### User Story 3 - Conversation Memory (Priority: P3)

The chatbot remembers previous messages in the session, allowing follow-up questions like "Show me code for that" without re-stating context.

**Why this priority**: Enhances UX but not critical for MVP. Natural conversations require session memory.

**Independent Test**: Ask "What is URDF?", then ask "Show me an example", verify the chatbot provides URDF XML without needing to repeat the topic.

**Acceptance Scenarios**:

1. **Given** a student asks "What is a ROS 2 node?" and receives an answer, **When** they ask "Can you show code?", **Then** the chatbot provides a node example from Chapter 2 without confusion
2. **Given** a 5-message conversation about digital twins, **When** the student asks "How do I deploy this?", **Then** the chatbot understands "this" refers to digital twins and provides sim-to-real deployment steps

---

### User Story 4 - Citation Links (Priority: P1)

Every chatbot response includes clickable markdown links to source chapters, enabling students to verify information and read full context.

**Why this priority**: Critical for educational integrity. Students must be able to trace answers back to authoritative sources.

**Independent Test**: Ask any question, verify response includes links like `[Chapter 2: Speaking Python](../module-1-ros2-basics/chapter-2-pub-sub.md)` that navigate correctly.

**Acceptance Scenarios**:

1. **Given** the chatbot cites Chapter 1 in its response, **When** the student clicks the citation, **Then** the browser navigates to `docs/module-1-ros2-basics/chapter-1-intro.md`
2. **Given** the chatbot cites multiple chapters, **When** each link is clicked, **Then** all links navigate to the correct chapter files

---

### Edge Cases

- **What happens when a student asks about content not in the textbook?** Chatbot responds: "I can only answer questions based on the Physical AI & Humanoid Robotics textbook (Modules 1-4). Your question about [topic] isn't covered. Try asking about ROS 2, Digital Twins, Isaac Sim, or VLA models."

- **How does the system handle very broad questions like "Teach me robotics"?** Chatbot requests clarification: "The textbook has 4 modules. Which topic interests you? 1) ROS 2 Basics, 2) Digital Twins, 3) Isaac Sim, 4) VLA Models. Or ask a specific question."

- **What happens if Qdrant vector database is unreachable?** Display error: "The chatbot is temporarily unavailable. Please refresh the page or try again later."

- **How does the system handle questions with typos (e.g., "What is urdff")?** Use fuzzy matching on vector search to retrieve URDF-related content despite typo, then respond with corrected spelling: "I think you meant 'URDF'. Here's information about Unified Robot Description Format..."

- **What happens when a student sends empty messages or only emojis?** Chatbot responds: "Please ask a question about the textbook content (e.g., 'How do I create a ROS 2 node?')."

## Requirements

### Functional Requirements

- **FR-001**: System MUST display a floating chat widget button on all Docusaurus pages (bottom-right corner)
- **FR-002**: Chat widget MUST open/close on button click without page reload
- **FR-003**: Students MUST be able to type natural language questions up to 500 words
- **FR-004**: System MUST retrieve top-5 most relevant text chunks from Qdrant using cosine similarity (threshold ≥ 0.7)
- **FR-005**: System MUST generate responses using Google Gemini 1.5 Flash with retrieved chunks as context
- **FR-006**: Every response MUST include clickable citation links to source chapters
- **FR-007**: System MUST maintain conversation history for the duration of the browser session
- **FR-008**: System MUST clear conversation history when the chat widget is closed or page is refreshed
- **FR-009**: Chat widget MUST show loading spinner while waiting for responses
- **FR-010**: System MUST display error messages for network failures, rate limits, or service unavailability
- **FR-011**: Backend MUST provide a POST `/api/chat` endpoint accepting `{message: string, history: array}`
- **FR-012**: Backend MUST return responses in format `{response: string, sources: [{title: string, url: string, chapter_id: string}]}`
- **FR-013**: System MUST parse all Markdown files in `/docs` directory during ingestion
- **FR-014**: Ingestion script MUST chunk content into 512-token segments with 50-token overlap (per ADR-003)
- **FR-015**: Each chunk MUST be converted to 768-dim vector using Google Gemini `text-embedding-004`
- **FR-016**: Chunks MUST be uploaded to Qdrant with metadata: `{chapter_id, module_id, title, section, file_path}`
- **FR-017**: System MUST rate-limit to 10 queries per minute per IP address to prevent API abuse
- **FR-018**: System MUST log all queries (question, response, tokens_used, timestamp) to Neon Postgres for analytics
- **FR-019**: Chat UI MUST support markdown rendering in responses (code blocks, lists, tables, bold/italic)
- **FR-020**: System MUST provide a "Copy" button for code snippets in chatbot responses

### Key Entities

- **ChatMessage**: Represents a single message (role: "user" | "assistant", content: string, timestamp: Date, sources: Citation[])
- **ChatSession**: Represents a conversation thread (session_id: UUID, messages: ChatMessage[], started_at: Date, chapter_context: string optional)
- **VectorChunk**: Textbook content segment (chunk_id: string, text: 512 tokens, embedding: float[768], metadata: {chapter_id, module_id, title, section, file_path})
- **Citation**: Source reference (title: string, url: string, chapter_id: string)
- **QueryLog**: Analytics record (query_id: UUID, question: string, answer: string, tokens_used: number, response_time_ms: number, session_id: UUID, timestamp: Date)

## Success Criteria

### Measurable Outcomes

- **SC-001**: Students can ask a question and receive a relevant answer in under 3 seconds (95th percentile)
- **SC-002**: Chatbot provides factually accurate answers for 90%+ of questions about topics covered in the textbook
- **SC-003**: Citation links navigate correctly to source chapters 100% of the time
- **SC-004**: System retrieves relevant content for 85%+ of questions about textbook topics
- **SC-005**: Students rate chatbot responses as "helpful" or "very helpful" in 80%+ of cases
- **SC-006**: Follow-up questions work correctly (chatbot remembers context) in 95%+ of conversations
- **SC-007**: System handles 100 concurrent users without response time degradation (stays under 5 seconds)
- **SC-008**: Markdown ingestion completes for all 13 chapters in under 10 minutes
- **SC-009**: Chatbot correctly identifies out-of-scope questions 95%+ of the time
- **SC-010**: Zero XSS or injection vulnerabilities after security testing

### Assumptions

- All textbook chapters are in Markdown format in `/docs` directory with consistent frontmatter
- Google Gemini API key has sufficient quota for embeddings (text-embedding-004) and chat (gemini-1.5-flash)
- Qdrant Cloud free tier (1GB) is sufficient for ~65 chunks × 4.5KB = 293KB storage
- Students use modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- Chat widget does not need to persist conversations across browser sessions (no user accounts for MVP)
- Backend FastAPI service is deployed with HTTPS on Railway or similar platform
- Frontend is deployed on GitHub Pages (static site)
- Conversation history is client-side only (stored in React state, not database)
- Chatbot responses are in English only (Urdu translation is a separate P5 feature)
- Chat UI follows Docusaurus default theme colors and typography

### Out of Scope

- Voice input/output (text-only for MVP)
- Multi-language support beyond English (Urdu is separate feature)
- User authentication (chatbot works for anonymous users)
- Persistent conversation history across sessions
- Custom LLM training (uses pre-trained OpenAI models)
- Real-time collaboration (multiple users in same chat)
- Mobile app (responsive web only)
- Offline mode (requires internet)
- Fine-tuning on textbook content (RAG retrieval only)

### Dependencies

- **Google Gemini API**: For embeddings and chat completions
- **Qdrant Cloud**: Vector database (free tier 1GB)
- **Docusaurus 3.x**: Already installed
- **FastAPI**: Already scaffolded in `backend/src/main.py`
- **Neon Postgres**: For query logs (schema already exists in `backend/db/migrations/001_initial_schema.sql`)
- **GitHub Pages**: Frontend deployment
- **Railway**: Backend deployment

### Constraints

- **Cost**: Must operate within $10/month budget (Google Gemini + Qdrant free tiers)
- **Storage**: Qdrant limited to 1GB (sufficient per ADR-003 calculations - 293KB used)
- **Latency**: Google Gemini API adds 1-3 seconds per request (unavoidable)
- **Rate Limits**: Google Gemini free tier limits requests/minute (implement throttling)
- **CORS**: Backend must allow requests from GitHub Pages domain

### Agent Assignments

- **@Backend-Engineer** (using `skills/fastapi-coder.md`):
  - Create `/api/chat` POST endpoint in `backend/src/chat/routes.py`
  - Implement Qdrant vector search integration
  - Implement Google Gemini 1.5 Flash integration for response generation
  - Add query logging to Neon Postgres
  - Implement rate limiting middleware
  - Write ingestion script (`backend/scripts/ingest_docs.py`)

- **@Frontend-Architect** (using `skills/react-component.md`):
  - Create `<ChatWidget />` React component in `src/components/ChatWidget/`
  - Swizzle Docusaurus layout to embed chat widget globally
  - Implement chat UI with Tailwind CSS styling
  - Add markdown rendering for responses
  - Implement session management (client-side state)
  - Add accessibility (ARIA labels, keyboard navigation)

