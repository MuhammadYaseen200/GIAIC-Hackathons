# CEO Briefing Quickstart

## Prerequisites
- Odoo Docker: `docker run -p 8069:8069 odoo:latest`
- `.env` filled: ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD
- WhatsApp bridge running (for HITL notifications)

## Run Daily Briefing
```bash
cd /mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0
python3 orchestrator/ceo_briefing.py --now
```

## Expected Output
- `vault/CEO_Briefings/YYYY-MM-DD.md` created
- 7 sections (Email Triage, Financial Alert, Calendar, Social, LinkedIn, Pending HITL, System Health)
- WhatsApp notification sent to owner
- YAML frontmatter: `status: pending_approval`

## Approve and Email
Reply APPROVE to WhatsApp -> briefing emailed via Gmail MCP.

## Cron Schedule (daily 07:00)
```bash
0 7 * * * python3 /mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/orchestrator/ceo_briefing.py --now
```

## Run Weekly Audit
```bash
python3 orchestrator/weekly_audit.py --now
```

## Troubleshooting
- **Odoo unavailable**: Financial section shows "Odoo unavailable" -- briefing still generated
- **LLM unavailable**: `[TEMPLATE MODE]` flag in briefing -- still delivered
- **WhatsApp fails**: Notification skipped (non-blocking) -- briefing still in vault
