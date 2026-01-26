# SKILLS REGISTRY

Reusable micro-intelligence patterns for the Evolution of Todo project.

## PURPOSE

Skills are cheap, fast, repeatable solutions to common problems. They do NOT think or decide - they execute defined patterns.

## SKILL DEFINITION

A Skill is:
- **Atomic**: Single, well-defined purpose
- **Reusable**: Solves a pattern that repeats 3+ times
- **Deterministic**: Same inputs → same outputs
- **Documented**: Clear prompt, verification steps
- **Fast**: Completes in seconds/minutes, not hours

## CORE SKILLS (Always Available)

### A-Priority (Always Use)

#### building-mcp-servers (~1.3k tokens)
**Purpose**: MCP server construction patterns
**When**: Building MCP tools for backend services
**Triggers**: Phase III+, exposing FastAPI as MCP tools
**Output**: MCP server code, tool schemas, type definitions

#### scaffolding-openai-agents (~3.3k tokens)
**Purpose**: OpenAI Agents SDK integration patterns
**When**: Integrating AI agents with tool calling
**Triggers**: Phase III AI chatbot implementation
**Output**: Agent initialization code, tool routing, state management

#### streaming-llm-responses (~2.0k tokens)
**Purpose**: SSE/streaming patterns for LLM responses
**When**: Implementing real-time AI responses
**Triggers**: ChatKit integration, streaming endpoints
**Output**: SSE streaming code, event handlers, error recovery

#### building-chat-interfaces (~2.4k tokens)
**Purpose**: ChatKit/chat UI patterns
**When**: Building chat UI components
**Triggers**: Phase III frontend implementation
**Output**: Chat components, message rendering, session management

#### chatkit-integration (NEW - Phase 3 Retrospective)
**Purpose**: Prevent ChatKit integration failures from Phase 3
**When**: Integrating OpenAI ChatKit (session management, SSE streaming)
**Triggers**: ChatKit setup, HTTP 500 session errors
**Output**: Validated configuration, isolation tests, integration code
**Priority**: A-Priority (Always Use)
**Created**: 2026-01-25 (from 34-day overrun analysis)

#### openrouter-provider (NEW - Phase 3 Retrospective)
**Purpose**: Multi-provider LLM configuration with OpenRouter
**When**: Switching from OpenAI to OpenRouter, implementing model fallback
**Triggers**: Multi-model support, cost optimization, provider fallback
**Output**: OpenRouter configuration, fallback logic, model routing
**Priority**: A-Priority (Always Use when using OpenRouter)
**Created**: 2026-01-25 (from Phase 3 learnings)

#### sse-stream-debugger (NEW - Phase 3 Retrospective)
**Purpose**: Systematic SSE streaming debugging workflow
**When**: SSE connections fail, no data received, EventSource errors
**Triggers**: Streaming endpoints malfunction, HTTP 500 on streams
**Output**: Diagnostic reports, fix recommendations, test scripts
**Priority**: A-Priority (Always Use for SSE issues)
**Created**: 2026-01-25 (from Phase 3 SSE failures)

#### deployment-preflight-check (~751 tokens)
**Purpose**: Pre-deployment validation checklist
**When**: BEFORE deploying to production
**Triggers**: Before Vercel deployment, before K8s apply
**Output**: Validation report, blocker list

#### security-scan (~607 tokens)
**Purpose**: Static security analysis
**When**: BEFORE git push, before deployment
**Triggers**: Detects hardcoded secrets, SQL injection, XSS
**Output**: Security findings, severity levels

#### env-validator (~611 tokens)
**Purpose**: Environment variable validation
**When**: BEFORE every development session
**Triggers**: Missing vars, malformed values, concatenation bugs
**Output**: Validation report, missing/invalid vars list

#### spec-driven-development (~162 tokens)
**Purpose**: SDD workflow enforcement
**When**: Ensuring SPEC → IMPLEMENT → TEST → QA cycle
**Triggers**: Before implementation, before claiming "complete"
**Output**: Workflow validation, gate checks

### B-Priority (Situational Use)

#### skill-creator (~4.4k tokens)
**Purpose**: Creating new reusable skills
**When**: Pattern repeats 3+ times, no existing skill matches
**Triggers**: User requests skill creation, agent identifies pattern
**Output**: New skill definition (YAML + prompts + verification)

#### systematic-debugging (~1.4k tokens)
**Purpose**: Methodical debugging approach
**When**: Encountering complex bugs, reproduction steps unclear
**Triggers**: HTTP 500 errors, test failures, integration issues
**Output**: Root cause analysis, reproduction steps, fix proposal

#### configuring-better-auth (~1.8k tokens)
**Purpose**: Better Auth setup and modification patterns
**When**: Auth setup, JWT configuration, session management
**Triggers**: Phase II+ authentication work
**Output**: Auth config, middleware, protected routes

#### scaffolding-fastapi-dapr (~2.2k tokens)
**Purpose**: Backend microservice setup with Dapr
**When**: Building event-driven microservices
**Triggers**: Phase V cloud deployment
**Output**: FastAPI + Dapr integration, pub/sub patterns

#### deploying-cloud-k8s (~2.1k tokens)
**Purpose**: Cloud K8s deployment patterns
**When**: Deploying to AKS/GKE/DOKS
**Triggers**: Phase V production deployment
**Output**: K8s manifests, CI/CD pipelines, monitoring

#### containerizing-applications (~1.9k tokens)
**Purpose**: Docker containerization patterns
**When**: Creating Dockerfiles, docker-compose
**Triggers**: Phase IV local K8s
**Output**: Multi-stage Dockerfiles, docker-compose.yml

## SKILL CREATION TRIGGERS

Create a new Skill when:

1. **Pattern repeats 3+ times** - Same problem solved multiple times
2. **Solution is deterministic** - Clear input → output mapping
3. **Reusable across phases** - Not one-off solution
4. **Saves significant time** - Automation worth the investment

**Examples from Phase 3**:
- ✅ **NOW CREATED** (2026-01-25):
  - `chatkit-integration` - ChatKit SDK setup (was solved 3+ times without skill)
  - `openrouter-provider` - OpenRouter configuration (was solved 2+ times without skill)
  - `sse-stream-debugger` - SSE debugging workflow (was solved 3+ times without skill)

## SKILL USAGE RULES

### Skills Do NOT:
- Think or make decisions
- Modify constitution or governance
- Override specs or plans
- Create new features
- Deploy to production (only prepare/validate)

### Skills DO:
- Execute defined patterns
- Validate configurations
- Generate boilerplate code
- Run security checks
- Prepare deployment artifacts

## SKILL INVOCATION

### Via Claude Code
Use the Skill tool:
```
User: "Run security scan before deployment"
Claude: [Invokes Skill tool with skill="security-scan"]
```

### Via Spec-Kit Plus
Some skills integrate with /sp commands:
- `spec-driven-development` → Enforced by `/sp.implement`
- `deployment-preflight-check` → Run before deployment
- `env-validator` → Run at session start

### Via Agent Delegation
Agents can use skills:
```
backend-builder: "Use building-mcp-servers skill to scaffold MCP server"
```

## SKILL LIFECYCLE

### 1. Creation
- User identifies pattern (3+ occurrences)
- Use `skill-creator` skill to generate definition
- Store in `.claude/skills/<skill-name>/skill.md`
- Register in THIS file (SKILLS.md)

### 2. Usage
- Agents/Claude invoke via Skill tool
- Skill executes defined pattern
- Returns structured output

### 3. Evolution
- Skill usage tracked in PHRs
- If pattern changes, update skill definition
- Version bump (semantic versioning)

### 4. Retirement
- If pattern no longer relevant (tech stack change)
- Move to "RETIRED SKILLS" section
- Archive with deprecation notice

## SKILL COMPOSITION

Skills can call other skills:
```
deployment-preflight-check:
  1. Calls env-validator
  2. Calls security-scan
  3. Calls spec-driven-development (verify tests passing)
  4. Aggregates results
```

## PHASE-SPECIFIC SKILLS

### Phase I (Console App)
- Basic Python patterns
- No specific skills created

### Phase II (Full-Stack Web)
- `configuring-better-auth` - Auth setup
- `scaffolding-fastapi-dapr` - Backend setup

### Phase III (AI Chatbot)
- `building-mcp-servers` ⭐
- `scaffolding-openai-agents` ⭐
- `streaming-llm-responses` ⭐
- `building-chat-interfaces` ⭐
- `chatkit-integration` ⭐ (CREATED 2026-01-25)
- `openrouter-provider` ⭐ (CREATED 2026-01-25)
- `sse-stream-debugger` ⭐ (CREATED 2026-01-25)
  - `chatkit-integration`
  - `openrouter-provider`
  - `sse-stream-debugger`

### Phase IV (Local K8s)
- `containerizing-applications`
- `deploying-cloud-k8s`
- `operating-k8s-local`

### Phase V (Cloud Deployment)
- `deploying-cloud-k8s`
- `scaffolding-fastapi-dapr`
- `operating-production-services`

## SKILL MAINTENANCE

### Monthly Review
- lead-architect reviews skill usage stats
- Identify underused skills (candidates for retirement)
- Identify missing skills (high-frequency patterns without skills)
- Update skill definitions for accuracy

### After Each Phase
- Create retrospective of skill usage
- Document new skills created
- Document skills that SHOULD have been created
- Update THIS file (SKILLS.md)

## RETIRED SKILLS

*(None yet)*

## VERSION

**Version**: 1.1.0
**Created**: 2026-01-25
**Last Updated**: 2026-01-25
**Changes**: Added 3 Phase 3 retrospective skills (chatkit-integration, openrouter-provider, sse-stream-debugger)
**Next Review**: Before Phase 4 kickoff
