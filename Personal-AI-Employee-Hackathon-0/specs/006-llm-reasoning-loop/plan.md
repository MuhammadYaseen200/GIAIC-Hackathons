# Implementation Plan: Multi-LLM Reasoning Loop (Ralph Wiggum Orchestrator) -- Phase 3

**Feature Branch**: `006-llm-reasoning-loop`
**Spec**: `specs/006-llm-reasoning-loop/spec.md` (Draft, 2026-02-22)
**Date**: 2026-02-22
**Status**: Draft
**Author**: Modular-AI-Architect (Opus)
**ADRs**: ADR-0001 (inherited), ADR-0002 (inherited), ADR-0003 (inherited), ADR-0005 (new), ADR-0006 (new), ADR-0007 (new)

---

## 1. Context

### Why

Phase 3 adds intelligence to Phase 2's perception. Phase 2 (Gmail Watcher) gave the AI Employee eyes -- it can see incoming emails and file them as structured markdown in the vault. Phase 3 gives it a brain -- the Ralph Wiggum reasoning loop reads those vault files, sends them to an LLM for triage, and writes structured decisions back to the vault (draft replies, status updates, audit logs).

Without Phase 3, `vault/Needs_Action/` is a growing pile of unread markdown files. With Phase 3, every email gets an intelligent triage decision: reply, ask for more info, archive, escalate, or delegate. The human reviews LLM-generated drafts in Obsidian instead of reading raw email.

This is the core value proposition of the Personal AI Employee: Loop 2 (Ralph Wiggum) from LOOP.md -- the autonomous completion pattern where the system reasons about work items and produces actionable output without human prompting.

### Current State

- **Branch**: `005-gmail-watcher` (Phase 2 complete), will create `006-llm-reasoning-loop` from `main`
- **Spec**: `specs/006-llm-reasoning-loop/spec.md` is complete with 6 user stories, 24 functional requirements, 10 success criteria, full edge case coverage, and 3 data contracts
- **Constitution**: v1.0.0 ratified (2026-02-16) -- all 10 principles apply
- **Governance**: `ai-control/` fully established (AGENTS.md, LOOP.md, SWARM.md, MCP.md, HUMAN-TASKS.md)
- **Phase 2 Output**: GmailWatcher operational -- 52 emails processed in live run (2026-02-20), 16 files in `vault/Needs_Action/` with `status: pending`, BaseWatcher ABC with full lifecycle, all tests passing
- **Vault**: Initialized at `vault/` with canonical folder structure (HT-001 DONE)
- **Gmail OAuth2**: Operational (HT-002 DONE)
- **LLM API Keys**: Pending HT-009 (human must obtain API key from chosen provider)
- **vault/Drafts/**: Does not yet exist -- orchestrator creates it (FR-024)

### Phase 3 Entry Requirements

Per Constitution Principle VII, Phase 3 MUST NOT begin until Phase 2 exit criteria are met:

- [x] BaseWatcher abstract class exists with lifecycle contract (start/stop/poll/process_item)
- [x] GmailWatcher extends BaseWatcher, connects via OAuth2, reads inbox
- [x] Emails produce correctly formatted markdown files in vault directories
- [x] Watcher runs continuously without crashes (52 emails processed in live run 2026-02-20)
- [x] Integration tests pass with mock Gmail data
- [x] All Phase 2 acceptance scenarios verified by QA-Overseer
- [x] `vault/Needs_Action/` contains real emails with `status: pending` in YAML frontmatter
- [x] `vault/Logs/gmail_watcher_state.json` exists with valid persistent state

All entry criteria satisfied. Phase 3 may proceed.

---

## 2. Technical Context

### Runtime

| Constraint | Value | Source |
|------------|-------|--------|
| Python | 3.13+ | Constitution Tech Stack |
| Async model | `asyncio` with `asyncio.to_thread()` for sync SDK calls | ADR-0002 |
| Platform | Local machine (no cloud deployment) | Spec constraints |
| Process model | Long-lived async process, single instance via file lock | Spec FR-019 |
| Memory ceiling | 256 MB RSS after 24 hours | Spec NFR Performance |
| LLM call latency budget | 30 seconds per email | Spec Performance Limits |
| Token budget per email | 4,000 tokens (system + context) | Spec Performance Limits |
| Concurrent LLM calls | 1 (sequential) | Spec Performance Limits |
| Poll interval | Default 120s, minimum 60s | Spec Performance Limits |
| Ralph Wiggum retry limit | 5 iterations per email | Spec Performance Limits |
| API retry ceiling | 3 retries with exponential backoff (2s, 4s, 8s) | Spec Performance Limits |

### Dependencies

**Production (`requirements.txt` additions)**:

| Package | Version | Purpose |
|---------|---------|---------|
| anthropic | >=0.40.0 | Anthropic Claude API (native SDK for primary provider) |
| openai | >=1.50.0 | OpenAI-compatible API (covers OpenAI, Gemini, OpenRouter, Qwen, GLM, Goose) |
| pydantic | >=2.0.0 | Structured output validation (LLMDecision, EmailContext, DraftReply models) |
| pyyaml | >=6.0 | YAML frontmatter parsing and rendering (inherited from Phase 2) |
| python-dotenv | >=1.0.0 | `.env` file loading for API keys (inherited from Phase 2) |

**Development (`requirements-dev.txt` additions)**:

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=8.0.0 | Test runner (inherited) |
| pytest-asyncio | >=0.23.0 | Async test support (inherited) |
| pytest-cov | >=4.1.0 | Coverage reporting (inherited) |
| pytest-mock | >=3.12.0 | Mock factories for LLM provider responses |

**Not adding**:

| Package | Reason Not Added |
|---------|------------------|
| tiktoken | Token counting is approximated via `len(text) / 4` heuristic (FR-022: within 20% accuracy). Adding tiktoken would introduce a 3 MB dependency and model-specific tokenizer downloads for marginal accuracy gain. Deferred to Phase 6+ if cost tracking requires exact counts. |
| litellm | Would provide multi-provider abstraction out of the box, but introduces a large transitive dependency tree, version coupling to 7+ providers, and violates the Constitution's MCP-First principle (we want explicit control over API calls). Our 2-adapter pattern is ~200 lines of code total. |
| instructor | Structured output library for LLMs. Our Pydantic + prompt engineering approach (ADR-0006) achieves the same result with zero additional dependencies and full provider portability. |

### Storage

| Artifact | Location | Format | Source |
|----------|----------|--------|--------|
| Orchestrator state | `vault/Logs/orchestrator_state.json` | JSON (single object) | FR-015, ADR-0003 |
| Activity logs | `vault/Logs/orchestrator_YYYY-MM-DD.log` | JSONL (one JSON object per line) | FR-013, ADR-0003 |
| Instance lock | `vault/Logs/.orchestrator.lock` | PID file | FR-019 |
| Draft replies | `vault/Drafts/YYYY-MM-DD-HHmm-re-<subject>.md` | Markdown + YAML frontmatter | FR-011 |
| Updated email files | `vault/Needs_Action/<original>.md` | In-place frontmatter update | FR-009, FR-010 |
| Archived emails | `vault/Done/<original>.md` | Moved from Needs_Action | FR-009 (archive) |

### Performance Budget

| Operation | Budget | Measurement |
|-----------|--------|-------------|
| Poll cycle overhead (excluding LLM calls) | <500 ms | Timer around `_run_poll_cycle()` minus LLM call time |
| File read/write latency | <100 ms per vault file | Timer around `atomic_write()` |
| YAML frontmatter parse | <10 ms per file | `yaml.safe_load()` on frontmatter block |
| Token estimation | <1 ms | Pure Python `len(text) / 4` |
| LLM API call | <30 seconds per email | Network round-trip timeout |
| Full poll (16 emails) | <10 minutes end-to-end | SC-002 requirement |
| Memory after 24h | <256 MB RSS | `psutil.Process().memory_info().rss` |

---

## 3. Constitution Compliance Check

Every implementation decision maps back to a Constitution principle. This table ensures no principle is overlooked.

| Principle | Requirement | How This Plan Satisfies It | Verified By |
|-----------|-------------|---------------------------|-------------|
| **I. Spec-Driven** | Spec before code | This plan follows `spec.md`; `tasks.md` follows this plan; code follows tasks. Loop 1 strictly enforced. | Loop-Controller enforcement |
| **II. Local-First Privacy** | All data local, secrets in `.env` | API keys via `.env`; vault files local-only; draft replies never sent externally; LLM API call is the only external data flow, acknowledged in HT-009 privacy notice. | Security scan pre-push |
| **III. HITL for Sensitive Actions** | Approval for external sends | Phase 3 is REASON-ONLY. No email sending. Drafts written to `vault/Drafts/` for human review. All external actions deferred to Phase 4/5. SC-009 enforces zero external sends. | test_no_external_actions, spec constraints |
| **IV. MCP-First** | External calls via MCP | No LLM MCP server standard exists yet (spec: "No MCP routing for LLM calls"). LLM calls are direct HTTP via provider SDKs. This is an authorized exception documented in the spec. When an LLM MCP emerges, Phase 6+ may refactor. | Spec constraints section |
| **V. TDD** | Tests first, >85% coverage | TDD mandated in tasks.md; all phases start with RED tests; coverage target >85% on `orchestrator/` package. | `pytest --cov` |
| **VI. Watcher Architecture** | BaseWatcher inheritance, idempotency | ADR-0007 decides to extend BaseWatcher. Orchestrator reuses lifecycle (start/stop/poll/_retry_with_backoff/state/logging/locking). Processed_ids prevent duplicate processing. Structured markdown with YAML frontmatter. | test_orchestrator_lifecycle |
| **VII. Phase-Gated** | Entry/exit criteria, no phase skip | Phase 2 exit criteria checked (all passed). Phase 3 exit criteria defined in spec. `/phase-execution-controller` validates. | QA-Overseer sign-off |
| **VIII. Reusable Intelligence** | PHRs for every prompt, ADRs for decisions | ADR-0005, ADR-0006, ADR-0007 created for Phase 3 decisions. PHRs created per session. | history/adr/, history/prompts/ |
| **IX. Security by Default** | No hardcoded secrets, input validation | API keys from `.env` only, never logged (masked to last 4 chars). LLM responses validated against Pydantic schema before any vault write. `.gitignore` blocks `.env`. Rate limit handling prevents API abuse. | test_key_masking, test_response_validation |
| **X. Graceful Degradation** | Independent failure, structured logging, health checks | Orchestrator operates independently of GmailWatcher (separate lock, separate state). Retry with backoff on LLM failures. Ralph Wiggum safety limit of 5 iterations. Auth backoff loop on expired keys. JSONL structured logs. Health_check() method inherited. | test_independent_failure, test_retry_*, test_health_check |

---

## 4. Architecture Decisions

Three architectural decisions were evaluated for Phase 3. Each was tested against the three-part significance criteria (Impact + Alternatives + Scope = all true).

### ADR-0005: Multi-LLM Provider Abstraction Pattern

**Decision**: Implement exactly 2 adapter classes: `AnthropicAdapter` (uses native `anthropic` Python SDK) and `OpenAICompatibleAdapter` (uses `openai` SDK parameterized by `base_url` and `api_key`). The OpenAI-compatible adapter covers 6 providers: OpenAI, Gemini, OpenRouter, Qwen, GLM, and Goose.

**Status**: DECIDED (2026-02-22 via `/sp.clarify`)

**Rationale**: The OpenAI chat completions API has become a de facto standard. Google Gemini exposes an official OpenAI-compatible endpoint at `generativelanguage.googleapis.com/v1beta/openai/`. OpenRouter, Qwen (DashScope), GLM (BigModel), and Goose all implement the same format. Only Anthropic uses a different API format (different `system` parameter handling, different response structure, different streaming protocol). By writing one `OpenAICompatibleAdapter` parameterized by `base_url`/`api_key`, we cover 6 providers with zero code duplication. The `AnthropicAdapter` handles the single provider that differs.

**Consequences**:
- Only 2 code paths to test and maintain (not 7)
- Adding a new OpenAI-compatible provider requires zero code changes -- only a new entry in the provider registry (env var -> base_url + api_key mapping)
- Anthropic's richer system prompt handling (dedicated `system` parameter vs. system role message) is properly supported through its native SDK
- If Anthropic ever adds an OpenAI-compatible endpoint, the `AnthropicAdapter` could be deprecated
- Trade-off: provider-specific features (function calling, vision, caching) are inaccessible through the unified interface -- acceptable because Phase 3 only uses text-in/text-out chat completions

**Alternatives Considered**:
- (a) One adapter per provider (7 classes): Maximum customization per provider, but massive code duplication for identical OpenAI-compatible APIs. Rejected: YAGNI, violates DRY.
- (b) Single adapter with if/else for Anthropic: Simpler but puts SDK-specific logic in conditionals, making the adapter a god class. Rejected: violates Single Responsibility.
- (c) Use `litellm` third-party library: Provides multi-provider abstraction out of the box. Rejected: large dependency tree (~50+ transitive deps), version coupling, black-box error handling, reduces control over API calls.

**Reference**: `history/adr/0005-multi-llm-provider-abstraction.md` (to be created)

---

### ADR-0006: LLM Structured Output Enforcement Strategy

**Decision**: Use Pydantic model validation + prompt engineering with JSON schema embedded in the system prompt + retry with correction prompt on validation error. Do NOT use native JSON mode or regex parsing.

**Status**: DECIDED

**Rationale**: Structured output must work identically across all 7 supported providers. Native JSON mode (`response_format: { type: "json_object" }`) is supported by OpenAI and Anthropic but NOT by all OpenAI-compatible endpoints (Gemini's OpenAI-compatible endpoint supports it; Qwen and GLM may not). Prompt engineering with explicit JSON schema in the system prompt is the most portable approach -- it works with every LLM that can follow instructions. Pydantic validates the LLM output after parsing, catching invalid field values (e.g., `decision: "maybe"` instead of one of the 5 allowed types). The retry loop (Ralph Wiggum principle, max 5 iterations) handles cases where the LLM returns invalid output by sending a correction prompt.

**Implementation Details**:
1. The system prompt includes the full JSON schema as a fenced code block with field descriptions and allowed values
2. The system prompt ends with: "Respond ONLY with the JSON object. No markdown, no explanation, no code fences."
3. The LLM response is parsed with `json.loads()` first (catch malformed JSON), then validated with `LLMDecision.model_validate()` (Pydantic v2)
4. On validation failure, a correction prompt is sent: "Your response was not valid. Error: {error}. Please respond ONLY with a JSON object matching the schema."
5. After 5 failed iterations, the email is marked `status: failed` with the errors logged

**Consequences**:
- Works identically with all 7 providers without relying on provider-specific JSON mode features
- Pydantic provides type coercion (string "0.85" -> float 0.85), default values, and field validation in one step
- The retry mechanism adds latency on failures but prevents vault corruption from malformed LLM output
- Small risk of prompt injection if email body contains instructions that override the schema request -- mitigated by clear system prompt boundaries and JSON-only response instruction
- Token overhead: the JSON schema in the system prompt adds ~200 tokens, which is within the 4,000 token budget

**Alternatives Considered**:
- (a) Native JSON mode (`response_format: { type: "json_object" }`): Guaranteed valid JSON but NOT guaranteed to match our schema (could return any valid JSON). Not supported by all providers. Rejected: not portable, still needs Pydantic validation.
- (b) Regex parsing: Parse key fields from free-text LLM output using regex patterns. Rejected: fragile, handles only simple cases, fails on nested fields like `reply_body`, impossible to maintain across LLM model changes.
- (c) `instructor` library: Wraps Pydantic models into LLM calls with automatic retries. Rejected: additional dependency, does not support all 7 providers, hides retry logic that we want explicit control over.

**Reference**: `history/adr/0006-llm-structured-output-enforcement.md` (to be created)

---

### ADR-0007: Orchestrator Base Class Relationship

**Decision**: The `RalphWiggumOrchestrator` extends `BaseWatcher` (same inheritance tree as `GmailWatcher`), overriding `poll()`, `process_item()`, and `validate_prerequisites()`.

**Status**: DECIDED

**Rationale**: Constitution Principle VI mandates consistent watcher architecture. `BaseWatcher` provides the exact lifecycle the orchestrator needs: `start()` (validate, load state, acquire lock, enter poll loop), `stop()` (save state, release lock), `_retry_with_backoff()`, `_load_state()/_save_state()`, `_log()`, `_acquire_lock()/_release_lock()`, and `health_check()`. The orchestrator's `poll()` scans `vault/Needs_Action/` instead of calling the Gmail API, and `process_item()` calls the LLM and applies the decision instead of writing a new file. The lifecycle semantics are identical.

**What the orchestrator overrides**:
- `poll()`: Scan `vault/Needs_Action/` for files with `status: pending`, parse YAML frontmatter, return list of `EmailContext` objects
- `process_item(item)`: Construct LLM prompt, call provider, validate response, apply decision (update frontmatter, write draft, move file), log decision
- `validate_prerequisites()`: Check LLM_PROVIDER, API key, vault directories, create `vault/Drafts/` if missing

**What the orchestrator inherits unchanged**:
- `start()`: Lifecycle entry (validate -> load state -> acquire lock -> poll loop with asyncio.sleep)
- `stop()`: Lifecycle exit (save state -> release lock -> log shutdown)
- `_retry_with_backoff()`: Exponential backoff for transient failures
- `_load_state()` / `_save_state()`: JSON state persistence with atomic writes
- `_log()`: JSONL structured logging to daily log files
- `_acquire_lock()` / `_release_lock()`: PID-based file lock
- `health_check()`: Health status dict

**State extension**: The orchestrator uses `OrchestratorState` (a superset of `WatcherState`) that adds `decisions_by_type` and `total_tokens_used` fields. The `_load_state()` / `_save_state()` methods are overridden to use `OrchestratorState.from_dict()` / `.to_dict()` instead of the base `WatcherState`.

**Consequences**:
- Maximum code reuse: ~150 lines of lifecycle code inherited for free
- Consistent architecture: same start/stop/poll pattern as GmailWatcher, same log format, same state format, same lock pattern
- Future orchestrators (CalendarOrchestrator, WhatsAppOrchestrator in Phase 5+) follow the same pattern
- Trade-off: `BaseWatcher` has a `total_emails_processed` field name that is email-specific but semantically means "total items processed" -- acceptable, not worth a breaking rename
- Trade-off: `_run_poll_cycle()` in BaseWatcher calls `process_item()` in a simple loop without the Ralph Wiggum retry sub-loop. The orchestrator overrides `process_item()` to internally implement the 5-iteration retry with correction prompts. The base class retry (`_retry_with_backoff()`) handles transient API failures (network, rate limit), while the orchestrator's internal retry handles invalid LLM output.

**Alternatives Considered**:
- (a) Parallel `BaseOrchestrator` class: New ABC sharing some utilities but not the watcher lifecycle. Pro: cleaner naming (no "watcher" for something that orchestrates). Con: duplicates ~150 lines of lifecycle code (start/stop/poll/state/lock/log), violates DRY, diverges from Constitution Principle VI. Rejected.
- (b) Composition (orchestrator HAS-A BaseWatcher): Orchestrator contains a BaseWatcher instance, delegates lifecycle calls. Pro: decoupled. Con: requires proxy methods for every lifecycle call, awkward API, doesn't match Constitution's "inherit from" language. Rejected.
- (c) Do not extend, build standalone: Write a completely independent orchestrator with its own lifecycle. Pro: zero coupling. Con: reimplements 200+ lines of battle-tested lifecycle code, diverges architecturally from Phase 2. Rejected.

**Reference**: `history/adr/0007-orchestrator-base-class-design.md` (to be created)

---

## 5. Module Design

### 5.1 `orchestrator/models.py` -- Data Models

**Responsibility**: Define all Pydantic and dataclass models for the orchestrator domain.

**Models**:

| Model | Type | Fields | Purpose |
|-------|------|--------|---------|
| `DecisionType` | `str, enum.Enum` | `DRAFT_REPLY`, `NEEDS_INFO`, `ARCHIVE`, `URGENT`, `DELEGATE` | Enum of exactly 5 decision types |
| `LLMDecision` | `pydantic.BaseModel` (frozen) | `decision`, `confidence`, `reasoning`, `reply_body`, `delegation_target`, `info_needed` | Validated structured output from LLM |
| `EmailContext` | `pydantic.BaseModel` (frozen) | `file_path`, `message_id`, `sender`, `subject`, `date_received`, `classification`, `priority`, `has_attachments`, `body`, `body_truncated` | Parsed vault file ready for LLM consumption |
| `DraftReply` | `dataclass` (frozen) | `source_message_id`, `original_subject`, `original_from`, `original_date`, `to`, `subject`, `priority`, `drafted_by`, `drafted_at`, `decision_confidence`, `body` | Data for rendering draft reply markdown |
| `OrchestratorState` | `dataclass` | Extends `WatcherState` pattern: `last_poll_timestamp`, `processed_ids`, `error_count`, `total_items_processed`, `uptime_start`, `decisions_by_type`, `total_tokens_used` | Persistent state across restarts |
| `DecisionLogEntry` | `dataclass` (frozen) | `timestamp`, `watcher_name`, `event`, `severity`, `provider`, `model`, `email_message_id`, `email_subject`, `decision`, `confidence`, `reasoning`, `tokens_input`, `tokens_output`, `latency_ms`, `iteration`, `details` | Structured JSONL log entry for audit trail |

**Key validation rules on `LLMDecision`**:
- `decision`: Must be one of 5 `DecisionType` values (Pydantic validator)
- `confidence`: Clamped to `[0.0, 1.0]` range (Pydantic validator)
- `reasoning`: Must be non-empty string (min_length=1)
- `reply_body`: Required when `decision == DRAFT_REPLY`, optional when `decision == URGENT`, must be None otherwise (Pydantic model_validator)
- `delegation_target`: Required when `decision == DELEGATE`, must be None otherwise
- `info_needed`: Required when `decision == NEEDS_INFO`, must be None otherwise

**Interfaces with other modules**:
- Consumed by: `orchestrator.py`, `prompts.py`, `vault_ops.py`, `providers/*.py`
- No external dependencies beyond `pydantic`, `enum`, `dataclasses`

---

### 5.2 `orchestrator/providers/` -- Provider Abstraction Layer

**Responsibility**: Abstract LLM API calls behind a common interface. Factory creates the correct adapter from `LLM_PROVIDER` env var.

#### 5.2.1 `providers/base.py` -- LLMProvider ABC

```python
class LLMProvider(abc.ABC):
    """Abstract base for all LLM provider adapters."""

    @abc.abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> tuple[str, int, int]:
        """Send a chat completion request.

        Returns:
            (response_text, input_tokens, output_tokens)
        """
        ...

    @abc.abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g., 'anthropic', 'openai')."""
        ...

    @abc.abstractmethod
    def model_name(self) -> str:
        """Return the model identifier (e.g., 'claude-sonnet-4-20250514')."""
        ...
```

**Design notes**:
- `complete()` is async because both SDKs support async clients
- Returns `(text, input_tokens, output_tokens)` tuple for logging/auditing
- Temperature default 0.3 (low variance for deterministic classification)
- Max tokens 1024 (sufficient for JSON decision + draft reply)

#### 5.2.2 `providers/anthropic_adapter.py` -- AnthropicAdapter

**Responsibility**: Wrap the `anthropic` Python SDK for Claude models.

**Key differences from OpenAI-compatible**:
- Uses dedicated `system` parameter (not a system role message in the messages array)
- Response structure: `response.content[0].text` (not `response.choices[0].message.content`)
- Token usage: `response.usage.input_tokens` / `response.usage.output_tokens`
- Model default: `claude-sonnet-4-20250514`
- API key env var: `ANTHROPIC_API_KEY`

**Implementation pattern**:
```python
class AnthropicAdapter(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete(self, system_prompt, user_message, temperature=0.3, max_tokens=1024):
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,  # Anthropic-specific: dedicated system param
            messages=[{"role": "user", "content": user_message}],
        )
        text = response.content[0].text
        return (text, response.usage.input_tokens, response.usage.output_tokens)
```

#### 5.2.3 `providers/openai_compatible_adapter.py` -- OpenAICompatibleAdapter

**Responsibility**: Wrap the `openai` Python SDK for all OpenAI-compatible providers, parameterized by `base_url` and `api_key`.

**Covers 6 providers**:

| Provider | `base_url` | Notes |
|----------|-----------|-------|
| OpenAI | `https://api.openai.com/v1` | Default openai SDK behavior |
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | Google's official OpenAI-compatible endpoint |
| OpenRouter | `https://openrouter.ai/api/v1` | Multi-model routing |
| Qwen | `https://dashscope.aliyuncs.com/compatible-mode/v1` | Alibaba Cloud DashScope |
| GLM | `https://open.bigmodel.cn/api/paas/v4` | Zhipu AI BigModel |
| Goose | User-defined via `GOOSE_BASE_URL` env var | Self-hosted or custom endpoint |

**Implementation pattern**:
```python
class OpenAICompatibleAdapter(LLMProvider):
    def __init__(self, api_key: str, model: str, base_url: str, provider_key: str):
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._provider_key = provider_key

    async def complete(self, system_prompt, user_message, temperature=0.3, max_tokens=1024):
        response = await self._client.chat.completions.create(
            model=self._model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        text = response.choices[0].message.content
        usage = response.usage
        return (text, usage.prompt_tokens, usage.completion_tokens)
```

#### 5.2.4 `providers/registry.py` -- Provider Factory

**Responsibility**: Create the correct `LLMProvider` instance from `.env` configuration.

**Registry table** (hardcoded, maps provider key to config):

```python
PROVIDER_REGISTRY = {
    "anthropic": {
        "adapter": "anthropic",
        "api_key_env": "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4-20250514",
        "base_url": None,  # native SDK, no base_url
    },
    "openai": {
        "adapter": "openai_compatible",
        "api_key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
    },
    "gemini": {
        "adapter": "openai_compatible",
        "api_key_env": "GEMINI_API_KEY",
        "default_model": "gemini-2.0-flash",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    },
    "openrouter": {
        "adapter": "openai_compatible",
        "api_key_env": "OPENROUTER_API_KEY",
        "default_model": None,  # user MUST set LLM_MODEL
        "base_url": "https://openrouter.ai/api/v1",
    },
    "qwen": {
        "adapter": "openai_compatible",
        "api_key_env": "QWEN_API_KEY",
        "default_model": "qwen-turbo",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    },
    "glm": {
        "adapter": "openai_compatible",
        "api_key_env": "GLM_API_KEY",
        "default_model": "glm-4-flash",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
    },
    "goose": {
        "adapter": "openai_compatible",
        "api_key_env": "GOOSE_API_KEY",
        "default_model": None,  # user MUST set LLM_MODEL
        "base_url": None,  # user MUST set GOOSE_BASE_URL
    },
}
```

**Factory function**: `create_provider(provider_key: str, model_override: str | None) -> LLMProvider`
- Reads `LLM_PROVIDER` from env
- Looks up registry entry
- Reads the corresponding API key env var
- Applies `LLM_MODEL` override if set
- Returns instantiated adapter
- Raises `PrerequisiteError` with HT-009 reference on missing key

**Key masking**: The factory logs `provider: {key}, model: {model}, api_key: ...{last_4_chars}` at INFO level. Never logs the full key.

---

### 5.3 `orchestrator/prompts.py` -- Prompt Engineering

**Responsibility**: Build the system prompt and user message for LLM calls. Implements the Ralph Wiggum structured prompting principle.

**Components**:

| Function | Purpose |
|----------|---------|
| `build_system_prompt()` -> `str` | Construct the full system prompt with agent role, decision vocabulary, JSON schema, behavioral constraints, and financial safety rule |
| `build_user_message(context: EmailContext)` -> `str` | Construct the user message with email metadata + body |
| `build_correction_prompt(error: str)` -> `str` | Construct the retry prompt for invalid LLM output |
| `estimate_tokens(text: str)` -> `int` | Approximate token count via `len(text) / 4` (FR-022) |
| `truncate_body(body: str, budget: int, system_tokens: int)` -> `tuple[str, bool]` | Truncate body to fit token budget, return (truncated_body, was_truncated) |

**System prompt structure** (see Section 9 for full design):
1. Agent role definition
2. Decision vocabulary (5 types with descriptions)
3. JSON output schema with field constraints
4. Financial safety constraint
5. Response format instruction

---

### 5.4 `orchestrator/vault_ops.py` -- Vault File Operations

**Responsibility**: Atomic vault file operations -- read email context, update frontmatter, write drafts, move files.

**Functions**:

| Function | Purpose |
|----------|---------|
| `read_email_context(file_path: Path)` -> `EmailContext` | Parse vault markdown file into EmailContext model |
| `update_frontmatter(file_path: Path, updates: dict)` -> `None` | Atomically update YAML frontmatter fields in-place |
| `append_to_body(file_path: Path, text: str)` -> `None` | Atomically append text to the body section of a vault file |
| `write_draft_reply(drafts_dir: Path, draft: DraftReply)` -> `Path` | Write a draft reply markdown file to `vault/Drafts/`, return file path |
| `move_to_done(file_path: Path, done_dir: Path)` -> `Path` | Move a vault file from Needs_Action to Done, return new path |
| `scan_pending_emails(needs_action_dir: Path)` -> `list[Path]` | Scan directory for files with `status: pending` in frontmatter |
| `ensure_directory(dir_path: Path)` -> `None` | Create directory if it does not exist (FR-024) |

**Key implementation details**:
- All write operations use `atomic_write()` from `watchers/utils.py`
- `update_frontmatter()` reads the full file, parses frontmatter, applies updates, re-renders frontmatter, writes atomically. The body content is preserved exactly.
- `read_email_context()` handles corrupt/missing frontmatter by raising `ValueError` (orchestrator catches and skips)
- `move_to_done()` uses `shutil.move()` after verifying destination directory exists
- `scan_pending_emails()` reads only the frontmatter (not the full body) for performance -- uses a regex to extract the YAML block between `---` delimiters, then `yaml.safe_load()`, then checks `status == "pending"`

---

### 5.5 `orchestrator/orchestrator.py` -- RalphWiggumOrchestrator

**Responsibility**: The main orchestrator class. Extends `BaseWatcher`, implements the reasoning loop.

**Class structure**:

```python
class RalphWiggumOrchestrator(BaseWatcher):
    """Email triage orchestrator using LLM reasoning.

    Extends BaseWatcher with:
    - poll(): Scan vault/Needs_Action/ for status: pending files
    - process_item(): LLM call -> validate -> apply decision
    - validate_prerequisites(): Check LLM provider, API key, vault dirs
    """

    def __init__(
        self,
        provider: LLMProvider,
        poll_interval: int = 120,
        vault_path: str = "vault",
        max_iterations: int = 5,
    ) -> None: ...

    def validate_prerequisites(self) -> None: ...
    async def poll(self) -> list[EmailContext]: ...
    async def process_item(self, item: Any) -> None: ...

    # Internal methods
    async def _call_llm(self, context: EmailContext) -> LLMDecision: ...
    async def _call_llm_with_retry(self, context: EmailContext) -> LLMDecision: ...
    async def _apply_decision(self, context: EmailContext, decision: LLMDecision) -> None: ...
    def _log_decision(self, context: EmailContext, decision: LLMDecision, ...) -> None: ...
    def _load_state(self) -> None: ...  # Override for OrchestratorState
    def _save_state(self) -> None: ...  # Override for OrchestratorState
```

**`poll()` implementation**:
1. Call `scan_pending_emails(vault/Needs_Action/)`
2. Filter out already-processed message_ids (from state.processed_ids)
3. For each pending file, call `read_email_context(file_path)`, catch ValueError and skip corrupt files
4. Return list of `EmailContext` objects

**`process_item()` implementation**:
1. Call `_call_llm_with_retry(context)` -- handles the 5-iteration Ralph Wiggum loop
2. If `LLMDecision` obtained, call `_apply_decision(context, decision)`
3. Call `_log_decision()` to write JSONL audit entry
4. Add `message_id` to `state.processed_ids`
5. Update `state.decisions_by_type` counter
6. On failure (5 retries exhausted), update frontmatter to `status: failed`, log with ERROR severity

**`_call_llm_with_retry()` implementation** (Ralph Wiggum loop):
1. Build system prompt via `build_system_prompt()`
2. Build user message via `build_user_message(context)`
3. For iteration 1 to max_iterations:
   a. Call `provider.complete(system_prompt, user_message)` wrapped in `asyncio.to_thread()` if SDK is sync, or directly if async
   b. Parse response as JSON
   c. Validate with `LLMDecision.model_validate(parsed_json)`
   d. If valid, return decision
   e. If invalid (JSONDecodeError or ValidationError), build correction prompt, replace user_message, continue loop
4. If all iterations exhausted, raise `MaxIterationsExceeded`

**`_apply_decision()` implementation** (switch on decision.decision):
- `DRAFT_REPLY`: Write draft via `write_draft_reply()`, update frontmatter (`status: pending_approval`, `draft_path`), update frontmatter decision fields
- `NEEDS_INFO`: Update frontmatter (`status: needs_info`), append `decision.info_needed` to body, update frontmatter decision fields
- `ARCHIVE`: Update frontmatter (`status: done`), update frontmatter decision fields, move file via `move_to_done()`
- `URGENT`: Update frontmatter (`priority: urgent`, `status: pending_approval`), write draft if `reply_body` present, update frontmatter decision fields
- `DELEGATE`: Update frontmatter (`status: pending_approval`), append delegation recommendation to body, update frontmatter decision fields

All decisions update frontmatter with: `decision`, `decision_reason`, `decided_by`, `decided_at`, `iteration_count`.

---

### 5.6 `scripts/verify_llm_provider.py` -- HT-009 Verification Script

**Responsibility**: Standalone script for verifying LLM provider configuration after HT-009 completion.

**Checks**:
1. `.env` file exists and is loadable
2. `LLM_PROVIDER` is set and is a supported value
3. Corresponding API key env var is set and non-empty
4. API key is valid -- makes a minimal test call ("Say hello" -> verify response received)
5. Model is accessible (if `LLM_MODEL` is set, verify the model exists)

**Output**: Human-readable status report with PASS/FAIL per check and masked API key suffix.

---

## 6. Data Flow

### Sequence: Email Triage (Happy Path)

```
GmailWatcher                    Vault                        Orchestrator                    LLM API
    |                              |                              |                              |
    |--- write email file -------->|                              |                              |
    |   vault/Needs_Action/        |                              |                              |
    |   status: pending            |                              |                              |
    |                              |                              |                              |
    |                              |<---- poll() scan ------------|                              |
    |                              |      find pending files      |                              |
    |                              |                              |                              |
    |                              |---- read_email_context() --->|                              |
    |                              |     return EmailContext       |                              |
    |                              |                              |                              |
    |                              |                              |--- complete() -------------->|
    |                              |                              |    system_prompt +            |
    |                              |                              |    email context              |
    |                              |                              |                              |
    |                              |                              |<--- JSON response ------------|
    |                              |                              |    {decision, confidence,     |
    |                              |                              |     reasoning, reply_body}    |
    |                              |                              |                              |
    |                              |                              |--- validate with Pydantic --->|
    |                              |                              |    LLMDecision.model_validate |
    |                              |                              |                              |
    |                              |<---- apply_decision() -------|                              |
    |                              |      update frontmatter      |                              |
    |                              |      write draft (if any)    |                              |
    |                              |      move to Done (archive)  |                              |
    |                              |                              |                              |
    |                              |<---- log_decision() ---------|                              |
    |                              |      vault/Logs/JSONL        |                              |
    |                              |                              |                              |
```

### Sequence: Invalid LLM Response (Retry Path)

```
Orchestrator                    LLM API
    |                              |
    |--- complete() (attempt 1) -->|
    |                              |
    |<--- "Sure! Here's my..." ---|  (not JSON)
    |                              |
    |--- json.loads() FAILS        |
    |--- build_correction_prompt() |
    |                              |
    |--- complete() (attempt 2) -->|
    |    correction prompt          |
    |                              |
    |<--- {"decision": "arc..." ---|  (valid JSON)
    |                              |
    |--- LLMDecision.validate() -->|  (valid schema)
    |--- ACCEPT, iteration=2       |
```

### Sequence: Rate Limit (Backoff Path)

```
Orchestrator                    LLM API
    |                              |
    |--- complete() (attempt 1) -->|
    |                              |
    |<--- HTTP 429 + Retry-After --|
    |                              |
    |--- wait Retry-After (60s) ---|
    |                              |
    |--- complete() (retry 1) ---->|
    |                              |
    |<--- HTTP 200 + response -----|
    |                              |
    |--- ACCEPT                    |
```

---

## 7. State Machine

The orchestrator implements the Ralph Wiggum state machine defined in spec Loop 2. Files transition through states based on LLM decisions.

### States and Transitions

```
                                   GmailWatcher writes file
                                          |
                                          v
                                   +-----------+
                                   |  PENDING  |   vault/Needs_Action/
                                   |           |   status: pending
                                   +-----+-----+
                                         |
                         Orchestrator processes email (LLM call)
                                         |
              +-------------+------------+------------+-------------+
              |             |            |            |             |
              v             v            v            v             v
     +--------+----+ +-----+------+ +---+----+ +----+------+ +----+-------+
     |DRAFT_REPLY  | |NEEDS_INFO  | |ARCHIVE | |  URGENT   | | DELEGATE   |
     |             | |            | |        | |           | |            |
     |pending_     | |needs_info  | | done   | |pending_   | |pending_    |
     |approval     | |            | |        | |approval   | |approval    |
     +--------+----+ +-----+------+ +---+----+ +----+------+ +----+-------+
              |             |            |            |             |
              v             v            v            v             v
        Stay in        Stay in      Move to      Stay in       Stay in
        Needs_Action   Needs_Action  vault/Done/  Needs_Action  Needs_Action
        + write draft  + append      (file moved) + write draft + append
          to Drafts/     info note                  to Drafts/    delegation
                                                   + priority:    note
                                                     urgent

                                   +----------+
                                   |  FAILED  |   vault/Needs_Action/
                                   |          |   status: failed
                                   +----------+
                                        ^
                                        |
                                  5 retries exhausted
                                  (Ralph Wiggum safety limit)
```

### State Transition Table

| Current State | Trigger | Decision | New Status | File Location | Side Effects |
|---------------|---------|----------|------------|---------------|--------------|
| `pending` | LLM returns `draft_reply` | `draft_reply` | `pending_approval` | `vault/Needs_Action/` (in-place) | Draft written to `vault/Drafts/`, `draft_path` added to frontmatter |
| `pending` | LLM returns `needs_info` | `needs_info` | `needs_info` | `vault/Needs_Action/` (in-place) | Info request appended to body |
| `pending` | LLM returns `archive` | `archive` | `done` | `vault/Done/` (moved) | File physically moved |
| `pending` | LLM returns `urgent` | `urgent` | `pending_approval` | `vault/Needs_Action/` (in-place) | `priority` set to `urgent`, draft written if reply_body present |
| `pending` | LLM returns `delegate` | `delegate` | `pending_approval` | `vault/Needs_Action/` (in-place) | Delegation recommendation appended to body |
| `pending` | 5 iterations exhausted | (failure) | `failed` | `vault/Needs_Action/` (in-place) | Error logged with all failed attempts |

### Scope Boundary

Phase 3 transitions files FROM `pending` TO the next state. It does NOT handle subsequent transitions:
- `pending_approval` -> `approved` -> execute (Phase 5)
- `needs_info` -> human provides info -> re-queue (Phase 5)
- `failed` -> human intervention -> re-queue (manual)

---

## 8. Provider Abstraction Design

### LLMProvider ABC Interface

```
                +-------------------+
                |  LLMProvider      |  (ABC)
                |-------------------|
                | + complete()      |  -> (text, in_tokens, out_tokens)
                | + provider_name() |  -> str
                | + model_name()    |  -> str
                +--------+----------+
                         |
            +------------+------------+
            |                         |
  +---------+----------+  +-----------+-----------+
  | AnthropicAdapter   |  | OpenAICompatibleAdapter|
  |--------------------|  |------------------------|
  | - _client:         |  | - _client:             |
  |   AsyncAnthropic   |  |   AsyncOpenAI          |
  | - _model: str      |  | - _model: str          |
  |                    |  | - _provider_key: str   |
  +--------------------+  +------------------------+
                                    |
                         Parameterized by base_url:
                         - OpenAI (api.openai.com)
                         - Gemini (googleapis.com)
                         - OpenRouter (openrouter.ai)
                         - Qwen (dashscope.aliyuncs.com)
                         - GLM (open.bigmodel.cn)
                         - Goose (user-defined)
```

### How AnthropicAdapter Differs from OpenAICompatibleAdapter

| Aspect | AnthropicAdapter | OpenAICompatibleAdapter |
|--------|------------------|------------------------|
| SDK | `anthropic.AsyncAnthropic` | `openai.AsyncOpenAI` |
| System prompt | Dedicated `system` parameter | First message with `role: "system"` |
| Response text | `response.content[0].text` | `response.choices[0].message.content` |
| Input tokens | `response.usage.input_tokens` | `response.usage.prompt_tokens` |
| Output tokens | `response.usage.output_tokens` | `response.usage.completion_tokens` |
| Rate limit header | `anthropic-ratelimit-*` headers | `x-ratelimit-*` headers |
| Timeout | `httpx.Timeout(30.0)` | `timeout=30.0` parameter |
| Error handling | `anthropic.RateLimitError` | `openai.RateLimitError` |

### Factory Pattern

```python
def create_provider() -> LLMProvider:
    """Create LLM provider from .env configuration.

    Reads:
        LLM_PROVIDER: Provider key (e.g., 'anthropic', 'openai', 'gemini')
        LLM_MODEL: Optional model override
        {PROVIDER}_API_KEY: API key for the selected provider

    Returns:
        Configured LLMProvider instance

    Raises:
        PrerequisiteError: If provider unsupported or API key missing (ref: HT-009)
    """
```

**Flow**:
1. Load `.env` via `python-dotenv`
2. Read `LLM_PROVIDER` -- if missing, raise `PrerequisiteError("LLM_PROVIDER not set", ht_reference="HT-009")`
3. Look up in `PROVIDER_REGISTRY` -- if not found, raise with list of supported providers
4. Read the `api_key_env` var -- if missing, raise `PrerequisiteError("LLM_PROVIDER is set to X but X_API_KEY is not configured", ht_reference="HT-009")`
5. Determine model: `LLM_MODEL` env var, or registry default, or raise if both are None
6. Log: `provider: {key}, model: {model}, api_key: ...{last_4}` at INFO level
7. Instantiate and return the correct adapter

---

## 9. Prompt Engineering Design

### System Prompt Structure

The system prompt is the critical artifact that makes LLM output deterministic and parseable. It follows the Ralph Wiggum principle: constrain the LLM's output space to exactly what the system can handle.

**Template**:

```
You are an AI email triage assistant for a solo founder/CEO. Your job is to classify
each email and make a decision about what action to take.

## Decision Types

You must choose exactly ONE of these 5 decisions for each email:

1. **draft_reply** - The email requires a response. You will draft a professional reply.
2. **needs_info** - You cannot make a decision without more context. Specify what info is needed.
3. **archive** - The email is informational, promotional, or requires no action. Safe to archive.
4. **urgent** - The email requires IMMEDIATE human attention. Use sparingly.
5. **delegate** - The email should be forwarded to someone else. Specify who and why.

## Safety Rules

- Emails about MONEY (payment, invoice, subscription, billing, charge, refund) must NEVER
  be classified as "archive". Always use "urgent" or "needs_info" for financial emails.
- When in doubt between "archive" and another action, choose the other action.
- Draft replies should be professional, concise, and address the sender's request directly.

## Output Format

Respond ONLY with a JSON object matching this exact schema. No markdown, no explanation,
no code fences, no extra text before or after the JSON.

{
  "decision": "draft_reply | needs_info | archive | urgent | delegate",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<brief explanation of why you chose this decision>",
  "reply_body": "<draft reply text, REQUIRED for draft_reply, OPTIONAL for urgent, null otherwise>",
  "delegation_target": "<who to delegate to and why, REQUIRED for delegate, null otherwise>",
  "info_needed": "<what additional information is needed, REQUIRED for needs_info, null otherwise>"
}

## Field Rules

- "decision": REQUIRED. Exactly one of: draft_reply, needs_info, archive, urgent, delegate
- "confidence": REQUIRED. Float 0.0-1.0. How certain you are about this decision.
- "reasoning": REQUIRED. Non-empty string explaining your decision.
- "reply_body": Include ONLY for draft_reply (required) and urgent (optional). Must be null for others.
- "delegation_target": Include ONLY for delegate (required). Must be null for others.
- "info_needed": Include ONLY for needs_info (required). Must be null for others.
```

### User Message Structure

```
## Email to Triage

**From:** {sender}
**Subject:** {subject}
**Date:** {date_received}
**Classification:** {classification}
**Has Attachments:** {has_attachments}

## Email Body

{body}

{truncation_notice if body was truncated}
```

### Correction Prompt (for invalid responses)

```
Your previous response was not valid JSON or did not match the required schema.

Error: {validation_error_message}

Please respond ONLY with a valid JSON object matching the schema. No markdown, no
explanation, no code fences. Just the JSON object.
```

### Token Budget Management

1. Compute `system_tokens = estimate_tokens(system_prompt)` (~350 tokens)
2. Compute `metadata_tokens = estimate_tokens(user_message_without_body)` (~100 tokens)
3. Compute `remaining_budget = 4000 - system_tokens - metadata_tokens - 200` (200 token safety margin for response)
4. If `estimate_tokens(body) > remaining_budget`: truncate body to `remaining_budget * 4` characters and append: `[EMAIL TRUNCATED: original body was ~{N} tokens, truncated to ~{remaining_budget} tokens for processing.]`

---

## 10. Testing Strategy

### Testing Principles

Per Constitution Principle V (TDD mandated):
1. **Red**: Write tests first, verify they fail
2. **Green**: Implement until tests pass
3. **Refactor**: Clean up without breaking tests
4. **Coverage target**: >85% on `orchestrator/` package
5. **No live LLM in CI**: All LLM API calls mocked; live testing is manual via `scripts/verify_llm_provider.py`
6. **Async testing**: `pytest-asyncio` for all orchestrator lifecycle tests

### Unit Tests

| Test File | Module Under Test | Key Test Cases | Count |
|-----------|-------------------|----------------|-------|
| `tests/unit/test_orchestrator_models.py` | `orchestrator/models.py` | DecisionType enum values; LLMDecision validation (valid, invalid decision, out-of-range confidence, missing required fields, cross-field validation); EmailContext construction; OrchestratorState serialization/deserialization; DecisionLogEntry serialization | ~18 tests |
| `tests/unit/test_providers.py` | `orchestrator/providers/` | AnthropicAdapter.complete() with mock response; OpenAICompatibleAdapter.complete() with mock response; Provider factory with valid config; Factory with missing provider; Factory with missing API key; Factory with unsupported provider; API key masking in logs; Model override via LLM_MODEL; Default model fallback; Provider name/model name accessors | ~15 tests |
| `tests/unit/test_prompts.py` | `orchestrator/prompts.py` | System prompt contains JSON schema; System prompt contains financial safety rule; User message includes all metadata fields; Token estimation accuracy (within 20% of known count); Body truncation when over budget; Body not truncated when under budget; Truncation notice appended; Correction prompt includes error message; Empty body handling | ~12 tests |
| `tests/unit/test_orchestrator.py` | `orchestrator/orchestrator.py` | poll() finds pending files; poll() skips non-pending files; poll() skips already-processed IDs; process_item() with draft_reply decision; process_item() with needs_info decision; process_item() with archive decision; process_item() with urgent decision; process_item() with delegate decision; process_item() with invalid LLM response + retry succeeds; process_item() with 5 retries exhausted -> failed; validate_prerequisites() passes; validate_prerequisites() fails on missing provider; validate_prerequisites() fails on missing API key; validate_prerequisites() fails on missing vault dirs; validate_prerequisites() creates Drafts dir; State load/save with OrchestratorState; Decision counter increment; Corrupt frontmatter skipped gracefully; Rate limit handling triggers backoff; No external actions (SC-009 compliance) | ~22 tests |

### Integration Tests

| Test File | Test Name | Description |
|-----------|-----------|-------------|
| `tests/integration/test_orchestrator_integration.py` | `test_full_triage_cycle` | Place 3 mock email files in tmp vault/Needs_Action/ (1 requiring reply, 1 archive, 1 needs_info). Run one poll cycle with mocked LLM returning appropriate decisions. Verify: frontmatter updated, draft file created, archive moved to Done/, log entries written. |
| | `test_provider_switching` | Run same test email through AnthropicAdapter mock and OpenAICompatibleAdapter mock. Verify identical LLMDecision schema output from both. |
| | `test_state_persistence_across_restart` | Process 3 emails, save state. Create new orchestrator instance, load state. Verify: processed_ids loaded, re-poll finds no new pending items. |
| | `test_ralph_wiggum_retry_exhaustion` | Mock LLM to return invalid JSON 5 times. Verify: email marked `status: failed`, all 5 attempts logged, error count incremented. |
| | `test_concurrent_instance_prevention` | Start orchestrator, acquire lock. Attempt second instance. Verify: RuntimeError with lock message. |
| | `test_graceful_shutdown` | Start orchestrator, send SIGINT. Verify: state saved, lock released, shutdown logged. |
| | `test_orchestrator_independent_of_watcher` | Run orchestrator with no GmailWatcher running. Place mock files manually. Verify: orchestrator processes them without error (no dependency on watcher process). |
| | `test_financial_email_never_archived` | Send mock emails with financial keywords (payment, invoice, billing). Mock LLM to return `archive`. Verify: validation rejects the decision (test at prompt level, not at orchestrator level -- this is a prompt engineering test). |

### Coverage Targets

```bash
pytest tests/ -v --cov=orchestrator --cov-report=term-missing
```

**Target**: >85% line coverage on `orchestrator/` package.

**Expected coverage gaps** (acceptable):
- `__main__` block in `orchestrator.py` (CLI entry point)
- Signal handler registration (platform-dependent, Windows compatibility)
- `scripts/verify_llm_provider.py` (manual-only, not in `orchestrator/` package)

---

## 11. Implementation Order

### Files to Create (14 source files + 1 script + 8 test files = 23 total)

| # | File | Phase | Purpose | Dependencies |
|---|------|-------|---------|--------------|
| 1 | `orchestrator/__init__.py` | A | Package init, re-exports | None |
| 2 | `orchestrator/models.py` | A | DecisionType, LLMDecision, EmailContext, DraftReply, OrchestratorState, DecisionLogEntry | pydantic |
| 3 | `orchestrator/providers/__init__.py` | B | Providers sub-package init | None |
| 4 | `orchestrator/providers/base.py` | B | LLMProvider ABC | abc |
| 5 | `orchestrator/providers/anthropic_adapter.py` | B | AnthropicAdapter | anthropic, base.py |
| 6 | `orchestrator/providers/openai_compatible_adapter.py` | B | OpenAICompatibleAdapter | openai, base.py |
| 7 | `orchestrator/providers/registry.py` | B | Provider factory + PROVIDER_REGISTRY | adapters, dotenv |
| 8 | `orchestrator/prompts.py` | C | System prompt builder, token estimation, truncation | models.py |
| 9 | `orchestrator/vault_ops.py` | C | Vault file operations (read, update, write, move, scan) | models.py, watchers/utils.py |
| 10 | `orchestrator/orchestrator.py` | D | RalphWiggumOrchestrator (extends BaseWatcher) | All above + watchers/base_watcher.py |
| 11 | `scripts/verify_llm_provider.py` | D | HT-009 verification script | providers/registry.py |
| 12 | `tests/unit/test_orchestrator_models.py` | A | Model unit tests | orchestrator/models.py |
| 13 | `tests/unit/test_providers.py` | B | Provider unit tests | orchestrator/providers/ |
| 14 | `tests/unit/test_prompts.py` | C | Prompt unit tests | orchestrator/prompts.py |
| 15 | `tests/unit/test_vault_ops.py` | C | Vault ops unit tests | orchestrator/vault_ops.py |
| 16 | `tests/unit/test_orchestrator.py` | D | Orchestrator unit tests | orchestrator/orchestrator.py |
| 17 | `tests/integration/test_orchestrator_integration.py` | E | Integration tests | All modules |

### Dependency Chain (5 Phases)

```
Phase A: Models (no internal dependencies)
  orchestrator/__init__.py            (standalone)
  orchestrator/models.py              (standalone, uses pydantic)
  tests/unit/test_orchestrator_models.py  (depends on models)

Phase B: Providers (depends on Phase A)
  orchestrator/providers/__init__.py
  orchestrator/providers/base.py                  (standalone ABC)
  orchestrator/providers/anthropic_adapter.py      (imports base.py)
  orchestrator/providers/openai_compatible_adapter.py  (imports base.py)
  orchestrator/providers/registry.py               (imports adapters)
  tests/unit/test_providers.py                     (imports providers/)

Phase C: Prompts + Vault Ops (depends on Phase A)
  orchestrator/prompts.py             (imports models.py)
  orchestrator/vault_ops.py           (imports models.py + watchers/utils.py)
  tests/unit/test_prompts.py          (imports prompts.py)
  tests/unit/test_vault_ops.py        (imports vault_ops.py)

Phase D: Orchestrator (depends on Phases A, B, C)
  orchestrator/orchestrator.py        (imports all above + watchers/base_watcher.py)
  scripts/verify_llm_provider.py      (imports providers/registry.py)
  tests/unit/test_orchestrator.py     (imports orchestrator.py)

Phase E: Integration & Polish (depends on Phase D)
  tests/integration/test_orchestrator_integration.py
  Final coverage run and cleanup
```

### TDD Sequence within Each Phase

**Phase A -- Models** (~20 min):
1. Write `tests/unit/test_orchestrator_models.py` (RED -- tests fail, no implementation)
2. Implement `orchestrator/models.py`
3. Run `pytest tests/unit/test_orchestrator_models.py -v` (GREEN)
4. **Checkpoint**: All model tests pass, Pydantic validation works

**Phase B -- Providers** (~30 min):
1. Write `tests/unit/test_providers.py` (RED)
2. Implement `orchestrator/providers/base.py` (ABC)
3. Implement `orchestrator/providers/anthropic_adapter.py`
4. Implement `orchestrator/providers/openai_compatible_adapter.py`
5. Implement `orchestrator/providers/registry.py`
6. Run `pytest tests/unit/test_providers.py -v` (GREEN)
7. **Checkpoint**: Provider abstraction fully functional with mocked SDKs

**Phase C -- Prompts + Vault Ops** (~30 min):
1. Write `tests/unit/test_prompts.py` (RED)
2. Write `tests/unit/test_vault_ops.py` (RED)
3. Implement `orchestrator/prompts.py`
4. Implement `orchestrator/vault_ops.py`
5. Run `pytest tests/unit/test_prompts.py tests/unit/test_vault_ops.py -v` (GREEN)
6. **Checkpoint**: Prompt construction and vault operations work correctly

**Phase D -- Orchestrator** (~45 min):
1. Write `tests/unit/test_orchestrator.py` (RED)
2. Implement `orchestrator/orchestrator.py`
3. Implement `scripts/verify_llm_provider.py`
4. Run `pytest tests/unit/test_orchestrator.py -v` (GREEN)
5. **Checkpoint**: Full orchestrator lifecycle works with mocked LLM

**Phase E -- Integration & Polish** (~25 min):
1. Write `tests/integration/test_orchestrator_integration.py`
2. Run `pytest tests/ -v --cov=orchestrator --cov-report=term-missing` (GREEN, >85% coverage)
3. **Checkpoint**: All tests pass, coverage met, integration verified

### Source Code Layout

```
orchestrator/
  __init__.py              # Public API re-exports
  models.py                # DecisionType, LLMDecision, EmailContext, DraftReply,
                           #   OrchestratorState, DecisionLogEntry
  providers/
    __init__.py            # Provider sub-package
    base.py                # LLMProvider ABC (complete, provider_name, model_name)
    anthropic_adapter.py   # AnthropicAdapter (native anthropic SDK)
    openai_compatible_adapter.py  # OpenAICompatibleAdapter (openai SDK + base_url)
    registry.py            # PROVIDER_REGISTRY dict + create_provider() factory
  prompts.py               # build_system_prompt, build_user_message,
                           #   build_correction_prompt, estimate_tokens, truncate_body
  vault_ops.py             # read_email_context, update_frontmatter, append_to_body,
                           #   write_draft_reply, move_to_done, scan_pending_emails,
                           #   ensure_directory
  orchestrator.py          # RalphWiggumOrchestrator (extends BaseWatcher)

scripts/
  verify_llm_provider.py   # HT-009 verification (standalone)

tests/
  unit/
    test_orchestrator_models.py   # Model validation tests
    test_providers.py             # Provider adapter + factory tests
    test_prompts.py               # Prompt construction + token estimation tests
    test_vault_ops.py             # Vault file operation tests
    test_orchestrator.py          # Orchestrator lifecycle + decision tests
  integration/
    test_orchestrator_integration.py  # Full cycle, state persistence, retry, lock tests
```

### Module Dependency Graph

```
                    models.py  (pydantic, no internal imports)
                   /    |    \
                  /     |     \
         providers/  prompts.py  vault_ops.py
        (base.py +                (imports watchers/utils.py
         adapters +                for atomic_write, etc.)
         registry.py)
                  \     |     /
                   \    |    /
                 orchestrator.py
                 (imports all above +
                  watchers/base_watcher.py)
                        |
                   __init__.py  (re-exports)
```

---

## 12. Risks

### Risk 1: LLM Output Inconsistency Across Providers

**Likelihood**: Medium (different LLMs have varying JSON compliance)
**Impact**: High (invalid output causes retries, wasted tokens, delayed processing)
**Mitigation**:
- ADR-0006: Pydantic validation catches all schema violations regardless of provider
- Ralph Wiggum retry loop (5 iterations) with correction prompt recovers 95%+ of failures (SC-003)
- System prompt explicitly states "Respond ONLY with the JSON object. No markdown, no explanation, no code fences."
- Provider-specific quirks documented in research.md for reference during debugging
- Fallback on exhausted retries: mark `status: failed`, log all attempts for post-mortem

### Risk 2: API Key Exposure in Logs or Error Traces

**Likelihood**: Low (if masking is implemented correctly)
**Impact**: Critical (leaked API key enables unauthorized access and billing)
**Mitigation**:
- API key masking function applied at the factory level -- adapters never log keys
- `_mask_key(key: str) -> str` returns `...{key[-4:]}` for display
- Tests explicitly verify no API key patterns in log output
- `.env` is in `.gitignore` (verified in Phase 2)
- Exception handlers catch and re-raise without including API key in the message
- Pre-push `/security-scan` skill checks for key patterns

### Risk 3: Vault File Corruption from Concurrent Access

**Likelihood**: Low (file lock prevents concurrent orchestrator instances; GmailWatcher writes to different files than orchestrator updates)
**Impact**: High (corrupted frontmatter breaks the entire pipeline)
**Mitigation**:
- All vault writes use `atomic_write()` (temp file + `os.replace()`) -- no partial writes possible
- Orchestrator uses its own lock file (`vault/Logs/.orchestrator.lock`), separate from GmailWatcher's lock (`vault/Logs/.gmail_watcher.lock`)
- The only shared resource is `vault/Needs_Action/` directory -- GmailWatcher creates new files (write), orchestrator updates existing files (read-modify-write). No conflict because they operate on different files (GmailWatcher creates, orchestrator reads files already created).
- Edge case: GmailWatcher writing a file at the exact moment orchestrator reads it. Mitigated by atomic writes from Phase 2 -- the orchestrator either sees the complete file or no file at all.

### Risk 4: Token Budget Exceeded Leading to LLM Errors

**Likelihood**: Medium (some emails have very long bodies)
**Impact**: Low (truncation handles it, but truncated emails may get less accurate decisions)
**Mitigation**:
- `truncate_body()` enforces the 4,000 token budget (FR-018)
- Truncation notice appended to LLM context so the model knows the body is incomplete
- `estimate_tokens()` is within 20% of actual (FR-022) -- 200 token safety margin accounts for estimation error
- Truncation event logged for monitoring

### Risk 5: Human Prerequisite (HT-009) Not Completed

**Likelihood**: High (human tasks are the most common blockers)
**Impact**: Critical (orchestrator cannot start without an API key)
**Mitigation**:
- `validate_prerequisites()` fails fast with clear error: "LLM_PROVIDER is set to [X] but [X_API_KEY] is not configured in .env. Complete HT-009: Configure LLM Provider API Key(s). See ai-control/HUMAN-TASKS.md"
- `scripts/verify_llm_provider.py` provides guided verification with PASS/FAIL checks
- HT-009 includes step-by-step instructions with example `.env` content
- The orchestrator can be developed and tested with mocked LLM responses before HT-009 is completed

---

## 13. Verification Plan

### How to Verify Each Exit Criterion

| Exit Criterion | Verification Method | Test |
|---------------|---------------------|------|
| Multi-LLM provider abstraction supports Claude + one alternative | Run `verify_llm_provider.py` with `LLM_PROVIDER=anthropic`, then `LLM_PROVIDER=openai`. Both return valid responses. | `test_provider_switching` |
| Switching providers requires ONLY `.env` changes (SC-001) | Change `LLM_PROVIDER` and API key in `.env`, restart orchestrator. Zero code changes. Verify both produce LLMDecision schema output. | `test_provider_switching` |
| Orchestrator reads `vault/Needs_Action/` with `status: pending` | Place test files with `status: pending`, run poll(). Verify files are found. Place files with `status: done`, verify they are skipped. | `test_poll_finds_pending`, `test_poll_skips_non_pending` |
| LLM produces structured JSON decisions (SC-003) | Mock LLM responses with all 5 decision types. Verify each parses into `LLMDecision` via Pydantic. | `test_orchestrator_models.py` |
| Draft replies written to `vault/Drafts/` | Process a `draft_reply` decision. Verify file exists in `vault/Drafts/` with correct frontmatter. | `test_draft_reply_written` |
| YAML frontmatter updated on every processed file | Process all 5 decision types. Verify each file has `decision`, `decision_reason`, `decided_by`, `decided_at`, `iteration_count` fields. | `test_frontmatter_updated` |
| NEVER sends email automatically (SC-009) | Static analysis: grep orchestrator/ for `send`, `smtp`, `requests.post`, etc. Dynamic: mock LLM, verify no HTTP calls made other than to LLM provider. | `test_no_external_actions` |
| Every decision logged to `vault/Logs/` (SC-005) | Process N emails. Verify N log entries in JSONL file. Compare processed count to log entry count. | `test_decision_logging` |
| Orchestrator runs alongside GmailWatcher | Start both in separate processes. Verify no lock conflicts, no file corruption, orchestrator picks up watcher's output. | `test_orchestrator_independent_of_watcher` |
| State-transition tests pass for all 5 decision types | One test per decision type verifying status transition. | `test_draft_reply`, `test_needs_info`, `test_archive`, `test_urgent`, `test_delegate` |
| Integration tests pass with mock LLM | Full cycle integration test with mocked provider. | `test_full_triage_cycle` |
| `/phase-execution-controller` validates | Run phase execution validation script after all tests pass. | Manual + automated |

### Coverage Report

```bash
pytest tests/ -v --cov=orchestrator --cov-report=term-missing
```

**Target**: >85% line coverage on `orchestrator/` package.

### Manual Verification (Post-Implementation)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Complete HT-009 (obtain API key) | API key in `.env` |
| 2 | Run `python scripts/verify_llm_provider.py` | All checks PASS |
| 3 | Place test email in `vault/Needs_Action/` with `status: pending` | File exists |
| 4 | Run `python -m orchestrator.orchestrator` | Orchestrator starts, processes email |
| 5 | Check `vault/Needs_Action/` | Frontmatter updated with decision fields |
| 6 | Check `vault/Drafts/` (if draft_reply) | Draft file exists with correct frontmatter |
| 7 | Check `vault/Done/` (if archive) | File moved from Needs_Action |
| 8 | Check `vault/Logs/` | JSONL log entry with decision details |
| 9 | Change `LLM_PROVIDER` in `.env`, restart | Works with new provider, zero code changes |
| 10 | Start alongside GmailWatcher | Both run without interference |
| 11 | Ctrl+C the orchestrator | Graceful shutdown, state saved |
| 12 | Restart orchestrator | Processed emails not re-processed |

---

## 14. Next Steps

1. **Generate `tasks.md`**: Break this plan into atomic, testable implementation tasks with TDD ordering per phase.

2. **Complete HT-009**: Human obtains LLM provider API key and configures `.env`.

3. **Create ADR files**: Write `history/adr/0005-multi-llm-provider-abstraction.md`, `0006-llm-structured-output-enforcement.md`, `0007-orchestrator-base-class-design.md` from the decisions documented in Section 4.

4. **Begin Phase A implementation**: Models (tests first per Constitution Principle V).

5. **Phase 4 forward-compatibility**: Ensure all draft files in `vault/Drafts/` contain sufficient metadata (`source_message_id`, `to`, `subject`) for Phase 4 (MCP Integration) to send them as actual emails without re-reading the original.

---

## Appendix A: Acceptance Criteria Traceability

| Spec Requirement | Plan Section | ADR | Implementation Phase |
|-----------------|--------------|-----|---------------------|
| FR-001 (Provider abstraction) | Section 5.2, 8 | ADR-0005 | B |
| FR-002 (Provider via env var) | Section 5.2.4 | ADR-0005 | B |
| FR-003 (Model via env var) | Section 5.2.4 | ADR-0005 | B |
| FR-004 (Orchestrator poll loop) | Section 5.5 | ADR-0007 | D |
| FR-005 (Parse YAML frontmatter) | Section 5.4 | -- | C |
| FR-006 (Structured LLM prompt) | Section 5.3, 9 | ADR-0006 | C |
| FR-007 (Enforce JSON output) | Section 5.5, 9 | ADR-0006 | D |
| FR-008 (5 decision types) | Section 5.1 | -- | A |
| FR-009 (Post-decision actions) | Section 5.5 | -- | D |
| FR-010 (Update frontmatter) | Section 5.4 | -- | C |
| FR-011 (Draft reply files) | Section 5.4 | -- | C |
| FR-012 (No email sending) | Section 3 (Principle III) | -- | D (verified by test) |
| FR-013 (Decision logging) | Section 5.5 | ADR-0003 | D |
| FR-014 (Ralph Wiggum retry) | Section 5.5 | -- | D |
| FR-015 (State persistence) | Section 5.5, 5.1 | ADR-0003 | D |
| FR-016 (BaseWatcher lifecycle) | Section 5.5 | ADR-0007 | D |
| FR-017 (Startup validation) | Section 5.5 | -- | D |
| FR-018 (Body truncation) | Section 5.3, 9 | -- | C |
| FR-019 (File lock) | Section 5.5 (inherited) | ADR-0001 | D |
| FR-020 (Independent of watcher) | Section 3 (Principle X) | -- | D (verified by test) |
| FR-021 (Rate limit handling) | Section 5.2 | -- | B |
| FR-022 (Token estimation) | Section 5.3 | -- | C |
| FR-023 (Skip non-pending) | Section 5.4 | -- | C |
| FR-024 (Create vault/Drafts/) | Section 5.5 | -- | D |

## Appendix B: Environment Variable Reference

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `LLM_PROVIDER` | Yes | -- | Provider key: anthropic, openai, gemini, openrouter, qwen, glm, goose |
| `LLM_MODEL` | No | Per-provider default | Model override (e.g., `claude-sonnet-4-20250514`, `gpt-4o-mini`) |
| `ANTHROPIC_API_KEY` | If provider=anthropic | -- | Anthropic API key |
| `OPENAI_API_KEY` | If provider=openai | -- | OpenAI API key |
| `GEMINI_API_KEY` | If provider=gemini | -- | Google Gemini API key |
| `OPENROUTER_API_KEY` | If provider=openrouter | -- | OpenRouter API key |
| `QWEN_API_KEY` | If provider=qwen | -- | Alibaba Qwen API key |
| `GLM_API_KEY` | If provider=glm | -- | Zhipu GLM API key |
| `GOOSE_API_KEY` | If provider=goose | -- | Goose API key |
| `GOOSE_BASE_URL` | If provider=goose | -- | Goose endpoint base URL |
| `ORCHESTRATOR_POLL_INTERVAL` | No | 120 | Poll interval in seconds (min 60) |
| `ORCHESTRATOR_MAX_ITERATIONS` | No | 5 | Ralph Wiggum retry limit |
| `VAULT_PATH` | No | vault | Path to Obsidian vault directory |
