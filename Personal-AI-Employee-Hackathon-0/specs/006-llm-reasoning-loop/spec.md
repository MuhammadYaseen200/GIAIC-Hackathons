# Feature Specification: Multi-LLM Reasoning Loop (Ralph Wiggum Orchestrator) -- Phase 3

**Feature Branch**: `006-llm-reasoning-loop`
**Created**: 2026-02-22
**Status**: Complete
**Phase**: 3 (Claude Reasoning Loop)
**Input**: User description: "Build Multi-LLM reasoning loop that reads vault/Needs_Action/ files, sends to LLM for decision, writes drafts, updates status, and logs every decision -- with provider abstraction layer supporting Claude, OpenAI, Gemini, OpenRouter, Qwen, GLM, Goose via .env config"

## Governance Alignment

This specification is governed by the following project control documents. All requirements herein MUST comply with these references. Any conflict between this spec and a governance document MUST be resolved in favor of the governance document.

| Document | Principles Applied | Reference |
|----------|-------------------|-----------|
| Constitution | I (Spec-First), II (Local-First Privacy), III (HITL), V (TDD), VI (Watcher Architecture), VII (Phase-Gated), IX (Security), X (Graceful Degradation) | `.specify/memory/constitution.md` |
| LOOP.md | Loop 1 (Spec-Driven), Loop 2 (Ralph Wiggum -- primary), Loop 3 (HITL), Loop 4 (Directory Guard) | `ai-control/LOOP.md` |
| MCP.md | Fallback Protocol, MCP Development Standards | `ai-control/MCP.md` |
| AGENTS.md | Modular-AI-Architect (design), Backend-Builder (implement), Spec-Architect (this spec) | `ai-control/AGENTS.md` |
| SWARM.md | Phase 3 config: Pipeline (design then implement) | `ai-control/SWARM.md` |
| HUMAN-TASKS.md | HT-009 (LLM API Key Setup -- new) | `ai-control/HUMAN-TASKS.md` |
| ADR-0001 | BaseWatcher ABC design (orchestrator follows same pattern) | `history/adr/0001-watcher-base-class-design.md` |
| ADR-0003 | Local file-based persistence (state + JSONL logs) | `history/adr/0003-local-file-based-data-persistence.md` |

## Clarifications

### Session 2026-02-22

- Q: What provider abstraction architecture should the system use? → A: Unified OpenAI-compatible core for 6 providers (OpenAI, OpenRouter, Qwen, GLM, Goose, Gemini via `generativelanguage.googleapis.com/v1beta/openai/`), with a dedicated adapter class only for Anthropic (primary provider). This means only 2 code paths: `AnthropicAdapter` and `OpenAICompatibleAdapter` (parameterized by base_url + api_key).

## Phase 3 Entry/Exit Criteria

Per Constitution Principle VII (Phase-Gated Delivery), Phase 3 MUST NOT begin until Phase 2 exit criteria are met, and Phase 4 MUST NOT begin until Phase 3 exit criteria are met.

### Entry Criteria (from Phase 2)

- [x] BaseWatcher abstract class exists with lifecycle contract (start/stop/poll/process_item)
- [x] GmailWatcher extends BaseWatcher, connects via OAuth2, reads inbox
- [x] Emails produce correctly formatted markdown files in vault directories
- [x] Watcher runs continuously without crashes (52 emails processed in live run 2026-02-20)
- [x] Integration tests pass with mock Gmail data
- [x] All Phase 2 acceptance scenarios verified by QA-Overseer
- [x] `vault/Needs_Action/` contains real emails with `status: pending` in YAML frontmatter
- [x] `vault/Logs/gmail_watcher_state.json` exists with valid persistent state

### Exit Criteria (for Phase 3)

- [x] Multi-LLM provider abstraction layer exists, supporting at minimum Claude and one alternative (OpenAI or Gemini)
- [x] Switching LLM providers requires ONLY `.env` changes, zero code modifications (SC-001)
- [x] Ralph Wiggum orchestrator reads `vault/Needs_Action/` files with `status: pending`
- [x] LLM produces structured JSON decisions for every processed email (SC-003)
- [x] Draft replies written to `vault/Drafts/` for `draft_reply` decisions
- [x] YAML frontmatter updated on every processed file: `pending` transitions to `pending_approval`, `needs_info`, or `done`
- [x] NEVER sends email automatically -- all external actions require human approval (Constitution Principle III)
- [x] Every decision logged to `vault/Logs/` with full audit trail (SC-005)
- [x] Orchestrator runs as a separate process alongside GmailWatcher without interference
- [x] State-transition tests pass for all 5 decision types (385/385 passed, 97% coverage)
- [x] Integration tests pass with mock LLM responses (test_full_triage_cycle.py + test_lifecycle_integration.py)
- [x] QA-Overseer verified: 385/385 tests pass, 97% orchestrator/ coverage, security scan clean, all files correctly placed — 2026-02-23

## Constraints (DEFINE FIRST)

Per the Spec-Architect mandate: define what the system CANNOT do before defining what it CAN do.

### NOT Supported in Phase 3

- **No email sending** -- Sending email is Phase 4 (MCP Integration). The orchestrator writes drafts to `vault/Drafts/` only. It does NOT execute any external action.
- **No approval workflow execution** -- The HITL approval pipeline (vault/Pending_Approval/ -> vault/Approved/ -> MCP executes) is Phase 5. Phase 3 ONLY writes to `vault/Drafts/` and updates frontmatter to `pending_approval`. The human reviews via Obsidian.
- **No multi-turn conversations** -- The LLM receives a single email context and returns a single decision. Multi-turn reasoning chains, memory across emails, or conversation threading are out of scope.
- **No attachment analysis** -- Email attachments referenced in frontmatter (`has_attachments: true`) are NOT sent to the LLM. The LLM reasons only on text metadata and body.
- **No learning or fine-tuning** -- The LLM uses a static system prompt per run. No feedback loops, no prompt tuning based on past decisions, no RLHF.
- **No streaming responses** -- LLM calls use synchronous (request/response) mode. Streaming is unnecessary for email triage decisions.
- **No MCP routing for LLM calls** -- Unlike Gmail (which uses the MCP Fallback Protocol), LLM API calls are direct HTTP calls via provider SDKs. This is because no LLM MCP server standard exists yet. If one emerges, Phase 6+ may refactor.
- **No cloud deployment** -- The orchestrator runs as a local long-lived process. Daemonization (tmux/systemd) is Phase 7 (Platinum).
- **No WhatsApp or Calendar integration** -- Those watchers and their reasoning flows are Phase 5+.
- **No automatic re-classification** -- The orchestrator trusts the watcher's classification. It does not override the `actionable`/`informational` routing from Phase 2.
- **No financial decision-making** -- If an email involves money (invoices, payments, subscriptions), the LLM MUST classify it as `urgent` or `needs_info`, NEVER `archive`. Financial emails are always escalated.

### Performance Limits

- **LLM call latency budget**: Maximum 30 seconds per email decision (includes network round-trip). If exceeded, the request is timed out and the email is marked `needs_info` with a log entry.
- **Processing throughput**: The orchestrator MUST process at least 10 emails per poll cycle. With a default poll interval of 120 seconds, this handles the typical vault backlog.
- **Memory ceiling**: Orchestrator process MUST NOT exceed 256 MB RSS after 24 hours of continuous operation.
- **Token budget per email**: The combined system prompt + email context MUST NOT exceed 4,000 tokens (to keep costs low and compatible with all providers). Emails exceeding this limit are truncated with a note appended to the LLM context.
- **Ralph Wiggum safety**: Maximum 5 iterations per email processing attempt (LOOP.md). If the LLM returns an unparseable response 5 times for the same email, the email is marked `status: failed` and logged with root cause analysis.
- **Poll interval**: Configurable, default 120 seconds, minimum 60 seconds.
- **Retry ceiling**: Maximum 3 retries per transient LLM API failure, with exponential backoff starting at 2 seconds (2s, 4s, 8s).
- **Concurrent LLM calls**: 1 (sequential processing). No parallel LLM calls in Phase 3 to avoid rate limit issues and simplify state management.

### Security Boundaries (Constitution Principle IX)

- **API keys**: All LLM provider API keys MUST be read from `.env` variables. Hardcoding is FORBIDDEN. Keys MUST be listed in `.gitignore`.
- **No key logging**: API keys MUST NEVER appear in log files, error messages, or exception traces. Log only the provider name and a masked key suffix (last 4 characters).
- **Email content in LLM calls**: Email body text is sent to the configured LLM provider. Per Constitution Principle II (Local-First Privacy), the user MUST be informed during setup that email content will be sent to a third-party LLM API. This is documented in the prerequisites section.
- **Draft content**: Draft replies written to `vault/Drafts/` are local-only. They MUST NOT be sent anywhere without explicit human approval (Phase 5).
- **Input validation**: All LLM responses MUST be validated against the expected JSON schema before any vault file is modified. Malformed LLM output MUST NOT corrupt vault files.
- **Rate limiting**: The orchestrator MUST respect per-provider rate limits. If a rate limit is hit, the orchestrator backs off for the provider's recommended duration (or 60 seconds if unspecified).
- **Audit logging**: Every LLM call MUST be logged to `vault/Logs/` with: timestamp, provider, model, email message_id, decision, token usage, and latency. This is the audit trail for Constitution Principle III compliance.

### Technical Debt (Known Limitations)

- Provider abstraction supports only text-in/text-out (chat completions). Vision, embeddings, and function-calling modes are deferred.
- No response caching -- if the orchestrator re-processes an email (after crash recovery), it makes a new LLM call. Caching is a future optimization.
- Prompt engineering is static -- the system prompt is hardcoded. A future enhancement could load prompts from `vault/Templates/` for user customization.
- No cost tracking -- token usage is logged but not aggregated into cost estimates. Cost dashboard is a Phase 6+ feature.
- Sequential processing (1 email at a time) is a throughput bottleneck for large backlogs. Parallel processing is deferred to Phase 6+.

## Human-Dependent Prerequisites

Per `ai-control/HUMAN-TASKS.md`, the following tasks MUST be completed by a human before this feature can function. Claude CANNOT perform these tasks autonomously.

| Task ID | Task | Status | Blocks |
|---------|------|--------|--------|
| **HT-001** | Create Obsidian Vault and Folder Structure | DONE (2026-02-17) | Vault directories for file output |
| **HT-002** | Set Up Gmail API OAuth2 Credentials | DONE (2026-02-20) | Gmail watcher producing vault files |
| **HT-009** | Configure LLM Provider API Key(s) | PENDING | LLM reasoning calls |

### HT-009: Configure LLM Provider API Key(s) (NEW)

- **Status**: PENDING
- **Blocks**: Phase 3 (LLM Reasoning Loop)
- **Why Human**: LLM provider accounts require sign-up with billing (credit card), interactive web flows, and agreement to terms of service. Claude cannot perform these actions.
- **Instructions**:
  1. Choose a primary LLM provider (Claude recommended for best structured output compliance)
  2. Obtain an API key from the provider's developer console
  3. Add to `.env`:
     ```
     # Required: Primary provider selection
     LLM_PROVIDER=anthropic

     # Provider-specific API keys (add only the one(s) you use)
     ANTHROPIC_API_KEY=sk-ant-...
     OPENAI_API_KEY=sk-...
     GEMINI_API_KEY=AIza...
     OPENROUTER_API_KEY=sk-or-...

     # Optional: Model override (defaults provided per provider)
     LLM_MODEL=claude-sonnet-4-20250514
     ```
  4. Ensure the chosen API key has sufficient quota/credits for email triage (estimated 1,000-5,000 tokens per email, ~50 emails/day = ~250k tokens/day)
- **Verification**: Run `python scripts/verify_llm_provider.py` (Phase 3 will provide this script) to confirm API key validity and model availability
- **Claude Can Then**: Build orchestrator, make LLM calls, process vault items

**Privacy Notice**: By configuring an LLM API key, the user acknowledges that email subject lines and body text from `vault/Needs_Action/` files will be sent to the configured third-party LLM provider for classification. No email attachments are sent. Draft replies generated by the LLM are stored locally in `vault/Drafts/` and are NEVER sent externally without explicit human approval.

**Verification protocol**: Before starting the orchestrator for the first time, the system MUST verify:
1. `.env` contains `LLM_PROVIDER` with a supported value
2. `.env` contains the corresponding API key variable for the selected provider
3. `vault/Needs_Action/` directory exists and contains at least one file with `status: pending`
4. `vault/Drafts/` directory exists (or can be created)
5. `vault/Logs/` directory exists (inherited from Phase 2)

If any check fails, the orchestrator MUST exit with a clear error message referencing the specific HT-xxx task and setup instructions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 -- Email Triage Decision (Priority: P1)

As a solo founder/CEO, I want my AI employee to read each actionable email in my vault and make an intelligent triage decision (reply, ask for info, archive, escalate, or delegate), so I spend zero time reading routine emails myself.

**Why this priority**: This is the core value proposition of Phase 3 and the entire reasoning loop. Without LLM-powered triage, the vault is just a pile of unprocessed markdown files. This story implements Loop 2 (Ralph Wiggum) from LOOP.md -- the autonomous completion pattern that is the project's central innovation.

**Independent Test**: Can be tested by placing a mock email file in `vault/Needs_Action/` with `status: pending`, running the orchestrator for one cycle, and verifying the file's frontmatter `status` field changes and a decision log entry appears in `vault/Logs/`.

**Acceptance Scenarios**:

1. **Given** a file exists in `vault/Needs_Action/` with `status: pending` and the orchestrator is running, **When** the orchestrator's poll cycle executes, **Then** the LLM is called with the email's sender, subject, body, and classification metadata, and a structured JSON decision is returned containing exactly one of: `draft_reply`, `needs_info`, `archive`, `urgent`, `delegate`.
2. **Given** the LLM returns a `draft_reply` decision for an email, **When** the orchestrator processes the decision, **Then** a draft reply file is created in `vault/Drafts/` with YAML frontmatter linking it to the original email's `message_id`, the original file's status is updated to `pending_approval`, and a log entry is written to `vault/Logs/`.
3. **Given** the LLM returns an `archive` decision for an email, **When** the orchestrator processes the decision, **Then** the original file's status is updated to `done`, the file is moved to `vault/Done/`, and a log entry is written.
4. **Given** the LLM returns a `needs_info` decision for an email, **When** the orchestrator processes the decision, **Then** the original file's status is updated to `needs_info`, a note is appended to the file body explaining what information is needed (from LLM reasoning), and a log entry is written.
5. **Given** the LLM returns an `urgent` decision for an email, **When** the orchestrator processes the decision, **Then** the original file's `priority` field is updated to `urgent`, status is updated to `pending_approval`, a draft is written to `vault/Drafts/` if the LLM provided reply content, and a log entry is written with `severity: WARN`.
6. **Given** the LLM returns a `delegate` decision for an email, **When** the orchestrator processes the decision, **Then** the original file's status is updated to `pending_approval`, a note is appended with the LLM's delegation recommendation (who and why), and a log entry is written.
7. **Given** the orchestrator processes an email, **When** the decision is applied, **Then** the original file's YAML frontmatter is updated to include: `decision`, `decision_reason`, `decided_by` (provider + model name), `decided_at` (ISO 8601 timestamp), and `iteration_count`.

---

### User Story 2 -- Multi-LLM Provider Abstraction (Priority: P2)

As a developer/power user, I want to switch between LLM providers (Claude, OpenAI, Gemini, OpenRouter, Qwen, GLM, Goose) by changing only my `.env` file, so I am never locked into a single vendor and can optimize for cost, speed, or availability.

**Why this priority**: The multi-provider abstraction is an architectural foundation that prevents vendor lock-in and enables cost optimization. Without it, the system is hardcoded to one LLM, violating the user's explicit requirement. This also enables graceful degradation (Constitution Principle X) -- if one provider has an outage, the user switches to another with a single env change.

**Independent Test**: Can be tested by configuring `.env` with `LLM_PROVIDER=openai`, starting the orchestrator, verifying it calls the OpenAI API. Then changing to `LLM_PROVIDER=anthropic`, restarting, and verifying it calls the Anthropic API. Both produce identical decision schema output. Zero code changes between tests.

**Acceptance Scenarios**:

1. **Given** `.env` contains `LLM_PROVIDER=anthropic` and a valid `ANTHROPIC_API_KEY`, **When** the orchestrator starts, **Then** it uses the Anthropic API (Claude) for all LLM calls and logs `provider: anthropic` in every decision log entry.
2. **Given** `.env` contains `LLM_PROVIDER=openai` and a valid `OPENAI_API_KEY`, **When** the orchestrator starts, **Then** it uses the OpenAI API for all LLM calls and logs `provider: openai` in every decision log entry.
3. **Given** `.env` contains `LLM_PROVIDER=gemini` and a valid `GEMINI_API_KEY`, **When** the orchestrator starts, **Then** it uses the Google Gemini API for all LLM calls.
4. **Given** `.env` contains `LLM_PROVIDER=openrouter` and a valid `OPENROUTER_API_KEY`, **When** the orchestrator starts, **Then** it routes requests through OpenRouter to the model specified by `LLM_MODEL`.
5. **Given** `.env` contains an unsupported `LLM_PROVIDER` value, **When** the orchestrator starts, **Then** it exits with a clear error message listing all supported providers.
6. **Given** `.env` contains `LLM_PROVIDER` but the corresponding API key variable is missing or empty, **When** the orchestrator starts, **Then** it exits with a clear error message: "LLM_PROVIDER is set to [X] but [X_API_KEY] is not configured in .env".
7. **Given** any supported provider is configured, **When** the LLM returns a decision, **Then** the response is normalized into the same `LLMDecision` schema regardless of provider-specific response format differences.

---

### User Story 3 -- Draft Reply Generation (Priority: P3)

As a solo founder/CEO, I want my AI employee to write a suggested reply for emails that need a response, saved locally in my vault for review, so I can approve or edit replies instead of writing them from scratch.

**Why this priority**: Draft generation is the highest-value output of the reasoning loop. It transforms the AI employee from a classifier into an assistant that saves real time. However, it depends on P1 (decision-making) and builds on P2 (provider abstraction).

**Independent Test**: Can be tested by placing a mock email file in `vault/Needs_Action/` containing a question that requires a reply, running the orchestrator, and verifying a draft file appears in `vault/Drafts/` with the suggested reply text, linked to the original email by `message_id`.

**Acceptance Scenarios**:

1. **Given** the LLM returns a `draft_reply` decision with a `reply_body` field, **When** the orchestrator writes the draft, **Then** a new markdown file is created in `vault/Drafts/` with YAML frontmatter containing: `type: draft_reply`, `status: pending_approval`, `source_message_id`, `to` (original sender), `subject` (prefixed with "Re: " if not already), `drafted_by` (provider + model), `drafted_at` (ISO 8601), and the reply body as markdown content.
2. **Given** a draft file is created in `vault/Drafts/`, **When** a human reviews it in Obsidian, **Then** the draft contains enough context (original subject, sender, date) for the human to understand what is being replied to without opening the original email file.
3. **Given** the LLM returns a `draft_reply` decision, **When** the draft is written, **Then** the original email file in `vault/Needs_Action/` has its `status` updated to `pending_approval` and a new frontmatter field `draft_path` is added pointing to the relative path of the draft file.
4. **Given** the LLM returns an `urgent` decision with reply content, **When** the orchestrator processes it, **Then** a draft is also written to `vault/Drafts/` with `priority: urgent` in frontmatter, so the human sees it prominently.
5. **Given** the draft file exists in `vault/Drafts/`, **When** it is NOT yet approved by a human, **Then** it remains in `vault/Drafts/` and is NEVER sent externally (Constitution Principle III: HITL for sensitive actions). Sending is Phase 4/5.

---

### User Story 4 -- Structured Prompting (Ralph Wiggum Principle) (Priority: P4)

As a system architect, I want the LLM to receive clear, deterministic, structured prompts that constrain its output to the exact JSON schema required, so that LLM responses are predictable, parseable, and never ambiguous.

**Why this priority**: The Ralph Wiggum principle (LOOP.md, Loop 2) is a safety mechanism. Unstructured LLM output leads to parsing failures, incorrect state transitions, and vault corruption. This story ensures reliability of the entire pipeline.

**Independent Test**: Can be tested by sending the system prompt and a mock email to any LLM provider and verifying the response parses into the expected JSON schema without modification. Can also be tested by sending deliberately adversarial inputs (edge-case emails) and verifying the LLM still returns valid JSON.

**Acceptance Scenarios**:

1. **Given** the orchestrator constructs an LLM prompt, **When** the prompt is sent, **Then** it includes: (a) a system prompt defining the agent's role, decision vocabulary, and output schema; (b) the email context (sender, subject, body, metadata); and (c) explicit instructions to respond ONLY in the defined JSON format.
2. **Given** the system prompt defines the JSON output schema, **When** the LLM responds, **Then** the response MUST be parseable as valid JSON containing at minimum: `decision` (enum: draft_reply|needs_info|archive|urgent|delegate), `confidence` (float 0.0-1.0), and `reasoning` (string explaining the decision).
3. **Given** the LLM returns a response that is NOT valid JSON, **When** the orchestrator attempts to parse it, **Then** it retries with a correction prompt ("Your response was not valid JSON. Please respond ONLY with the JSON object.") up to the Ralph Wiggum safety limit of 5 iterations.
4. **Given** the LLM returns valid JSON but with an invalid `decision` value (not one of the 5 allowed), **When** the orchestrator validates it, **Then** the response is rejected, a retry is attempted, and if all retries fail, the email is marked `status: needs_info` with a note "LLM could not determine action" and a log entry.
5. **Given** any LLM provider is configured, **When** the system prompt is sent, **Then** the same system prompt text is used regardless of provider (the abstraction layer handles provider-specific formatting like Anthropic's system parameter vs. OpenAI's system role message).

---

### User Story 5 -- Audit Trail and Observability (Priority: P5)

As an operator monitoring the AI employee, I want every LLM decision logged with full context (provider, model, tokens used, latency, decision, reasoning) to `vault/Logs/`, so I can audit past decisions, debug failures, and track costs.

**Why this priority**: Constitution Principle IX (Security) mandates audit logging for all significant actions. LLM decisions on personal email are significant. Without an audit trail, there is no accountability and no debugging capability.

**Independent Test**: Can be tested by running the orchestrator for one poll cycle with real or mock emails, then inspecting `vault/Logs/` for structured log entries that match the expected schema. Can be queried via Obsidian Dataview.

**Acceptance Scenarios**:

1. **Given** the orchestrator makes an LLM call, **When** the call completes (success or failure), **Then** a JSONL log entry is appended to `vault/Logs/orchestrator_YYYY-MM-DD.log` containing: `timestamp`, `event` ("llm_decision"), `provider`, `model`, `email_message_id`, `email_subject`, `decision`, `confidence`, `reasoning`, `tokens_input`, `tokens_output`, `latency_ms`, and `iteration`.
2. **Given** an LLM call fails (timeout, API error, rate limit), **When** the error is logged, **Then** the log entry includes: `severity` (ERROR), `error_type`, `error_message`, `retry_count`, and `provider`.
3. **Given** the orchestrator retries an LLM call due to invalid JSON, **When** the retry succeeds, **Then** both the original failure and the successful retry are logged as separate entries, and the final decision log entry includes `iteration: N` (where N > 1).
4. **Given** the orchestrator completes a full poll cycle, **When** the cycle finishes, **Then** a summary log entry is written with: `event: poll_cycle_complete`, `emails_found`, `emails_processed`, `decisions` (count by type: draft_reply, needs_info, archive, urgent, delegate), `errors`, `total_latency_ms`, and `next_poll_time`.
5. **Given** log entries exist in `vault/Logs/`, **When** queried via Obsidian Dataview, **Then** the entries are parseable for dashboard integration (SC-007).

---

### User Story 6 -- Orchestrator Lifecycle (Runs Alongside GmailWatcher) (Priority: P6)

As a developer, I want the reasoning loop orchestrator to follow the same BaseWatcher lifecycle pattern (start/stop/poll) and run as a separate process alongside the GmailWatcher without conflicts, so the system has a consistent architecture.

**Why this priority**: Constitution Principle VI (Watcher Architecture) mandates the BaseWatcher pattern. Running alongside GmailWatcher without interference is an operational requirement. However, this is architectural plumbing -- it enables the higher-priority stories.

**Independent Test**: Can be tested by starting both GmailWatcher and the orchestrator in separate terminal sessions, running them for 10+ minutes, and verifying: (a) both processes operate without interfering with each other, (b) files written by GmailWatcher are correctly picked up by the orchestrator, (c) no file lock conflicts occur.

**Acceptance Scenarios**:

1. **Given** the orchestrator extends BaseWatcher (or a compatible base class), **When** `start()` is called, **Then** it validates prerequisites (LLM API key, vault directories), loads state, acquires its own file lock (`vault/Logs/.orchestrator.lock`), and enters the polling loop.
2. **Given** both GmailWatcher and the orchestrator are running, **When** GmailWatcher writes a new file to `vault/Needs_Action/`, **Then** the orchestrator picks it up on its next poll cycle without file lock conflicts (they use separate lock files).
3. **Given** the orchestrator is running and a graceful shutdown signal (SIGINT/SIGTERM) is received, **When** shutdown begins, **Then** it completes any in-progress email processing, saves its state to `vault/Logs/orchestrator_state.json`, releases its lock, and logs the shutdown event.
4. **Given** the orchestrator crashes and is restarted, **When** it loads its persisted state, **Then** it resumes from where it left off -- emails already processed (tracked by message_id) are NOT re-processed, and emails that were in-progress during the crash are re-processed from the beginning.
5. **Given** the GmailWatcher fails and stops writing new files, **When** the orchestrator polls, **Then** it simply finds no new `status: pending` files and logs an idle cycle. It does NOT crash or error because of watcher absence (Constitution Principle X: independent failure).

---

### Edge Cases

- **LLM returns empty response**: Treated as invalid JSON. Retry up to 5 times per Ralph Wiggum safety limit. After exhaustion, mark email `status: needs_info` with note "LLM returned empty response" and log with severity ERROR.
- **LLM API key expired or revoked**: The orchestrator logs the authentication error, marks the current email `status: pending` (unchanged -- do not corrupt state), and enters a backoff loop (60s, 120s, 240s up to 15 minutes). It does NOT exit, allowing the user to fix the key in `.env` without restarting.
- **Vault directory `vault/Drafts/` does not exist**: The orchestrator creates it on first use. Unlike vault/Needs_Action/ (which must pre-exist from Phase 1), Drafts is a new Phase 3 directory and MAY be created by the orchestrator.
- **Email body exceeds token budget (>4,000 tokens)**: The body is truncated to fit the token budget. A note is appended to the LLM context: "[EMAIL TRUNCATED: original body was N tokens, truncated to 4000 tokens for processing.]" The truncation is logged.
- **Two orchestrator instances started accidentally**: The file-based lock (`vault/Logs/.orchestrator.lock`) prevents concurrent instances. A second instance MUST exit with a clear error: "Another orchestrator instance is already running."
- **LLM hallucinates a decision type not in the vocabulary**: The response is rejected and retried. If all 5 retries return invalid decisions, the email is marked `needs_info` with a log entry including the invalid responses for debugging.
- **Email file has missing or corrupt YAML frontmatter**: The orchestrator logs a warning with the filename, skips the file (does NOT crash), and continues to the next file. The corrupt file remains in `vault/Needs_Action/` for manual inspection.
- **Email file is being written by GmailWatcher at the moment of reading**: Handled by atomic writes (FR-017 from Phase 2). The orchestrator reads only complete files. If a read fails due to a partial write, it skips and retries on the next cycle.
- **Rate limit hit from LLM provider**: The orchestrator pauses processing for the provider's recommended backoff period (or 60 seconds if unspecified), logs the rate limit event, and resumes. It does NOT skip emails -- it resumes from where it stopped.
- **Network outage during LLM call**: The call times out at 30 seconds. The orchestrator retries up to 3 times with exponential backoff (2s, 4s, 8s). If all retries fail, the email is left as `status: pending` (unchanged) and the next email is attempted.
- **Email about financial matters (payment failed, invoice, subscription)**: The system prompt MUST instruct the LLM to classify these as `urgent` or `needs_info`, NEVER as `archive`. This is a safety constraint, not a suggestion.
- **All emails in vault/Needs_Action/ already processed**: The orchestrator's poll cycle finds no `status: pending` files, logs an idle cycle, and waits for the next poll interval. This is normal operation, not an error.
- **Vault disk is full**: The orchestrator catches the write error, logs to stderr (since vault/Logs/ may also be full), and enters a backoff loop. It does NOT corrupt existing files by partial writes.
- **LLM provider changes its response format between API versions**: The provider abstraction layer normalizes responses. If a new format is encountered that does not match the expected schema, it is treated as an invalid response and retried. This provides a buffer until the abstraction layer is updated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a provider abstraction layer that supports at minimum: Anthropic (Claude), OpenAI, Google Gemini, and OpenRouter. Additional providers (Qwen, GLM, Goose) MUST be addable by implementing a single interface without modifying existing code.
- **FR-002**: System MUST select the LLM provider based solely on the `LLM_PROVIDER` environment variable. Changing the provider MUST require zero code changes.
- **FR-003**: System MUST select the LLM model based on the `LLM_MODEL` environment variable. If `LLM_MODEL` is not set, a sensible default MUST be used per provider (e.g., `claude-sonnet-4-20250514` for Anthropic, `gpt-4o-mini` for OpenAI, `gemini-2.0-flash` for Gemini).
- **FR-004**: System MUST implement an orchestrator process (Ralph Wiggum loop) that scans `vault/Needs_Action/` for files with `status: pending` in their YAML frontmatter on each poll cycle.
- **FR-005**: System MUST parse YAML frontmatter from each pending email file, extracting at minimum: `type`, `status`, `source`, `message_id`, `from`, `subject`, `date_received`, `classification`, `priority`, and `has_attachments`.
- **FR-006**: System MUST construct a structured LLM prompt for each email containing: (a) a system prompt defining the agent role, decision vocabulary, and JSON output schema; (b) the email metadata (sender, subject, date, classification); (c) the email body text (truncated to token budget if necessary).
- **FR-007**: System MUST enforce structured JSON output from the LLM. The response MUST conform to the `LLMDecision` schema (see Data Contracts below). Non-conforming responses MUST trigger retry with a correction prompt.
- **FR-008**: System MUST support exactly 5 decision types: `draft_reply`, `needs_info`, `archive`, `urgent`, `delegate`. No other decision types are valid.
- **FR-009**: System MUST execute the appropriate post-decision action for each decision type:
  - `draft_reply`: Write draft to `vault/Drafts/`, update source file status to `pending_approval`, add `draft_path` to source frontmatter.
  - `needs_info`: Update source file status to `needs_info`, append LLM's information request to file body.
  - `archive`: Update source file status to `done`, move file to `vault/Done/`.
  - `urgent`: Update source file `priority` to `urgent` and `status` to `pending_approval`, write draft to `vault/Drafts/` if reply content provided.
  - `delegate`: Update source file status to `pending_approval`, append delegation recommendation to file body.
- **FR-010**: System MUST update YAML frontmatter on processed files to include: `decision`, `decision_reason` (from LLM reasoning), `decided_by` (provider:model), `decided_at` (ISO 8601), and `iteration_count`.
- **FR-011**: System MUST write draft reply files to `vault/Drafts/` following the DraftReply schema (see Data Contracts). Draft filenames MUST follow the pattern `YYYY-MM-DD-HHmm-re-<sanitized-original-subject>.md`.
- **FR-012**: System MUST NEVER send any email, API call, or external communication as a result of an LLM decision. All actions are vault-local file operations only. External actions are Phase 4/5.
- **FR-013**: System MUST log every LLM decision to `vault/Logs/` in JSONL format following the DecisionLogEntry schema (see Data Contracts).
- **FR-014**: System MUST implement the Ralph Wiggum retry loop: if the LLM returns invalid output, retry with a correction prompt up to a maximum of 5 iterations per email. Track iteration count in frontmatter.
- **FR-015**: System MUST persist its state (processed message_ids, last poll timestamp, error counts) to `vault/Logs/orchestrator_state.json` using atomic writes, consistent with the ADR-0003 pattern.
- **FR-016**: System MUST follow the BaseWatcher lifecycle pattern (per ADR-0001): validate prerequisites at startup, load state, acquire file lock, enter async poll loop, save state on shutdown, release lock.
- **FR-017**: System MUST validate all prerequisites at startup: LLM provider configured, API key present, vault directories exist. Fail fast with actionable error messages referencing HT-xxx tasks.
- **FR-018**: System MUST handle email body truncation when the combined prompt exceeds the token budget. Truncation MUST preserve the first N characters of the body (not random middle sections) and append a truncation notice to the LLM context.
- **FR-019**: System MUST use a file-based lock (`vault/Logs/.orchestrator.lock`) to prevent concurrent orchestrator instances.
- **FR-020**: System MUST operate independently of the GmailWatcher process. The orchestrator's failure MUST NOT affect the watcher, and vice versa (Constitution Principle X).
- **FR-021**: System MUST implement per-provider rate limit handling. When a rate limit response (HTTP 429) is received, the orchestrator MUST wait for the duration specified in the `Retry-After` header (or 60 seconds if absent) before retrying.
- **FR-022**: System MUST implement a token estimation function that approximates the token count of a text string without making an API call. This is used for the token budget check (FR-018). The estimation MUST be within 20% of the actual token count.
- **FR-023**: System MUST skip files in `vault/Needs_Action/` that have a status other than `pending`. Files with `status: pending_approval`, `status: needs_info`, `status: done`, or any other status MUST be ignored during scanning.
- **FR-024**: System MUST create the `vault/Drafts/` directory if it does not exist at startup, as this is a new directory introduced in Phase 3.

### Key Entities

- **LLMProvider (Abstract)**: The provider abstraction interface. Defines a single method contract: given a system prompt and user message, return a structured response. Each concrete provider (Anthropic, OpenAI, Gemini, OpenRouter) implements this interface. Per Constitution Principle X, if one provider fails, the system logs the error; it does NOT try a different provider automatically (that would be a "fallback chain" which adds complexity and is deferred).

- **LLMDecision**: The structured output from every LLM call. Contains: `decision` (enum of 5 types), `confidence` (0.0-1.0), `reasoning` (explanation string), and optional `reply_body` (draft text for `draft_reply` and `urgent` decisions), `delegation_target` (for `delegate` decisions), `info_needed` (for `needs_info` decisions). Frozen after creation.

- **EmailContext**: The parsed representation of a vault/Needs_Action/ markdown file ready for LLM consumption. Contains: all YAML frontmatter fields plus the email body text (potentially truncated). This is the input to the LLM prompt construction.

- **DraftReply**: A markdown file in `vault/Drafts/` representing a suggested email reply. Contains YAML frontmatter linking it to the source email and the reply body as content. This file is the artifact that Phase 5 (HITL Approval) will act upon.

- **OrchestratorState**: Persistent state across restarts. Extends the same pattern as WatcherState (ADR-0003): last poll timestamp, set of processed message_ids, error count, total items processed, uptime start, and additionally: decisions_by_type counts (draft_reply: N, archive: N, etc.) and total_tokens_used.

- **DecisionLogEntry**: A structured JSONL log entry written to `vault/Logs/orchestrator_YYYY-MM-DD.log` for every LLM decision. Contains all fields needed for auditing: timestamp, provider, model, email metadata, decision, confidence, reasoning, token counts, and latency.

- **SystemPrompt**: The structured prompt template that instructs the LLM on its role, decision vocabulary, output format, and behavioral constraints. This is a critical artifact -- it is the "Ralph Wiggum" instructions that make LLM output deterministic and parseable.

## Data Contracts

### LLM Decision Schema (Output from LLM)

```json
{
  "decision": "draft_reply | needs_info | archive | urgent | delegate",
  "confidence": 0.85,
  "reasoning": "This email requires a response because the sender asked a direct question about project timeline.",
  "reply_body": "Hi [sender], thank you for your email. Regarding the project timeline...",
  "delegation_target": null,
  "info_needed": null
}
```

**Field constraints**:
- `decision`: REQUIRED. One of exactly 5 string values. Any other value is invalid.
- `confidence`: REQUIRED. Float between 0.0 and 1.0 inclusive. Values outside this range are clamped.
- `reasoning`: REQUIRED. Non-empty string. If empty, the response is invalid.
- `reply_body`: REQUIRED when `decision` is `draft_reply`. OPTIONAL when `decision` is `urgent`. MUST be null/absent for `archive`, `needs_info`, `delegate`.
- `delegation_target`: REQUIRED when `decision` is `delegate`. String describing who to delegate to and why. MUST be null/absent otherwise.
- `info_needed`: REQUIRED when `decision` is `needs_info`. String describing what additional information is required. MUST be null/absent otherwise.

### Updated Email Frontmatter (After Processing)

```yaml
---
type: email
status: pending_approval  # was "pending", now updated by orchestrator
source: gmail
message_id: 19c5b01ea4118499
from: '"Anthropic, PBC" <failed-payments@mail.anthropic.com>'
subject: $20.00 payment to Anthropic, PBC was unsuccessful again
date_received: Sat, 14 Feb 2026 07:16:18 +0000
date_processed: '2026-02-19T21:28:49.515111+00:00'
classification: actionable
priority: urgent  # may be updated by orchestrator (e.g., "urgent" decision)
has_attachments: false
watcher: gmail_watcher
# --- Fields added by orchestrator (Phase 3) ---
decision: urgent
decision_reason: "Payment failure for active subscription requires immediate attention"
decided_by: "anthropic:claude-sonnet-4-20250514"
decided_at: '2026-02-22T10:15:30.000000+00:00'
iteration_count: 1
draft_path: "vault/Drafts/2026-02-22-1015-re-20-00-payment-to-anthropic-pbc-was-unsuccessful-again.md"
---
```

### Draft Reply File Schema (vault/Drafts/)

```yaml
---
type: draft_reply
status: pending_approval
source_message_id: 19c5b01ea4118499
original_subject: "$20.00 payment to Anthropic, PBC was unsuccessful again"
original_from: '"Anthropic, PBC" <failed-payments@mail.anthropic.com>'
original_date: "Sat, 14 Feb 2026 07:16:18 +0000"
to: "failed-payments@mail.anthropic.com"
subject: "Re: $20.00 payment to Anthropic, PBC was unsuccessful again"
priority: urgent
drafted_by: "anthropic:claude-sonnet-4-20250514"
drafted_at: '2026-02-22T10:15:30.000000+00:00'
decision_confidence: 0.92
---

Dear Anthropic Billing Team,

I am writing regarding the unsuccessful payment of $20.00 for my subscription.
I have updated my billing information and would like to confirm the payment
will be retried. Please let me know if any further action is needed on my end.

Best regards,
[User Name]
```

### Decision Log Entry Schema (vault/Logs/orchestrator_YYYY-MM-DD.log)

Each line is a JSON object:

```json
{
  "timestamp": "2026-02-22T10:15:30.000000+00:00",
  "watcher_name": "orchestrator",
  "event": "llm_decision",
  "severity": "info",
  "provider": "anthropic",
  "model": "claude-sonnet-4-20250514",
  "email_message_id": "19c5b01ea4118499",
  "email_subject": "$20.00 payment to Anthropic, PBC was unsuccessful again",
  "decision": "urgent",
  "confidence": 0.92,
  "reasoning": "Payment failure for active subscription requires immediate attention",
  "tokens_input": 847,
  "tokens_output": 156,
  "latency_ms": 2340,
  "iteration": 1,
  "details": {}
}
```

### Orchestrator State Schema (vault/Logs/orchestrator_state.json)

```json
{
  "last_poll_timestamp": "2026-02-22T10:20:00.000000+00:00",
  "processed_ids": ["19c5b01ea4118499", "19c77b5e740507d6"],
  "error_count": 0,
  "total_items_processed": 16,
  "uptime_start": "2026-02-22T08:00:00.000000+00:00",
  "decisions_by_type": {
    "draft_reply": 5,
    "needs_info": 2,
    "archive": 7,
    "urgent": 1,
    "delegate": 1
  },
  "total_tokens_used": 42350
}
```

### Supported Providers Registry

| Provider Key | API Key Env Var | Default Model | SDK/Library |
|-------------|----------------|---------------|-------------|
| `anthropic` | `ANTHROPIC_API_KEY` | `claude-sonnet-4-20250514` | `anthropic` Python SDK |
| `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` | `openai` Python SDK |
| `gemini` | `GEMINI_API_KEY` | `gemini-2.0-flash` | `openai` SDK with base_url override (`generativelanguage.googleapis.com/v1beta/openai/`) |
| `openrouter` | `OPENROUTER_API_KEY` | (user must set `LLM_MODEL`) | `openai` SDK with base_url override |
| `qwen` | `QWEN_API_KEY` | `qwen-turbo` | `openai` SDK with base_url override |
| `glm` | `GLM_API_KEY` | `glm-4-flash` | `openai` SDK with base_url override |
| `goose` | `GOOSE_API_KEY` | (user must set `LLM_MODEL`) | `openai` SDK with base_url override |

**Note**: All providers except `anthropic` use the OpenAI-compatible API format via the `openai` SDK with different `base_url` and `api_key` values. `gemini` uses Google's official OpenAI-compatible endpoint (`generativelanguage.googleapis.com/v1beta/openai/`). This means the implementation has exactly **2 adapter classes**: `AnthropicAdapter` (uses `anthropic` SDK natively) and `OpenAICompatibleAdapter` (parameterized by base_url, handles the other 6 providers). Decision recorded in Clarifications (2026-02-22).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Switching LLM providers requires changing ONLY `.env` variables (`LLM_PROVIDER` and the corresponding API key). Zero code changes, zero configuration file changes beyond `.env`. Verified by running the orchestrator with 2+ different providers against the same vault files and confirming identical decision schema output.
- **SC-002**: The orchestrator processes all `status: pending` files in `vault/Needs_Action/` within one poll cycle. For a vault with 16 pending files (current real data), processing completes within 10 minutes (assuming 30-second LLM latency per email).
- **SC-003**: 100% of LLM responses are valid JSON conforming to the `LLMDecision` schema within 5 iterations. Measured across 50+ test emails. If the LLM returns invalid JSON on the first attempt, the retry mechanism recovers in 95%+ of cases.
- **SC-004**: Draft replies in `vault/Drafts/` contain coherent, contextually appropriate text that addresses the original email's content. Measured by human review of 20+ drafts -- 80%+ are usable as-is or with minor edits.
- **SC-005**: Every LLM decision has a corresponding log entry in `vault/Logs/orchestrator_YYYY-MM-DD.log`. Zero decisions occur without logging. Verified by comparing processed file count to log entry count.
- **SC-006**: The orchestrator runs continuously for 24+ hours without memory leaks (RSS stays below 256 MB), crashes, or state corruption.
- **SC-007**: Log entries in `vault/Logs/` are parseable by Obsidian Dataview plugin queries for Dashboard.md integration. A sample Dataview query can list all decisions by type and date.
- **SC-008**: The orchestrator recovers from transient LLM API failures (network drops, rate limits, timeouts) without manual intervention in 95% of cases.
- **SC-009**: No email is sent, no external API call is made (other than to the LLM provider), and no data leaves the local machine as a result of orchestrator decisions. Constitution Principle III compliance is absolute.
- **SC-010**: Financial emails (containing keywords: payment, invoice, subscription, billing, charge, refund) are NEVER classified as `archive`. 100% of financial emails receive `urgent` or `needs_info` decisions.

## Non-Functional Requirements

### Performance

- LLM call latency: under 30 seconds per email (timeout if exceeded)
- Poll cycle overhead (excluding LLM calls): under 500 ms
- File read/write latency: under 100 ms per vault file operation
- Token estimation accuracy: within 20% of actual token count
- Memory: under 256 MB RSS after 24 hours continuous operation

### Scalability

- Phase 3 target: 1 LLM provider, up to 50 emails per poll cycle
- Processed-ID set: MUST handle up to 100,000 IDs without degradation (same as watcher)
- State file size: MUST remain under 10 MB
- Log files: One log file per day, naturally bounded (~1 MB/day at 120s polls with full decision logging)

### Security (Constitution Principle IX)

- API keys MUST use `.env` file, never hardcoded, never committed
- API keys MUST be listed in `.gitignore`
- API keys MUST NOT appear in any log file or error trace (log only masked suffix: `...XXXX`)
- Email content sent to LLM provider is acknowledged in privacy notice (HT-009)
- All vault file modifications use atomic writes (temp file + rename) to prevent corruption
- File-based lock prevents unauthorized concurrent access
- LLM responses are validated before any vault modification (untrusted input from external service)

### Observability (Constitution Principle X)

- All LLM decisions logged to `vault/Logs/orchestrator_YYYY-MM-DD.log` in JSONL format
- All state transitions logged (pending -> pending_approval, pending -> done, etc.)
- Error logs include severity, error type, provider, and recovery action taken
- Health status queryable from `vault/Logs/orchestrator_state.json`
- Dashboard.md integration via Dataview queries on log files
- Poll cycle summaries logged with email counts and decision distribution

## Enforcement Loop Integration

This feature participates in the following enforcement loops defined in `ai-control/LOOP.md`:

### Loop 1: Spec-Driven Loop

This specification (`specs/006-llm-reasoning-loop/spec.md`) MUST exist and be approved before any implementation code is written. The implementation sequence is:
1. This spec (current document) -- MUST be approved
2. `specs/006-llm-reasoning-loop/plan.md` -- Architecture decisions
3. `specs/006-llm-reasoning-loop/tasks.md` -- Atomic implementation tasks
4. Implementation code in `orchestrator/` directory
5. Tests in `tests/` directory
6. QA-Overseer verification

### Loop 2: Ralph Wiggum Loop (THIS IS THE IMPLEMENTATION)

This feature IS the Ralph Wiggum loop. The state machine it implements:

| State | Vault Location | YAML status field | Meaning | Transition Trigger |
|-------|---------------|-------------------|---------|-------------------|
| PENDING | `vault/Needs_Action/` | `status: pending` | New email awaiting reasoning | GmailWatcher writes file (Phase 2) |
| PENDING_APPROVAL | `vault/Needs_Action/` | `status: pending_approval` | LLM decided, awaiting human review | Orchestrator decision: draft_reply, urgent, delegate |
| NEEDS_INFO | `vault/Needs_Action/` | `status: needs_info` | LLM needs more context | Orchestrator decision: needs_info |
| DONE | `vault/Done/` | `status: done` | Completed (archived) | Orchestrator decision: archive |
| FAILED | `vault/Needs_Action/` | `status: failed` | LLM could not process (5 retries exhausted) | Ralph Wiggum safety limit reached |

**Note on file movement**: Only `archive` decisions move the file to `vault/Done/`. All other decisions update the file in-place in `vault/Needs_Action/`. This is intentional -- `pending_approval` and `needs_info` files remain visible in Needs_Action for human review in Obsidian.

**Phase 3 scope boundary**: The orchestrator transitions files FROM `pending` TO the next state. It does NOT handle transitions beyond that (e.g., `pending_approval` -> `approved` -> execute action). Those transitions are Phase 5 (HITL Approval).

### Loop 3: Human-in-the-Loop (Preparation Only)

Phase 3 PREPARES for HITL but does NOT execute it:
- Files marked `pending_approval` are ready for human review in Obsidian
- Draft files in `vault/Drafts/` are ready for human editing
- No mechanism exists in Phase 3 to detect human approval or execute approved actions
- Phase 5 will add the approval detection and MCP execution pipeline

### Loop 4: Directory Guard

All file writes MUST comply with the canonical directory map in LOOP.md:
- Orchestrator source code: `orchestrator/`
- Email triage output: `vault/Needs_Action/` (status updates in-place)
- Archived emails: `vault/Done/` (moved by archive decision)
- Draft replies: `vault/Drafts/` (new in Phase 3)
- Orchestrator logs: `vault/Logs/orchestrator_YYYY-MM-DD.log`
- Orchestrator state: `vault/Logs/orchestrator_state.json`
- Tests: `tests/`
- Spec artifacts: `specs/006-llm-reasoning-loop/`

## Agent Assignments

Per `ai-control/AGENTS.md` and `ai-control/SWARM.md` Phase 3 configuration:

| Agent | Role | Deliverable |
|-------|------|-------------|
| **Spec-Architect** | Specification (this document) | `specs/006-llm-reasoning-loop/spec.md` |
| **Modular-AI-Architect** | Architecture design (provider abstraction, state machine) | `specs/006-llm-reasoning-loop/plan.md` |
| **Backend-Builder** | Implementation | `orchestrator/` directory contents |
| **QA-Overseer** | Verification | Acceptance criteria validation, test review |
| **Loop-Controller** | Enforcement | Verify spec-driven loop compliance throughout |

**Swarm Pattern**: Pipeline (Modular-AI-Architect designs -> Backend-Builder implements) with parallel tracks for provider abstraction and state machine, converging at QA-Overseer merge point.

## Assumptions

- User has completed HT-009 (LLM API key setup) and at least one provider API key exists in `.env`.
- The Obsidian vault is initialized at `vault/` with canonical folder structure (HT-001 DONE).
- GmailWatcher has been running and `vault/Needs_Action/` contains real email files with `status: pending` (verified: 16 files exist as of 2026-02-22).
- The `vault/Drafts/` directory may not exist yet. The orchestrator MUST create it if absent.
- The existing YAML frontmatter format produced by GmailWatcher (Phase 2) is stable and will not change.
- The user understands and accepts that email content will be sent to a third-party LLM API (documented in HT-009 privacy notice).
- The orchestrator runs as a long-lived Python process (not serverless/cron). Persistent session management (tmux/systemd) is Phase 7 (Platinum).
- LLM providers are generally available with reasonable uptime (99%+). The orchestrator handles transient failures but does NOT implement automatic failover between providers.
- The `.env` file exists with `LLM_PROVIDER` and the corresponding API key variable defined.
- Python 3.13+ is available (Constitution Tech Stack Constraints).
- The `asyncio.to_thread()` pattern from ADR-0002 is used for LLM SDK calls that are synchronous.

## Scope

### In Scope

- Multi-LLM provider abstraction layer (Anthropic, OpenAI, Gemini, OpenRouter + extensible for Qwen, GLM, Goose)
- Ralph Wiggum orchestrator loop (poll vault, send to LLM, apply decision)
- 5 decision types: draft_reply, needs_info, archive, urgent, delegate
- Structured JSON output enforcement (Ralph Wiggum principle)
- Draft reply generation to `vault/Drafts/`
- YAML frontmatter updates on processed files
- Orchestrator state persistence (processed IDs, error counts, decision counts)
- Full audit trail logging to `vault/Logs/`
- Token estimation and body truncation for budget compliance
- File-based lock for single-instance enforcement
- Startup prerequisite validation (fail-fast)
- Rate limit handling for LLM providers
- Graceful shutdown with state preservation

### Out of Scope

- Email sending (Phase 4 -- MCP Integration)
- HITL approval workflow execution (Phase 5 -- detecting approval, executing approved actions)
- WhatsApp or Calendar reasoning (Phase 5+)
- Cloud deployment / daemonization (Phase 7)
- Automatic provider failover (switching to backup provider on failure)
- Multi-turn conversation or email threading
- Attachment analysis (sending attachments to LLM)
- Cost tracking dashboard (Phase 6+)
- Prompt customization via vault templates (future enhancement)
- Parallel LLM calls (Phase 6+)
- Learning/feedback loops on LLM decisions
- Database persistence for orchestrator state (Phase 6 -- Neon PostgreSQL)
- Vision/multimodal LLM capabilities

## Dependencies

### Upstream (what this feature consumes)

- `vault/Needs_Action/*.md` files from GmailWatcher (Phase 2 output)
- `.env` with `LLM_PROVIDER` and corresponding API key (from HT-009, human-provided)
- `watchers/base_watcher.py` -- BaseWatcher abstract class (or compatible base for orchestrator)
- `watchers/models.py` -- WatcherState, WatcherLogEntry, LogSeverity models
- `watchers/utils.py` -- FileLock, atomic_write utilities
- LLM Provider APIs (external services): Anthropic, OpenAI, Google Gemini, OpenRouter

### Downstream (what consumes this feature's output)

- **Phase 4 -- Gmail MCP**: Will enable sending drafts from `vault/Drafts/` as actual emails
- **Phase 5 -- HITL Approval**: Reads `status: pending_approval` files and `vault/Drafts/` for human review workflow
- **Phase 6 -- CEO Briefing**: Decision statistics and summaries feed into daily briefings
- **Dashboard.md**: Orchestrator health, decision distribution, and email processing stats via Dataview queries on log files

### External Services

- **Anthropic API**: Claude models for email triage (primary recommended provider)
- **OpenAI API**: GPT models (alternative provider)
- **Google Gemini API**: Gemini models (alternative provider)
- **OpenRouter API**: Multi-model routing (alternative provider, accesses 100+ models)
- **Qwen/GLM/Goose APIs**: Additional providers via OpenAI-compatible endpoints

## ADR Suggestions

The following architectural decisions are significant enough to warrant formal ADRs during the planning phase:

1. **Provider Abstraction Pattern**: **DECIDED (2026-02-22 via /sp.clarify)**: `AnthropicAdapter` (native SDK) + `OpenAICompatibleAdapter` (openai SDK, parameterized by base_url/api_key, covers OpenAI/Gemini/OpenRouter/Qwen/GLM/Goose). 2 adapter classes total.

   > Architectural decision detected: Multi-LLM provider abstraction pattern — decided. Document reasoning and tradeoffs? Run `/sp.adr multi-llm-provider-abstraction-pattern`

2. **Structured Output Enforcement Strategy**: The choice of how to enforce JSON output from LLMs (native JSON mode vs. prompt-only enforcement vs. output parsing with Pydantic) impacts reliability, provider compatibility, and error handling across all future LLM interactions.

   > Architectural decision detected: LLM structured output enforcement strategy (native JSON mode vs. prompt engineering vs. output parsing). Document reasoning and tradeoffs? Run `/sp.adr llm-structured-output-enforcement`

3. **Orchestrator Base Class Relationship**: Whether the orchestrator extends BaseWatcher (same inheritance tree as GmailWatcher) or uses a parallel BaseOrchestrator class (sharing utilities but not the watcher interface) affects code reuse, testability, and future orchestrator types.

   > Architectural decision detected: Orchestrator inheritance model (extend BaseWatcher vs. parallel BaseOrchestrator vs. composition). Document reasoning and tradeoffs? Run `/sp.adr orchestrator-base-class-design`
