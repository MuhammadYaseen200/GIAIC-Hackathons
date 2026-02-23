"""Prompt engineering for the Ralph Wiggum Orchestrator.

Implements the Ralph Wiggum principle: constrain the LLM's output space to
exactly what the system can handle.  The system prompt embeds the full JSON
schema so the LLM knows precisely what to return.

Design decisions (per ADR-0006):
- JSON schema embedded in system prompt (portable across all 7 providers)
- No native JSON mode / response_format (not universally supported)
- Retry with correction prompt on validation failure (max 5 iterations)
- Financial safety constraint: payment/invoice/billing → never archive
"""

from __future__ import annotations

from orchestrator.models import EmailContext

# ---------------------------------------------------------------------------
# Token budget constants
# ---------------------------------------------------------------------------

_TOTAL_BUDGET_TOKENS = 4000
_SAFETY_MARGIN_TOKENS = 200   # reserved for response

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an AI email triage assistant for a solo founder/CEO. Your job is to classify \
each email and make a decision about what action to take.

## Decision Types

You must choose exactly ONE of these 5 decisions for each email:

1. **draft_reply** - The email requires a response. You will draft a professional reply.
2. **needs_info** - You cannot make a decision without more context. Specify what info is needed.
3. **archive** - The email is informational, promotional, or requires no action. Safe to archive.
4. **urgent** - The email requires IMMEDIATE human attention. Use sparingly.
5. **delegate** - The email should be forwarded to someone else. Specify who and why.

## Safety Rules

- Emails about MONEY (payment, invoice, subscription, billing, charge, refund) must NEVER \
be classified as "archive". Always use "urgent" or "needs_info" for financial emails.
- When in doubt between "archive" and another action, choose the other action.
- Draft replies should be professional, concise, and address the sender's request directly.

## Output Format

Respond ONLY with a JSON object matching this exact schema. No markdown, no explanation, \
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
- "info_needed": Include ONLY for needs_info (required). Must be null for others.\
"""


def build_system_prompt() -> str:
    """Return the full Ralph Wiggum system prompt.

    Includes: agent role, 5 decision types, financial safety constraint,
    JSON output schema with field rules.
    """
    return _SYSTEM_PROMPT


def build_user_message(context: EmailContext, truncated_body: str | None = None) -> str:
    """Build the user-turn message from an EmailContext.

    Args:
        context: Parsed email context from the vault markdown file.
        truncated_body: If provided, use this body text instead of context.body.
            Pass when the body has already been truncated for the token budget.

    Returns:
        Formatted user message string.
    """
    body = truncated_body if truncated_body is not None else context.body
    return (
        f"## Email to Triage\n\n"
        f"**From:** {context.sender}\n"
        f"**Subject:** {context.subject}\n"
        f"**Date:** {context.date_received}\n"
        f"**Classification:** {context.classification}\n"
        f"**Has Attachments:** {context.has_attachments}\n\n"
        f"## Email Body\n\n"
        f"{body}"
    )


def build_correction_prompt(error: str, original_response: str = "") -> str:
    """Build the correction prompt for invalid LLM output (Ralph Wiggum retry).

    Args:
        error: The validation or JSON parse error message.
        original_response: The LLM's previous invalid response (for context).

    Returns:
        Correction prompt to send as the next user message.
    """
    lines = [
        "Your previous response was not valid JSON or did not match the required schema.",
        "",
        f"Error: {error}",
        "",
        "Please respond ONLY with a valid JSON object matching the schema. No markdown, no",
        "explanation, no code fences. Just the JSON object.",
    ]
    if original_response:
        lines += [
            "",
            "Your previous response was:",
            original_response[:500],  # cap to avoid ballooning the prompt
        ]
    return "\n".join(lines)


def estimate_tokens(text: str) -> int:
    """Approximate token count for a string.

    Uses the heuristic of 4 characters per token (FR-022).
    Sufficient precision for budget management; not used for billing.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def truncate_body(body: str, remaining_budget_tokens: int) -> tuple[str, bool]:
    """Truncate an email body to fit within the remaining token budget.

    Args:
        body: The full email body text.
        remaining_budget_tokens: Max tokens available for the body.

    Returns:
        (body_text, was_truncated):
            - body_text: Possibly truncated body with notice appended.
            - was_truncated: True if truncation occurred.
    """
    if not body:
        return ("", False)

    body_tokens = estimate_tokens(body)
    if body_tokens <= remaining_budget_tokens:
        return (body, False)

    # Truncate to budget (chars = tokens * 4)
    max_chars = remaining_budget_tokens * 4
    truncated = body[:max_chars]
    notice = (
        f"\n\n[EMAIL TRUNCATED: original body was ~{body_tokens} tokens, "
        f"truncated to ~{remaining_budget_tokens} tokens for processing.]"
    )
    return (truncated + notice, True)


def prepare_body_for_context(
    system_prompt: str,
    user_message_without_body: str,
    body: str,
) -> tuple[str, bool]:
    """Apply token budget management to the email body.

    Follows the 4-step process from plan.md Section 9:
    1. Compute system_tokens
    2. Compute metadata_tokens
    3. Compute remaining_budget = 4000 - system - metadata - 200 (safety margin)
    4. Truncate body if needed

    Args:
        system_prompt: The system prompt string.
        user_message_without_body: The user message without the body text.
        body: The raw email body.

    Returns:
        (prepared_body, was_truncated)
    """
    system_tokens = estimate_tokens(system_prompt)
    metadata_tokens = estimate_tokens(user_message_without_body)
    remaining = _TOTAL_BUDGET_TOKENS - system_tokens - metadata_tokens - _SAFETY_MARGIN_TOKENS
    remaining = max(remaining, 200)  # always allow at least 200 tokens for body
    return truncate_body(body, remaining)
