# ADR-0005: MCP Server Framework Stack — FastMCP + Pydantic v2 + stdio

> **Scope**: Defines the Python framework, schema definition strategy, and transport mechanism for all MCP servers built in Phase 4.

- **Status:** Accepted
- **Date:** 2026-02-24
- **Feature:** mcp-integration (007)
- **Context:** Phase 4 requires building two MCP servers (Gmail and Obsidian). The Python `mcp` SDK provides two levels of API: a low-level `Server` class (explicit JSON-RPC handler registration) and a high-level `FastMCP` wrapper (decorator-based tool registration with automatic schema generation). Constitution Principle IV mandates all external actions route through MCP. Constitution Principle II mandates local-first stdio transport. The project uses Pydantic v2 for all data models (established in Phase 3). The building-mcp-servers skill guide recommends FastMCP as the production-ready approach.

## Decision

Use **FastMCP** (`mcp.server.fastmcp.FastMCP`) with **Pydantic v2 BaseModel** for input schemas and **stdio transport** for both MCP servers.

Components:
- **Server framework**: `FastMCP("server_name")` — decorator-based tool registration, automatic JSON schema generation from Pydantic models, built-in error normalization
- **Tool registration**: `@mcp.tool(name="...", annotations={...})` decorators on async functions; Pydantic `BaseModel` parameters for validated input
- **Transport**: `mcp.run()` defaults to stdio (stdin/stdout JSON-RPC) — matches Claude Code's subprocess invocation model
- **Schema definition**: `Pydantic v2` `BaseModel` with `ConfigDict(str_strip_whitespace=True, extra="forbid")` and `Field(...)` with explicit constraints and descriptions
- **Lifespan management**: `@asynccontextmanager` lifespan for persistent resources (Gmail service singleton); stateless for Obsidian server
- **Entry point**: `if __name__ == "__main__": mcp.run()` — each server is an independently executable Python script

## Consequences

### Positive

- **Simpler registration**: `@mcp.tool` decorator vs. explicit `@server.list_tools()` + `@server.call_tool()` pair — ~50% less boilerplate per tool
- **Auto-schema**: Pydantic v2 `model_json_schema()` generates accurate JSON Schema for `inputSchema` without manual JSON definition
- **Consistent with existing codebase**: Pydantic v2 already used for `LLMDecision`, `EmailContext`, `DraftReply` in Phase 3 — same patterns
- **Input validation**: Pydantic rejects invalid inputs before tool handler runs — no manual validation code in tools
- **Lifespan support**: `FastMCP(lifespan=...)` enables Gmail service singleton initialization at startup, avoiding per-call OAuth overhead
- **Claude Code compatible**: stdio transport matches Claude Code MCP registration (`"command": "python3", "args": ["server.py"]`)
- **Testable**: Each server is a standalone Python module; tools callable directly in unit tests without spinning up the MCP server

### Negative

- **FastMCP abstraction**: Hides some low-level MCP protocol details; harder to debug raw JSON-RPC framing if issues arise
- **Auto-schema quirks**: Pydantic v2 schema output includes `title` fields and `$defs` that may differ from hand-authored JSON Schema — contract tests must use schema validation, not literal equality
- **Revision from initial research**: research.md D1 chose low-level Server API; FastMCP is a scope change discovered from the `building-mcp-servers` skill guide — tasks.md reflects the update

## Alternatives Considered

**Alternative A: Low-level `mcp.server.lowlevel.server.Server` (original research.md D1)**
- Components: `@server.list_tools()` + `@server.call_tool()` + manual `stdio_server()` context manager
- Pros: Explicit control over every protocol detail; no hidden abstractions; exact tool schema control
- Cons: ~2× more boilerplate; manual schema definition for each tool (10 tools = 10 JSON schemas by hand); no lifespan management; no auto-validation
- Rejected: FastMCP provides identical runtime behavior with significantly less code; `building-mcp-servers` skill guide identifies it as the recommended production approach

**Alternative B: FastAPI + MCP HTTP adapter (SSE transport)**
- Components: FastAPI server + SSE transport + `uvicorn`
- Pros: HTTP transport enables multi-client access; REST-familiar debugging
- Cons: Adds `fastapi`, `uvicorn` dependencies; no streaming needed (spec constraint); WSL2 port management complexity; Claude Code stdio integration is simpler
- Rejected: Spec explicitly states "No streaming tool responses" and servers are local-only; stdio is the correct transport for this use case

**Alternative C: TypeScript MCP SDK**
- Components: `@modelcontextprotocol/sdk` + Node.js + `ts-node`
- Pros: TypeScript SDK has excellent type safety; larger ecosystem of examples; recommended in `building-mcp-servers` guide for new projects
- Cons: Entire project is Python; mixing Node.js + Python adds `node_modules`, `tsconfig.json`, `package.json` for 2 servers; no reuse of `watchers/utils.py` or `gmail_watcher.py` OAuth logic
- Rejected: Python consistency with rest of project; direct reuse of existing auth and util code is a hard spec constraint (FR-007, FR-010)

## References

- Feature Spec: `specs/007-mcp-integration/spec.md` (FR-001—FR-014)
- Implementation Plan: `specs/007-mcp-integration/plan.md` (Phase A, Phase B)
- Research: `specs/007-mcp-integration/research.md` (D1 — revised to FastMCP)
- Tasks: `specs/007-mcp-integration/tasks.md` (T013, T023 — server.py implementations)
- Skill: `building-mcp-servers` references/python_mcp_server.md
- Related ADRs: ADR-0002 (async SDK integration pattern), ADR-0001 (watcher base class — non-watcher MCP servers do NOT use BaseWatcher)
- Constitution: `.specify/memory/constitution.md` Principle II (Local-First), Principle IV (MCP-First External Actions)
