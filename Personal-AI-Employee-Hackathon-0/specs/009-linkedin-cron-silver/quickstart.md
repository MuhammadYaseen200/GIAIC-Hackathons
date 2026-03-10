# Quickstart: LinkedIn Auto-Poster + Cron Scheduling

**Feature**: `009-linkedin-cron-silver` | **Date**: 2026-03-05

---

## Prerequisites

- Phase 5 complete (WhatsApp bridge running, HITLManager working)
- LinkedIn Developer App created (HT-013 DONE) — Client ID + Secret in `.env`
- `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET` in `.env`
- Cron daemon running (`crontab -l` works without error)

---

## Step 1: LinkedIn OAuth2 Initial Authentication (one-time)

```bash
cd /mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0
python3 scripts/linkedin_auth.py
```

This opens a browser, prompts LinkedIn login + app authorization, then saves `linkedin_token.json` in the project root. The token includes `offline_access` scope for auto-refresh.

Verify:
```bash
python3 -c "
import json
with open('linkedin_token.json') as f:
    t = json.load(f)
print('access_token:', t['access_token'][:20], '...')
print('refresh_token:', 'PRESENT' if t.get('refresh_token') else 'MISSING')
print('person_urn:', t.get('person_urn', 'NOT SET'))
"
```

---

## Step 2: Add LINKEDIN_PERSON_URN to .env

`scripts/linkedin_auth.py` prints the person URN after auth. Add it:

```bash
# In .env:
LINKEDIN_PERSON_URN=urn:li:person:your_id_here
```

---

## Step 3: Create Topic File

```bash
mkdir -p vault/Config
cat > vault/Config/linkedin_topics.md << 'EOF'
# LinkedIn Post Topics

- AI learning progress and experiments with Claude
- Web development projects and milestones
- Freelance availability and Python/AI service offerings
- Hackathon participation and achievements
- Python automation and agent development insights
- Building Personal AI Employee — lessons learned
EOF
```

---

## Step 4: Run LinkedIn MCP Health Check

```bash
python3 -c "
import asyncio
from mcp_servers.linkedin.server import mcp
print('LinkedIn MCP server loaded OK')
"
```

---

## Step 5: Test Manual Draft (smoke test)

```bash
python3 orchestrator/linkedin_poster.py --draft "building AI agents with Claude Code"
```

Expected:
1. WhatsApp message received: `[LinkedIn Draft] Topic: building AI agents...`
2. File appears in `vault/Pending_Approval/`
3. Reply "approve" → post published to LinkedIn within 60s
4. Entry in `vault/Logs/linkedin_posts.jsonl` with `status=published`

---

## Step 6: Install Cron Jobs

```bash
chmod +x scripts/setup_cron.sh
./scripts/setup_cron.sh
crontab -l  # should show exactly 2 H0 entries
```

Verify cron entries:
```
*/15 * * * * cd /path/to/project && ... orchestrator.py >> vault/Logs/cron.log 2>&1
0 9 * * *   cd /path/to/project && ... linkedin_poster.py --auto >> vault/Logs/cron.log 2>&1
```

---

## Step 7: Verify Cron is Running

```bash
# Wait for first 15-minute tick, then:
tail -f vault/Logs/cron.log
```

Expected output:
```
2026-03-05T09:15:00 [orchestrator] Starting run — checking vault/Needs_Action/
2026-03-05T09:15:01 [orchestrator] 0 items found. Done.
```

---

## Uninstall Cron Jobs

```bash
chmod +x scripts/remove_cron.sh
./scripts/remove_cron.sh
crontab -l  # H0 entries should be gone
```

---

## Key File Locations

| File | Purpose |
|------|---------|
| `linkedin_token.json` | OAuth2 tokens (gitignored) |
| `vault/Config/linkedin_topics.md` | Daily post topic pool |
| `vault/Pending_Approval/` | Posts awaiting owner approval |
| `vault/Done/` | Published posts |
| `vault/Rejected/` | Rejected/expired drafts |
| `vault/Logs/linkedin_posts.jsonl` | Full audit log |
| `vault/Logs/cron.log` | Cron execution log |
| `scripts/setup_cron.sh` | Install cron jobs |
| `scripts/remove_cron.sh` | Remove cron jobs |
| `scripts/linkedin_auth.py` | One-time OAuth2 setup |
| `orchestrator/linkedin_poster.py` | LinkedIn posting workflow |
| `mcp_servers/linkedin/server.py` | LinkedIn MCP server |
