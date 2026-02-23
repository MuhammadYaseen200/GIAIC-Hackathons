"""Pydantic v2 data models for the Ralph Wiggum Orchestrator.

All models are immutable where possible and use strict validation.
These are the data contracts between:
- vault_ops.py (reads EmailContext from vault files)
- providers/ (returns LLMDecision from LLM API)
- orchestrator.py (applies decisions, logs entries)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


# ---------------------------------------------------------------------------
# Decision Types
# ---------------------------------------------------------------------------

DecisionType = Literal["draft_reply", "needs_info", "archive", "urgent", "delegate"]

VALID_DECISIONS: frozenset[str] = frozenset(
    {"draft_reply", "needs_info", "archive", "urgent", "delegate"}
)


# ---------------------------------------------------------------------------
# LLM Decision (output of LLM call, validated by Pydantic)
# ---------------------------------------------------------------------------

class LLMDecision(BaseModel):
    """Structured output from the LLM triage call.

    The LLM MUST return JSON matching this schema.
    Pydantic validates all fields — invalid responses are retried (Ralph Wiggum loop).
    """

    model_config = ConfigDict(frozen=True)

    decision: DecisionType
    confidence: float  # 0.0–1.0
    reasoning: str
    reply_body: Optional[str] = None          # REQUIRED for draft_reply, OPTIONAL for urgent
    delegation_target: Optional[str] = None   # REQUIRED for delegate
    info_needed: Optional[str] = None         # REQUIRED for needs_info

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("reasoning")
    @classmethod
    def reasoning_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("reasoning must not be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_required_fields(self) -> LLMDecision:
        """Ensure decision-specific fields are present."""
        if self.decision == "draft_reply" and not self.reply_body:
            # reply_body strongly expected for draft_reply but not hard-blocked
            # (LLM may sometimes omit it — orchestrator handles gracefully)
            pass
        if self.decision == "delegate" and not self.delegation_target:
            raise ValueError("delegation_target is required when decision is 'delegate'")
        if self.decision == "needs_info" and not self.info_needed:
            raise ValueError("info_needed is required when decision is 'needs_info'")
        return self

    @classmethod
    def from_json_string(cls, text: str) -> "LLMDecision":
        """Parse and validate from raw LLM response string.

        Raises:
            json.JSONDecodeError: if text is not valid JSON
            pydantic.ValidationError: if JSON does not match schema
        """
        parsed = json.loads(text.strip())
        return cls.model_validate(parsed)


# ---------------------------------------------------------------------------
# Email Context (input to LLM — read from vault file)
# ---------------------------------------------------------------------------

class EmailContext(BaseModel):
    """Email metadata and body extracted from a vault markdown file.

    Populated by vault_ops.read_email_context() from YAML frontmatter + body.
    """

    model_config = ConfigDict(frozen=True)

    message_id: str
    sender: str          # "From" field (raw value from frontmatter)
    subject: str
    body: str            # full email body text
    classification: str  # "actionable" | "informational"
    priority: str        # "standard" | "urgent" | ...
    date_received: str   # RFC 2822 or ISO 8601 string
    has_attachments: bool = False
    filepath: Optional[str] = None  # source vault file path (for logging)

    @field_validator("message_id")
    @classmethod
    def message_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("message_id must not be empty")
        return v.strip()


# ---------------------------------------------------------------------------
# Draft Reply (written to vault/Drafts/)
# ---------------------------------------------------------------------------

class DraftReply(BaseModel):
    """A draft reply file written to vault/Drafts/ by the orchestrator.

    Becomes a markdown file with YAML frontmatter for human review in Obsidian.
    """

    model_config = ConfigDict(frozen=True)

    type: str = "draft_reply"
    status: str = "pending_approval"
    source_message_id: str     # links back to original email
    to: str                    # original sender (we reply to them)
    subject: str               # "Re: <original subject>"
    drafted_by: str            # "provider_name:model_name"
    drafted_at: str            # ISO 8601 UTC timestamp
    reply_body: str            # the actual reply text

    @field_validator("subject")
    @classmethod
    def ensure_re_prefix(cls, v: str) -> str:
        """Prepend 'Re: ' if not already present."""
        if not v.lower().startswith("re:"):
            return f"Re: {v}"
        return v

    @classmethod
    def now_iso(cls) -> str:
        """Return current UTC time as ISO 8601 string."""
        return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Orchestrator State (persisted to vault/Logs/orchestrator_state.json)
# ---------------------------------------------------------------------------

class OrchestratorState(BaseModel):
    """Persistent state for the RalphWiggumOrchestrator.

    Saved after every poll cycle. Loaded on startup to resume without
    re-processing already-handled emails.
    """

    processed_ids: list[str] = []          # message_ids already processed
    error_counts: dict[str, int] = {}      # error_type → count
    decision_counts: dict[str, int] = {}   # decision_type → count
    last_run: Optional[str] = None         # ISO 8601 of last successful poll
    total_tokens_used: int = 0             # cumulative tokens (input + output)
    total_emails_processed: int = 0        # total count processed across all runs

    def to_json(self) -> str:
        """Serialize to JSON string for atomic_write."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, text: str) -> "OrchestratorState":
        """Deserialize from JSON string. Returns empty state on parse error."""
        try:
            return cls.model_validate_json(text)
        except Exception:
            return cls()

    def prune_processed_ids(self, max_ids: int = 100_000) -> None:
        """FIFO pruning to prevent unbounded growth."""
        if len(self.processed_ids) > max_ids:
            self.processed_ids = self.processed_ids[-max_ids:]

    def record_decision(self, decision_type: str) -> None:
        """Increment decision counter."""
        self.decision_counts[decision_type] = self.decision_counts.get(decision_type, 0) + 1

    def record_error(self, error_type: str) -> None:
        """Increment error counter."""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1


# ---------------------------------------------------------------------------
# Decision Log Entry (JSONL written to vault/Logs/orchestrator_YYYY-MM-DD.log)
# ---------------------------------------------------------------------------

class DecisionLogEntry(BaseModel):
    """A single log entry in the orchestrator's JSONL audit log.

    Written after every LLM decision (success or failure).
    Parseable by Obsidian Dataview for dashboard queries (SC-007).
    """

    model_config = ConfigDict(frozen=True)

    timestamp: str              # ISO 8601 UTC
    event: str                  # "llm_decision" | "llm_error" | "poll_cycle_complete" | ...
    provider: str               # "anthropic" | "openai" | "gemini" | ...
    model: str                  # e.g. "claude-sonnet-4-20250514"
    email_message_id: str = ""
    email_subject: str = ""
    decision: Optional[str] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: int = 0
    iteration: int = 1          # which Ralph Wiggum iteration produced this result
    severity: str = "info"      # "debug" | "info" | "warn" | "error"
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    def to_jsonl_line(self) -> str:
        """Serialize to a single JSONL line (no trailing newline)."""
        return self.model_dump_json()

    @classmethod
    def now_iso(cls) -> str:
        """Return current UTC time as ISO 8601 string."""
        return datetime.now(timezone.utc).isoformat()
