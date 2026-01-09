---
id: PHR-308
title: Phase 3 Checklist Generation
stage: tasks
created: 2026-01-08
tags: [phase-3, checklist, ai-chatbot, requirements]
---

# Phase 3 Checklist Generation

## Overview
Generated a comprehensive checklist for Phase 3: AI Chatbot implementation with MCP and OpenAI Agents SDK.

## Original Prompt
```
# Phase 3: AI Chatbot Implementation - Checklist Generation Prompt

## Context
We are implementing Phase 3 of the "Evolution of Todo" hackathon project, transitioning from a Full-Stack Web Application (Phase 2) to an AI-powered Chatbot using MCP (Model Context Protocol) and OpenAI Agents SDK with Gemini integration.

## Project Structure
```
hackathon-todo/
├── .specify/                    # Spec-Kit configuration
│   ├── memory/
│   │   └── constitution.md
│   └── templates/
├── specs/                       # Specifications
│   ├── features/
│   ├── api/
│   └── database/
├── history/
│   ├── prompts/
│   │   └── phase-3-chatbot/
│   └── adr/
├── frontend/                    # Next.js app (Phase II)
├── backend/                     # FastAPI app (Phase II)
└── phase_3_chatbot/            # NEW: Phase III implementation
```

## Phase 3 Requirements

### Technology Stack
- **AI Framework**: OpenAI Agents SDK with Gemini (OpenAI-compatible endpoint)
- **MCP Server**: Official MCP SDK (Python)
- **Chat UI**: OpenAI ChatKit (Next.js integration)
- **Backend**: FastAPI (existing from Phase 2)
- **Database**: Neon PostgreSQL (existing)
- **State Management**: Stateless API + DB persistence
- **New Features**: Priorities (high/medium/low), Tags/Categories, Search & Filter

### Architectural Decisions (ADRs)
1. **ADR-009**: Hybrid AI Engine (OpenAI Agents SDK + Gemini)
   - Use OpenAICompatibleModel with Gemini endpoint
   - No direct OpenAI API calls

2. **ADR-010**: MCP Service Wrapping Strategy
   - Port Phase 2 logic to `phase_3_chatbot/backend/services/`
   - NO cross-phase imports (from phase_2_web)
   - Create isolated MCP tools layer

3. **ADR-011**: Task Schema Extension
   - Add `priority` enum (high/medium/low) with default='medium'
   - Add `tags` JSON column with default='[]'
   - Alembic migration required

### Task Dependencies (32 Tasks, T-301 to T-332)

**Layer 0: Configuration**
- T-301: Backend dependencies (google-generativeai, mcp, openai-agents-sdk)
- T-302: Environment configuration (.env updates)
- T-303: Frontend dependencies (ChatKit, UI components)

**Layer 1: Database**
- T-304: Priority enum definition
- T-305: Alembic migration for priority + tags
- T-306: Conversations table schema
- T-307: Conversations migration
- T-308: Conversation service (CRUD operations)
- T-309: Task service extension (priority, tags, search/filter)

**Layer 2: MCP Server**
- T-310: Core MCP tool definitions (add_task, list_tasks, etc.)
- T-311: MCP server initialization
- T-312: Core tool handlers (basic CRUD)
- T-313: Extended tool handlers (priority, tags, search)

**Layer 3: AI Engine**
- T-314: Gemini configuration (OpenAI-compatible)
- T-315: Agent initialization + tool binding
- T-316: System prompts and instruction templates

**Layer 4: Chat API**
- T-317: Chat endpoint implementation
- T-318: Router integration with FastAPI
- T-319: Agent wiring to MCP tools

**Layer 5: Frontend**
- T-320: Chat UI components (ChatKit integration)
- T-321: Chat page (/chat route)
- T-322: Chat action (API client)
- T-323: Dashboard navigation update

**Layer 6: Integration**
- T-324: E2E chat flow testing
- T-325: Priority management via chat
- T-326: Tags management via chat
- T-327: Search/filter via chat
- T-328: Task list synchronization

**Layer 7: Polish**
- T-329: Error handling and validation
- T-330: Loading states and UX refinements
- T-331: PHR documentation
- T-332: CLAUDE.md update

## Agents to Use

### Command Team (Always Active)
- **qa-overseer**: Validate acceptance criteria at each layer
- **loop-controller**: Manage task execution order and dependencies
- **imperator**: Enforce constitution and brownfield protocol
- **path-warden**: Prevent cross-phase imports and architectural violations

### Build Team (Task-Specific)
- **modular-ai-architect**: Design agent architecture and tool interfaces (Layer 2-3)
- **ux-frontend-developer**: Implement ChatKit UI (Layer 5)
- **spec-architect**: Review and validate specifications against ADRs
- **backend-builder**: Implement MCP server and FastAPI endpoints (Layer 2, 4)

## Skills to Use

### Core Skills (Always)
- **spec-driven-development**: Ensure all code traces to approved tasks
- **deployment-preflight-check**: Validate environment before each layer
- **security-scan**: Check for hardcoded secrets, JWT validation
- **env-validator**: Verify .env file completeness

### Specialized Skills
- **building-mcp-servers**: Guide MCP server implementation (Layer 2)
- **scaffolding-openai-agents**: Configure OpenAI Agents SDK with Gemini (Layer 3)
- **streaming-llm-responses**: Implement streaming chat responses (Layer 4)
- **building-chat-interfaces**: Integrate ChatKit UI components (Layer 5)

### Quality Skills
- **systematic-debugging**: Debug MCP tool failures
- **webapp-testing**: E2E testing strategy (Layer 6)

## MCPs to Use

### Required MCPs
- **context7**: Query Next.js, FastAPI, SQLModel, MCP SDK documentation
- **code-search**: Search Phase 2 codebase for reusable patterns
- **postgres**: Direct database queries for migration validation

### Optional MCPs
- **github**: Convert tasks to GitHub issues (/sp.taskstoissues)
- **docker**: If containerization is needed for testing

## Brownfield Protocol Constraints

### Critical Rules
1. **NO Direct Imports**: Never `from phase_2_web import ...`
2. **Port, Don't Import**: Copy and adapt Phase 2 logic to Phase 3 directory
3. **Isolation**: Phase 3 must run independently (separate FastAPI instance on different port)
4. **Backward Compatibility**: Phase 2 REST API must continue to function
5. **Database Sharing**: Both phases share the same Neon PostgreSQL database

### Pre-Implementation Checklist
- [ ] Backup `CLAUDE.md` and current specs
- [ ] Verify Phase 2 acceptance criteria still pass
- [ ] Create migration spec before modifying database schema
- [ ] Review ADR-009, ADR-010, ADR-011

## Success Criteria

### Layer Completion Gates
- **Layer 0**: Dependencies installed, .env configured, no import errors
- **Layer 1**: Migrations run successfully, new columns exist, backward compatible
- **Layer 2**: MCP server starts, tools registered, basic tool calls work
- **Layer 3**: Agent initializes with Gemini, tools bound correctly
- **Layer 4**: Chat endpoint returns responses, conversation state persists
- **Layer 5**: Chat UI renders, messages send/receive, typing indicators work
- **Layer 6**: All MCP tools callable via chat, task CRUD works, search/filter functional
- **Layer 7**: Error messages clear, loading states smooth, documentation complete

### Final Acceptance
- [ ] User can chat with AI to manage tasks
- [ ] User can set task priorities via chat
- [ ] User can add/remove tags via chat
- [ ] User can search/filter tasks via natural language
- [ ] Conversation history persists across sessions
- [ ] Phase 2 REST API still functional
- [ ] No cross-phase imports detected
- [ ] All 32 tasks completed with PHR records

## Checklist Generation Command

```bash
/sp.checklist
```

### Prompt for Checklist Generation

Generate a detailed, actionable checklist for Phase 3: AI Chatbot implementation with the following requirements:

1. **Layer-by-Layer Breakdown**: Organize checklist into 8 layers (0-7) matching the task dependency structure
2. **Agent Assignment**: Specify which agent should handle each checklist section
3. **Skill Integration**: Reference specific skills to use for each task group
4. **MCP Tool Usage**: Indicate when to use context7, code-search, postgres MCPs
5. **Validation Steps**: Include manual verification steps after each layer
6. **Brownfield Safeguards**: Add warnings before tasks that could break Phase 2
7. **ADR Enforcement**: Link checklist items to ADR-009, ADR-010, ADR-011 constraints
8. **Time Estimates**: Provide realistic time estimates per layer
9. **Rollback Points**: Identify safe rollback points if a layer fails
10. **Documentation Triggers**: Specify when to create PHR records

### Special Considerations

- **Priority**: Focus on MCP tool reliability (Layer 2) before agent complexity (Layer 3)
- **Testing Strategy**: Each layer must be testable in isolation
- **Error Handling**: Anticipate common failures (MCP connection, Gemini API, DB migration)
- **User Experience**: Chat UI should feel responsive (use streaming responses)
- **Security**: Validate JWT tokens, sanitize chat inputs, scope queries to user_id

### Deliverables

The checklist should produce:
1. A markdown file: `specs/checklists/phase-3-implementation-checklist.md`
2. GitHub issues (if /sp.taskstoissues is run)
3. A printable/shareable format for team coordination
4. Links to relevant ADRs, specs, and PHR records

---

**Deadline**: Phase 3 must be complete by December 21, 2025
**Current Date**: January 8, 2026 (NOTE: We are past deadline, but continuing with implementation)
**Points**: 200 points for Phase 3 completion

## Additional Context

This is a hackathon project demonstrating mastery of:
- Spec-Driven Development (SDD)
- Cloud-Native AI architectures
- MCP protocol for tool interoperability
- Brownfield refactoring without breaking existing systems
- Agentic AI orchestration

The checklist should be **prescriptive** (tell what to do), **sequential** (enforce dependency order), and **verifiable** (every item can be tested).
```

## Response Summary
Created a comprehensive 84-item checklist (CHK001-CHK084) organized into 8 categories:
1. Requirement Completeness (8 items)
2. Requirement Clarity (8 items)
3. Layer-by-Layer Requirements (48 items across 8 layers)
4. Validation & Verification Requirements (6 items)
5. Non-Functional Requirements (6 items)
6. Scenario Coverage (6 items)
7. Edge Case Coverage (6 items)
8. Consistency Requirements (12 items)

The checklist validates requirements quality focusing on completeness, clarity, consistency, and coverage rather than implementation verification. Each item tests the requirements themselves for quality attributes.

## Checklist Location
The checklist was created at: `E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo\specs\checklists\phase-3-implementation-checklist.md`