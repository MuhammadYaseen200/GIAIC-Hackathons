# Feature Specification: Full Communication Automation (Phase 6.5)

**Feature Branch**: `011-full-comms-automation`
**Created**: 2026-04-11
**Status**: Draft
**Input**: User description: "Phase 6.5: Full Communication Automation — WhatsApp, LinkedIn, Gmail, Calendar, Facebook, Instagram, Twitter full read/write/manage with HITL guardrails"

---

## Overview

Phase 6.5 extends the Personal AI Employee from a notification/briefing system into a full communication management platform. The AI Employee gains the ability to read, write, organize, and act across all of the CEO's communication channels — with Human-in-the-Loop (HITL) approval gates protecting sensitive actions.

**Scope**: 5 platform groups — WhatsApp, LinkedIn, Gmail/Email, Google Calendar, Social (Facebook / Instagram / Twitter)

---

## Clarifications

### Session 2026-04-11

- Q: After HITL 90s timeout — what happens to the pending action? → A: Non-blocking model. Agent sends the WhatsApp approval request and immediately moves on (does not wait or block). Action stays queued indefinitely until CEO responds. Pending actions are surfaced as reminders in the daily briefing until actioned. No auto-execution. No permanent cancellation on timeout.
- Q: Does CEO have an active WhatsApp Business account? → A: CEO has personal WhatsApp only. No CEO-owned Business account. A family member's WhatsApp Business account will be used for development and testing. Business WhatsApp support is in scope but secondary — personal WhatsApp is the primary account.
- Q: Gmail auto-replies — pre-written templates or AI-generated? → A: Pre-written templates (Option A). No LLM call for greeting detection — use lightweight rule-based classifier only (keyword/pattern match). Greeting formats vary by language and culture (Namaste, Assalam o Alaikum, etc.) — all map to one CEO-defined polite template per language or a universal English fallback. Avoids token cost on zero-value emails.
- Q: LinkedIn DMs — apply for API access or use browser automation fallback? → A: Apply for LinkedIn partner/Messaging API access (human task). DMs are deferred to Phase 7 if application is rejected. No browser automation or unofficial scraping — ban risk and ToS violation.
- Q: Cross-platform contacts — auto-link or keep separate? → A: Link on explicit CEO request only (Option C). ContactRecord stores all available identifiers (full name, phone number, email, platform-specific IDs) to distinguish people with the same name and support suggested matches. No auto-linking — CEO confirms every cross-platform link before it is saved.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — WhatsApp Full Management (Priority: P1)

The CEO wants the AI Employee to handle their WhatsApp communications end-to-end: reading new messages, drafting replies, sending approved messages, forwarding media, managing group interactions, and organizing the inbox — on both personal and business WhatsApp accounts.

**Why this priority**: WhatsApp is the primary real-time communication channel. HITL approval is already wired through WhatsApp, so it is the highest-leverage channel to automate first.

**Independent Test**: Can be fully tested by asking the AI to "summarize my unread WhatsApp messages and draft a reply to [contact]", approving via HITL, and verifying delivery.

**Acceptance Scenarios**:

1. **Given** new unread messages exist, **When** CEO asks "what's new on WhatsApp?", **Then** AI returns a prioritized summary of unread messages grouped by contact/group, with no raw message data exposed in logs.
2. **Given** CEO says "reply to [contact] that I'll call back at 5pm", **When** AI drafts the reply, **Then** HITL approval is requested before sending; message is delivered only after CEO approves.
3. **Given** CEO says "send [image/document] to [contact]", **When** AI sends media, **Then** media is delivered with a confirmation receipt; no media is sent without HITL if the file is sensitive.
4. **Given** CEO says "create a group with [list of contacts] called [name]", **When** AI creates the group, **Then** group is created with correct members and confirmation is sent to CEO.
5. **Given** CEO says "post a status update: [text]", **When** AI posts the status, **Then** status is visible with correct privacy settings as specified (or default "contacts only" if unspecified).
6. **Given** AI encounters an unknown contact number, **When** CEO explicitly says "save this contact as [name]", **Then** AI saves the contact and requests CEO verification before persisting.

---

### User Story 2 — Gmail Full Management (Priority: P2)

The CEO wants the AI Employee to read, categorize, draft, and manage their Gmail inbox — flagging opportunities, deleting clutter, auto-replying to low-stakes messages (greetings/thanks), and escalating sensitive emails for HITL approval before any reply is sent.

**Why this priority**: Email is the highest-volume communication channel. Automated triage and drafting reclaims significant CEO time daily.

**Independent Test**: Can be fully tested by triggering the Gmail tool against a live inbox, verifying categorization accuracy, checking that a draft reply is staged (not sent) for a sensitive email, and confirming that a greeting auto-reply is sent without HITL.

**Acceptance Scenarios**:

1. **Given** CEO says "organize my inbox", **When** AI processes the inbox, **Then** emails are categorized into: Urgent/Action-required, Opportunity Alerts, Promotional/Ads, Spam/Fraud, One-time codes, and Routine — with labels applied in Gmail.
2. **Given** an email is a simple greeting/thanks/congratulations with no decision content, **When** AI processes it, **Then** an auto-reply is sent without HITL, and the CEO is notified in the daily briefing.
3. **Given** an email requires a sensitive reply (financial, legal, personal, job offer, client decision), **When** AI drafts the response, **Then** draft is created in Gmail as a draft (not sent), and CEO is notified via WhatsApp HITL for approval.
4. **Given** CEO says "find and delete all spam and one-time-code emails older than 7 days", **When** AI processes the inbox, **Then** matching emails are moved to Trash (not permanently deleted) and CEO receives a count summary before permanent deletion.
5. **Given** an email contains an attachment flagged as sensitive (OTP, password, legal doc, suspicious link), **When** AI processes it, **Then** AI flags the email with a "Sensitive Attachment" label and includes it in the daily briefing with a warning.
6. **Given** CEO says "summarize this week's emails", **When** AI generates the summary, **Then** output includes: total received, action-required count, opportunities found, spam removed, and top 3 senders.

---

### User Story 3 — LinkedIn Full Management (Priority: P3)

The CEO wants the AI Employee to manage their LinkedIn presence: posting content (text, image, video), reacting/commenting on relevant posts, handling DMs (with HITL for job inquiries and decisions), managing connections, and monitoring analytics.

**Why this priority**: LinkedIn is the primary professional brand channel. Automated posting and engagement compounds network growth; DM handling protects against missed opportunities.

**Independent Test**: Can be fully tested by posting a text update, replying to a test DM (with HITL gate triggered), and verifying connection stats are returned.

**Acceptance Scenarios**:

1. **Given** CEO says "post on LinkedIn: [content]" (with optional image/video), **When** AI publishes the post, **Then** post is live on LinkedIn with correct media, and CEO receives a confirmation with the post URL.
2. **Given** a new LinkedIn DM is a job inquiry, **When** AI detects it, **Then** AI drafts a reply referencing CEO's current open-to-work status (from profile), and sends HITL approval to CEO before replying.
3. **Given** CEO says "accept all pending connection requests from [filter: e.g. AI/tech professionals]", **When** AI processes connections, **Then** only matching profiles are accepted; all others remain pending; CEO receives a summary.
4. **Given** CEO says "show my LinkedIn analytics for this week", **When** AI queries analytics, **Then** AI returns: impressions, profile views, post reach, follower growth, and top-performing post.
5. **Given** CEO says "update my LinkedIn headline to [new headline]", **When** AI updates the profile, **Then** profile is updated and CEO receives confirmation with a link.
6. **Given** CEO says "save this post", **When** AI saves the LinkedIn post, **Then** it appears in CEO's LinkedIn Saved Items, and the URL is logged to vault for reference.

---

### User Story 4 — Google Calendar Full Management (Priority: P4)

The CEO wants the AI Employee to create, update, delete, and query calendar events — including extracting events from emails, setting reminders, and blocking focus time.

**Why this priority**: Calendar management closes the loop between email/communication intake and action scheduling. Lower priority because Phase 6 already has read access; this extends to write.

**Independent Test**: Can be fully tested by asking the AI to "create a meeting with [contact] at [time]", verifying it appears in Google Calendar, and then asking AI to "reschedule to [new time]" and confirming the change.

**Acceptance Scenarios**:

1. **Given** CEO says "schedule a meeting with [contact] on [date] at [time]", **When** AI creates the event, **Then** event appears in Google Calendar with correct time, title, and attendee (invite sent if email available).
2. **Given** an incoming email contains a meeting invite or event details, **When** AI processes the email, **Then** AI offers to create a calendar event from the email with pre-filled details; CEO confirms via HITL before creation.
3. **Given** CEO says "what's on my calendar this week?", **When** AI queries the calendar, **Then** AI returns a human-readable agenda grouped by day with event names, times, and attendees.
4. **Given** CEO says "delete [event name] from my calendar", **When** AI deletes it, **Then** event is removed and attendees are notified of cancellation if applicable.
5. **Given** CEO says "block [day/time range] for deep work", **When** AI creates the block, **Then** a "Focus Time" event is created spanning the requested period with status set to "Busy".

---

### User Story 5 — Social Media Full Automation: Facebook, Instagram, Twitter (Priority: P5)

The CEO wants the AI Employee to manage their Facebook, Instagram, and Twitter/X presence: posting, commenting, reacting, managing DMs, community management, and analytics — mirroring LinkedIn capability per platform.

**Why this priority**: Social platforms compound brand presence and are lower risk than WhatsApp/Gmail (no private/sensitive data risk at same level). Analytics visibility is immediately actionable.

**Independent Test**: Can be fully tested by posting a tweet, verifying it appears on Twitter, then querying recent engagement, and confirming a DM reply requires HITL before sending.

**Acceptance Scenarios**:

1. **Given** CEO says "post [content] on Twitter/Facebook/Instagram", **When** AI publishes, **Then** post is live on the specified platform(s) with correct content; CEO receives confirmation with post URL/ID.
2. **Given** a DM arrives on any social platform from a non-spam account, **When** AI processes it, **Then** AI drafts a reply and sends HITL approval to CEO before responding.
3. **Given** CEO says "show my social media summary for today", **When** AI queries all platforms, **Then** AI returns: posts published today, total reach/impressions, new followers, DMs received, and top engagement.
4. **Given** CEO says "comment [text] on [post URL]", **When** AI comments, **Then** comment is posted and CEO receives confirmation.
5. **Given** a comment on CEO's posts is flagged as spam or offensive, **When** AI detects it, **Then** AI hides/deletes the comment (within platform rules) and includes it in the daily briefing report.

---

### Edge Cases

- What happens when the WhatsApp bridge goes offline mid-action? — AI logs the failure, queues the action, retries after bridge reconnect; CEO is notified in next briefing.
- What happens when a Gmail reply draft is declined by CEO? — Draft is kept as-is in Drafts folder; CEO can edit manually. AI logs the declination and asks if alternative reply is needed.
- What happens when a LinkedIn post fails due to API rate limiting? — AI retries after cooldown period, notifies CEO of the delay, never double-posts.
- What happens when a calendar event conflicts with an existing event? — AI detects the conflict and presents both events to CEO before creating; does not auto-resolve conflicts.
- What happens when a social platform DM is from a potential client vs. spam? — AI classifies by signal strength (verified account, mutual connections, keywords); uncertain cases always get HITL; clear spam is silently deleted.
- What happens when WhatsApp bulk messages are requested for more than 10 recipients? — AI caps at 10 and warns CEO of ban risk; does NOT proceed beyond cap regardless of instruction.
- What happens when `OAUTHLIB_RELAX_TOKEN_SCOPE` triggers on LinkedIn re-auth? — Same WSL2 manual code-paste fallback flow as Gmail; AI prints the auth URL and waits for code.

---

## Requirements *(mandatory)*

### Functional Requirements

#### WhatsApp
- **FR-001**: System MUST read and return a prioritized summary of unread WhatsApp messages on demand, grouping by contact and group chat.
- **FR-002**: System MUST draft WhatsApp text replies and require HITL approval before sending to any recipient.
- **FR-003**: System MUST send text messages, links, images, videos, documents, and audio files to individual contacts after HITL approval.
- **FR-004**: System MUST support group chat interactions: reply in group, mention members, and send broadcast messages (max 10 recipients per broadcast to prevent ban risk).
- **FR-005**: System MUST post, update, and delete WhatsApp Status with configurable privacy (default: "My Contacts").
- **FR-006**: System MUST save new contacts only on explicit CEO command with a verification confirmation step.
- **FR-007**: System MUST organize chats: star/unstar, archive/unarchive, mark read/unread, and mute/unmute on demand.
- **FR-008**: System MUST support personal WhatsApp as the primary account. WhatsApp Business support is secondary — a family member's Business account will be used for development and testing. Dual-bridge configuration (personal on port 8080, Business on port 8081) is the target architecture, but personal-only is the MVP.
- **FR-009**: System MUST create WhatsApp groups with specified members and settings (group name, description) after HITL approval.
- **FR-010**: System MUST NOT attempt voice or video calls autonomously — these require explicit real-time CEO initiation.

#### Gmail / Email
- **FR-011**: System MUST categorize all inbox emails into: Urgent/Action-required, Opportunity, Promotional, Spam/Fraud, One-time codes, and Routine — applying Gmail labels.
- **FR-012**: System MUST auto-reply to low-stakes emails (greetings, thanks, congratulations, simple requests with no decision content) without HITL, using CEO-defined pre-written templates. Detection MUST use a lightweight rule-based classifier (keyword/pattern matching) — NOT an LLM call — to avoid unnecessary token costs. Templates must support multi-language/cultural greetings (Assalam o Alaikum, Namaste, Hi/Hello, etc.) mapping to a universal polite reply or a CEO-defined per-language template.
- **FR-013**: System MUST create Gmail drafts for all sensitive reply candidates and send HITL approval via WhatsApp before sending.
- **FR-014**: System MUST detect and flag sensitive attachments: OTPs, passwords, legal documents, suspicious/phishing links, media containing PII.
- **FR-015**: System MUST move (not permanently delete) spam, fraud, one-time-code, and promotional emails to Trash on demand after CEO confirms a count summary.
- **FR-016**: System MUST extract event/meeting information from emails and offer calendar event creation via HITL.
- **FR-017**: System MUST generate daily, weekly, and monthly email summaries including: total received, action-required count, opportunities, spam removed, top senders.

#### LinkedIn
- **FR-018**: System MUST publish posts on LinkedIn with text, images, video, and document attachments after HITL approval.
- **FR-019**: System MUST react (like/celebrate/support) and comment on LinkedIn posts matching CEO's defined interest filters on demand.
- **FR-020**: System MUST handle LinkedIn DMs via the official LinkedIn Messaging API (requires partner access application — HT required). If API access is granted: classify DM intent (job inquiry, networking, spam, sales) and draft context-aware replies for HITL approval. If partner access is denied: LinkedIn DMs are deferred to Phase 7. Browser automation and unofficial scraping are explicitly prohibited (ban risk, ToS violation).
- **FR-021**: System MUST manage connections: accept, reject, send, withdraw connection requests with filter-based batch operations (never auto-bulk-connect to prevent ban).
- **FR-022**: System MUST update LinkedIn profile fields: headline, summary, experience, skills, services on demand.
- **FR-023**: System MUST query and return LinkedIn analytics: impressions, profile views, post reach, follower growth, top post.
- **FR-024**: System MUST save and unsave LinkedIn posts to CEO's Saved Items on demand.
- **FR-025**: System MUST NOT send bulk DMs to more than 5 recipients per day to prevent LinkedIn account restriction.

#### Google Calendar
- **FR-026**: System MUST create calendar events with title, date, time, duration, attendees, location, and description on demand.
- **FR-027**: System MUST update and delete existing events, sending cancellation notifications to attendees if applicable.
- **FR-028**: System MUST query and return the CEO's calendar for any date range in a readable agenda format.
- **FR-029**: System MUST detect scheduling conflicts before creating events and present both conflicting events to CEO for resolution.
- **FR-030**: System MUST create "Focus Time / Deep Work" blocks that mark the CEO as Busy on the calendar.
- **FR-031**: System MUST extract and propose calendar events from email content via the Gmail integration (FR-016 link).

#### Facebook / Instagram / Twitter
- **FR-032**: System MUST publish posts on Facebook, Instagram, and Twitter/X with text, images, and video after HITL approval.
- **FR-033**: System MUST reply to comments on CEO's posts after HITL approval.
- **FR-034**: System MUST handle platform DMs with HITL approval before any reply is sent.
- **FR-035**: System MUST hide or delete spam/offensive comments on CEO's posts within platform API constraints.
- **FR-036**: System MUST return a daily social media summary: posts published, reach/impressions, new followers, DMs received, top engagement.
- **FR-037**: System MUST follow/unfollow accounts on demand on Twitter/X and Facebook pages.

#### Cross-Platform / HITL Guardrails
- **FR-038**: System MUST enforce HITL approval for ALL outbound communications that are irreversible (send message, post, delete email, accept/reject connection). HITL requests are non-blocking — agent sends the approval message and immediately continues; the action waits in queue indefinitely until CEO responds. Pending actions are surfaced in the daily briefing as reminders until actioned. Actions are NEVER auto-executed due to timeout.
- **FR-039**: System MUST NOT expose raw PII (phone numbers, email addresses, full message content) in logs or terminal output.
- **FR-040**: System MUST respect platform-specific rate limits and ban-risk thresholds: WhatsApp ≤10 bulk recipients, LinkedIn DMs ≤5/day, LinkedIn connections ≤20/day auto-accept.
- **FR-041**: System MUST queue failed actions (bridge offline, API error) and retry on next run, notifying CEO of the delay.
- **FR-042**: System MUST log all actions taken to `vault/Logs/` with timestamp, platform, action type, and outcome (no PII in logs per SC-003 from Phase 6).
- **FR-043**: When routing tasks to free/third-party models (Tier 1), system MUST send only metadata (email subject, sender domain, keyword flags, message length) — NEVER the full message body or attachment content. Full content is sent only to Tier 2 (Anthropic), which already handles CEO data. (See ADR-0020)

### Key Entities

- **CommunicationAction**: Represents a single outbound action (send message, post, reply, delete) with: platform, action_type, target, content_ref, status (pending_hitl / approved / sent / failed), created_at, approved_at.
- **HITLRequest**: A pending approval sent to CEO via WhatsApp: action_id, summary_text (≤500 chars, SC-002), sent_at, response (approved / declined / pending). No expiry timeout — requests remain pending indefinitely until CEO replies. Pending requests surface in daily briefing as reminders.
- **ContactRecord**: A contact entry with all known identifiers: full_name, phone_number, email_address, platform_ids (WhatsApp JID, LinkedIn URL, Gmail address, Twitter handle, Instagram handle, Facebook ID), last_interaction, CEO-verified flag. Cross-platform linking is never automatic — AI may suggest a link when identifiers overlap, but CEO must explicitly confirm before the link is saved. Multiple contacts with the same name are distinguished by their unique identifiers (phone/email).
- **ContentDraft**: A draft message/post before approval: platform, content, attachments, target, draft_created_at, hitl_status.
- **PlatformCredential**: OAuth token or session key per platform: platform, token_ref (pointer to env var, never inline), expires_at, requires_reauth flag.
- **InboxSummary**: Aggregated view of unread/unprocessed items per platform: platform, unread_count, action_required_count, opportunities_count, generated_at.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: CEO can send a WhatsApp message to any contact within 60 seconds of issuing the command, including HITL approval time.
- **SC-002**: 100% of outbound irreversible communications (message sends, posts, email replies) require and receive explicit HITL approval before execution — zero silent actions.
- **SC-003**: Gmail inbox categorization achieves ≥85% accuracy on the CEO's live inbox (measured by CEO spot-check over 7 days).
- **SC-004**: LinkedIn post publishing succeeds within 30 seconds of HITL approval, with zero double-posts on retry.
- **SC-005**: Calendar event creation, update, and deletion complete without error for 100% of well-formed CEO requests (correct date, contact, duration provided).
- **SC-006**: Social media daily summary (all 3 platforms) is returned within 10 seconds of CEO's request.
- **SC-007**: Zero platform account restrictions or bans result from AI Employee actions over a 90-day operating window — enforced via rate-limit caps (FR-040).
- **SC-008**: All failed actions are queued and retried; CEO is notified of any action that fails more than 2 consecutive retries.
- **SC-009**: PII audit of vault/Logs/ confirms zero raw phone numbers, email addresses, or full message content stored in log files.
- **SC-010**: CEO can get a cross-platform communication summary (WhatsApp, Gmail, LinkedIn, Social) in a single briefing request, with all sections populated within 30 seconds.

---

## Assumptions

1. **WhatsApp bridge**: The existing Go-based WhatsApp bridge (`~/whatsapp-mcp/whatsapp-bridge/`) is extended to support media send and group management. CEO's personal WhatsApp is the primary bridge (port 8080). WhatsApp Business support uses a family member's account for development/testing via a second bridge instance (port 8081) — not a CEO-owned Business account.
2. **LinkedIn API**: LinkedIn's official OAuth2 API is used for profile, posts, and analytics. DM access requires the LinkedIn Messaging API (requires partner approval) — Phase 6.5 assumes this is obtainable or falls back to browser automation via a headless approach.
3. **Facebook/Instagram**: Meta Graph API via the existing `mcp_servers/facebook/` integration. Instagram is accessed via the Instagram Graph API (requires Facebook Business Suite connection).
4. **Twitter/X**: Existing `mcp_servers/twitter/` integration. Free tier allows read + limited write; if rate limits are hit, CEO is notified with retry ETA.
5. **HITL channel**: All HITL approval requests are delivered via WhatsApp (existing SC-001/SC-002 constraints from Phase 6 apply: 90s timeout, ≤500 char summary).
6. **Credential storage**: All tokens/credentials stored only in `.env` and `vault/` (gitignored). No new secrets are hardcoded.
7. **Auto-reply templates**: A small set of pre-approved auto-reply templates for greetings/thanks is defined by CEO before enabling auto-reply (not AI-generated freestyle).
8. **Calendar write scope**: Google Calendar OAuth scope is extended from `calendar.readonly` to `calendar` (full read/write). Re-auth via WSL2 manual code-paste flow required.
9. **Voice/video calls**: Explicitly out of scope for autonomous execution. AI can prepare call details but cannot initiate calls.
10. **LinkedIn DM API**: If LinkedIn Messaging API is unavailable, DM read/reply is deferred to Phase 7.

---

## Constraints & Non-Goals

### Constraints
- WhatsApp bulk messages: max 10 recipients per broadcast (ban risk)
- LinkedIn DMs: max 5 per day auto-drafted (account restriction risk)
- LinkedIn auto-accept connections: max 20 per day
- HITL timeout: 90 seconds (SC-001 inherited from Phase 6)
- HITL message: ≤500 characters (SC-002 inherited from Phase 6)
- No PII in logs (SC-003 inherited from Phase 6)
- OAuth re-auth follows WSL2 manual code-paste flow for all platforms

### Non-Goals (explicitly excluded)
- WhatsApp voice/video call initiation (real-time action, out of scope)
- LinkedIn bulk DM campaigns (ban risk)
- Autonomous email replies without HITL for any sensitive content
- Managing multiple CEO accounts on the same platform (1 account per platform)
- Building new MCP servers from scratch — Phase 6.5 extends existing MCP servers
- Platform web scraping as a primary method (API-first; scraping only as fallback for analytics)
- Payments, e-commerce, or transactional operations via any platform

---

## Dependencies

| Dependency | Status | Owner | Notes |
|------------|--------|-------|-------|
| WhatsApp Go bridge | Running (Phase 6) | CEO | Needs media-send extension |
| Gmail MCP (`mcp_servers/gmail/`) | Running (Phase 6) | Agent | Needs write/draft tools added |
| Calendar MCP (`mcp_servers/calendar/`) | Running (Phase 6, read-only) | Agent | Needs write scope + create/update/delete tools |
| LinkedIn MCP (`mcp_servers/linkedin/`) | Running (Phase 6) | Agent | Needs DM + profile-write + analytics tools |
| Facebook/Instagram MCP (`mcp_servers/facebook/`) | Running (Phase 6) | Agent | Needs comment/DM/analytics tools |
| Twitter MCP (`mcp_servers/twitter/`) | Running (Phase 6) | Agent | Needs DM + analytics tools |
| HITL approval loop | Running (Phase 6) | Agent | Shared across all new actions |
| LinkedIn Messaging API approval | Pending | CEO | HT: Apply for LinkedIn partner access |

---

## Risks

1. **LinkedIn Messaging API access denied** — CEO will apply for LinkedIn partner/Messaging API access (HT). If rejected: DM read/reply deferred to Phase 7; LinkedIn posting, profile management, search, and analytics proceed as planned in Phase 6.5. No browser automation fallback.
2. **WhatsApp bridge instability under media load** — Mitigation: media send uses separate retry queue with 3-attempt limit; bridge restart instructions in actionable error messages.
3. **OAuth token churn** — LinkedIn 60-day tokens, Facebook ~60-day tokens require periodic re-auth. Mitigation: `PlatformCredential.requires_reauth` flag triggers early warning in CEO briefing 7 days before expiry.
