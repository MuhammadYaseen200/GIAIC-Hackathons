# Feature Specification: LinkedIn Auto-Poster + Cron Scheduling

**Feature Branch**: `009-linkedin-cron-silver`
**Created**: 2026-03-05
**Status**: Complete
**Phase**: 5.5 — Silver Tier Completion
**Input**: LinkedIn Auto-Poster with HITL approval + Cron scheduling for orchestrator and daily drafting

---

## Clarifications

### Session 2026-03-05

- Q: When the LinkedIn access token expires, should the system auto-refresh using a stored refresh token or require manual re-authentication? → A: Auto-refresh — request `offline_access` scope during initial `linkedin_auth.py` OAuth2 flow; store refresh token in `linkedin_token.json`; automatically refresh on 401 response without owner intervention.
- Q: What should drive the daily auto-draft post topic? → A: Configurable topic file — owner maintains `vault/Config/linkedin_topics.md` as a list of topics; AI picks one randomly each day.
- Q: What format should the WhatsApp approval notification use? → A: Structured summary — topic name, type, content preview (first 300 chars), any links/attachments/media referenced, vault file path for full draft, and approve/reject instructions.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — LinkedIn Post Drafted and Approved via WhatsApp (Priority: P1)

The owner wants the AI to draft a professional LinkedIn post about their AI/web dev work, send it for WhatsApp approval, and publish it only after explicit "approve" reply — exactly like the email HITL workflow.

**Why this priority**: This is the core Silver tier requirement. Without this, LinkedIn posting cannot happen at all.

**Independent Test**: Can be fully tested by running `python orchestrator/linkedin_poster.py --draft "building AI agents"`, receiving WhatsApp notification, replying "approve", and verifying the post appears on LinkedIn profile.

**Acceptance Scenarios**:

1. **Given** the owner triggers a LinkedIn draft with a topic, **When** the AI drafts content through the Privacy Gate, **Then** a draft appears in `vault/Pending_Approval/` with type=linkedin_post and the owner receives a WhatsApp notification containing: topic name, type, 300-character content preview, any referenced links, vault file path for the full draft, and approve/reject instructions.

2. **Given** a post is pending in `vault/Pending_Approval/`, **When** the owner replies "approve" via WhatsApp, **Then** the post is published to LinkedIn within 60 seconds and logged to `vault/Logs/linkedin_posts.jsonl` with status=published.

3. **Given** a post is pending in `vault/Pending_Approval/`, **When** the owner replies "reject" or ignores for 24 hours, **Then** the post is moved to `vault/Rejected/` and logged with status=rejected — no LinkedIn post is made.

4. **Given** the Privacy Gate detects sensitive content in a draft topic, **When** the draft is generated, **Then** the sensitive terms are redacted to `[REDACTED]` before the draft is shown to the owner for approval.

---

### User Story 2 — Daily LinkedIn Post Drafted Automatically at Scheduled Time (Priority: P2)

The AI automatically drafts one LinkedIn post every morning about the owner's AI learning journey and sends it for approval — no manual trigger required.

**Why this priority**: This is the "Automatically Post on LinkedIn" Silver tier requirement. The cron schedule drives consistent professional presence without daily manual effort.

**Independent Test**: Can be fully tested by setting cron time to 2 minutes from now, waiting for WhatsApp notification with a LinkedIn draft, and verifying `vault/Pending_Approval/` contains the draft file.

**Acceptance Scenarios**:

1. **Given** the cron job is installed and the scheduled time arrives, **When** no LinkedIn post has been made today, **Then** the system automatically drafts one post about AI/web dev/freelance and sends it for WhatsApp approval.

2. **Given** a LinkedIn post was already published today, **When** the cron schedule triggers again, **Then** the system skips drafting (rate limit: 1 post per day) and logs "daily limit reached" to `vault/Logs/cron.log`.

3. **Given** LinkedIn API is unreachable at scheduled time, **When** the cron job runs, **Then** the draft is still created and awaits approval — the failure only occurs at publish time, not at draft time. Warning is logged.

---

### User Story 3 — Orchestrator Runs on Cron Every 15 Minutes (Priority: P2)

The main orchestrator processes `vault/Needs_Action/` items automatically every 15 minutes without manual invocation.

**Why this priority**: Cron scheduling is the second explicit Silver tier requirement. Without it, the AI Employee requires manual triggering — not autonomous.

**Independent Test**: Can be tested by placing a test item in `vault/Needs_Action/` and verifying it is processed within 15 minutes with output in `vault/Logs/cron.log`.

**Acceptance Scenarios**:

1. **Given** cron is installed via `scripts/setup_cron.sh`, **When** 15 minutes elapse, **Then** the orchestrator runs, processes any items in `vault/Needs_Action/`, and appends a timestamped entry to `vault/Logs/cron.log`.

2. **Given** `scripts/setup_cron.sh` is run, **When** the script completes, **Then** `crontab -l` shows exactly two entries: orchestrator (every 15 min) and LinkedIn drafter (daily at configured time).

3. **Given** `scripts/remove_cron.sh` is run, **When** the script completes, **Then** `crontab -l` shows neither the orchestrator nor the LinkedIn drafter entries.

---

### User Story 4 — Vault-Triggered LinkedIn Post from Needs_Action Item (Priority: P3)

Any system component can request a LinkedIn post by writing a structured item to `vault/Needs_Action/` with `type: linkedin_post`. The orchestrator picks it up and routes it through the HITL workflow.

**Why this priority**: Enables future automation (e.g., posting when a project milestone is reached) without hardcoding LinkedIn logic everywhere.

**Independent Test**: Can be tested by manually writing a markdown file with `type: linkedin_post` frontmatter to `vault/Needs_Action/` and confirming a WhatsApp approval request arrives within 15 minutes.

**Acceptance Scenarios**:

1. **Given** a file with `type: linkedin_post` and `content: "topic"` in `vault/Needs_Action/`, **When** the orchestrator runs, **Then** it drafts a LinkedIn post on that topic, sends for WhatsApp approval, and moves the trigger file to `vault/Done/`.

2. **Given** a `vault/Needs_Action/` item has `tag: #linkedin` in its body, **When** the orchestrator runs, **Then** it detects the LinkedIn tag and routes it through the LinkedIn poster workflow.

---

### Edge Cases

- **LinkedIn API rate limit hit**: If more than 1 post is approved in a day, second post is queued to next day's slot and owner is notified via WhatsApp.
- **WhatsApp bridge offline during approval**: Draft stays in `vault/Pending_Approval/` indefinitely. On bridge recovery, owner is notified. No post is made without approval.
- **Owner never responds**: Draft expires after 24 hours, moved to `vault/Rejected/` with reason=expired. Logged.
- **LinkedIn token expired**: OAuth2 refresh attempted automatically. If refresh fails, owner notified via WhatsApp with re-auth instructions. Graceful degradation: no crash.
- **Post content is empty after Privacy Gate redaction**: Draft is discarded, not sent for approval. Warning logged.
- **Cron job runs while previous orchestrator is still running**: New invocation detects lock file and exits cleanly. No duplicate processing.
- **`setup_cron.sh` run twice**: Script is idempotent — checks for existing entries before adding. No duplicates in crontab.

---

## Requirements *(mandatory)*

### Functional Requirements

**LinkedIn Auto-Poster:**

- **FR-001**: The system MUST require explicit owner approval via WhatsApp before publishing any LinkedIn post.
- **FR-002**: The system MUST apply the Privacy Gate to all AI-drafted post content before presenting it for approval — no sensitive data may appear in drafts.
- **FR-003**: The system MUST limit publishing to a maximum of 1 LinkedIn post per calendar day regardless of how many approvals are given.
- **FR-004**: The system MUST log every LinkedIn post attempt (draft, approved, rejected, published, failed) to `vault/Logs/linkedin_posts.jsonl` with timestamp, status, and content hash.
- **FR-005**: The system MUST write approval requests to `vault/Pending_Approval/` with YAML frontmatter including type, topic, content preview, expiry timestamp, visibility, and any referenced links. The WhatsApp notification MUST include: topic name, type (`linkedin_post`), content preview (first 300 characters), any links or media referenced in the draft, vault file path, and `Reply "approve" or "reject"` instructions.
- **FR-006**: The system MUST support manual trigger: the owner can run a command with a topic to immediately draft and queue a post for approval.
- **FR-007**: The system MUST detect `vault/Needs_Action/` items with `type: linkedin_post` or body tag `#linkedin` and route them through the approval workflow.
- **FR-008**: The system MUST gracefully degrade when LinkedIn is unreachable: draft and approval workflow continues, failure only occurs at publish time with warning logged.
- **FR-009**: The system MUST never expose LinkedIn OAuth tokens or credentials in logs, vault files, or post content.
- **FR-010**: The system MUST support post visibility configuration: PUBLIC (default) or CONNECTIONS only.
- **FR-017**: The system MUST read daily post topics from `vault/Config/linkedin_topics.md`; if the file is absent, fall back to four built-in default topics. The owner can update the file at any time without restarting the system.

**Cron Scheduling:**

- **FR-011**: The system MUST provide `scripts/setup_cron.sh` that installs cron entries with absolute paths and sources `.env` before execution.
- **FR-012**: The cron schedule MUST run the main orchestrator every 15 minutes to process `vault/Needs_Action/` items.
- **FR-013**: The cron schedule MUST run the LinkedIn post drafter once daily at a configurable time (default 09:00, set via `CRON_LINKEDIN_TIME` in `.env`).
- **FR-014**: All cron job output (stdout + stderr) MUST be appended to `vault/Logs/cron.log` with timestamps.
- **FR-015**: The system MUST provide `scripts/remove_cron.sh` that cleanly removes all project cron entries without affecting other system cron jobs.
- **FR-016**: `scripts/setup_cron.sh` MUST be idempotent — running it multiple times must not create duplicate cron entries.

### Key Entities

- **LinkedInDraft**: Pending post content, topic, visibility, expiry timestamp, Privacy Gate result, approval status.
- **LinkedInPost**: Published post record: post URN from LinkedIn API, published timestamp, content hash, word count.
- **CronEntry**: Schedule definition: job name, schedule expression, command, log target.
- **ApprovalRequest**: vault/Pending_Approval/ file: type=linkedin_post, content preview, created, expires, agent.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A LinkedIn post draft is created and WhatsApp approval notification sent within 30 seconds of manual trigger or vault item detection.
- **SC-002**: Approved posts are published to LinkedIn within 60 seconds of owner "approve" reply.
- **SC-003**: Zero LinkedIn posts are ever published without an explicit "approve" reply — invariant holds across 100% of test cases.
- **SC-004**: The Privacy Gate blocks 100% of posts containing sensitive patterns (passwords, phone numbers, PII) before they reach the owner for approval.
- **SC-005**: The cron orchestrator processes `vault/Needs_Action/` items within 15 minutes of file creation — verified across 95% of runs.
- **SC-006**: `scripts/setup_cron.sh` runs to completion in under 5 seconds and `crontab -l` shows the correct entries immediately after.
- **SC-007**: `scripts/setup_cron.sh` is idempotent — running it 3 times produces exactly 2 cron entries (not 6).
- **SC-008**: Test coverage for LinkedIn MCP tools and cron scripts exceeds 80%.
- **SC-009**: All LinkedIn post events are traceable in `vault/Logs/linkedin_posts.jsonl` — no silent failures.
- **SC-010**: LinkedIn token refresh succeeds automatically when token expires, without owner intervention, in 95% of cases.

---

## Assumptions

- Owner has created a LinkedIn Developer App with "Share on LinkedIn" product approved (HT-013 DONE).
- `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET` are present in `.env`.
- `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_REFRESH_TOKEN`, and `LINKEDIN_PERSON_URN` will be generated by `scripts/linkedin_auth.py` during implementation. The auth flow MUST request `offline_access` scope to obtain a refresh token.
- WhatsApp bridge (Go bridge on port 8080) is running for HITL notifications.
- The existing `HITLManager` and `PrivacyGate` classes are reused without modification.
- LinkedIn personal app is limited to 1 post per day — this is a hard API constraint, not a configurable preference.
- Cron daemon is already running on the system (confirmed: PID 1076 in session audit).
- Post content topics are read from `vault/Config/linkedin_topics.md` — a markdown list maintained by the owner. Default seed topics: AI learning progress, web development projects, freelance availability, hackathon milestones. If the file is missing, the system falls back to these four defaults.
- `linkedin_token.json` is gitignored and stored in project root alongside `token.json` and `calendar_token.json`.

---

## Out of Scope

- LinkedIn comment reading or responding (Phase 6+ social media manager)
- LinkedIn messaging / InMail (future phase)
- LinkedIn analytics / post performance tracking (future phase)
- Multiple LinkedIn accounts (single owner account only)
- Image or video attachments in posts (text-only posts for this phase)
- Twitter, Facebook, Instagram integration (future social media phase)
- n8n or external workflow orchestration (cron-native only for this phase)

---

## Dependencies

- `watchers/privacy_gate.py` — PrivacyGate class (existing, Phase 5)
- `orchestrator/hitl_manager.py` — HITLManager class (existing, Phase 5)
- `mcp_servers/whatsapp/bridge.py` — GoBridge for WhatsApp HITL notifications (existing, Phase 5)
- `mcp_servers/gmail/server.py` — reference pattern for MCP server structure (existing, Phase 4)
- LinkedIn Developer App credentials (HT-013, DONE)
- Cron daemon running on system (confirmed)
- `requests-oauthlib` or `httpx` for LinkedIn API calls (to be added to requirements.txt)
