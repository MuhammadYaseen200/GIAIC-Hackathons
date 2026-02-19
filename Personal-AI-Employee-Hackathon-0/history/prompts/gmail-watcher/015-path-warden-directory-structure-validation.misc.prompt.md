---
id: 015
title: PATH-WARDEN Directory Structure Validation
stage: misc
date: 2026-02-19
surface: agent
model: claude-sonnet-4-6
feature: gmail-watcher
branch: 005-gmail-watcher
user: MuhammadYaseen200
command: PATH-WARDEN validation
labels: ["path-warden","validation","directory-structure","compliance","gmail-watcher"]
links:
  spec: specs/005-gmail-watcher/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - (read-only) specs/005-gmail-watcher/plan.md
  - (read-only) specs/005-gmail-watcher/checklists/requirements.md
  - (read-only) history/prompts/gmail-watcher/ (directory scan)
tests:
  - none (validation task, no tests run)
---

## Prompt

You are acting as PATH-WARDEN for the Gmail Watcher project at /mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/.

Validate that all files are in their correct directory locations per the spec plan.

The expected directory structure (from specs/005-gmail-watcher/plan.md) is:
```
Personal-AI-Employee-Hackathon-0/
├── watchers/
│   ├── __init__.py
│   ├── base_watcher.py
│   ├── gmail_watcher.py
│   ├── models.py
│   └── utils.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_base_watcher.py
│   │   ├── test_gmail_watcher.py
│   │   ├── test_models.py
│   │   └── test_utils.py
│   └── integration/
│       └── test_gmail_integration.py
├── scripts/
│   └── gmail_auth.py
├── vault/
│   ├── Needs_Action/
│   ├── Inbox/
│   └── Logs/
├── specs/005-gmail-watcher/
│   ├── spec.md
│   ├── plan.md
│   └── tasks.md
├── history/prompts/gmail-watcher/
├── history/adr/
├── .gitignore
├── .env.example
├── pyproject.toml
└── CLAUDE.md
```

Tasks:
1. List the actual directory tree (use ls/find on the project root)
2. Check each expected file/directory exists
3. Flag any files found that are NOT in the plan (misplaced or unexpected)
4. Check if specs/005-gmail-watcher/checklists/ directory exists - is it documented in plan.md?

Report: PASS or FAIL with specific violations. Keep it brief.

## Response snapshot

Result: FAIL — 3 high-severity violations found.

Checked 24 expected paths. 22 PASS, 2 FAIL:
- `pyproject.toml` — MISSING (not present at project root)
- `.env.example` — MISSING (not present at project root)

Undocumented files/directories found:
- `credentials.json` at project root (HIGH — sensitive OAuth2 file; plan requires it at GMAIL_CREDENTIALS_PATH path, not committed to repo)
- `specs/005-gmail-watcher/checklists/requirements.md` — exists but not documented in plan.md
- `requirements.txt` / `requirements-dev.txt` — present but plan specifies pyproject.toml
- `docs/`, `mcp-servers/`, `orchestrator/` — no plan entry
- Extra vault subdirectories: Approved/, CEO_Briefings/, Done/, Pending_Approval/, Plans/, Templates/

`checklists/` directory: EXISTS at specs/005-gmail-watcher/checklists/ — NOT documented in plan.md (word "checklists" has zero occurrences in plan.md).

## Outcome

- Impact: Identified 3 high-severity and 4 low/info violations against the plan's expected structure
- Tests: none (structural validation only)
- Files: no files created or modified; read-only validation
- Next prompts: Fix violations — create pyproject.toml, create .env.example, verify credentials.json is in .gitignore and not committed, optionally document checklists/ in plan.md
- Reflection: The credentials.json at project root is the most critical finding; it may represent a real secret file that should not be in version control

## Evaluation notes (flywheel)

- Failure modes observed: none — tree scan and plan.md grep executed cleanly
- Graders run and results (PASS/FAIL): PATH-WARDEN structural check — FAIL (3 HIGH violations)
- Prompt variant (if applicable): null
- Next experiment: Re-run PATH-WARDEN after pyproject.toml and .env.example are created and credentials.json is confirmed gitignored
