"""Gmail watcher -- reads inbox emails via OAuth2 and writes to vault.

Implements GmailWatcher (extends BaseWatcher) for Phase 2 Bronze Tier.
Per Constitution Principle VI, ADR-0001, ADR-0002, ADR-0004.
"""

from __future__ import annotations

import asyncio
import base64
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from watchers.base_watcher import BaseWatcher
from watchers.models import Classification, EmailItem, LogSeverity
from watchers.utils import (
    PrerequisiteError,
    atomic_write,
    load_env,
    render_yaml_frontmatter,
    sanitize_filename,
    sanitize_utf8,
    truncate_subject,
)

# OAuth2 scopes -- future-proofing per plan (readonly now, send/modify later)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

# ── T077: Keyword score dictionaries (ADR-0004) ─────────────────────────

ACTIONABLE_KEYWORDS: dict[str, int] = {
    "action required": 5,
    "please review": 4,
    "approve": 4,
    "urgent": 3,
    "deadline": 3,
    "invoice": 3,
    "payment": 3,
    "meeting": 2,
    "request": 2,
    "follow up": 2,
    "follow-up": 2,
    "respond": 2,
    "confirm": 2,
    "asap": 3,
    "reminder": 2,
    "schedule": 2,
    "sign": 3,
    "submit": 2,
}

INFORMATIONAL_KEYWORDS: dict[str, int] = {
    "newsletter": 5,
    "unsubscribe": 4,
    "no-reply": 3,
    "noreply": 3,
    "digest": 3,
    "automated": 3,
    "notification": 2,
    "update": 1,
    "weekly": 2,
    "monthly": 2,
    "daily": 2,
    "summary": 2,
    "report": 1,
    "alert": 1,
    "do not reply": 3,
}

INFORMATIONAL_SENDER_PATTERNS: list[re.Pattern] = [
    re.compile(r"no[-_]?reply@", re.IGNORECASE),
    re.compile(r"noreply@", re.IGNORECASE),
    re.compile(r"notifications?@", re.IGNORECASE),
    re.compile(r"newsletter@", re.IGNORECASE),
    re.compile(r"digest@", re.IGNORECASE),
    re.compile(r"automated@", re.IGNORECASE),
    re.compile(r"mailer-daemon@", re.IGNORECASE),
    re.compile(r"do[-_]?not[-_]?reply@", re.IGNORECASE),
]

# Informational score threshold over actionable to classify as INFORMATIONAL
_CLASSIFICATION_THRESHOLD = 2


class GmailWatcher(BaseWatcher):
    """Concrete watcher for Gmail inbox.

    Reads unread emails, classifies them, and writes structured
    markdown files to the Obsidian vault.
    """

    def __init__(
        self,
        poll_interval: int = 60,
        vault_path: str = "vault",
        credentials_path: str | None = None,
        token_path: str | None = None,
    ) -> None:
        super().__init__("gmail_watcher", poll_interval, vault_path)

        if credentials_path is not None:
            self._credentials_path = Path(credentials_path)
        else:
            self._credentials_path = None

        if token_path is not None:
            self._token_path = Path(token_path)
        else:
            self._token_path = None

        self._service = None  # Gmail API service, set by _authenticate()

    def _resolve_paths(self) -> None:
        """Resolve credentials/token paths from .env if not provided."""
        if self._credentials_path is None or self._token_path is None:
            env = load_env()
            if self._credentials_path is None:
                self._credentials_path = Path(env["GMAIL_CREDENTIALS_PATH"])
            if self._token_path is None:
                self._token_path = Path(env["GMAIL_TOKEN_PATH"])

    async def start(self) -> None:
        """Override to authenticate with Gmail before entering the poll loop.

        Fixes: BaseWatcher.start() never called _authenticate(), leaving
        self._service = None and causing AttributeError on first poll().
        """
        self._resolve_paths()
        self._authenticate()
        await super().start()

    def validate_prerequisites(self) -> None:
        """Check that all required resources exist.

        Validates:
            - Vault directories (HT-001)
            - credentials.json (HT-002)
            - .env variables
        """
        required_dirs = ["Needs_Action", "Inbox", "Logs"]
        for dir_name in required_dirs:
            dir_path = self.vault_path / dir_name
            if not dir_path.exists():
                raise PrerequisiteError(
                    f"Vault directory missing: {dir_path}. "
                    f"Create the Obsidian vault structure first.",
                    ht_reference="HT-001",
                )

        self._resolve_paths()

        if not self._credentials_path.exists():
            raise PrerequisiteError(
                f"Gmail credentials file not found: {self._credentials_path}. "
                f"Download from Google Cloud Console.",
                ht_reference="HT-002",
            )

    def _authenticate(self) -> None:
        """Authenticate with Gmail API via OAuth2.

        Flow:
            1. Load token.json if exists
            2. If valid, use directly
            3. If expired with refresh_token, refresh
            4. If no token or corrupt, run browser flow
            5. Save token atomically
        """
        creds = None

        if self._token_path and self._token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(self._token_path), SCOPES
                )
            except (ValueError, KeyError):
                self._log("token_corrupt", LogSeverity.WARN, {
                    "action": "delete_and_reauth",
                    "path": str(self._token_path),
                })
                self._token_path.unlink(missing_ok=True)
                creds = None

        if creds and creds.valid:
            pass
        elif creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self._save_token(creds)
            self._log("token_refreshed", LogSeverity.INFO, {"action": "refreshed"})
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self._credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
            self._save_token(creds)
            self._log("token_created", LogSeverity.INFO, {
                "action": "browser_flow_completed",
            })

        self._service = build("gmail", "v1", credentials=creds)

    def _save_token(self, creds: Credentials) -> None:
        """Save OAuth2 token atomically."""
        atomic_write(self._token_path, creds.to_json())

    # ── T078: Classification (ADR-0004) ──────────────────────────────────

    def _classify_email(self, email: EmailItem) -> Classification:
        """Classify email as ACTIONABLE or INFORMATIONAL using keyword heuristics.

        Scores sender + subject + body[:500] against keyword dictionaries.
        Default-to-actionable policy: only classify as INFORMATIONAL if
        informational_score > actionable_score + threshold.
        """
        text = f"{email.sender} {email.subject} {email.body[:500]}".lower()

        actionable_score = 0
        for keyword, weight in ACTIONABLE_KEYWORDS.items():
            if keyword in text:
                actionable_score += weight

        informational_score = 0
        for keyword, weight in INFORMATIONAL_KEYWORDS.items():
            if keyword in text:
                informational_score += weight

        # Check sender patterns for informational bonus
        for pattern in INFORMATIONAL_SENDER_PATTERNS:
            if pattern.search(email.sender):
                informational_score += 3
                break

        # Default-to-actionable: only INFORMATIONAL if clearly informational
        if informational_score > actionable_score + _CLASSIFICATION_THRESHOLD:
            return Classification.INFORMATIONAL
        return Classification.ACTIONABLE

    # ── T079: Email parsing ──────────────────────────────────────────────

    def _parse_email(self, raw: dict[str, Any]) -> EmailItem:
        """Parse a raw Gmail API message dict into an EmailItem.

        Extracts headers, decodes body (prefers text/plain, strips HTML tags
        from text/html), detects attachments, and sanitizes text.
        """
        msg_id = raw.get("id", "")
        labels = raw.get("labelIds", [])
        size = raw.get("sizeEstimate", 0)

        payload = raw.get("payload", {})
        headers = {
            h["name"].lower(): h["value"]
            for h in payload.get("headers", [])
        }

        sender = headers.get("from", "")
        recipients = [
            r.strip() for r in headers.get("to", "").split(",") if r.strip()
        ]
        subject = headers.get("subject", "")
        date = headers.get("date", "")

        # Extract body and detect attachments
        body = ""
        has_attachments = False
        body, has_attachments = self._extract_body_and_attachments(payload)

        if not body:
            body = "No email body content."

        body = sanitize_utf8(body)
        subject = sanitize_utf8(subject)

        return EmailItem(
            message_id=msg_id,
            sender=sender,
            recipients=recipients,
            subject=subject,
            body=body,
            date=date,
            labels=labels,
            classification=Classification.ACTIONABLE,  # placeholder, classified later
            has_attachments=has_attachments,
            raw_size=size,
        )

    def _extract_body_and_attachments(
        self, payload: dict[str, Any]
    ) -> tuple[str, bool]:
        """Extract body text and attachment flag from payload."""
        body = ""
        has_attachments = False
        parts = payload.get("parts", [])

        if parts:
            for part in parts:
                mime = part.get("mimeType", "")
                filename = part.get("filename", "")

                if filename:
                    has_attachments = True
                    continue

                if mime == "text/plain" and not body:
                    body = self._decode_body(part.get("body", {}))
                elif mime == "text/html" and not body:
                    html_body = self._decode_body(part.get("body", {}))
                    body = self._strip_html(html_body)
                elif mime.startswith("multipart/"):
                    # Recurse into nested multipart
                    nested_body, nested_attach = self._extract_body_and_attachments(part)
                    if nested_body and not body:
                        body = nested_body
                    if nested_attach:
                        has_attachments = True
        else:
            # Single-part message
            body_data = payload.get("body", {})
            body = self._decode_body(body_data)
            if payload.get("mimeType", "") == "text/html":
                body = self._strip_html(body)

        return body, has_attachments

    @staticmethod
    def _decode_body(body_obj: dict[str, Any]) -> str:
        """Decode base64url-encoded body data."""
        data = body_obj.get("data", "")
        if not data:
            return ""
        try:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        except Exception:
            return ""

    @staticmethod
    def _strip_html(html: str) -> str:
        """Strip HTML tags for plain text extraction."""
        text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        return text.strip()

    # ── T080: Fetch unread emails (ADR-0002: asyncio.to_thread) ──────────

    async def _fetch_unread_emails(self) -> list[dict[str, Any]]:
        """Fetch unread inbox emails via Gmail API, wrapped in asyncio.to_thread."""
        return await asyncio.to_thread(self._fetch_unread_emails_sync)

    def _fetch_unread_emails_sync(self) -> list[dict[str, Any]]:
        """Synchronous Gmail API call for messages.list + messages.get."""
        results = (
            self._service.users()
            .messages()
            .list(userId="me", q="is:unread in:inbox", maxResults=50)
            .execute()
        )

        messages = results.get("messages", [])
        if not messages:
            return []

        full_messages = []
        for msg_ref in messages:
            msg = (
                self._service.users()
                .messages()
                .get(userId="me", id=msg_ref["id"], format="full")
                .execute()
            )
            full_messages.append(msg)

        return full_messages

    # ── T081: Poll ───────────────────────────────────────────────────────

    async def poll(self) -> list[EmailItem]:
        """Fetch unread emails, filter processed, parse, classify."""
        raw_messages = await self._fetch_unread_emails()

        items = []
        for raw in raw_messages:
            msg_id = raw.get("id", "")
            if msg_id in self.state.processed_ids:
                continue

            email = self._parse_email(raw)
            classification = self._classify_email(email)

            # Re-create with correct classification
            email = EmailItem(
                message_id=email.message_id,
                sender=email.sender,
                recipients=email.recipients,
                subject=email.subject,
                body=email.body,
                date=email.date,
                labels=email.labels,
                classification=classification,
                has_attachments=email.has_attachments,
                raw_size=email.raw_size,
            )
            items.append(email)

        return items

    # ── T082: Filename generation ────────────────────────────────────────

    def _generate_filename(self, email: EmailItem, target_dir: Path) -> str:
        """Generate a unique filename: YYYY-MM-DD-HHmm-sanitized-subject.md."""
        try:
            dt = datetime.fromisoformat(email.date.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            dt = datetime.now(timezone.utc)

        date_prefix = dt.strftime("%Y-%m-%d-%H%M")
        subject_slug = sanitize_filename(email.subject, max_length=60)
        base_name = f"{date_prefix}-{subject_slug}.md"

        if not (target_dir / base_name).exists():
            return base_name

        # Handle collisions
        for i in range(1, 1000):
            collision_name = f"{date_prefix}-{subject_slug}-{i:03d}.md"
            if not (target_dir / collision_name).exists():
                return collision_name

        return base_name  # fallback

    # ── T083: Markdown rendering ─────────────────────────────────────────

    def _render_markdown(self, email: EmailItem) -> str:
        """Render EmailItem as markdown with YAML frontmatter."""
        now = datetime.now(timezone.utc).isoformat()

        fields = {
            "type": "email",
            "status": "pending",
            "source": "gmail",
            "message_id": email.message_id,
            "from": email.sender,
            "subject": truncate_subject(email.subject, max_length=200),
            "date_received": email.date,
            "date_processed": now,
            "classification": email.classification.value,
            "priority": "standard",
            "has_attachments": email.has_attachments,
            "watcher": "gmail_watcher",
        }

        frontmatter = render_yaml_frontmatter(fields)
        return f"{frontmatter}\n{email.body}\n"

    # ── T084: Vault target directory ─────────────────────────────────────

    def _get_vault_target_dir(self, classification: Classification) -> Path:
        """Return the vault directory for a given classification."""
        if classification == Classification.ACTIONABLE:
            return self.vault_path / "Needs_Action"
        return self.vault_path / "Inbox"

    # ── T085: Process item ───────────────────────────────────────────────

    async def process_item(self, item: Any) -> None:
        """Process a single email: generate file, write to vault, update state."""
        email: EmailItem = item
        target_dir = self._get_vault_target_dir(email.classification)
        filename = self._generate_filename(email, target_dir)
        content = self._render_markdown(email)

        file_path = target_dir / filename
        atomic_write(file_path, content)

        self.state.processed_ids.append(email.message_id)

        self._log("email_processed", LogSeverity.INFO, {
            "message_id": email.message_id,
            "classification": email.classification.value,
            "file": str(file_path),
            "subject": truncate_subject(email.subject, max_length=80),
        })


# ── T086: __main__ block ─────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gmail Watcher for Personal AI Employee")
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=60,
        help="Poll interval in seconds (minimum 30)",
    )
    parser.add_argument(
        "--vault-path",
        type=str,
        default="vault",
        help="Path to Obsidian vault directory",
    )
    args = parser.parse_args()

    watcher = GmailWatcher(
        poll_interval=args.poll_interval,
        vault_path=args.vault_path,
    )
    asyncio.run(watcher.start())
