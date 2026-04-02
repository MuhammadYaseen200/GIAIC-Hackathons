---
id: "013"
title: "Security Scan QA All Risks Fixed"
stage: green
date: "2026-04-02"
surface: agent
model: claude-sonnet-4-6
feature: ceo-briefing-odoo-gold
branch: 010-ceo-briefing-odoo-gold
user: MuhammadYaseen200
command: "security scan + qa-overseer + path-warden + fix all risks"
labels: ["security", "qa", "pii", "gitignore", "oauth", "odoo", "facebook", "whatsapp"]
links:
  spec: "specs/010-ceo-briefing-odoo-gold/spec.md"
  adr: "null"
  pr: "null"
files:
  - scripts/gmail_auth.py
  - scripts/calendar_auth.py
  - mcp_servers/odoo/auth.py
  - mcp_servers/facebook/client.py
  - orchestrator/ceo_briefing.py
  - orchestrator/weekly_audit.py
  - tests/unit/test_odoo_mcp.py
  - .gitignore
  - .mcp.json.example
tests:
  - "749 unit tests green"
  - "82 targeted tests (odoo + calendar + ceo_briefing) green"
  - "live CEO briefing run: 7/7 sections, LLM drafted"
  - "live weekly audit run: GL+AR+invoices live, LLM drafted"
---

## Prompt

Security scan, PII/secrets audit, QA-overseer validation, path-warden audit.
Fix all risks (High, Medium, Low, Minor). Gmail re-auth. WhatsApp bridge reconnect.
Run phase-execution-controller + qa-overseer + path-warden. Then sp.git.commit_pr.

## Fixes Applied

### MEDIUM
- `mcp_servers/facebook/client.py:141` — `access_token` moved from URL query param to `Authorization: Bearer` header (prevents token appearing in HTTP access logs)
- `vault/.obsidian/plugins/` — removed from git tracking; added to `.gitignore`

### LOW
- `mcp_servers/odoo/auth.py` — hardcoded `"h0_odoo"`/`"admin"` defaults removed; runtime `OdooAuthError` raised if `ODOO_DB`/`ODOO_USER` unset
- `mcp_servers/facebook/client.py:39` — auth error log changed from `e.response.text` to `HTTP {status_code}` only
- `scripts/gmail_auth.py` — catches `RefreshError` (invalid_grant) and falls through to full re-auth; adds `OAUTHLIB_RELAX_TOKEN_SCOPE=1` for scope superset handling
- `.gitignore` — added `.mcp.json` to prevent accidental commit of live credentials

### MINOR
- `orchestrator/weekly_audit.py` — LLM wait_for timeout 25s → 55s; error log shows exception type
- HITL warning in both orchestrators now shows bridge URL + restart command
- `scripts/calendar_auth.py` — WSL2 OAuth flow (previous session)
- `orchestrator/ceo_briefing.py` — calendar result parser (previous session)

### Test Fix
- `tests/unit/test_odoo_mcp.py::test_get_odoo_session_success` — added monkeypatch for `ODOO_DB`/`ODOO_USER` (required by new runtime guard)

### New File
- `.mcp.json.example` — sanitized template with `<placeholder>` values for all credentials

## Phase Execution Results

| Component | Status |
|---|---|
| CEO briefing `--now` | ✅ LLM drafted, 7 sections, written |
| Weekly audit `--now` | ✅ LLM drafted, 7 sections, written |
| Unit tests | ✅ 749 passed, 0 failed |
| Spec FR validation | ✅ All 19 FRs checked, all pass |
| Security scan | ✅ PASSED — no secrets in committed files |
| QA-overseer | ✅ APPROVED FOR MERGE |
| Path-warden | ✅ All files correctly placed |
| Gmail OAuth | ✅ Renewed (1907 messages verified) |
| WhatsApp bridge | ✅ QR scanned, session saved |
