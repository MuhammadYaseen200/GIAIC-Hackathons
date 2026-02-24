---
id: 010
title: Phase 4 Structure Audit All Files Approved
stage: misc
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: mcp-integration
branch: 007-mcp-integration
user: m-y-j
command: path-warden audit
labels: [path-warden,structure-audit,mcp-integration,file-validation,governance]
links:
  spec: specs/007-mcp-integration/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - mcp_servers/__init__.py
  - mcp_servers/gmail/__init__.py
  - mcp_servers/gmail/auth.py
  - mcp_servers/gmail/models.py
  - mcp_servers/gmail/tools.py
  - mcp_servers/gmail/server.py
  - mcp_servers/obsidian/__init__.py
  - mcp_servers/obsidian/models.py
  - mcp_servers/obsidian/tools.py
  - mcp_servers/obsidian/server.py
  - orchestrator/mcp_client.py
  - tests/contract/__init__.py
  - tests/contract/test_gmail_send_contract.py
  - tests/contract/test_gmail_mcp_contracts.py
  - tests/contract/test_obsidian_mcp_contracts.py
  - tests/unit/test_mcp_client.py
  - tests/unit/test_orchestrator_mcp.py
  - tests/integration/test_approved_draft_send.py
  - tests/integration/test_gmail_mcp_integration.py
  - tests/integration/test_obsidian_mcp_integration.py
  - tests/integration/test_orchestrator_mcp_integration.py
  - history/prompts/mcp-integration/008-phase4-6-us2-us3-us4-t017-t027-complete.green.prompt.md
  - history/prompts/mcp-integration/009-phase7-polish-t028-t031-complete.green.prompt.md
tests:
  - none (audit only — no new tests run)
---

## Prompt

Validate all Phase 4 MCP Integration file placements against project structure standards.

**Project root**: `/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0`

**Files created in Phase 4** (verify each is in the correct location):

Source files:
- `mcp_servers/__init__.py` — Python package init
- `mcp_servers/gmail/__init__.py` — Gmail package init
- `mcp_servers/gmail/auth.py` — OAuth2 singleton
- `mcp_servers/gmail/models.py` — Pydantic input models
- `mcp_servers/gmail/tools.py` — GmailTools class
- `mcp_servers/gmail/server.py` — FastMCP entry point
- `mcp_servers/obsidian/__init__.py` — Obsidian package init
- `mcp_servers/obsidian/models.py` — Pydantic input models
- `mcp_servers/obsidian/tools.py` — ObsidianTools class
- `mcp_servers/obsidian/server.py` — FastMCP entry point
- `orchestrator/mcp_client.py` — MCPClient fallback protocol

Test files:
- `tests/contract/__init__.py`
- `tests/contract/test_gmail_send_contract.py`
- `tests/contract/test_gmail_mcp_contracts.py`
- `tests/contract/test_obsidian_mcp_contracts.py`
- `tests/unit/test_mcp_client.py`
- `tests/unit/test_orchestrator_mcp.py`
- `tests/integration/test_approved_draft_send.py`
- `tests/integration/test_gmail_mcp_integration.py`
- `tests/integration/test_obsidian_mcp_integration.py`
- `tests/integration/test_orchestrator_mcp_integration.py`

Documentation:
- `history/prompts/mcp-integration/008-phase4-6-us2-us3-us4-t017-t027-complete.green.prompt.md`
- `history/prompts/mcp-integration/009-phase7-polish-t028-t031-complete.green.prompt.md`

**Project structure rules** (from constitution):
- MCP servers → `mcp_servers/<server-name>/` (underscores, valid Python package)
- Orchestrator code → `orchestrator/`
- Contract tests → `tests/contract/`
- Unit tests → `tests/unit/`
- Integration tests → `tests/integration/`
- PHRs → `history/prompts/<feature-name>/`

Verify all files exist at the stated paths and that no files were accidentally placed in wrong directories. Report any misplacements or missing files.

## Response snapshot

All 23 Phase 4 files verified PRESENT at stated paths. Zero files missing. Zero Phase 4 files misplaced.

Key finding: `mcp_servers/` (underscore) vs constitution's `mcp-servers/` (hyphen) — resolved as an intentional, documented deviation recorded in tasks.md T002: "directory renamed to mcp_servers/ (underscores) for valid Python package import." The deviation is justified by Python packaging constraints and does not require correction.

Pre-existing WARNING from Phase 3 audit (PHR 014) carried forward: three root-level scripts (`live_run.py`, `smoke_test.py`, `verify_bronze_exit.py`) belong in `scripts/`. These are outside Phase 4 scope and are already tracked.

## Outcome

- Impact: All 23 Phase 4 MCP Integration files confirmed at architecturally correct paths. No corrective action required for Phase 4 output.
- Tests: No new tests run (audit task only).
- Files: 23 files audited — all PRESENT, all APPROVED.
- Next prompts: Address the pre-existing root-level script violation (live_run.py, smoke_test.py, verify_bronze_exit.py) in a dedicated cleanup task before Phase 5 begins.
- Reflection: The mcp_servers/ underscore naming was a correct deviation — Python package import requirements are a legitimate override of the convention-level hyphen in the constitution. The constitution's canonical directory map should be updated in a future amendment to reflect mcp_servers/ as the authoritative name.

## Evaluation notes (flywheel)

- Failure modes observed: none — all files present and correctly placed
- Graders run and results (PASS/FAIL): path-warden audit PASS (23/23 files approved)
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Update constitution.md canonical directory map to show `mcp_servers/` (underscore) to eliminate future confusion on this naming point
