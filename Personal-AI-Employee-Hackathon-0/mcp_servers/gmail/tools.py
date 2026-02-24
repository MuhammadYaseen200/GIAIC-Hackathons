"""Gmail MCP tool handler implementations. Called by FastMCP server in server.py."""
import asyncio
import base64
import email as email_lib
import email.mime.text
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from googleapiclient.errors import HttpError

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.utils import atomic_write

from .auth import AuthRequiredError, get_gmail_service


class GmailTools:
    """Implements all Gmail MCP tool handlers. Stateless — each call gets fresh service if needed."""

    def __init__(self, vault_path: Path):
        self._vault_path = vault_path
        self._log_dir = vault_path / "Logs"

    # ── health_check ────────────────────────────────────────────────────────

    async def health_check(self) -> dict:
        """Verify server is operational and OAuth token is valid."""
        try:
            service = get_gmail_service()
            profile = await asyncio.to_thread(
                lambda: service.users().getProfile(userId="me").execute()
            )
            return {
                "status": "ok",
                "authenticated_as": profile.get("emailAddress", "unknown"),
                "token_expires_at": "managed_by_google_auth",
            }
        except AuthRequiredError as e:
            return {"error": "auth_required", "message": str(e)}
        except Exception as e:
            return {"error": "internal_error", "message": str(e)}

    # ── send_email ───────────────────────────────────────────────────────────

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        reply_to_message_id: str | None = None,
    ) -> dict:
        """Send email. Writes pre-action audit log BEFORE Gmail API call (Constitution Principle IX)."""
        # Step 1: Pre-action audit log (written before API call)
        self._write_audit_log(to, subject, body, reply_to_message_id)

        try:
            service = get_gmail_service()

            # Build MIME message
            msg = email.mime.text.MIMEText(body, "plain", "utf-8")
            msg["To"] = to
            msg["Subject"] = subject
            if reply_to_message_id:
                msg["In-Reply-To"] = reply_to_message_id
                msg["References"] = reply_to_message_id

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            body_payload: dict[str, Any] = {"raw": raw}

            if reply_to_message_id:
                # Fetch thread ID for proper email threading
                orig = await asyncio.to_thread(
                    lambda: service.users().messages().get(
                        userId="me", id=reply_to_message_id, format="minimal"
                    ).execute()
                )
                body_payload["threadId"] = orig.get("threadId")

            sent = await asyncio.to_thread(
                lambda: service.users().messages().send(
                    userId="me", body=body_payload
                ).execute()
            )

            return {
                "message_id": sent["id"],
                "thread_id": sent.get("threadId", ""),
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }

        except AuthRequiredError as e:
            return {"error": "auth_required", "message": str(e)}
        except HttpError as e:
            if e.resp.status == 429:
                return {
                    "error": "rate_limited",
                    "message": "Gmail API rate limit hit",
                    "details": {"retry_after": 60},
                }
            return {
                "error": "send_failed",
                "message": f"Gmail API error: {e.resp.status} {e._get_reason()}",
            }
        except Exception as e:
            return {"error": "internal_error", "message": str(e)}

    # ── list_emails ──────────────────────────────────────────────────────────

    async def list_emails(self, query: str = "is:unread", max_results: int = 10) -> dict:
        """List emails matching Gmail search query."""
        try:
            service = get_gmail_service()
            results = await asyncio.to_thread(
                lambda: service.users().messages().list(
                    userId="me", q=query, maxResults=max_results
                ).execute()
            )
            messages = results.get("messages", [])
            emails = []
            for msg in messages:
                meta = await asyncio.to_thread(
                    lambda m=msg: service.users().messages().get(
                        userId="me",
                        id=m["id"],
                        format="metadata",
                        metadataHeaders=["Subject", "From", "Date"],
                    ).execute()
                )
                headers = {
                    h["name"]: h["value"]
                    for h in meta.get("payload", {}).get("headers", [])
                }
                emails.append({
                    "id": meta["id"],
                    "subject": headers.get("Subject", "(no subject)"),
                    "sender": headers.get("From", ""),
                    "date": headers.get("Date", ""),
                    "snippet": meta.get("snippet", ""),
                })
            return {"emails": emails, "total_count": len(emails)}
        except AuthRequiredError as e:
            return {"error": "auth_required", "message": str(e)}
        except HttpError as e:
            if e.resp.status == 429:
                return {
                    "error": "rate_limited",
                    "message": "Rate limit hit",
                    "details": {"retry_after": 60},
                }
            return {"error": "internal_error", "message": str(e)}
        except Exception as e:
            return {"error": "internal_error", "message": str(e)}

    # ── get_email ────────────────────────────────────────────────────────────

    async def get_email(self, message_id: str) -> dict:
        """Get full email content by message ID."""
        try:
            service = get_gmail_service()
            msg = await asyncio.to_thread(
                lambda: service.users().messages().get(
                    userId="me", id=message_id, format="full"
                ).execute()
            )
            payload = msg.get("payload", {})
            headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

            # Decode body from MIME parts
            body = ""
            parts = payload.get("parts", [payload])
            for part in parts:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(
                        part["body"]["data"]
                    ).decode("utf-8", errors="replace")
                    break

            attachments = [
                p.get("filename", "")
                for p in payload.get("parts", [])
                if p.get("filename")
            ]

            return {
                "id": msg["id"],
                "subject": headers.get("Subject", ""),
                "sender": headers.get("From", ""),
                "to": headers.get("To", ""),
                "date": headers.get("Date", ""),
                "body": body,
                "has_attachments": bool(attachments),
                "attachment_names": attachments,
            }
        except AuthRequiredError as e:
            return {"error": "auth_required", "message": str(e)}
        except HttpError as e:
            if e.resp.status == 404:
                return {"error": "not_found", "message": f"Email {message_id} not found"}
            if e.resp.status == 429:
                return {
                    "error": "rate_limited",
                    "message": "Rate limit hit",
                    "details": {"retry_after": 60},
                }
            return {"error": "internal_error", "message": str(e)}
        except Exception as e:
            return {"error": "internal_error", "message": str(e)}

    # ── move_email ───────────────────────────────────────────────────────────

    async def move_email(self, message_id: str, destination_label: str) -> dict:
        """Move email to destination Gmail label."""
        try:
            service = get_gmail_service()
            labels_response = await asyncio.to_thread(
                lambda: service.users().labels().list(userId="me").execute()
            )
            label_id = None
            for lbl in labels_response.get("labels", []):
                if lbl["name"].upper() == destination_label.upper():
                    label_id = lbl["id"]
                    break
            if not label_id:
                # Use built-in label name directly
                label_id = destination_label

            await asyncio.to_thread(
                lambda: service.users().messages().modify(
                    userId="me",
                    id=message_id,
                    body={"addLabelIds": [label_id], "removeLabelIds": ["INBOX"]},
                ).execute()
            )
            return {"moved": True, "message_id": message_id, "label": destination_label}
        except AuthRequiredError as e:
            return {"error": "auth_required", "message": str(e)}
        except HttpError as e:
            if e.resp.status == 404:
                return {"error": "not_found", "message": f"Email {message_id} not found"}
            return {"error": "internal_error", "message": str(e)}
        except Exception as e:
            return {"error": "internal_error", "message": str(e)}

    # ── add_label ────────────────────────────────────────────────────────────

    async def add_label(self, message_id: str, label_name: str) -> dict:
        """Apply Gmail label to email. Creates label if it doesn't exist."""
        try:
            service = get_gmail_service()
            labels_response = await asyncio.to_thread(
                lambda: service.users().labels().list(userId="me").execute()
            )
            label_id = None
            for lbl in labels_response.get("labels", []):
                if lbl["name"] == label_name:
                    label_id = lbl["id"]
                    break
            if not label_id:
                new_label = await asyncio.to_thread(
                    lambda: service.users().labels().create(
                        userId="me", body={"name": label_name}
                    ).execute()
                )
                label_id = new_label["id"]

            await asyncio.to_thread(
                lambda: service.users().messages().modify(
                    userId="me",
                    id=message_id,
                    body={"addLabelIds": [label_id]},
                ).execute()
            )
            return {"labeled": True, "message_id": message_id, "label": label_name}
        except AuthRequiredError as e:
            return {"error": "auth_required", "message": str(e)}
        except HttpError as e:
            if e.resp.status == 404:
                return {"error": "not_found", "message": f"Email {message_id} not found"}
            return {"error": "internal_error", "message": str(e)}
        except Exception as e:
            return {"error": "internal_error", "message": str(e)}

    # ── internal helpers ─────────────────────────────────────────────────────

    def _write_audit_log(
        self, to: str, subject: str, body: str, reply_to: str | None
    ) -> None:
        """Write pre-send audit JSONL entry before Gmail API call (Constitution Principle IX)."""
        self._log_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "event": "pre_send_audit",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "to": to,
            "subject": subject,
            "body_preview": body[:200],
            "reply_to_message_id": reply_to,
            "severity": "INFO",
        }
        date_str = datetime.now(timezone.utc).date().isoformat()
        log_path = self._log_dir / f"gmail_mcp_{date_str}.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
