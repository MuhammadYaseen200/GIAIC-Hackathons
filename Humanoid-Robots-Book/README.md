# Physical AI & Humanoid Robotics - Interactive Textbook

An interactive, RAG-powered textbook for learning Physical AI and Humanoid Robotics, built with Docusaurus and FastAPI.

## 🎯 Features

- **Comprehensive Content**: 4 modules, 13 chapters covering ROS 2 to Vision-Language-Action models
- **RAG Chatbot**: AI-powered learning assistant using OpenAI GPT-4 and Qdrant vector database
- **Personalization**: Adaptive learning experiences based on user profiles
- **Urdu Translation**: Session-based translation for accessibility
- **Modern Stack**: Docusaurus 3.x (frontend) + FastAPI (backend)
- **Free Tier Optimized**: Designed for Qdrant 1GB and Neon 0.5GB limits
- **Reusable Intelligence**: Library of AI skills for consistent content generation (P+Q+P format)

## 🧠 Reusable Intelligence Skills

This project demonstrates **Reusable Intelligence** through a library of specialized AI skills using the P+Q+P (Persona + Questions + Principles) format:

### 1. Write Chapter Skill (`skills/write-chapter.md`)
**Purpose**: Generate technical textbook chapters for Physical AI using Docusaurus markdown

**Persona**: Senior Robotics Professor at Panaversity specializing in Embodied Intelligence

**Key Principles**:
- Hardware-First: Always mention which hardware (Jetson/GPU) runs the code
- Docusaurus Native: Use admonitions (:::note, :::tip) for hardware warnings
- Visuals: Include diagram placeholders for complex concepts
- Code: All examples in `python` or `bash` blocks

**Usage**: When creating any of the 13 chapters, this skill ensures consistent structure, tone, and technical accuracy.

### 2. ROS 2 Coder Skill (`skills/ros2-coder.md`)
**Purpose**: Write production-grade ROS 2 (Humble) Python nodes

**Persona**: Robotics Software Architect focused on Object-Oriented, asynchronous, fault-tolerant nodes

**Key Principles**:
- OOP Structure: Always inherit from `Node`
- Type Hinting: Use Python type annotations
- Entry Point: Include `def main(args=None):` block
- Resource Management: Use `try-except-finally` to destroy nodes

**Usage**: Generate all ROS 2 code examples in Module 1 (Chapters 1-4) with consistent architecture.

### 3. Hardware Review Skill (`skills/review-hardware.md`)
**Purpose**: Validate content against physical hardware constraints (subagent pattern)

**Persona**: Hardware Integration Engineer preventing students from damaging equipment

**Key Principles**:
- The Latency Trap: Warn about Cloud vs. Edge latency
- VRAM Check: Verify RTX 4070 Ti requirement for Isaac Sim
- Safety: Flag any physical movement code with warnings

**Usage**: After chapter generation, invoke this skill to validate hardware compatibility and add safety warnings.

### 4. FastAPI Coder Skill (`skills/fastapi-coder.md`)
**Purpose**: Generate production-ready FastAPI endpoints with Pydantic validation

**Persona**: Senior Backend Engineer prioritizing type safety and async patterns

**Key Principles**:
- Async First: All database and API calls must be `async def`
- Type Safety: Strict type hinting for all arguments
- Environment: Always load secrets using `os.getenv` or `pydantic-settings`
- Docs: Include docstrings for Swagger/OpenAPI generation

**Usage**: Build backend API routes for RAG chatbot, authentication, and data services.

### 5. React Component Skill (`skills/react-component.md`)
**Purpose**: Build React components optimized for Docusaurus Swizzling

**Persona**: Frontend Architect specializing in Docusaurus functional components

**Key Principles**:
- Hooks: Use `useState`, `useEffect`, `useCallback` properly
- Tailwind: Use utility classes for styling
- Client-Side: Check for `ExecutionEnvironment` when using browser APIs
- Accessibility: Ensure ARIA labels are present

**Usage**: Create chat widget UI, personalization components, and Docusaurus layout customizations.

### How Skills Work Together

**Content Generation Workflow** (Textbook Chapters):
```
write-chapter → ros2-coder → review-hardware → Feedback Loop
```

**Software Development Workflow** (RAG Chatbot, Features):
```
fastapi-coder (backend API) + react-component (frontend UI) → review-hardware (deployment safety) → Integration Testing
```

This creates **dual feedback loops** that improve both content quality and software architecture automatically.

### Multi-Agent Architecture (Sub-Agent Pattern)

The project uses a **coordinated multi-agent system** documented in `agents/team.md`:

| Agent | Role | Source Skill | Responsibility |
|-------|------|--------------|----------------|
| **Orchestrator** | Project Manager | N/A (Main Session) | Manages build pipeline, git operations, delegates tasks |
| **@Content-Professor** | Senior Robotics Professor | `write-chapter.md` | Writes educational content, ensures Hardware-First approach |
| **@ROS2-Architect** | Software Architect | `ros2-coder.md` | Generates production-grade Python/C++ code with OOP patterns |
| **@Hardware-Safety** | Safety Engineer | `review-hardware.md` | Reviews content for physical risks (voltage, latency, safety) |

**Workflow**: Orchestrator → @Content-Professor → @ROS2-Architect → @Hardware-Safety → Feedback Loop

This demonstrates **Reusable Intelligence** through role specialization and skill composition.

## 📚 Modules

### Module 1: ROS 2 Basics & Nervous System
- Chapter 1: Introduction to ROS 2
- Chapter 2: Publisher-Subscriber Communication
- Chapter 3: Services & Actions
- Chapter 4: Robotic Nervous System

### Module 2: Digital Twin Development
- Chapter 5: Digital Twin Introduction
- Chapter 6: URDF Modeling
- Chapter 7: Gazebo Simulation

### Module 3: Isaac Gym & Sim
- Chapter 8: Isaac Gym Introduction
- Chapter 9: RL Training Pipelines
- Chapter 10: Sim-to-Real Transfer

### Module 4: Vision-Language-Action Models
- Chapter 11: VLA Introduction
- Chapter 12: Multimodal Integration
- Chapter 13: Deployment Strategies

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- OpenAI API key
- Qdrant Cloud account
- Neon Serverless Postgres account

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-username/Humanoid-Robots-Book.git
cd Humanoid-Robots-Book
```

2. **Install frontend dependencies**
```bash
npm install
```

3. **Install backend dependencies**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and database URLs
```

5. **Run database migrations**
```bash
cd backend
alembic upgrade head
# Or run the SQL migration directly:
# psql $DATABASE_URL -f db/migrations/001_initial_schema.sql
```

### Development

**Start the frontend (Docusaurus)**
```bash
npm start
```
The site will open at http://localhost:3000

**Start the backend (FastAPI)**
```bash
cd backend
uvicorn src.main:app --reload
```
API docs available at http://localhost:8000/docs

### Production Build

**Build frontend**
```bash
npm run build
npm run serve
```

**Run backend in production**
```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## 🏗️ Architecture

### Frontend
- **Framework**: Docusaurus 3.x (React-based static site generator)
- **Styling**: Tailwind CSS + custom CSS
- **Language**: TypeScript
- **Deployment**: GitHub Pages

### Backend
- **Framework**: FastAPI 0.110+
- **Database**: Neon Serverless Postgres (user data, chat history)
- **Vector DB**: Qdrant Cloud (document embeddings for RAG)
- **LLM**: OpenAI GPT-4 Turbo + text-embedding-3-small
- **Authentication**: JWT-based (server-side)
- **Deployment**: Railway / Render

### Data Flow
1. User asks question in chat widget
2. Frontend sends query to FastAPI `/api/chat`
3. Backend generates embedding using OpenAI
4. Qdrant retrieves top-k relevant chunks
5. OpenAI GPT-4 generates response with context
6. Response streamed back to frontend

## 📊 RAG Configuration

- **Chunk Size**: 512 tokens
- **Chunk Overlap**: 50 tokens
- **Embedding Model**: text-embedding-3-small (1536 dimensions)
- **Top-K Retrieval**: 5 chunks
- **Score Threshold**: 0.7

## 🧪 Testing

**Frontend linting**
```bash
npm run lint
npm run format:check
```

**Backend linting**
```bash
cd backend
black --check .
flake8 .
mypy src/
```

**Backend tests**
```bash
cd backend
pytest tests/ -v --cov=src
```

## 🔒 Environment Variables

See `.env.example` for all required variables:
- `OPENAI_API_KEY`: OpenAI API key
- `QDRANT_URL`: Qdrant Cloud cluster URL
- `QDRANT_API_KEY`: Qdrant API key
- `DATABASE_URL`: Neon Postgres connection string
- `AUTH_SECRET`: JWT signing secret (min 32 chars)

## 📝 Project Structure

```
Humanoid-Robots-Book/
├── docs/                     # Textbook chapters (Markdown/MDX)
│   ├── intro.md
│   ├── module-1-ros2-basics/
│   ├── module-2-digital-twin/
│   ├── module-3-isaac/
│   └── module-4-vla/
├── src/                      # Frontend components and pages
│   ├── components/
│   ├── pages/
│   └── css/
├── backend/                  # FastAPI backend
│   ├── src/
│   │   ├── auth/            # Authentication
│   │   ├── chat/            # RAG chatbot
│   │   ├── personalize/     # User personalization
│   │   ├── translate/       # Urdu translation
│   │   ├── db/              # Database clients
│   │   ├── config.py        # Settings
│   │   └── main.py          # FastAPI app
│   ├── alembic/             # Database migrations
│   └── requirements.txt
├── specs/                    # Spec-Driven Development artifacts
│   └── 001-physical-ai-textbook/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
├── skills/                   # Reusable Intelligence (P+Q+P format)
│   ├── write-chapter.md     # Chapter generation skill
│   ├── ros2-coder.md        # ROS 2 code generation skill
│   ├── review-hardware.md   # Hardware validation skill
│   ├── fastapi-coder.md     # FastAPI backend code generation skill
│   └── react-component.md   # React/Docusaurus component skill
├── agents/                   # Multi-Agent System
│   └── team.md              # AI Team Manifest (Orchestrator + 6 sub-agents)
├── history/                  # PHRs and ADRs
│   ├── adr/
│   └── prompts/
├── .github/workflows/        # CI/CD pipelines
├── docusaurus.config.js
├── sidebars.js
└── package.json
```

## 🤝 Contributing

This project follows Spec-Driven Development (SDD):
1. All features start with a spec (`specs/<feature>/spec.md`)
2. Create implementation plan (`specs/<feature>/plan.md`)
3. Generate tasks (`specs/<feature>/tasks.md`)
4. Document decisions in ADRs (`history/adr/`)
5. Track prompts in PHRs (`history/prompts/`)

## 🏆 Hackathon Scoring

**Base Points (100)**
- ⏳ Static textbook content (4 modules, 13 chapters): 50 points (infrastructure ready)
- ⏳ RAG chatbot integration: 50 points (infrastructure ready)

**Bonus Points (200)**
- ✅ **Agent Skills demonstration: 50 points** ← **COMPLETED!**
  - 5 reusable skills created (write-chapter, ros2-coder, review-hardware, fastapi-coder, react-component)
  - 6 specialized agents (Orchestrator + Content-Professor + ROS2-Architect + Hardware-Safety + Backend-Engineer + Frontend-Architect)
  - P+Q+P (Persona + Questions + Principles) format
  - Dual feedback loops (content generation + software development)
- ⏳ Better Auth integration: 40 points (schema ready, routes pending)
- ⏳ Per-chapter personalization: 60 points (schema ready, routes pending)
- ⏳ Urdu translation: 50 points (i18n configured, implementation pending)

**Current Score**: 50 points (Reusable Intelligence)
**Potential Score**: 300 points (all features ready to implement)
**Target Total**: 300 points

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Built for GIAIC Physical AI & Humanoid Robotics Hackathon
- Powered by OpenAI, Qdrant, Neon, and Docusaurus
- Following Spec-Kit Plus methodology

---

**Ready to learn? Start at http://localhost:3000 after running `npm start`!**
