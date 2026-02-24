"""Ralph Wiggum Orchestrator — core email triage engine.

Extends BaseWatcher to implement the LLM reasoning loop:
    1. poll()         — scan vault/Needs_Action/ for status: pending files
    2. process_item() — call LLM, validate JSON, apply decision to vault file
    3. validate_prerequisites() — verify LLM provider and vault structure

The Ralph Wiggum principle: retry with a correction prompt up to max_iterations
times when the LLM response is invalid JSON or fails Pydantic validation.

Decision types applied:
    draft_reply   → write draft to vault/Drafts/, update frontmatter
    needs_info    → append info_needed note to body, update frontmatter
    archive       → update frontmatter status=done, move file to vault/Done/
    urgent        → update priority=urgent, write draft if reply_body present
    delegate      → append delegation note to body, update frontmatter
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from watchers.base_watcher import BaseWatcher
from watchers.models import LogSeverity
from watchers.utils import PrerequisiteError

from orchestrator.models import (
    DecisionLogEntry,
    DraftReply,
    EmailContext,
    LLMDecision,
    OrchestratorState,
)
from orchestrator.prompts import (
    build_correction_prompt,
    build_system_prompt,
    build_user_message,
    prepare_body_for_context,
)
from orchestrator.mcp_client import MCPClient
from orchestrator.providers.base import LLMProvider
from orchestrator.vault_ops import (
    append_to_body,
    ensure_directory,
    move_to_done,
    read_email_context,
    scan_pending_emails,
    update_frontmatter,
    write_draft_reply,
)


class MaxIterationsExceeded(Exception):
    """Raised when the LLM fails to produce valid JSON after max_iterations."""


class RalphWiggumOrchestrator(BaseWatcher):
    """Email triage orchestrator using LLM reasoning.

    Extends BaseWatcher with:
    - poll():                Scan vault/Needs_Action/ for status: pending files
    - process_item():        LLM call → validate → apply decision
    - validate_prerequisites(): Check LLM provider, API key, vault structure
    """

    def __init__(
        self,
        provider: LLMProvider,
        poll_interval: int = 120,
        vault_path: str = "vault",
        max_iterations: int = 5,
    ) -> None:
        super().__init__(
            name="orchestrator",
            poll_interval=poll_interval,
            vault_path=vault_path,
        )
        self._provider = provider
        self._max_iterations = max_iterations

        # Extended state (decision_counts, total_tokens_used)
        self._orch_state = OrchestratorState()
        self._orch_state_path = self._log_dir / "orchestrator_extended_state.json"

        # Vault sub-directories
        self._needs_action_dir = self.vault_path / "Needs_Action"
        self._done_dir = self.vault_path / "Done"
        self._drafts_dir = self.vault_path / "Drafts"

        # Phase 4: MCP clients for approved draft send loop + vault operations
        self._gmail_mcp = MCPClient(
            server_name="gmail",
            command=["python3", "mcp_servers/gmail/server.py"],
            vault_path=self.vault_path,
        )
        self._obsidian_mcp = MCPClient(
            server_name="obsidian",
            command=["python3", "mcp_servers/obsidian/server.py"],
            vault_path=self.vault_path,
        )
        self._approved_dir = self.vault_path / "Approved"
        self._approved_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    # BaseWatcher abstract method implementations
    # -----------------------------------------------------------------------

    def validate_prerequisites(self) -> None:
        """Verify LLM provider configuration and vault directory structure."""
        # LLM_PROVIDER must be set (provider already instantiated, but validate env too)
        provider_key = os.getenv("LLM_PROVIDER", "").strip()
        if not provider_key:
            raise PrerequisiteError(
                "LLM_PROVIDER is not set. Set it in your .env file.",
                ht_reference="HT-009",
            )

        # Required vault directories
        if not self._needs_action_dir.exists():
            raise PrerequisiteError(
                f"vault/Needs_Action/ does not exist at {self._needs_action_dir}. "
                "Create the vault structure before starting the orchestrator.",
                ht_reference="HT-001",
            )
        if not self._done_dir.exists():
            raise PrerequisiteError(
                f"vault/Done/ does not exist at {self._done_dir}.",
                ht_reference="HT-001",
            )

        # Drafts directory is auto-created if missing (FR-024)
        ensure_directory(self._drafts_dir)
        ensure_directory(self._log_dir)

    async def poll(self) -> list[Any]:
        """Scan vault/Needs_Action/ for pending emails not yet processed.

        Returns:
            List of EmailContext objects ready for processing.
        """
        pending_paths = scan_pending_emails(self._needs_action_dir)
        contexts: list[EmailContext] = []

        for path in pending_paths:
            try:
                ctx = read_email_context(path)
            except (ValueError, OSError) as exc:
                self._log("read_error", LogSeverity.WARN, {
                    "file": str(path),
                    "error": str(exc),
                    "action": "skipped",
                })
                continue

            # Skip already-processed message IDs (BaseWatcher state)
            if ctx.message_id in self.state.processed_ids:
                continue

            contexts.append(ctx)

        return contexts

    async def process_item(self, item: Any) -> None:
        """Process one EmailContext: call LLM, validate, apply decision, log.

        Args:
            item: EmailContext (passed from BaseWatcher._run_poll_cycle)
        """
        context: EmailContext = item
        start_time = datetime.now(timezone.utc)

        try:
            decision, iteration, in_tok, out_tok = await self._call_llm_with_retry(context)
        except MaxIterationsExceeded as exc:
            self._log("llm_failed", LogSeverity.ERROR, {
                "email_message_id": context.message_id,
                "email_subject": context.subject,
                "error_type": "MaxIterationsExceeded",
                "error_message": str(exc),
                "max_iterations": self._max_iterations,
            })
            # Track error in extended state (T020 acceptance criterion)
            self._orch_state.record_error("MaxIterationsExceeded")
            self._save_orch_state()
            # Mark email as failed so it won't loop forever
            _safe_update(context, {"status": "failed", "orchestrator_error": str(exc)})
            # Add to processed_ids so we don't retry on next poll
            self.state.processed_ids.append(context.message_id)
            return

        # Write decision metadata to frontmatter BEFORE any file operations.
        # This ensures all 5 decision types have these fields — including archive,
        # whose file is moved afterward (fields are preserved in the moved file).
        decided_at = datetime.now(timezone.utc).isoformat()
        decided_by = f"{self._provider.provider_name()}:{self._provider.model_name()}"
        _safe_update(context, {
            "decision": decision.decision,
            "decision_reason": decision.reasoning,
            "decided_by": decided_by,
            "decided_at": decided_at,
            "iteration_count": iteration,
        })

        # Apply the decision to vault files (may move files, create drafts)
        draft_path: Path | None = None
        try:
            draft_path = await self._apply_decision(context, decision)
        except (OSError, ValueError) as exc:
            self._log("apply_decision_error", LogSeverity.ERROR, {
                "email_message_id": context.message_id,
                "decision": decision.decision,
                "error": str(exc),
            })

        # Add draft_path to frontmatter if a draft was created
        if draft_path:
            _safe_update(context, {"draft_path": str(draft_path)})

        # Update extended state counters
        self._orch_state.record_decision(decision.decision)
        self._orch_state.total_tokens_used += in_tok + out_tok
        self._orch_state.total_emails_processed += 1
        self._save_orch_state()

        # Mark as processed in BaseWatcher state
        self.state.processed_ids.append(context.message_id)

        # Write JSONL audit log entry
        latency_ms = int(
            (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        )
        self._write_decision_log(context, decision, in_tok, out_tok, latency_ms, iteration)

    # -----------------------------------------------------------------------
    # LLM interaction
    # -----------------------------------------------------------------------

    async def _call_llm_with_retry(
        self,
        context: EmailContext,
    ) -> tuple[LLMDecision, int, int, int]:
        """Call LLM with Ralph Wiggum retry loop.

        Returns:
            (decision, iteration_number, total_input_tokens, total_output_tokens)

        Raises:
            MaxIterationsExceeded: If all iterations fail.
        """
        system_prompt = build_system_prompt()

        # Prepare body with token budget management
        meta_msg = build_user_message(context, truncated_body="")
        body, _truncated = prepare_body_for_context(system_prompt, meta_msg, context.body)
        user_message = build_user_message(context, truncated_body=body)

        total_in = 0
        total_out = 0

        for iteration in range(1, self._max_iterations + 1):
            try:
                text, in_tok, out_tok = await self._provider.complete(
                    system_prompt=system_prompt,
                    user_message=user_message,
                )
                total_in += in_tok
                total_out += out_tok
            except Exception as exc:
                # Network/API error — log and continue to next iteration
                self._log("llm_api_error", LogSeverity.WARN, {
                    "iteration": iteration,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                })
                if iteration == self._max_iterations:
                    raise MaxIterationsExceeded(
                        f"LLM API error after {self._max_iterations} attempts: {exc}"
                    ) from exc
                user_message = build_correction_prompt(str(exc), text if 'text' in dir() else "")
                continue

            # Try to parse + validate
            parse_error: str = ""
            try:
                parsed = json.loads(text)
                decision = LLMDecision.model_validate(parsed)
                self._log("llm_decision", LogSeverity.INFO, {
                    "iteration": iteration,
                    "decision": decision.decision,
                    "confidence": decision.confidence,
                })
                return (decision, iteration, total_in, total_out)
            except json.JSONDecodeError as exc:
                parse_error = f"JSONDecodeError: {exc}"
            except ValidationError as exc:
                parse_error = f"ValidationError: {exc.error_count()} error(s): {exc.errors()[0]['msg']}"

            # Invalid response — build correction prompt for next iteration
            self._log("llm_invalid_response", LogSeverity.WARN, {
                "iteration": iteration,
                "error": parse_error,
                "response_preview": text[:200],
            })
            user_message = build_correction_prompt(parse_error, text)

        raise MaxIterationsExceeded(
            f"LLM did not produce valid JSON after {self._max_iterations} iterations"
        )

    # -----------------------------------------------------------------------
    # Decision application
    # -----------------------------------------------------------------------

    async def _apply_decision(
        self,
        context: EmailContext,
        decision: LLMDecision,
    ) -> Path | None:
        """Apply an LLM decision to vault files.

        MCP-first: uses Obsidian MCPClient for vault operations.
        Fallback: direct vault_ops calls if MCP unavailable.

        Returns:
            Path to the created draft file, or None if no draft was written.
        """
        filepath = Path(context.filepath) if context.filepath else None
        draft_path: Path | None = None
        decided_by = f"{self._provider.provider_name()}:{self._provider.model_name()}"

        if decision.decision == "draft_reply":
            if filepath and decision.reply_body:
                draft = DraftReply(
                    source_message_id=context.message_id,
                    to=context.sender,
                    subject=context.subject,
                    drafted_by=decided_by,
                    drafted_at=DraftReply.now_iso(),
                    reply_body=decision.reply_body,
                )
                # MCP-first: write draft via Obsidian MCP
                draft_rel = str(
                    Path("Drafts") / f"draft-{context.message_id[:8]}.md"
                )
                draft_fm = {
                    "type": draft.type,
                    "status": draft.status,
                    "source_message_id": draft.source_message_id,
                    "to": draft.to,
                    "subject": draft.subject,
                    "drafted_by": draft.drafted_by,
                    "drafted_at": draft.drafted_at,
                }
                await self._obsidian_mcp.call_tool(
                    "write_note",
                    {"path": draft_rel, "frontmatter": draft_fm, "body": draft.reply_body},
                    fallback=lambda: write_draft_reply(self._drafts_dir, draft),
                )
                draft_path = self._drafts_dir / f"draft-{context.message_id[:8]}.md"
            if filepath:
                src_rel = str(filepath.relative_to(self.vault_path))
                await self._obsidian_mcp.call_tool(
                    "write_note",
                    {"path": src_rel,
                     "frontmatter": {"status": "pending_approval"},
                     "body": context.body or ""},
                    fallback=lambda: update_frontmatter(filepath, {"status": "pending_approval"}),
                )

        elif decision.decision == "needs_info":
            if filepath:
                note = f"**AI needs more info**: {decision.info_needed}"
                src_rel = str(filepath.relative_to(self.vault_path))
                await self._obsidian_mcp.call_tool(
                    "write_note",
                    {"path": src_rel,
                     "frontmatter": {"status": "needs_info"},
                     "body": (context.body or "") + f"\n\n{note}"},
                    fallback=lambda: (
                        append_to_body(filepath, note),
                        update_frontmatter(filepath, {"status": "needs_info"}),
                    ),
                )

        elif decision.decision == "archive":
            if filepath:
                src_rel = str(filepath.relative_to(self.vault_path))
                dst_rel = str(
                    Path("Done") / filepath.name
                )
                await self._obsidian_mcp.call_tool(
                    "move_note",
                    {"source": src_rel, "destination": dst_rel},
                    fallback=lambda: (
                        update_frontmatter(filepath, {"status": "done"}),
                        move_to_done(filepath, self._done_dir),
                    ),
                )

        elif decision.decision == "urgent":
            if filepath:
                src_rel = str(filepath.relative_to(self.vault_path))
                await self._obsidian_mcp.call_tool(
                    "write_note",
                    {"path": src_rel,
                     "frontmatter": {"status": "pending_approval", "priority": "urgent"},
                     "body": context.body or ""},
                    fallback=lambda: update_frontmatter(
                        filepath, {"status": "pending_approval", "priority": "urgent"}
                    ),
                )
                if decision.reply_body:
                    draft = DraftReply(
                        source_message_id=context.message_id,
                        to=context.sender,
                        subject=context.subject,
                        drafted_by=decided_by,
                        drafted_at=DraftReply.now_iso(),
                        reply_body=decision.reply_body,
                    )
                    draft_rel = str(
                        Path("Drafts") / f"draft-{context.message_id[:8]}.md"
                    )
                    draft_fm = {
                        "type": draft.type,
                        "status": draft.status,
                        "source_message_id": draft.source_message_id,
                        "to": draft.to,
                        "subject": draft.subject,
                        "drafted_by": draft.drafted_by,
                        "drafted_at": draft.drafted_at,
                    }
                    await self._obsidian_mcp.call_tool(
                        "write_note",
                        {"path": draft_rel, "frontmatter": draft_fm, "body": draft.reply_body},
                        fallback=lambda: write_draft_reply(self._drafts_dir, draft),
                    )
                    draft_path = self._drafts_dir / f"draft-{context.message_id[:8]}.md"

        elif decision.decision == "delegate":
            if filepath:
                note = f"**AI delegation recommendation**: {decision.delegation_target}"
                src_rel = str(filepath.relative_to(self.vault_path))
                await self._obsidian_mcp.call_tool(
                    "write_note",
                    {"path": src_rel,
                     "frontmatter": {"status": "pending_approval"},
                     "body": (context.body or "") + f"\n\n{note}"},
                    fallback=lambda: (
                        append_to_body(filepath, note),
                        update_frontmatter(filepath, {"status": "pending_approval"}),
                    ),
                )

        return draft_path

    # -----------------------------------------------------------------------
    # Phase 4: Approved draft send loop (HITL send via Gmail MCP)
    # -----------------------------------------------------------------------

    async def _run_poll_cycle(self) -> None:
        """Override BaseWatcher poll cycle to add approved draft processing."""
        await super()._run_poll_cycle()

        # Process approved drafts (Phase 4 HITL send loop)
        try:
            approved = await self._scan_approved_drafts()
            for draft_path in approved:
                await self._send_approved_draft(draft_path)
        except Exception as e:
            self._log("approved_draft_scan_error", LogSeverity.ERROR, {"error": str(e)})

    async def _scan_approved_drafts(self) -> list[Path]:
        """Scan vault/Approved/ for *.md files with status: pending_approval.

        Approved draft files are not email notes (no message_id required).
        Parses frontmatter directly rather than using read_email_context.
        """
        import yaml

        approved = []
        for path in sorted(self._approved_dir.glob("*.md")):
            try:
                content = path.read_text(encoding="utf-8")
                parts = content.split("---", 2)
                if len(parts) < 3:
                    continue
                fm = yaml.safe_load(parts[1]) or {}
                if fm.get("status") == "pending_approval":
                    approved.append(path)
            except Exception as e:
                self._log("read_approved_error", LogSeverity.ERROR, {
                    "path": str(path),
                    "error": str(e),
                })
        return approved

    async def _send_approved_draft(self, draft_path: Path) -> None:
        """Send an approved draft via Gmail MCP, then move to Done/ on success."""
        import yaml

        content = draft_path.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        if len(parts) < 3:
            self._log("invalid_draft", LogSeverity.ERROR, {"path": str(draft_path)})
            return

        fm = yaml.safe_load(parts[1]) or {}
        body = parts[2].strip()
        to = fm.get("to", "")
        subject = fm.get("subject", "")
        reply_to = fm.get("original_message_id")

        if not to or not subject:
            self._log("incomplete_draft", LogSeverity.ERROR, {
                "path": str(draft_path),
                "fm": fm,
            })
            return

        async def fallback():
            """Fallback: keep draft in Approved/ for retry next cycle."""
            self._log("send_skipped_mcp_unavailable", LogSeverity.WARNING, {
                "path": str(draft_path),
            })
            return {}

        result = await self._gmail_mcp.call_tool(
            "send_email",
            {
                "to": to,
                "subject": subject,
                "body": body,
                "reply_to_message_id": reply_to,
            },
            fallback=fallback,
        )

        if result.get("error"):
            self._log("email_send_failed", LogSeverity.ERROR, {
                "path": str(draft_path),
                "error": result,
            })
            return

        # Success: move to Done/
        move_to_done(draft_path, self._done_dir)
        self._log("email_sent", LogSeverity.INFO, {
            "draft": str(draft_path),
            "message_id": result.get("message_id"),
            "sent_at": result.get("sent_at"),
        })

    # -----------------------------------------------------------------------
    # Extended state persistence
    # -----------------------------------------------------------------------

    def _save_orch_state(self) -> None:
        """Save extended orchestrator state (decision_counts, tokens) to JSON."""
        from watchers.utils import atomic_write as _atomic_write
        self._orch_state.last_run = datetime.now(timezone.utc).isoformat()
        _atomic_write(self._orch_state_path, self._orch_state.to_json())

    def _load_orch_state(self) -> None:
        """Load extended orchestrator state from JSON on startup."""
        if self._orch_state_path.exists():
            try:
                raw = self._orch_state_path.read_text(encoding="utf-8")
                self._orch_state = OrchestratorState.from_json(raw)
            except OSError:
                self._orch_state = OrchestratorState()

    # -----------------------------------------------------------------------
    # Decision audit log
    # -----------------------------------------------------------------------

    def _write_decision_log(
        self,
        context: EmailContext,
        decision: LLMDecision,
        in_tok: int,
        out_tok: int,
        latency_ms: int,
        iteration: int,
    ) -> None:
        """Write a DecisionLogEntry to the daily JSONL log file."""
        entry = DecisionLogEntry(
            timestamp=DecisionLogEntry.now_iso(),
            event="llm_decision",
            provider=self._provider.provider_name(),
            model=self._provider.model_name(),
            email_message_id=context.message_id,
            email_subject=context.subject,
            decision=decision.decision,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            tokens_input=in_tok,
            tokens_output=out_tok,
            latency_ms=latency_ms,
            iteration=iteration,
        )
        self._log("llm_decision_audit", LogSeverity.INFO, {
            **json.loads(entry.to_jsonl_line()),
        })


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_update(context: EmailContext, updates: dict) -> None:
    """Update frontmatter if context.filepath is available; silently skip if not."""
    if not context.filepath:
        return
    path = Path(context.filepath)
    if not path.exists():
        return
    try:
        update_frontmatter(path, updates)
    except (OSError, ValueError):
        pass
