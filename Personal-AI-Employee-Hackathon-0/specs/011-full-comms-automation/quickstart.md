# Quickstart: Full Communication Automation (Phase 6.5)

**Branch**: `011-full-comms-automation` | **Date**: 2026-04-11

---

## Prerequisites

### 1. OpenRouter API Key (Required for Tier 1 model routing)

```bash
# Sign up at https://openrouter.ai — free account gives free model access
# Add to .env:
echo "OPENROUTER_API_KEY=your_key_here" >> .env
```

### 2. Gmail Write OAuth (Required for Phase B)

```bash
# Re-auth with write scopes after scripts/gmail_write_auth.py is built
python3 scripts/gmail_write_auth.py
# Follow WSL2 manual code-paste flow (same as calendar_auth.py)
# Paste the auth code when prompted
```

### 3. Google Calendar Write OAuth (Required for Phase C)

```bash
# Re-run with full calendar scope (not readonly)
python3 scripts/calendar_auth.py
# Follow WSL2 manual code-paste flow
```

### 4. WhatsApp Business Bridge (Optional — Phase D dev/test)

```bash
# Start second bridge instance for Business WhatsApp (family member's account)
# Add to .env:
echo "WHATSAPP_BRIDGE_URL_BUSINESS=http://localhost:8081" >> .env

# Start bridge on port 8081
WHATSAPP_BRIDGE_PORT=8081 nohup ~/whatsapp-mcp/whatsapp-bridge/whatsapp-bridge \
  > /tmp/whatsapp-bridge-business.log 2>&1 &
# Scan QR code with family member's WhatsApp
```

### 5. LinkedIn Messaging API (Optional — Phase E DMs)

```bash
# Apply at: https://developer.linkedin.com/partner-programs/messaging
# When approved, add to .env:
echo "LINKEDIN_MESSAGING_API_KEY=your_key_here" >> .env
```

---

## Running the HITL Queue

```bash
# Check pending approvals
python3 -m orchestrator.hitl_queue --list-pending

# Process approved actions (called automatically by watchers)
python3 -m orchestrator.hitl_queue --execute-approved
```

---

## Running the Gmail Watcher

```bash
# Start gmail reply watcher (runs every 60s)
nohup python3 -m watchers.gmail_reply_watcher > /tmp/gmail_watcher.log 2>&1 &

# Or run once manually
python3 -m watchers.gmail_reply_watcher --once

# Classify inbox manually
python3 -m mcp_servers.gmail.server --classify --max-emails 50
```

---

## Running the LinkedIn Monitor

```bash
# Start (polls every 15 min)
nohup python3 -m watchers.linkedin_monitor > /tmp/linkedin_monitor.log 2>&1 &
```

---

## Testing

```bash
# Run all Phase 6.5 tests
pytest tests/unit/test_hitl_queue.py tests/unit/test_email_classifier.py -v

# Run full suite
pytest tests/ -v --tb=short

# Run coverage
pytest tests/ --cov=classifiers --cov=orchestrator/hitl_queue --cov-report=term-missing
```

---

## Environment Variables (new in Phase 6.5)

```bash
# Add to .env:
OPENROUTER_API_KEY=              # Required: Tier 1 free model access
WHATSAPP_BRIDGE_URL_BUSINESS=    # Optional: http://localhost:8081
LINKEDIN_MESSAGING_API_KEY=      # Optional: LinkedIn partner access
TWITTER_BASIC_TIER=false         # Set true if Twitter Basic tier active
```

---

## Checking HITL Queue in Briefing

The daily briefing (`python3 -m orchestrator.ceo_briefing --now`) will automatically include:
- Pending HITL approvals (if any in queue)
- Cross-platform daily summary (Gmail + LinkedIn + Social + WhatsApp unread)
