# Operational Specification: Development Environment Readiness

**Feature Branch**: `001-dev-env-setup`
**Created**: 2026-01-26
**Status**: Draft - Micro-Spec for Operations
**Type**: Environment Maintenance (not feature development)
**Input**: "Connect/link ai-control files, remove old dependencies/caches, kill/restart servers, configure browser MCPs for debugging"

## Purpose

Prepare the development environment for Phase 3/4 work by ensuring:
1. Governance files are synchronized
2. Development environment is clean (no stale caches/dependencies)
3. Development servers are fresh (no port conflicts/zombie processes)
4. Browser debugging tools are configured and working

## Clarifications

### Session 2026-01-26

- Q: Should the cleanup operation default to quick mode (caches only) or full mode (caches + dependencies removal)? → A: Default to quick mode (caches only), require explicit flag for full cleanup
- Q: How should the system behave if no old servers are running when attempting cleanup? → A: Skip gracefully with info message (idempotent - safe to run multiple times)
- Q: Should all three browser MCPs be configured, or is one primary tool with others as optional sufficient? → A: Playwright primary (required), ChromeDevTools optional for edge case debugging, Puppeteer optional for screenshot evidence/submissions
- Q: When environment validation detects issues, should the system block all operations or allow selective bypass? → A: Block all operations and require fixes before proceeding (fail-fast)
- Q: Should these operations be executed in a specific sequence, or can they run in any order/parallel? → A: Specific sequence required - AC-005 → AC-001 → AC-002 → AC-003 → AC-004 (validation first, browser tools last)

## Execution Order

Operations MUST be executed in this specific sequence to prevent cascading failures:

1. **AC-005: Environment Validation** (First - fail-fast if environment broken)
2. **AC-001: Governance File Synchronization** (Second - ensure instructions current)
3. **AC-002: Cache & Dependency Cleanup** (Third - prepare clean environment)
4. **AC-003: Server Lifecycle Management** (Fourth - start servers on clean state)
5. **AC-004: Browser Debugging Tools** (Last - verify tools against running servers)

**Rationale**: This sequence minimizes wasted time by catching environment issues immediately (validation), ensuring agents have correct instructions (governance), preparing a clean working state (cleanup), starting services fresh (servers), and finally verifying debugging tools work against live services (browser tools).

## Acceptance Criteria

### AC-001: Governance File Synchronization
- [ ] `ai-control/CLAUDE.md` references `@AGENTS.md` (thin wrapper pattern)
- [ ] `AGENTS.md` at root contains complete Spec-Kit workflow
- [ ] Both files reference constitution v2.0.0
- [ ] Agent team definitions (Command/Build/Support) are consistent

**Verification**: Read both files, check cross-references and version numbers

---

### AC-002: Cache & Dependency Cleanup
- [ ] All build caches cleared (frontend and backend) - **Default mode: Quick cleanup**
- [ ] All runtime caches cleared (Python bytecode, Node modules cache) - **Default mode: Quick cleanup**
- [ ] Dependency lock files preserved for reinstallation
- [ ] Optional with explicit flag: Full dependency cleanup (remove and reinstall dependencies)

**Verification**: Check for absence of cache directories; optionally reinstall dependencies with --full flag

---

### AC-003: Server Lifecycle Management
- [ ] Old development servers terminated (frontend and backend) - **Idempotent: Skip gracefully if no servers running**
- [ ] Required ports are free and available
- [ ] New development servers start without errors
- [ ] Frontend server responds to health check
- [ ] Backend server responds to health check
- [ ] Frontend can connect to backend API

**Verification**: Use process management tools to verify port status; test HTTP endpoints. Operation must be idempotent (safe to run multiple times).

---

### AC-004: Browser Debugging Tools
- [ ] **Playwright MCP** (required) is configured in MCP registry and responding
- [ ] Playwright can navigate to local application and capture screenshots
- [ ] **ChromeDevTools MCP** (optional) configured for edge case debugging
- [ ] **Puppeteer MCP** (optional) configured for screenshot evidence/submission artifacts

**Verification**: List available MCPs, verify Playwright is working (required), optionally verify ChromeDevTools and Puppeteer if installed

**Tool Priority**:
- **Playwright**: Primary testing and automation tool (REQUIRED)
- **ChromeDevTools**: Optional - for edge case debugging and deep browser inspection
- **Puppeteer**: Optional - for generating screenshot evidence for posts/submissions

---

### AC-005: Environment Validation
- [ ] All required environment variables exist and are correctly formatted
- [ ] Runtime versions meet requirements (Python, Node.js)
- [ ] Required CLI tools are installed
- [ ] Database connectivity verified
- [ ] Validation script runs without errors - **Fail-fast: Block all operations on validation failure**

**Verification**: Run environment validation script, verify exit code 0. If validation fails, system MUST block all development operations until issues are fixed.

**Failure Behavior**: When validation detects any issue (missing env vars, wrong versions, connectivity failures), the system MUST:
1. Display specific error messages for each failure
2. Provide suggested fix commands
3. Exit with non-zero code
4. Block server startup and development operations until validation passes

---

## Success Metrics

- **Time to Ready**: Developer can complete all 5 acceptance criteria in under 5 minutes
- **Error Reduction**: Zero "port in use" or "cache issue" errors after completion
- **Validation Coverage**: Environment validation catches 100% of common config errors before development

## Out of Scope

- Database setup/migration (only validates connectivity)
- Initial tool installation (assumes base tools already installed once)
- CI/CD integration (local development only)
- Production deployments
- MCP server installation (only validates configuration)

## Implementation Notes

This is operational maintenance, not feature development. Implementation can proceed immediately after user approval without full `/sp.clarify`, `/sp.plan`, `/sp.tasks` workflow (micro-spec exception per constitution Principle IV).

**Recommended Approach**:
1. Create automation scripts for repeatable operations
2. Use existing MCPs (filesystem, code-search) and Skills (env-validator, systematic-debugging)
3. Document in PHR for future reference
4. Consider creating a Skill if patterns repeat 3+ times

---

**Status**: Ready for user approval and immediate implementation
