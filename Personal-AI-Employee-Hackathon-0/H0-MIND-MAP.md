# H0 MIND-MAP: Personal AI Employee Hackathon 0

**Project:** Building Autonomous FTEs (Full-Time Equivalents) in 2026
**Generated:** 2026-02-16 | **Sources:** Evolution-of-Todo, Humanoid-Robots-Book, Hackathon Docs, Prompt Patterns

---

## 0. CORE VISION

```
                        ┌─────────────────────────────────┐
                        │    PERSONAL AI EMPLOYEE (H0)     │
                        │  "Digital FTE on Autopilot"      │
                        │  Local-first, Agent-driven,      │
                        │  Human-in-the-Loop               │
                        └───────────────┬─────────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
     ┌────────▼────────┐    ┌──────────▼──────────┐   ┌─────────▼─────────┐
     │  THE BRAIN       │    │  THE MEMORY/GUI     │   │  THE SENSES       │
     │  Claude Code     │    │  Obsidian Vault     │   │  Python Watchers  │
     │  (Reasoning)     │    │  (Local Dashboard)  │   │  (Gmail,WhatsApp) │
     └────────┬────────┘    └──────────┬──────────┘   └─────────┬─────────┘
              │                         │                         │
              └─────────────────────────┼─────────────────────────┘
                                        │
                              ┌─────────▼─────────┐
                              │  THE HANDS         │
                              │  MCP Servers       │
                              │  (External Actions)│
                              └───────────────────┘
```

**Value Proposition:**
- Human FTE: 2,000 hrs/year @ $3-6/task
- Digital FTE: 8,760 hrs/year @ $0.25-0.50/task (85-90% cost reduction)

---

## 1. TIER SYSTEM (Deliverables)

```
┌──────────────────────────────────────────────────────────────────┐
│  BRONZE (8-12 hrs)                                               │
│  ├── Basic Obsidian vault with folder structure                  │
│  ├── 1 watcher script (Gmail OR filesystem)                     │
│  ├── Claude reads /Needs_Action, creates /Plans                 │
│  └── Manual approval workflow                                    │
├──────────────────────────────────────────────────────────────────┤
│  SILVER (20-30 hrs)                                              │
│  ├── 2+ watchers (Gmail + WhatsApp)                             │
│  ├── MCP server integration                                     │
│  ├── Claude reasoning loop (Ralph Wiggum)                       │
│  ├── LinkedIn automation                                         │
│  └── Auto-categorization of incoming messages                   │
├──────────────────────────────────────────────────────────────────┤
│  GOLD (40+ hrs)                                                  │
│  ├── Full cross-domain integration                              │
│  ├── Odoo Community (ERP/Accounting)                            │
│  ├── Monday Morning CEO Briefing                                │
│  ├── Neon PostgreSQL for persistence                            │
│  └── Bank transaction auditing                                  │
├──────────────────────────────────────────────────────────────────┤
│  PLATINUM (60+ hrs)                                              │
│  ├── Cloud + Local hybrid (always-on)                           │
│  ├── Distributed agents (24/7)                                  │
│  ├── Multi-domain orchestration                                 │
│  └── Self-healing + graceful degradation                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. ARCHITECTURE MAP

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          WATCHER LAYER (Senses)                         │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐   │
│  │ Gmail     │  │ WhatsApp  │  │ Filesystem│  │ Banking/Social    │   │
│  │ Watcher   │  │ Watcher   │  │ Watcher   │  │ Watchers          │   │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └────────┬──────────┘   │
│        └───────────────┼───────────────┼─────────────────┘             │
│                        ▼                                               │
│              /Needs_Action/ folder                                      │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────────────┐
│                     REASONING LAYER (Brain)                             │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │  Claude Code + Ralph Wiggum Loop                           │        │
│  │  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐               │        │
│  │  │ Read │──►│Reason│──►│ Plan │──►│  Act │──► Check Done? │        │
│  │  └──────┘   └──────┘   └──────┘   └──────┘    │   NO ──┐  │        │
│  │                                                ▼        │  │        │
│  │                                            YES: Exit    │  │        │
│  │                                        ◄────────────────┘  │        │
│  └────────────────────────────────────────────────────────────┘        │
│                        │                                               │
│         ┌──────────────┼──────────────┐                                │
│         ▼              ▼              ▼                                 │
│    /Plans/      /Pending_Approval/  /Done/                             │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────────────┐
│                     ACTION LAYER (Hands)                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐      │
│  │ Gmail    │  │ Browser  │  │ File     │  │ Database          │      │
│  │ MCP      │  │ MCP      │  │ System   │  │ (Neon/SQLite)     │      │
│  │ (Send)   │  │ (Click)  │  │ MCP      │  │                   │      │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────────────┐
│                     MEMORY LAYER (Obsidian Vault)                       │
│  /Inbox/  /Needs_Action/  /Plans/  /Approved/  /Done/  /Logs/          │
│  /CEO_Briefings/  /Templates/  /Pending_Approval/                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. TECH STACK DECISIONS

```
CATEGORY           │ CHOICE                  │ RATIONALE (from past projects)
───────────────────┼─────────────────────────┼──────────────────────────────────
Reasoning Engine   │ Claude Code (Opus)      │ Primary orchestrator, proven in EoT
Dashboard          │ Obsidian                │ Local-first, Markdown, privacy
Watchers           │ Python 3.13+            │ watchdog, Playwright, async
MCP Protocol       │ Model Context Protocol  │ Standardized tool access (ADR-010)
Auth               │ JWT + HTTPOnly Cookies  │ Proven pattern (ADR-004 from EoT)
Database           │ SQLite dev / Neon prod  │ ADR-008 + Gold tier needs
ORM                │ SQLModel + Alembic      │ ADR-006 from EoT
API Framework      │ FastAPI                 │ Async, typed, battle-tested in EoT
Frontend (if any)  │ Next.js + Tailwind      │ Server Actions as data layer (ADR-005)
ERP (Gold)         │ Odoo Community          │ Open-source, accounting integration
Browser Automation │ Playwright              │ MCP + testing (ADR-012)
Version Control    │ Git + GitHub            │ PR workflow, issue tracking
Dev Environment    │ SDD + SpecKit Plus      │ Proven governance framework
```

---

## 4. AGENT TEAM (Claude Instances)

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMMAND LAYER                                 │
│  ┌───────────────────────────────────────────────────────┐      │
│  │  IMPERATOR (Opus)                                     │      │
│  │  Strategic decisions, scope protection, delegation    │      │
│  │  Reads: master-plan.md, constitution.md               │      │
│  └───────────────────────┬───────────────────────────────┘      │
│                          │                                       │
│  ┌───────────────────────▼───────────────────────────────┐      │
│  │  LEAD-ARCHITECT (Opus)                                │      │
│  │  Specs, plans, ADRs, phase transitions                │      │
│  │  Controls: /sp.specify → /sp.plan → /sp.tasks         │      │
│  └───────────────────────┬───────────────────────────────┘      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                  EXECUTION LAYER                                 │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │ BACKEND-       │  │ UX-FRONTEND-   │  │ DEVOPS-RAG-    │    │
│  │ BUILDER (Opus) │  │ DEVELOPER      │  │ ENGINEER       │    │
│  │                │  │ (Sonnet)       │  │ (Sonnet)       │    │
│  │ FastAPI, DB,   │  │ Next.js, UI,   │  │ Docker, deploy │    │
│  │ MCP servers,   │  │ Obsidian UI,   │  │ RAG pipeline,  │    │
│  │ Watchers       │  │ accessibility  │  │ vector DB      │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │ SPEC-ARCHITECT │  │ TASK-          │  │ MODULAR-AI-    │    │
│  │ (Opus)         │  │ ORCHESTRATOR   │  │ ARCHITECT      │    │
│  │                │  │ (Sonnet)       │  │ (Opus)         │    │
│  │ Rigorous specs │  │ Parallel work  │  │ Agent design,  │    │
│  │ before code    │  │ coordination   │  │ memory systems │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                  QUALITY LAYER                                   │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │ QA-OVERSEER    │  │ LOOP-          │  │ PATH-WARDEN    │    │
│  │ (Opus)         │  │ CONTROLLER     │  │ (Sonnet)       │    │
│  │                │  │ (Opus)         │  │                │    │
│  │ Final verify   │  │ Enforce SPEC→  │  │ File placement │    │
│  │ before "Done"  │  │ IMPL→TEST→QA  │  │ validation     │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐                         │
│  │ ENTERPRISE-    │  │ DOCUSAURUS-    │                         │
│  │ GRADE-         │  │ LIBRARIAN      │                         │
│  │ VALIDATOR      │  │ (Sonnet)       │                         │
│  │ (Sonnet)       │  │                │                         │
│  │ Production     │  │ Knowledge      │                         │
│  │ readiness      │  │ preservation   │                         │
│  └────────────────┘  └────────────────┘                         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. SKILLS REGISTRY (Reusable Intelligence)

### 5.1 Core Development Skills
```
SKILL                       │ TRIGGERS ON                    │ PURPOSE
────────────────────────────┼────────────────────────────────┼─────────────────────
/spec-architect             │ New feature request            │ Generate spec.md
/spec-driven-development    │ Any coding attempt             │ Enforce spec-first
/systematic-debugging       │ Bug encountered                │ Root cause analysis
/code-cleanliness           │ Before commit                  │ Style enforcement
/security-scan              │ Before git push                │ Vulnerability check
/env-validator              │ Project init, npm start fail   │ Validate .env setup
/hackathon-rules            │ Scope decisions                │ Enforce H0 rules
/todo-domain-expert         │ Task management logic          │ Domain knowledge
```

### 5.2 Frontend Skills
```
/frontend-design            │ UI implementation              │ Design quality
/styling-with-shadcn        │ Component creation             │ Accessible UI
/building-chat-interfaces   │ Chat UI for Obsidian/web       │ Auth + context
/building-chat-widgets      │ Interactive widgets            │ Agentic UIs
/webapp-testing             │ After UI changes               │ Playwright tests
/test-ui                    │ UI verification                │ Screenshot verify
/browsing-with-playwright   │ Browser automation             │ Navigate, fill, click
```

### 5.3 Backend Skills
```
/scaffolding-fastapi-dapr   │ API implementation             │ FastAPI + SQLModel
/building-rag-systems       │ Knowledge base creation        │ RAG pipeline
/building-mcp-servers       │ New MCP server needed          │ MCP protocol
/mcp-builder                │ MCP development                │ Server creation
/configuring-better-auth    │ Auth setup                     │ OAuth/JWT
/neon-db-setup              │ Database configuration         │ Neon PostgreSQL
/memory-systems             │ Agent memory design            │ State persistence
```

### 5.4 Governance Skills
```
/phase-execution-controller │ Phase transition               │ Runtime validation
/phase-progress-auditor     │ Phase status check             │ Detect gaps
/review-and-judge           │ Submission review              │ Rubric compliance
/session-state-manager      │ Session start/resume           │ State persistence
/command-orchestration       │ SDD command usage              │ Correct ordering
/template-selector          │ New artifact creation          │ Auto-template
/creating-skills            │ Repeated pattern found         │ New skill creation
/project-context            │ Any project task               │ Load H0 context
```

### 5.5 Deployment Skills
```
/deployment-preflight-check │ Before deploy                  │ Build integrity
/deployment-stability       │ After deploy                   │ Smoke tests
/containerizing-applications│ Docker setup                   │ Dockerfile gen
/operating-production-services│ SRE patterns                 │ SLOs, runbooks
```

---

## 6. MCP SERVERS (Connected Tools)

```
┌──────────────────────────────────────────────────────────────┐
│  CONNECTED (Working)                                         │
│  ├── filesystem     → Read/Write project files               │
│  ├── postgres       → Database queries                       │
│  ├── docker         → Container management                   │
│  ├── playwright     → Browser automation + testing           │
│  ├── chrome-devtools→ Browser debugging                      │
│  ├── context7       → Library documentation lookup           │
│  ├── github         → Repo, PR, issue management             │
│  ├── hopx-sandbox   → Isolated code execution                │
│  ├── scriptflow     → Script management + execution          │
│  ├── windows-cli    → Windows command execution              │
│  ├── ragie          → RAG document management                │
│  └── nx-mcp         → Monorepo management                   │
├──────────────────────────────────────────────────────────────┤
│  NEEDS FIXING                                                │
│  ├── git            → Git MCP (use CLI fallback)             │
│  ├── Neon           → Neon PostgreSQL (fix config)           │
│  ├── gemini-cli     → Gemini research (fix auth)             │
│  ├── n8n-local      → Workflow automation (fix connection)   │
│  └── codex-cli      → Code generation (fix setup)            │
├──────────────────────────────────────────────────────────────┤
│  NEEDED FOR H0 (To Add)                                      │
│  ├── Gmail MCP      → Email reading/sending                  │
│  ├── WhatsApp MCP   → Message monitoring                     │
│  ├── Obsidian MCP   → Vault read/write                       │
│  ├── Calendar MCP   → Schedule management                    │
│  └── Odoo MCP       → ERP integration (Gold tier)            │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. GOVERNANCE FRAMEWORK

### 7.1 Constitution Structure
```
.specify/memory/constitution.md
├── Core Principles (6 areas)
│   ├── Code Quality Standards
│   ├── Testing Requirements
│   ├── Performance Budgets
│   ├── Security Policies
│   ├── Architecture Constraints
│   └── Documentation Standards
├── Development Workflow
│   └── SPEC → IMPLEMENT → TEST → QA → FIX → REPEAT
├── Phase Gates
│   ├── Environment validation must pass before phase start
│   ├── Phase-aware config routing
│   └── Fail-fast on validation errors
├── Review Process & Quality Gates
└── Governance Rules
```

### 7.2 Control Files (from Evolution-of-Todo patterns)
```
/ai-control/
├── CLAUDE.md         → Supreme execution law (no code without spec)
├── AGENTS.md         → Agent governance & factory
├── SKILLS.md         → Reusable micro-intelligence registry
├── MCP.md            → External power sources registry
├── LOOP.md           → Spec-driven heartbeat enforcement
└── SWARM.md          → Parallel execution rules
```

### 7.3 Enforcement Loops
```
1. SPEC-DRIVEN LOOP (LOOP.md)
   SPEC → IMPLEMENT → TEST → QA → FIX → REPEAT
   Violation = STOP immediately

2. RALPH WIGGUM LOOP (Autonomous completion)
   Create state → Claude works → Try exit → Check /Done?
   NO → Re-inject prompt → Continue
   YES → Allow exit

3. HUMAN-IN-THE-LOOP (Sensitive actions)
   Detect sensitive → /Pending_Approval/ → Human reviews
   → /Approved/ → MCP executes → /Logs/

4. DIRECTORY GUARD (Path Warden)
   Wrong directory = STOP immediately
   Move everything to correct path, then resume
```

---

## 8. SDD WORKFLOW (Spec-Driven Development)

```
USER REQUEST
    │
    ▼
┌──────────────┐
│ /sp.specify  │──► specs/<feature>/spec.md
└──────┬───────┘
       ▼
┌──────────────┐
│ /sp.clarify  │──► Resolve unknowns (2-3 targeted questions)
└──────┬───────┘
       ▼
┌──────────────┐
│ /sp.plan     │──► specs/<feature>/plan.md + research.md + data-model.md
└──────┬───────┘
       ▼                    ┌──────────────┐
       ├───────────────────►│ /sp.adr      │──► history/adr/ADR-NNN.md
       │  (if significant)  └──────────────┘
       ▼
┌──────────────┐
│ /sp.tasks    │──► specs/<feature>/tasks.md
└──────┬───────┘
       ▼
┌──────────────────┐
│ /sp.taskstoissues│──► GitHub Issues (optional)
└──────┬───────────┘
       ▼
┌──────────────┐
│ /sp.implement│──► Code changes (smallest viable diff)
└──────┬───────┘
       ▼
┌──────────────────┐
│ /sp.git.commit_pr│──► Git commit + PR
└──────┬───────────┘
       ▼
┌──────────────┐
│ /sp.phr      │──► history/prompts/<feature>/NNN-slug.prompt.md
└──────────────┘
```

---

## 9. PATTERNS COPIED FROM PAST PROJECTS

### From Evolution-of-Todo (13 ADRs, 37+ PHRs)
```
PATTERN                         │ ADR    │ REUSE IN H0
────────────────────────────────┼────────┼─────────────────────────────
Service-Repository Pattern      │ ADR-001│ Watcher/Agent service layer
JWT + HTTPOnly Cookie Auth      │ ADR-004│ Obsidian dashboard auth
SQLModel + Alembic Migrations   │ ADR-006│ Persistent storage (Gold)
SQLite Dev / Neon Prod          │ ADR-008│ Development fallback DB
Hybrid AI Engine (Claude+Gemini)│ ADR-009│ Multi-model reasoning
MCP Service Wrapping            │ ADR-010│ All external actions via MCP
Cross-Platform Automation Stack │ ADR-012│ PowerShell + Python scripts
Fail-Fast Environment Validation│ ADR-013│ Startup validation
```

### From Humanoid-Robots-Book
```
PATTERN                         │ REUSE IN H0
────────────────────────────────┼─────────────────────────────
SpecKit Plus Templates          │ Same template system (.specify/)
PHR Tracking System             │ Same history/prompts/ structure
Skill-Based Architecture        │ Same skills library approach
RAG Chatbot Pattern             │ Knowledge retrieval for CEO briefings
Docusaurus as Memory Center     │ Obsidian as equivalent memory
Hardware-Aware Personalization  │ Environment-aware watcher configs
```

### From Prompt Patterns (How-I-give-prompts/)
```
PATTERN                         │ AUTOMATE AS
────────────────────────────────┼─────────────────────────────
Phase tracking in resume prompt │ /session-state-manager skill
Agent/Skill listing in prompts  │ Auto-loaded via CLAUDE.md
Directory validation            │ /path-warden agent
MCP listing in prompts          │ Auto-loaded via MCP.md
SDD command recommendations     │ /command-orchestration skill
Multi-model delegation          │ AGENTS.md governance
Limit reset context restoration │ /session-state-manager skill
```

---

## 10. PROJECT STRUCTURE (H0)

```
Personal-AI-Employee-Hackathon-0/
├── .specify/                    # SpecKit Plus (templates, scripts, constitution)
│   ├── memory/constitution.md   # Project principles
│   ├── templates/               # PHR, ADR, spec, plan, tasks templates
│   └── scripts/                 # Automation (bash/powershell)
├── .claude/
│   └── commands/                # SDD commands (sp.specify, sp.plan, etc.)
├── ai-control/                  # Governance files (NEW for H0)
│   ├── CLAUDE.md               # Execution law
│   ├── AGENTS.md               # Agent factory & governance
│   ├── SKILLS.md               # Skill registry
│   ├── MCP.md                  # MCP registry
│   ├── LOOP.md                 # Enforcement loops
│   └── SWARM.md                # Parallel execution
├── specs/                       # Feature specifications
│   ├── overview.md
│   └── <feature>/
│       ├── spec.md
│       ├── plan.md
│       ├── tasks.md
│       ├── research.md
│       └── data-model.md
├── history/                     # Decision tracking
│   ├── adr/                    # Architecture Decision Records
│   └── prompts/                # Prompt History Records
│       ├── constitution/
│       ├── <feature-name>/
│       └── general/
├── vault/                       # Obsidian Vault (the AI dashboard)
│   ├── Inbox/
│   ├── Needs_Action/
│   ├── Plans/
│   ├── Pending_Approval/
│   ├── Approved/
│   ├── Done/
│   ├── Logs/
│   ├── CEO_Briefings/
│   └── Templates/
├── watchers/                    # Python watcher scripts
│   ├── gmail_watcher.py
│   ├── whatsapp_watcher.py
│   ├── filesystem_watcher.py
│   └── bank_watcher.py
├── mcp-servers/                 # Custom MCP server implementations
│   ├── gmail-mcp/
│   ├── obsidian-mcp/
│   └── odoo-mcp/
├── orchestrator/                # Ralph Wiggum loop + task runner
│   ├── loop.py
│   ├── state.py
│   └── hooks/
│       ├── stop_hook.sh
│       └── approval_hook.sh
├── tests/                       # E2E, integration, unit tests
├── scripts/                     # Utility scripts
└── docs/                        # Documentation / Reusable Intelligence
```

---

## 11. EXECUTION PHASES

```
PHASE │ NAME                    │ DELIVERABLE                  │ AGENTS
──────┼─────────────────────────┼──────────────────────────────┼────────────────────
  0   │ Foundation & Governance │ Constitution, CLAUDE.md,     │ imperator,
      │                         │ ai-control/, project struct  │ lead-architect
──────┼─────────────────────────┼──────────────────────────────┼────────────────────
  1   │ Obsidian Vault          │ Vault structure, templates,  │ backend-builder,
      │                         │ folder taxonomy, markdown    │ spec-architect
──────┼─────────────────────────┼──────────────────────────────┼────────────────────
  2   │ First Watcher (Bronze)  │ Gmail/filesystem watcher,    │ backend-builder,
      │                         │ /Needs_Action population     │ devops-rag-engineer
──────┼─────────────────────────┼──────────────────────────────┼────────────────────
  3   │ Claude Reasoning Loop   │ Ralph Wiggum loop, read      │ modular-ai-architect,
      │                         │ /Needs_Action → /Plans       │ backend-builder
──────┼─────────────────────────┼──────────────────────────────┼────────────────────
  4   │ MCP Integration         │ Gmail MCP (send), Browser    │ backend-builder,
      │                         │ MCP (click), File MCP        │ mcp-builder skill
──────┼─────────────────────────┼──────────────────────────────┼────────────────────
  5   │ HITL Approval (Silver)  │ /Pending_Approval workflow,  │ ux-frontend-dev,
      │                         │ WhatsApp watcher             │ qa-overseer
──────┼─────────────────────────┼──────────────────────────────┼────────────────────
  6   │ CEO Briefing (Gold)     │ Monday audit, bank watcher,  │ backend-builder,
      │                         │ Odoo integration             │ enterprise-validator
──────┼─────────────────────────┼──────────────────────────────┼────────────────────
  7   │ Always-On (Platinum)    │ Cloud VM, distributed agents,│ devops-rag-engineer,
      │                         │ self-healing, 24/7 operation │ task-orchestrator
──────┼─────────────────────────┼──────────────────────────────┼────────────────────
  8   │ Polish & Demo           │ Testing, security scan,      │ qa-overseer,
      │                         │ demo video, submission       │ risk-assessor
```

---

## 12. CRITICAL SUCCESS FACTORS

```
1. SPEC BEFORE CODE         → No implementation without spec.md
2. PHR EVERY PROMPT         → Verbatim recording, never truncated
3. ADR FOR DECISIONS        → Impact + Alternatives + Scope test
4. HUMAN AS TOOL            → Ask user on ambiguity, not assume
5. SMALLEST VIABLE DIFF     → No unrelated refactoring
6. WRONG DIRECTORY = STOP   → Path validation on every operation
7. TEST DRIVEN              → Backend + Frontend + UI (Playwright)
8. BIDIRECTIONAL LEARNING   → Claude teaches user, user teaches Claude
9. GRACEFUL DEGRADATION     → Error recovery, not error hiding
10. LOCAL-FIRST PRIVACY     → Obsidian vault, no cloud dependency by default
```

---

## 13. RISK MAP

```
RISK                        │ MITIGATION                      │ OWNER
────────────────────────────┼─────────────────────────────────┼──────────
API cost overrun            │ Rate limiting, caching, Gemini  │ imperator
                            │ fallback                         │
────────────────────────────┼─────────────────────────────────┼──────────
Watcher process death       │ Tmux/systemd, health checks,   │ devops-rag
                            │ auto-restart scripts             │
────────────────────────────┼─────────────────────────────────┼──────────
Claude context overflow     │ Chunking, PHR summaries,        │ loop-controller
                            │ session state management         │
────────────────────────────┼─────────────────────────────────┼──────────
Scope creep                 │ Phase gates, imperator scope    │ imperator
                            │ protection, tier targeting       │
────────────────────────────┼─────────────────────────────────┼──────────
Security (token leak)       │ .env, never hardcode secrets,   │ qa-overseer
                            │ security-scan skill              │
────────────────────────────┼─────────────────────────────────┼──────────
Wrong directory writes      │ Path-warden agent, STOP on      │ path-warden
                            │ directory mismatch               │
────────────────────────────┼─────────────────────────────────┼──────────
MCP server failures         │ Graceful fallback, health       │ enterprise-
                            │ checks, retry logic              │ validator
```

---

## 14. NEXT STEPS (Constitution Creation)

```
1. [ ] Create H0 constitution using /sp.constitution
2. [ ] Set up ai-control/ governance files
3. [ ] Initialize vault/ structure in Obsidian
4. [ ] Fix broken MCPs (Neon, gemini-cli, git)
5. [ ] Add new MCPs needed (Gmail, WhatsApp, Obsidian)
6. [ ] Create Phase 0 spec: /sp.specify "H0 Foundation & Governance"
7. [ ] Run /sp.plan for Phase 0
8. [ ] Execute Phase 0 with parallel agent team
```

---

*This mind-map is a living document. Update after each phase completion.*
*Generated from 4 parallel exploration agents analyzing 3 codebases + hackathon docs.*
