# ADR-0020: Multi-Model Routing Strategy

- **Status:** Accepted
- **Date:** 2026-04-11
- **Feature:** full-comms-automation (Phase 6.5)
- **Context:** Phase 6.5 introduces a large number of AI-driven tasks across 5 communication
  platforms: email classification, greeting detection, contact intent analysis, content drafting,
  profile summarization, analytics interpretation, and cross-platform briefing synthesis.
  Not all tasks have equal complexity, risk, or value — yet under the previous single-model
  approach (ADR-0019: Claude `claude-sonnet-4-6` primary), every task consumes the same
  Anthropic API credits regardless of whether LLM reasoning is actually needed.
  The user has confirmed: Anthropic credits are a real cost constraint. Free/cheap models
  (Gemini Flash, Qwen, Mistral free tier via OpenRouter) have been verified as sufficient
  for routine classification tasks. A token-burn problem specifically was identified during
  `/sp.clarify` (Q3): generating AI replies for every greeting email (Namaste, Assalam o
  Alaikum, Hi/Hello) provides zero value while consuming tokens on every inbox scan.
  A routing strategy is needed to match task complexity to model cost.

## Decision

Implement a **three-tier model routing strategy** across all Phase 6.5 agents and
orchestrators. Route each task type to the lowest-cost model capable of handling it reliably:

**Tier 0 — Rule-Based (zero LLM cost)**
- Task types: greeting/thanks/congratulations detection, spam keyword matching, OTP/password
  attachment flagging, duplicate post detection, contact deduplication by identifier match
- Implementation: Python regex/keyword classifiers — no API call made
- Trigger: Pattern confidence ≥ threshold (configurable per task)
- Examples:
  - "Assalam o Alaikum" → greeting classifier → template reply (no LLM)
  - Email subject contains "OTP" → sensitive attachment flag (no LLM)
  - WhatsApp message from unknown number → "save contact?" prompt (no LLM)

**Tier 1 — Free/Cheap Model (near-zero cost)**
- Providers: OpenRouter (Gemini Flash 1.5, Qwen2.5-72B-Instruct, Mistral 7B free tier)
- Task types: email categorization (Urgent/Promotional/Spam/Opportunity), LinkedIn post
  intent classification, DM intent classification (job inquiry vs networking vs sales vs spam),
  calendar event extraction from email body, short content summarization (≤500 words)
- Trigger: Rule-based classifier confidence < threshold OR task requires contextual reasoning
  but output is low-risk (categorization, extraction, summarization)
- Provider selection: round-robin across available free-tier providers; fallback to next if
  rate-limited

**Tier 2 — Strong Model (paid, used sparingly)**
- Provider: Anthropic `claude-sonnet-4-6` (primary) or equivalent strong model
- Task types: drafting sensitive email replies (financial, legal, emotional, job decision),
  CEO daily/weekly briefing narrative synthesis, LinkedIn post drafting with tone/brand
  matching, complex WhatsApp reply drafting (multi-context, relationship-aware)
- Trigger: Task is high-stakes (irreversible send after HITL), requires synthesis across
  multiple data sources, or output quality directly reflects CEO's professional brand

**Routing contract** (applied in every agent/orchestrator):
```python
def route_task(task_type: str, confidence: float) -> ModelTier:
    if task_type in RULE_BASED_TASKS and confidence >= RULE_THRESHOLD:
        return ModelTier.ZERO          # no API call
    elif task_type in LOW_STAKES_TASKS:
        return ModelTier.FREE          # OpenRouter free tier
    else:
        return ModelTier.STRONG        # Anthropic / strong model
```

**Configuration**: Model tier assignments stored in `config/model_routing.yaml` (not hardcoded).
CEO can promote/demote task types between tiers via config edit — no code change required.

## Consequences

### Positive

- **Token cost reduction**: Greeting detection, spam flagging, and OTP marking produce zero
  LLM API calls — eliminates the most frequent and lowest-value token burns identified in Q3
- **Graceful cost scaling**: As communication volume grows (more emails, more DMs), cost
  grows only for tasks that genuinely require intelligence — not linearly with message count
- **Resilient to Anthropic credit exhaustion**: Tier 1 (free models) continues operating
  even when Anthropic credits = 0, covering the majority of daily classification tasks
- **Transparent to CEO**: Daily briefing includes a "model usage report" line showing how
  many tasks ran at each tier (Tier 0: N, Tier 1: N, Tier 2: N) — CEO can see ROI per tier
- **Configurable without code changes**: `config/model_routing.yaml` lets CEO or developer
  adjust tier assignments without touching agent code
- **Builds on ADR-0019**: Extends the two-tier LLM-fallback pattern into a proactive
  cost-optimization strategy (not just a fallback)

### Negative

- **Three provider dependencies instead of one**: OpenRouter (free tier) + Anthropic + rule
  engine. OpenRouter free tier has rate limits and model availability changes — monitoring
  needed
- **Tier 1 quality variance**: Free models (Gemini Flash, Qwen, Mistral 7B) have lower
  reasoning quality for edge cases. A misclassified email category (Opportunity filed as
  Promotional) is a real risk — mitigated by CEO spot-check SLA in SC-003 (85% accuracy)
- **Routing config maintenance**: Adding new task types requires updating `model_routing.yaml`
  AND writing the corresponding rule-based or free-model prompt — two places to update
- **Latency variation**: Free-tier models on OpenRouter may have higher p95 latency than
  Anthropic direct (rate-limit queuing). Tasks requiring near-real-time response (WhatsApp
  reply drafting) should default to Tier 2 regardless of classification
- **Privacy risk at Tier 1**: Sending email/message content to third-party free models
  (Google, Alibaba, Mistral) raises data residency questions. Mitigation: Tier 1 receives
  only metadata (subject, sender domain, keyword flags) — never full message body. Full
  content goes only to Tier 2 (Anthropic, which already handles CEO data in Phase 6)

## Alternatives Considered

**Alternative A: Single-model (Claude only, no routing)**
- All tasks sent to `claude-sonnet-4-6` regardless of complexity
- Rejected: Direct cause of the token burn problem identified in Q3. Greeting detection
  consuming the same token budget as briefing synthesis is economically indefensible at scale.
  Also violates the user's explicit instruction to use free models for development.

**Alternative B: Free-model only (Tier 1 for everything, no Tier 2)**
- Route all tasks to free OpenRouter models; only use Anthropic for CEO briefing
- Rejected: Free models produce noticeably lower quality for high-stakes outputs (sensitive
  email drafting, brand-voice LinkedIn posts). CEO professional reputation depends on Tier 2
  quality for these tasks. Cost saving is not worth quality risk for irreversible sends.

**Alternative C: Local LLM (Ollama + Mistral 7B or Qwen)**
- Run a quantized open-source model locally in WSL2 for all Tier 1 tasks
- Rejected: Requires 8GB+ RAM and GPU passthrough in WSL2 (not reliably available).
  Setup complexity conflicts with ADR-0003 (local-first, minimal infrastructure).
  OpenRouter free tier achieves the same cost (zero) with zero infra overhead.
  Revisit in Phase 7 (Oracle VM has dedicated compute).

**Alternative D: Single free provider (Gemini Flash only for Tier 1)**
- Use only Gemini Flash 1.5 (Google free tier) for all Tier 1 tasks
- Rejected: Single provider = single point of failure on rate limits. Google free tier
  has strict RPM limits. Round-robin across 3 providers (Gemini + Qwen + Mistral) provides
  natural load distribution and fallback without additional engineering.

**Alternative E: Per-platform model assignment (one model per platform)**
- WhatsApp → Qwen, Gmail → Gemini Flash, LinkedIn → Anthropic
- Rejected: Platform-based routing doesn't reflect actual task complexity — a LinkedIn
  comment classification is simpler than a LinkedIn post draft. Task-type routing is more
  precise and produces better cost/quality outcomes.

## References

- Feature Spec: `specs/011-full-comms-automation/spec.md` (FR-012 greeting templates, FR-038 HITL guardrails, SC-003 85% accuracy)
- Clarification record: `history/prompts/full-comms-automation/002-phase65-spec-clarifications-complete.spec.prompt.md` (Q3: auto-reply token burn, model switch decision)
- Related ADRs: ADR-0019 (CEO Briefing LLM Fallback — two-tier pattern this extends), ADR-0013 (three-layer email priority classifier — rule-based classification pattern reused in Tier 0), ADR-0004 (keyword heuristic email classification — basis for Tier 0 greeting detection)
- Evaluator Evidence: `history/prompts/full-comms-automation/002-phase65-spec-clarifications-complete.spec.prompt.md`
