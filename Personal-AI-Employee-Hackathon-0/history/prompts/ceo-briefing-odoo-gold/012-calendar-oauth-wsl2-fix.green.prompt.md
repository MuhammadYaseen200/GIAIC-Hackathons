---
id: "012"
title: "Calendar OAuth WSL2 Fix + Section Parser"
stage: green
date: "2026-04-02"
surface: agent
model: claude-sonnet-4-6
feature: ceo-briefing-odoo-gold
branch: 010-ceo-briefing-odoo-gold
user: MuhammadYaseen200
command: "fix calendar OAuth expired token + collect_calendar_section result parser"
labels: ["calendar", "oauth", "wsl2", "bugfix", "live-verification"]
links:
  spec: "specs/010-ceo-briefing-odoo-gold/spec.md"
  adr: "history/adr/0016-odoo-api-protocol-selection.md"
  pr: "null"
files:
  - scripts/calendar_auth.py
  - orchestrator/ceo_briefing.py
tests:
  - "manual: python3 -c 'asyncio.run(collect_calendar_section(\"daily\"))' → returns events dict"
  - "manual: python3 -c 'asyncio.run(run_daily_briefing())' → Section 3 shows real calendar data"
---

## Prompt

Calendar OAuth token expired (`invalid_grant: Bad Request` in live CEO briefing run).
Fix WSL2 re-auth flow and ensure Section 3 of briefing shows real calendar events.

## Response

### Root Causes Fixed

**1. calendar_auth.py — WSL2 OAuth flow**
- Previous: `flow.run_local_server(port=8085)` — browser redirect to localhost can't reach WSL2
- Previous: Missing `OAUTHLIB_INSECURE_TRANSPORT=1` → `InsecureTransportError` on http://localhost
- Fix: Manual code exchange flow (user pastes redirect URL); `OAUTHLIB_INSECURE_TRANSPORT=1` set inside script before import

**2. collect_calendar_section — result parser mismatch**
- `list_events()` returns `EventList.model_dump()` → `{"events": [], "calendar_id": "primary", "fetched_at": "..."}`
- Parser only checked for `{"content": ...}` wrapper → fell through to `{"status": "unavailable"}`
- Fix: Added `elif "events" in result: return result` branch

### Outcome
- `calendar_token.json` renewed via manual WSL2 OAuth flow (HT-011 complete)
- `collect_calendar_section("daily")` returns `{"events": [], "calendar_id": "primary", ...}`
- CEO briefing Section 3 now shows: **"No events scheduled in the next 48 hours on primary calendar"**
- All 7 sections now operational with live data
- Commit: `e4e9baf` pushed to `010-ceo-briefing-odoo-gold`
