# MCP REGISTRY

External power sources (MCP servers) for the Evolution of Todo project.

## PURPOSE

MCP (Model Context Protocol) is the "USB-C for AI tools" - a standardized way to connect agents to external data sources, tools, and services.

## AAIF COMPLIANCE

This project follows Agentic AI Foundation (AAIF) standards:
- MCP is vendor-neutral (works with Claude Code, Gemini CLI, Goose, OpenAI SDK)
- No business logic in MCP servers (stateless tools only)
- Community-governed protocol (Linux Foundation)

## ACTIVE MCP SERVERS

### Tier 1: Always Use

#### filesystem
**Purpose**: File operations (read, write, edit, search)
**Provider**: Claude Code built-in
**Usage**: ALL file operations
**Restrictions**: None (always available)

**Tools**:
- Read files
- Write files
- Edit files (exact string replacement)
- Search files (glob, grep)
- List directories

**When to Use**: Every session (mandatory)

---

#### postgres
**Purpose**: Neon database queries (PostgreSQL)
**Provider**: Official postgres MCP
**Usage**: Phase II+ database operations
**Restrictions**: Requires DATABASE_URL env var

**Tools**:
- Execute SQL queries
- Schema introspection
- Migration validation
- Connection testing

**When to Use**: Backend development, migrations, data validation

---

#### context7
**Purpose**: Documentation lookup (libraries, frameworks, APIs)
**Provider**: Context7 MCP
**Usage**: Research, SDK exploration
**Restrictions**: Requires API key (free tier available)

**Tools**:
- Fetch API documentation
- Search code examples
- Get usage patterns
- Find similar APIs

**When to Use**: When integrating new SDKs (ChatKit, OpenRouter, K8s), researching best practices

**Phase 3 Lesson**: SHOULD have used for ChatKit SDK research (would have saved 14 days)

---

#### code-search
**Purpose**: Codebase exploration and semantic search
**Provider**: Code Search MCP
**Usage**: Understanding existing code, finding patterns
**Restrictions**: None

**Tools**:
- Semantic code search
- Symbol lookup
- Cross-reference analysis
- Pattern matching

**When to Use**: Exploring existing codebase, finding similar implementations, refactoring

---

### Tier 2: High Priority

#### github
**Purpose**: Issue/PR management, repository operations
**Provider**: Official GitHub MCP
**Usage**: Project management, CI/CD
**Restrictions**: Requires GITHUB_TOKEN

**Tools**:
- Create/update issues
- Create/merge PRs
- Run GitHub Actions
- Manage labels/milestones

**When to Use**: `/sp.taskstoissues`, `/sp.git.commit_pr`, project tracking

**Phase 3 Gap**: NEVER used (tasks not pushed to GitHub Issues, no tracking)

---

### Tier 3: Phase-Specific

#### playwright
**Purpose**: UI testing, browser automation
**Provider**: Playwright MCP
**Usage**: E2E testing (development phase)
**Restrictions**: Requires browser installation

**Tools**:
- Navigate pages
- Click elements
- Fill forms
- Take screenshots
- Capture network traffic

**When to Use**: Phase III+ frontend testing, ChatKit UI validation

---

#### vercel
**Purpose**: Deployment management
**Provider**: Vercel Awesome AI MCP
**Usage**: Deployment phase
**Restrictions**: Requires VERCEL_TOKEN

**Tools**:
- Deploy projects
- Check deployment status
- Manage environment variables
- Rollback deployments

**When to Use**: Phase II+ deployment to Vercel

---

#### docker
**Purpose**: Container operations
**Provider**: Docker MCP
**Usage**: Phase IV+ containerization
**Restrictions**: Requires Docker Desktop running

**Tools**:
- Build images
- Run containers
- Inspect logs
- Manage networks/volumes

**When to Use**: Phase IV Local Kubernetes

---

### Tier 4: Optional/Future

#### chrome-devtools
**Purpose**: Browser debugging via Chrome DevTools Protocol
**Usage**: Advanced frontend debugging
**When**: Complex UI issues, performance profiling

#### nx-mcp
**Purpose**: Nx monorepo management
**Usage**: If project migrates to Nx workspace
**When**: Phase V+ (advanced monorepo needs)

#### ragie
**Purpose**: Document indexing and retrieval
**Usage**: RAG systems, documentation search
**When**: If implementing RAG chatbot features

#### n8n-local
**Purpose**: Workflow automation
**Usage**: CI/CD pipelines, event-driven workflows
**When**: Phase V+ (advanced automation)

#### mysql / mcp_server_mysql
**Purpose**: MySQL database operations
**Usage**: If migrating from PostgreSQL
**When**: Not planned (Neon PostgreSQL is stack)

## MCP USAGE RULES

### MCPs Are Stateless
- No business logic in MCP servers
- Pure input → output tools
- No internal state management

### MCPs Expose Tools Only
- Define clear tool schemas
- Provide type-safe interfaces
- Document required parameters

### No Business Logic in MCPs
- Business logic lives in backend services (FastAPI)
- MCPs are thin wrappers around external services

## MCP REGISTRATION PROCEDURE

When adding new MCP:

1. **Research**: Evaluate MCP server (source, maintenance, community)
2. **Install**: Follow provider installation instructions
3. **Configure**: Add to `~/.config/claude-code/mcp.json`
4. **Test**: Verify tools are accessible
5. **Document**: Add entry to THIS file (MCP.md)
6. **Register**: Update `.specify/memory/constitution.md` AAIF Compliance section

### Example: Adding Playwright MCP

```json
// ~/.config/claude-code/mcp.json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@executeautomation/playwright-mcp-server"],
      "env": {}
    }
  }
}
```

## MCP RETIREMENT PROCEDURE

When retiring MCP:

1. **Evaluate**: Why is MCP no longer needed?
2. **Document**: Create ADR explaining retirement
3. **Remove**: Delete from `mcp.json`
4. **Update**: Move to "RETIRED MCPs" section below
5. **Clean**: Remove related config/credentials

## MCP TROUBLESHOOTING

### Common Issues

#### MCP Not Showing in Tools List
- **Check**: `~/.config/claude-code/mcp.json` syntax
- **Restart**: Claude Code session
- **Test**: `npx <mcp-package>` manually

#### MCP Tools Failing
- **Check**: Environment variables (API keys, tokens)
- **Check**: Service connectivity (internet, VPN)
- **Verify**: MCP server version compatibility

#### MCP Timeout
- **Increase**: Timeout in mcp.json
- **Optimize**: Query parameters (reduce result size)
- **Fallback**: Use alternative MCP or manual approach

## MCP + AAIF INTEROPERABILITY

All MCPs registered here work with:
- ✅ Claude Code
- ✅ Gemini CLI (when MCP support added)
- ✅ Goose (via Goose recipes)
- ✅ OpenAI Agents SDK (via MCP client libraries)
- ✅ Any AAIF-compliant agent framework

This ensures vendor neutrality and agent swappability.

## RETIRED MCPs

*(None yet)*

## VERSION

**Version**: 1.0.0
**Created**: 2026-01-25
**Last Updated**: 2026-01-25
**Next Review**: Before Phase 4 kickoff
