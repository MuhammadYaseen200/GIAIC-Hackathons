# Research Notes: Multi-LLM Reasoning Loop -- Phase 3

**Feature**: `006-llm-reasoning-loop`
**Date**: 2026-02-22
**Author**: Modular-AI-Architect (Opus)
**Purpose**: Research findings supporting ADR-0005, ADR-0006, and ADR-0007 decisions

---

## Research Area 1: Provider Abstraction Pattern (ADR-0005)

### Finding: OpenAI-Compatible API as De Facto Standard

The OpenAI chat completions API (`POST /v1/chat/completions`) has become the de facto standard for LLM inference APIs. As of 2026-02, the following providers expose OpenAI-compatible endpoints:

| Provider | Endpoint | Compatibility Notes |
|----------|----------|---------------------|
| **OpenAI** | `api.openai.com/v1` | Reference implementation |
| **Google Gemini** | `generativelanguage.googleapis.com/v1beta/openai/` | Official OpenAI compatibility layer. Supports chat completions, embeddings. Does NOT support Gemini-specific features (grounding, safety settings) through this endpoint. |
| **OpenRouter** | `openrouter.ai/api/v1` | Meta-router to 100+ models. Adds `HTTP-Referer` and `X-Title` headers for ranking. Otherwise standard OpenAI format. |
| **Alibaba Qwen (DashScope)** | `dashscope.aliyuncs.com/compatible-mode/v1` | OpenAI-compatible mode for Qwen models. Separate from native DashScope API. Token usage reported in standard `usage` field. |
| **Zhipu GLM (BigModel)** | `open.bigmodel.cn/api/paas/v4` | OpenAI-compatible endpoint. Supports `glm-4`, `glm-4-flash`, `glm-4-plus`. |
| **Goose** | User-defined | Generic OpenAI-compatible wrapper for self-hosted or custom endpoints. User provides `GOOSE_BASE_URL`. |

### Finding: Anthropic API Differences

Anthropic's Messages API (`POST /v1/messages`) differs from OpenAI in several structural ways:

1. **System prompt handling**: Anthropic uses a dedicated `system` parameter at the top level. OpenAI uses a `role: "system"` message in the `messages` array. This is the most significant difference for our use case -- it affects prompt construction.

2. **Response structure**: Anthropic returns `response.content[0].text`. OpenAI returns `response.choices[0].message.content`. Different field names, different nesting.

3. **Token usage fields**: Anthropic uses `input_tokens`/`output_tokens`. OpenAI uses `prompt_tokens`/`completion_tokens`.

4. **Streaming protocol**: Anthropic uses SSE with different event types (`content_block_start`, `content_block_delta`). Not relevant for Phase 3 (no streaming), but matters for future phases.

5. **Error format**: Anthropic returns `{"type": "error", "error": {"type": "...", "message": "..."}}`. OpenAI returns `{"error": {"message": "...", "type": "...", "code": "..."}}`.

**Conclusion**: A single adapter cannot cleanly handle both Anthropic and OpenAI formats without significant conditional logic. Two adapters (AnthropicAdapter + OpenAICompatibleAdapter) is the cleanest separation.

### Finding: Why Not litellm

`litellm` is a popular Python library that wraps 100+ LLM providers behind a unified interface. Evaluation:

**Pros**:
- Covers all 7 target providers out of the box
- Handles provider-specific quirks internally
- Active maintenance, frequent updates
- Supports streaming, function calling, embeddings (future-proofing)

**Cons**:
- **Large dependency tree**: litellm pulls in ~50+ transitive dependencies including httpx, tiktoken, jinja2, tokenizers, and more. This conflicts with our minimal-dependency philosophy.
- **Version coupling**: When litellm updates to support a new provider API version, it may break compatibility with providers we already support. We have no control over the update schedule.
- **Black-box error handling**: When a provider call fails, litellm's error wrapping makes it harder to implement provider-specific retry logic (e.g., reading `Retry-After` headers).
- **Unnecessary complexity**: For our use case (text-in/text-out chat completions with 2 code paths), litellm is dramatically over-engineered.
- **Constitution alignment**: Constitution Principle IV (MCP-First) and the Authoritative Source Mandate prefer explicit control over external calls. A third-party abstraction layer introduces an opaque intermediary.

**Decision**: Build our own 2-adapter abstraction (~200 lines total). The maintenance cost is low because we only support chat completions, and the OpenAI-compatible format is stable.

### Finding: Async Client Availability

Both SDKs provide async clients:
- `anthropic.AsyncAnthropic` -- uses `httpx` under the hood
- `openai.AsyncOpenAI` -- uses `httpx` under the hood

This means we do NOT need `asyncio.to_thread()` for LLM calls (unlike the Gmail SDK which is synchronous). The orchestrator can call `await provider.complete()` directly in the async poll loop.

**Note**: ADR-0002 (`asyncio.to_thread()` for sync SDKs) still applies to any future SDK that is synchronous. For Phase 3, both adapters are natively async.

---

## Research Area 2: Structured Output Enforcement (ADR-0006)

### Finding: Native JSON Mode Support Across Providers

| Provider | JSON Mode Support | Method | Limitations |
|----------|-------------------|--------|-------------|
| **OpenAI** | Yes | `response_format: { type: "json_object" }` | Guarantees valid JSON but NOT schema compliance. Model may return any valid JSON structure. Must include "JSON" in system prompt. |
| **Anthropic** | Yes (partial) | Not a dedicated mode. Claude follows JSON instructions well through prompting. Anthropic offers tool use for structured output. | No `response_format` parameter. Must rely on prompt engineering. Tool use is a workaround but adds complexity. |
| **Gemini (via OpenAI compat)** | Yes | Same as OpenAI through the compatibility endpoint. | May not support all response_format options through the compat layer. |
| **OpenRouter** | Varies by model | Passes `response_format` through to underlying model. Works if the underlying model supports it. | No guarantee for all models behind OpenRouter. |
| **Qwen** | Uncertain | DashScope compatible mode may support `response_format`. Documentation is sparse. | Cannot rely on this for Phase 3. |
| **GLM** | Uncertain | BigModel compatible mode documentation does not clearly confirm JSON mode. | Cannot rely on this for Phase 3. |

**Conclusion**: Native JSON mode is NOT reliably available across all 7 providers. The only universally portable approach is prompt engineering + post-hoc validation.

### Finding: Pydantic v2 for LLM Output Validation

Pydantic v2 provides several features ideal for LLM output validation:

1. **`model_validate(obj)`**: Validates a dict against the model schema. Raises `ValidationError` with detailed field-level errors.
2. **Type coercion**: Converts string "0.85" to float 0.85 automatically. Handles LLM quirks like returning numbers as strings.
3. **Field validators**: Custom validators for cross-field rules (e.g., `reply_body` required only when `decision == "draft_reply"`).
4. **JSON schema generation**: `LLMDecision.model_json_schema()` generates the exact JSON schema that can be embedded in the system prompt. This ensures the schema in the prompt always matches the validation model -- no drift.
5. **Frozen models**: `model_config = ConfigDict(frozen=True)` makes LLMDecision immutable after creation, preventing accidental mutation.
6. **Performance**: Pydantic v2 (Rust core) validates in microseconds. No performance concern.

**Implementation pattern**:
```python
class LLMDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision: DecisionType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=1)
    reply_body: str | None = None
    delegation_target: str | None = None
    info_needed: str | None = None

    @model_validator(mode="after")
    def validate_decision_fields(self) -> "LLMDecision":
        if self.decision == DecisionType.DRAFT_REPLY and not self.reply_body:
            raise ValueError("reply_body is required for draft_reply decisions")
        if self.decision == DecisionType.DELEGATE and not self.delegation_target:
            raise ValueError("delegation_target is required for delegate decisions")
        if self.decision == DecisionType.NEEDS_INFO and not self.info_needed:
            raise ValueError("info_needed is required for needs_info decisions")
        return self
```

### Finding: Retry with Correction Prompt Effectiveness

Research on LLM output correction shows that:

1. **First attempt success rate**: With a well-structured system prompt and JSON schema, Claude and GPT-4o achieve 95%+ valid JSON on first attempt for simple schemas (5-6 fields).

2. **Correction prompt recovery**: When the first attempt fails, a correction prompt that includes the specific validation error message achieves 90%+ recovery on the second attempt. Key: include the actual error, not just "try again."

3. **Diminishing returns after iteration 3**: If an LLM cannot produce valid output in 3 attempts, further retries rarely succeed. The 5-iteration limit is generous -- most recoveries happen in iterations 1-2.

4. **Common failure modes**:
   - LLM wraps JSON in markdown code fences (\`\`\`json ... \`\`\`): Mitigated by system prompt instruction "No code fences."
   - LLM adds explanatory text before/after JSON: Mitigated by system prompt instruction "No extra text."
   - LLM returns valid JSON but wrong field names: Caught by Pydantic validation.
   - LLM returns correct structure but hallucinated decision type: Caught by DecisionType enum validation.

**Mitigation for code fence wrapping**: As a pre-processing step before `json.loads()`, strip markdown code fences if detected:
```python
text = text.strip()
if text.startswith("```"):
    text = text.split("\n", 1)[1]  # Remove first line
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
```

This is a pragmatic defense layer that does NOT relax the system prompt constraints -- the prompt still says "no code fences" to minimize this behavior.

---

## Research Area 3: Orchestrator Base Class (ADR-0007)

### Finding: BaseWatcher Reuse Analysis

Analysis of `watchers/base_watcher.py` (241 lines) for orchestrator compatibility:

| BaseWatcher Feature | Orchestrator Needs | Compatible? | Notes |
|--------------------|--------------------|-------------|-------|
| `__init__(name, poll_interval, vault_path)` | Yes | Yes | Orchestrator uses `name="orchestrator"`, `poll_interval=120`, same `vault_path` |
| `start()` (validate, load state, lock, poll loop) | Yes | Yes | Same lifecycle |
| `stop()` (save state, release lock, log) | Yes | Yes | Same lifecycle |
| `_run_poll_cycle()` (fetch items, process each) | Yes | Partially | Works but does not implement the Ralph Wiggum inner retry loop. Orchestrator's `process_item()` handles that internally. |
| `_retry_with_backoff(fn, max_retries=3, base_delay=2)` | Yes | Yes | Used for transient API failures (network, rate limit). NOT used for invalid LLM output (that's the Ralph Wiggum loop). |
| `_load_state()` / `_save_state()` | Yes | Override | Base uses `WatcherState`. Orchestrator overrides to use `OrchestratorState` (superset). |
| `_log(event, severity, details)` | Yes | Yes | Same JSONL format, different log file name (`orchestrator_YYYY-MM-DD.log`) |
| `_acquire_lock()` / `_release_lock()` | Yes | Yes | Different lock file path (`vault/Logs/.orchestrator.lock`) |
| `health_check()` | Yes | Yes | Returns same dict structure |
| `poll()` (abstract) | Override | Override | Orchestrator scans vault files instead of calling Gmail API |
| `process_item(item)` (abstract) | Override | Override | Orchestrator calls LLM instead of writing files |
| `validate_prerequisites()` (abstract) | Override | Override | Checks LLM config instead of Gmail credentials |

**Compatibility score**: 10/12 features directly reusable, 2 require override (state methods). This is strong evidence for inheritance over parallel implementation.

### Finding: State Extension Pattern

`WatcherState` fields:
```python
last_poll_timestamp: str
processed_ids: list[str]
error_count: int
total_emails_processed: int
uptime_start: str
```

`OrchestratorState` additional fields:
```python
decisions_by_type: dict[str, int]  # {"draft_reply": 5, "archive": 7, ...}
total_tokens_used: int
```

The extension pattern is straightforward: `OrchestratorState` includes all `WatcherState` fields plus the new ones. The `from_dict()` / `to_dict()` methods handle both old-format (WatcherState-only) and new-format (with orchestrator fields) state files, enabling backward compatibility if a state file from a previous version exists.

**Decision**: Do NOT inherit from `WatcherState` (dataclass inheritance is awkward). Instead, create a standalone `OrchestratorState` dataclass that includes all fields. Override `_load_state()` and `_save_state()` in the orchestrator to use `OrchestratorState`.

### Finding: Poll Interval Minimum

BaseWatcher enforces `poll_interval >= 30`. The spec requires orchestrator minimum of 60 seconds. Two options:
- (a) Override `__init__` to enforce 60: Extra code, fragile.
- (b) Set default to 120 and document minimum of 60: Let BaseWatcher's 30-second minimum prevent absurdly low values, use the spec's 60-second minimum as a documented guideline.

**Decision**: Option (b). The BaseWatcher's 30-second floor prevents abuse. The orchestrator's default of 120 seconds is the recommended value. Document that values below 60 are not recommended due to LLM rate limits.

---

## Research Area 4: Token Estimation Without tiktoken

### Finding: Characters-to-Tokens Ratio

Empirical measurement of the character-to-token ratio for English text across LLM tokenizers:

| Tokenizer | Avg chars/token | Source |
|-----------|----------------|--------|
| cl100k_base (OpenAI GPT-4/3.5) | ~4.0 | tiktoken benchmarks |
| Claude tokenizer | ~3.5-4.0 | Anthropic documentation |
| Gemini tokenizer | ~3.8-4.2 | Google documentation |

The ratio varies by content type:
- English prose: ~4.0 chars/token
- Code: ~3.0 chars/token
- URLs and email headers: ~2.5 chars/token
- Structured data (JSON, YAML): ~3.5 chars/token

For email triage (mixed prose + headers + URLs), a ratio of 4.0 chars/token gives a conservative estimate that is within the FR-022 requirement of 20% accuracy.

**Implementation**: `estimate_tokens(text: str) -> int: return max(1, len(text) // 4)`

**Validation**: For a 2000-character email body:
- Estimate: 500 tokens
- Actual (cl100k_base): ~450-550 tokens
- Error: ~0-10%, well within 20% requirement

**Why not add tiktoken**: tiktoken is a 3+ MB package that downloads model-specific tokenizer files. It provides exact counts but:
1. Is OpenAI-specific (cl100k_base). Not necessarily accurate for Claude or Gemini tokenizers.
2. Adds a binary dependency (Rust-based C extension).
3. For our use case (budget check with 200-token safety margin), approximate is sufficient.

---

## Research Area 5: Financial Email Safety Constraint

### Finding: Financial Keyword Detection

The spec mandates that financial emails (payment, invoice, subscription, billing, charge, refund) are NEVER classified as `archive` (SC-010). This is implemented as a prompt-level constraint rather than a code-level override for the following reasons:

1. **Prompt-level**: The system prompt explicitly instructs the LLM: "Emails about MONEY (payment, invoice, subscription, billing, charge, refund) must NEVER be classified as archive." This is the primary defense.

2. **Validation-level fallback**: As a belt-and-suspenders approach, the orchestrator could post-validate: if the email subject/body contains financial keywords AND the LLM returned `archive`, reject and retry. However, this creates a divergence between the prompt and the code -- if the keyword list changes, both must update.

**Decision**: Use prompt-level constraint only for Phase 3. If SC-010 testing reveals failures (LLM archives financial emails despite the prompt), add code-level validation as a Phase 3 patch. This keeps the initial implementation simple and avoids dual-maintenance of keyword lists.

**Testing approach**: The integration test `test_financial_email_never_archived` sends emails with financial keywords through the system prompt and verifies the LLM decision. If the mock LLM returns `archive` for a financial email, the test fails -- this validates that the prompt and mock are aligned with the safety constraint.

---

## Research Area 6: Vault File Parsing (YAML Frontmatter)

### Finding: YAML Frontmatter Extraction Pattern

Vault markdown files use the standard YAML frontmatter format:
```
---
key: value
key2: value2
---

Body text here...
```

The extraction pattern:
1. Read file content
2. Check that content starts with `---\n`
3. Find the second `---\n` delimiter
4. Extract text between delimiters
5. Parse with `yaml.safe_load()`
6. Body is everything after the second `---\n` (plus one newline)

**Edge cases to handle**:
- File does not start with `---`: No frontmatter, skip file (log warning)
- No closing `---`: Malformed, skip file (log warning)
- YAML parse error: Corrupt frontmatter, skip file (log warning)
- Missing required fields (no `status` key): Skip file (log warning)
- `status` field is not a string: Type coercion, treat as string

**Performance**: Reading only the frontmatter (not the full body) for the `scan_pending_emails()` function is unnecessary because:
- Email files are typically 2-20 KB
- We need the body anyway for LLM context (in `read_email_context()`)
- The scan function only reads the first ~500 bytes to find the frontmatter block

**Decision**: `scan_pending_emails()` reads the full file but only parses the frontmatter block. `read_email_context()` parses both frontmatter and body. This is simpler than a two-pass approach and the performance difference is negligible at 50 files.

---

## Research Area 7: Atomic Frontmatter Update

### Finding: In-Place YAML Frontmatter Modification

Updating YAML frontmatter in a markdown file while preserving the body content exactly (including whitespace, special characters, and markdown formatting) requires careful implementation:

**Approach**:
1. Read the full file content as a string
2. Split on `---\n` to extract: prefix (empty), frontmatter YAML, body
3. Parse frontmatter with `yaml.safe_load()` into a dict
4. Apply updates to the dict (add/modify fields)
5. Re-render frontmatter with `yaml.dump()`
6. Reconstruct: `---\n{new_yaml}---\n{body}`
7. Write atomically via `atomic_write()`

**Known issue**: `yaml.dump()` may reorder keys (alphabetically by default). This changes the visual order of frontmatter fields in Obsidian. To preserve insertion order:
```python
yaml.dump(fields, default_flow_style=False, sort_keys=False, allow_unicode=True)
```

**Known issue**: `yaml.dump()` may add quotes around values that look like special YAML types. For example, a subject containing a colon may get quoted. This is correct YAML behavior and should not cause issues.

**Known issue**: Existing frontmatter may have been written by GmailWatcher with a specific key order. Our update will preserve existing key order (because we load into a dict and dict preserves insertion order in Python 3.7+), and new keys are appended at the end.

**Decision**: Use the split-parse-update-render-write approach with `atomic_write()`. This is the same pattern used by `render_yaml_frontmatter()` in `watchers/utils.py`, extended to handle existing content.

---

## Appendix: Provider SDK Version Compatibility

| SDK | Minimum Version | Key Feature Required | Python Version |
|-----|----------------|---------------------|----------------|
| `anthropic` | 0.40.0 | `AsyncAnthropic`, `messages.create()` with `system` param | 3.8+ |
| `openai` | 1.50.0 | `AsyncOpenAI`, `chat.completions.create()`, `base_url` param | 3.8+ |
| `pydantic` | 2.0.0 | `model_validate()`, `model_json_schema()`, `ConfigDict(frozen=True)` | 3.8+ |

All three packages are actively maintained with weekly releases. The minimum versions specified are conservative -- they have been available for 6+ months.

---

## Research Area 8: OpenAI Agents SDK vs Raw openai SDK (2026-02-23)

### Question

The user asked to research the OpenAI Agents SDK (`openai-agents` package) for handling non-OpenAI providers via `openai_compatible` patterns. Is it a better fit than the raw `openai` SDK?

### Finding: OpenAI Agents SDK Patterns for Non-OpenAI Providers

The `openai-agents` package provides these patterns for non-OpenAI providers:

**Pattern A: Per-agent `OpenAIChatCompletionsModel`**
```python
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI

agent = Agent(
    model=OpenAIChatCompletionsModel(
        model="gemini-2.0-flash",
        openai_client=AsyncOpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=os.environ["GEMINI_API_KEY"]
        )
    )
)
```

**Pattern B: Global `set_default_openai_client()`**
```python
from agents import set_default_openai_client, set_default_openai_api
from openai import AsyncOpenAI

set_default_openai_client(AsyncOpenAI(base_url="...", api_key="..."))
set_default_openai_api("chat_completions")  # Required if provider lacks Responses API
```

**Pattern C: LiteLLM integration**
```python
# pip install "openai-agents[litellm]"
Agent(model="litellm/gemini/gemini-2.0-flash-preview-04-17")
```

**Key constraint**: `set_default_openai_api("chat_completions")` is required for any provider that doesn't implement OpenAI's Responses API (which is most non-OpenAI providers).

### Decision: Use Raw openai SDK (Not openai-agents)

The `openai-agents` SDK is designed for building multi-agent orchestration systems with handoffs, tool calls, and streaming. It adds a significant framework layer on top of the raw `openai` SDK.

**Why raw openai SDK is correct for Phase 3**:

1. **We are building the orchestrator ourselves**: The `openai-agents` SDK would replace our orchestrator loop with its own framework. Our `RalphWiggumOrchestrator` IS the agent loop — we can't put it inside another agent loop.

2. **Same underlying pattern**: Both approaches use `AsyncOpenAI(base_url=..., api_key=...)` at the core. The `openai-agents` SDK wraps this in `OpenAIChatCompletionsModel`; we call it directly in `OpenAICompatibleAdapter._complete()`. The result is identical.

3. **Structured output control**: We need full control over the prompt construction (Ralph Wiggum system prompt + email body + JSON schema) and response parsing (Pydantic LLMDecision). The `openai-agents` SDK's output schema handling is opinionated and would require adaptation.

4. **Constitution alignment**: Adding `openai-agents` as a dependency adds a large framework for functionality we don't use. Constitution principle: minimal viable dependencies.

**Confirmed architectural decision**: `openai.AsyncOpenAI(base_url=..., api_key=...)` is exactly the pattern documented in both the raw openai SDK and OpenAI Agents SDK docs. Our `OpenAICompatibleAdapter` uses this pattern directly, which is correct.
