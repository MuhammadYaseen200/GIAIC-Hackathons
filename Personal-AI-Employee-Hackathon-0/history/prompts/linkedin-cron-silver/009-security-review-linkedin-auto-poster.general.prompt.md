---
id: 009
title: Security Review LinkedIn Auto-Poster
stage: general
date: 2026-03-09
surface: agent
model: claude-sonnet-4-6
feature: linkedin-cron-silver
branch: 009-linkedin-cron-silver
user: m-y-j
command: security audit of Phase 5.5 LinkedIn implementation
labels: ["security","audit","linkedin","oauth2","hitl"]
links:
  spec: specs/009-linkedin-cron-silver/spec.md
  ticket: null
  adr: history/adr/0014-linkedin-oauth2-token-lifecycle.md
  pr: null
files:
  - history/reports/security-review-linkedin-2026-03-09.md
tests:
  - n/a (static security review — no tests run)
---

## Prompt

You are a **security reviewer** for the H0 Personal AI Employee project. Review the LinkedIn Auto-Poster codebase for security issues.

Working directory: `/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0`

## Your mission: Security audit of Phase 5.5 LinkedIn implementation

### Files to review:
1. `mcp_servers/linkedin/auth.py` — OAuth2 token lifecycle
2. `mcp_servers/linkedin/client.py` — LinkedIn API calls
3. `mcp_servers/linkedin/server.py` — FastMCP server
4. `orchestrator/linkedin_poster.py` — HITL workflow
5. `scripts/linkedin_auth.py` — OAuth2 auth script
6. `.gitignore` — Check linkedin_token.json is excluded
7. `mcp_servers/linkedin/models.py` — Input validation

### Security checks to perform:

1. **Hardcoded credentials**: Search for any hardcoded API keys, tokens, or secrets in the LinkedIn module files
2. **Input validation**: Verify PostUpdateInput has proper length/content constraints
3. **Token storage**: Verify linkedin_token.json is in .gitignore
4. **Injection risks**: Check for any command injection or prompt injection vectors
5. **Auth error handling**: Verify AuthRequiredError is raised (not logged) when token missing
6. **Sensitive data in logs**: Check logging calls don't log token values
7. **HITL enforcement**: Verify publish_approved() can only be called after status=approved
8. **Privacy gate**: Verify run_privacy_gate() is called on both topic AND post content

### Output format:
Produce a security report with:
- **CRITICAL** (blocks deployment): Issues that could expose credentials or allow unauthorized posting
- **HIGH** (fix before production): Issues that weaken security posture
- **MEDIUM** (fix in polish): Issues that are good practice to fix
- **PASS**: Items that are correctly implemented
- **Overall security grade**: A/B/C/D/F

Write your findings to: `history/reports/security-review-linkedin-2026-03-09.md`

## Response snapshot

Security audit completed. All 7 files reviewed. Findings:

- CRITICAL: 0
- HIGH: 0
- MEDIUM: 2
  1. OAuth2 state parameter generated but not verified in CallbackHandler (CSRF risk — localhost-only scope reduces practical risk)
  2. vault/Pending_Approval/*.md and vault/Done/*.md not in .gitignore (draft post content could be committed)
- LOW: 1
  - Token file written without os.chmod(0o600) — world-readable by default
- PASS: 7
  1. No hardcoded credentials anywhere
  2. linkedin_token.json correctly in .gitignore
  3. AuthRequiredError raised (not logged) on missing token
  4. No token values in log statements
  5. PostUpdateInput validated with min_length=1, max_length=3000, Literal visibility
  6. HITL gate enforced — publish_approved() only callable after status=approved in frontmatter
  7. run_privacy_gate() called on both topic AND post content in draft_and_notify()

Overall grade: **B+**

Report written to: `/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/history/reports/security-review-linkedin-2026-03-09.md`

## Outcome

- Impact: Static security review of LinkedIn Auto-Poster Phase 5.5 complete. Grade B+. No deployment blockers identified. Two medium polish-tier issues surfaced.
- Tests: n/a (static analysis)
- Files: history/reports/security-review-linkedin-2026-03-09.md (created)
- Next prompts: Fix MEDIUM issues — add state verification in linkedin_auth.py CallbackHandler; add vault/Pending_Approval and vault/Done to .gitignore
- Reflection: All core security invariants correctly implemented. Good separation of concerns between auth, client, and server layers.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): manual static review — PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Run automated secret-scanning tool (truffleHog/gitleaks) as complement to manual review
