"""
Privacy Gate — Layer 0 pre-processing for all watchers.
Pure function: no I/O, no side effects.
ADR-0010: watchers/privacy_gate.py
"""
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone


# Sensitive patterns to redact from message body
SENSITIVE_PATTERNS = [
    (re.compile(r'\b\d{13,19}\b'), '[REDACTED-CARD]'),           # Card numbers
    (re.compile(r'\b(?:cvv|cvc)\b[\s:=]+\d{3,4}', re.I), '[REDACTED-CVV]'),
    (re.compile(r'\b(?:otp|one.?time.?(?:password|code|pin))\b[\s:=]+\d{4,8}', re.I), '[REDACTED-OTP]'),
    (re.compile(r'(?<!\d)\b\d{6}\b(?!\d)'), '[REDACTED-OTP]'),   # Standalone 6-digit codes
    (re.compile(r'\b(?:password|passwd|pwd)\b[\s:=]+\S+', re.I), '[REDACTED-PASSWORD]'),
    (re.compile(r'\b(?:pin)\b[\s:=]+\d{4,8}', re.I), '[REDACTED-PIN]'),
    (re.compile(r'\b(?:secret|api.?key|access.?token|auth.?token)\b[\s:=]+\S+', re.I), '[REDACTED-SECRET]'),
]


@dataclass
class PrivacyGateResult:
    body: str
    media_blocked: bool = False
    redaction_applied: bool = False
    alert_message: str = ""
    patterns_matched: list = field(default_factory=list)


@dataclass
class PrivacyLogEntry:
    timestamp: str
    media_blocked: bool
    redaction_applied: bool
    patterns_matched: list
    source: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "media_blocked": self.media_blocked,
            "redaction_applied": self.redaction_applied,
            "patterns_matched": self.patterns_matched,
            "source": self.source,
        }


def run_privacy_gate(
    body: str,
    media_type: str,
    caption: str | None = None,
) -> PrivacyGateResult:
    """
    Layer 0 privacy gate. Pure function — no I/O.
    - Blocks all non-text media unconditionally.
    - Redacts sensitive patterns from text body and caption.
    - alert_message contains NO original sensitive content.
    """
    # Unconditional media block
    if media_type != "text":
        return PrivacyGateResult(
            body="[MEDIA — content not stored]",
            media_blocked=True,
            redaction_applied=False,
            alert_message=f"Privacy Gate: {media_type} media blocked — content not stored.",
            patterns_matched=[],
        )

    # Text redaction
    redacted_body = body
    patterns_matched = []

    for pattern, replacement in SENSITIVE_PATTERNS:
        new_body = pattern.sub(replacement, redacted_body)
        if new_body != redacted_body:
            patterns_matched.append(replacement)
            redacted_body = new_body

    # Caption redaction (if provided)
    if caption:
        for pattern, replacement in SENSITIVE_PATTERNS:
            caption = pattern.sub(replacement, caption)

    redaction_applied = len(patterns_matched) > 0
    alert_message = ""
    if redaction_applied:
        unique = list(dict.fromkeys(patterns_matched))
        alert_message = (
            f"Privacy Gate: {len(unique)} sensitive pattern(s) redacted "
            f"({', '.join(unique)}). Original content not stored."
        )

    return PrivacyGateResult(
        body=redacted_body,
        media_blocked=False,
        redaction_applied=redaction_applied,
        alert_message=alert_message,
        patterns_matched=patterns_matched,
    )
