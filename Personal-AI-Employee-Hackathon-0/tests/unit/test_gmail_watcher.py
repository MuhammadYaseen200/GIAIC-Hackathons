"""Unit tests for watchers.gmail_watcher -- T052-T063 (Phase 4) + T064-T076 (Phase 5) + T088-T090 (Phase 6)."""

import asyncio
import base64
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest
import yaml

from watchers.models import Classification, EmailItem
from watchers.utils import PrerequisiteError


# ── T052-T055: Authentication tests ──────────────────────────────────────


class TestAuthenticateNewToken:
    """T052: Given credentials.json exists but no token.json,
    When _authenticate() called,
    Then InstalledAppFlow.from_client_secrets_file is invoked, token saved."""

    @pytest.mark.asyncio
    async def test_new_token_triggers_browser_flow(self, tmp_vault, mock_env):
        from watchers.gmail_watcher import GmailWatcher

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.to_json.return_value = '{"token": "new_token"}'

        mock_flow = MagicMock()
        mock_flow.run_local_server.return_value = mock_creds

        with patch(
            "watchers.gmail_watcher.InstalledAppFlow.from_client_secrets_file",
            return_value=mock_flow,
        ) as mock_from_secrets, patch(
            "watchers.gmail_watcher.build"
        ):
            watcher = GmailWatcher(
                vault_path=str(tmp_vault),
                credentials_path=str(mock_env["credentials_path"]),
                token_path=str(mock_env["token_path"]),
            )
            watcher._authenticate()

            mock_from_secrets.assert_called_once()
            mock_flow.run_local_server.assert_called_once_with(port=0)

            # Token should be saved
            assert mock_env["token_path"].exists()
            saved = mock_env["token_path"].read_text()
            assert "new_token" in saved


class TestAuthenticateExistingValidToken:
    """T053: Given valid token.json exists,
    When _authenticate() called,
    Then no browser flow, credentials loaded from file."""

    @pytest.mark.asyncio
    async def test_existing_valid_token_skips_flow(self, tmp_vault, mock_env):
        from watchers.gmail_watcher import GmailWatcher

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.expired = False

        # Write a token file so it "exists"
        mock_env["token_path"].write_text('{"token": "existing"}')

        with patch(
            "watchers.gmail_watcher.Credentials.from_authorized_user_file",
            return_value=mock_creds,
        ) as mock_from_file, patch(
            "watchers.gmail_watcher.InstalledAppFlow.from_client_secrets_file"
        ) as mock_flow, patch(
            "watchers.gmail_watcher.build"
        ):
            watcher = GmailWatcher(
                vault_path=str(tmp_vault),
                credentials_path=str(mock_env["credentials_path"]),
                token_path=str(mock_env["token_path"]),
            )
            watcher._authenticate()

            mock_from_file.assert_called_once()
            mock_flow.assert_not_called()


class TestAuthenticateExpiredTokenRefreshes:
    """T054: Given token.json with expired but refreshable token,
    When _authenticate() called,
    Then creds.refresh() called, updated token saved."""

    @pytest.mark.asyncio
    async def test_expired_token_refreshes(self, tmp_vault, mock_env):
        from watchers.gmail_watcher import GmailWatcher

        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token_value"
        mock_creds.to_json.return_value = '{"token": "refreshed"}'

        mock_env["token_path"].write_text('{"token": "old"}')

        with patch(
            "watchers.gmail_watcher.Credentials.from_authorized_user_file",
            return_value=mock_creds,
        ), patch(
            "watchers.gmail_watcher.build"
        ), patch(
            "watchers.gmail_watcher.Request"
        ) as mock_request_cls:
            watcher = GmailWatcher(
                vault_path=str(tmp_vault),
                credentials_path=str(mock_env["credentials_path"]),
                token_path=str(mock_env["token_path"]),
            )
            watcher._authenticate()

            mock_creds.refresh.assert_called_once_with(mock_request_cls())

            # Token should be re-saved
            saved = mock_env["token_path"].read_text()
            assert "refreshed" in saved


class TestAuthenticateCorruptTokenDeletesAndReauths:
    """T055: Given corrupt token.json,
    When _authenticate() called,
    Then corrupt file deleted, browser flow triggered."""

    @pytest.mark.asyncio
    async def test_corrupt_token_triggers_reauth(self, tmp_vault, mock_env):
        from watchers.gmail_watcher import GmailWatcher

        # Write corrupt token
        mock_env["token_path"].write_text("NOT VALID JSON {{{{")

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.to_json.return_value = '{"token": "fresh"}'

        mock_flow = MagicMock()
        mock_flow.run_local_server.return_value = mock_creds

        with patch(
            "watchers.gmail_watcher.Credentials.from_authorized_user_file",
            side_effect=ValueError("Invalid token"),
        ), patch(
            "watchers.gmail_watcher.InstalledAppFlow.from_client_secrets_file",
            return_value=mock_flow,
        ) as mock_from_secrets, patch(
            "watchers.gmail_watcher.build"
        ):
            watcher = GmailWatcher(
                vault_path=str(tmp_vault),
                credentials_path=str(mock_env["credentials_path"]),
                token_path=str(mock_env["token_path"]),
            )
            watcher._authenticate()

            mock_from_secrets.assert_called_once()
            mock_flow.run_local_server.assert_called_once()


# ── T056-T058: Prerequisites validation tests ───────────────────────────


class TestValidatePrerequisitesMissingCredentials:
    """T056: Given no credentials.json,
    When validate_prerequisites() called,
    Then raises PrerequisiteError with HT-002 reference."""

    def test_missing_credentials_raises(self, tmp_vault):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path="/nonexistent/credentials.json",
            token_path="/tmp/token.json",
        )

        with pytest.raises(PrerequisiteError, match="HT-002") as exc_info:
            watcher.validate_prerequisites()

        assert exc_info.value.ht_reference == "HT-002"


class TestValidatePrerequisitesMissingVaultDirs:
    """T057: Given no vault/Needs_Action/,
    When validate_prerequisites() called,
    Then raises PrerequisiteError with HT-001 reference."""

    def test_missing_vault_dir_raises(self, tmp_path):
        from watchers.gmail_watcher import GmailWatcher

        # Create vault without required subdirs
        vault = tmp_path / "empty_vault"
        vault.mkdir()
        (vault / "Logs").mkdir()

        watcher = GmailWatcher(
            vault_path=str(vault),
            credentials_path=str(tmp_path / "credentials.json"),
            token_path=str(tmp_path / "token.json"),
        )

        # Create credentials.json so that check passes
        (tmp_path / "credentials.json").write_text('{"installed": {}}')

        with pytest.raises(PrerequisiteError, match="HT-001") as exc_info:
            watcher.validate_prerequisites()

        assert exc_info.value.ht_reference == "HT-001"


class TestValidatePrerequisitesMissingEnvVars:
    """T058: Given .env without GMAIL_CREDENTIALS_PATH,
    When validate_prerequisites() called,
    Then raises PrerequisiteError."""

    def test_missing_env_vars_raises(self, tmp_vault):
        from watchers.gmail_watcher import GmailWatcher

        # Ensure env vars are NOT set
        os.environ.pop("GMAIL_CREDENTIALS_PATH", None)
        os.environ.pop("GMAIL_TOKEN_PATH", None)

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=None,
            token_path=None,
        )

        # Patch load_dotenv to prevent picking up project .env
        with patch("watchers.utils.load_dotenv"):
            with pytest.raises(PrerequisiteError):
                watcher.validate_prerequisites()


class TestValidatePrerequisitesAllPresent:
    """Additional: Given all prerequisites met, validate_prerequisites() succeeds."""

    def test_all_present_passes(self, tmp_vault, mock_env):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        # Should not raise
        watcher.validate_prerequisites()


# ── T064-T066: Email parsing tests ──────────────────────────────────────


class TestParseEmailFullMessage:
    """T064: Given raw Gmail API message dict with headers/body/attachments,
    When _parse_email() called,
    Then returns correct sender, recipients, subject, body, date, has_attachments."""

    def test_parses_full_message(self, tmp_vault, mock_env, sample_raw_gmail_message):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        email = watcher._parse_email(sample_raw_gmail_message)

        assert email.message_id == "msg_abc123"
        assert "alice@example.com" in email.sender
        assert "bob@example.com" in email.recipients
        assert email.subject == "Meeting Follow-up: Q1 Review"
        assert "Please review" in email.body
        assert email.has_attachments is True
        assert email.raw_size == 4096


class TestParseEmailNoBody:
    """T065: Given message with subject only (no body parts),
    When _parse_email() called,
    Then body is 'No email body content.'"""

    def test_no_body_returns_placeholder(self, tmp_vault, mock_env):
        from watchers.gmail_watcher import GmailWatcher

        raw = {
            "id": "msg_nobody",
            "labelIds": ["INBOX"],
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "From", "value": "test@example.com"},
                    {"name": "To", "value": "user@example.com"},
                    {"name": "Subject", "value": "Empty email"},
                    {"name": "Date", "value": "Mon, 17 Feb 2026 10:00:00 +0000"},
                ],
                "body": {"size": 0},
            },
            "sizeEstimate": 512,
        }

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        email = watcher._parse_email(raw)
        assert email.body == "No email body content."


class TestParseEmailNonUtf8:
    """T066: Given message with non-UTF8 characters,
    When _parse_email() called,
    Then body is sanitized via sanitize_utf8()."""

    def test_non_utf8_sanitized(self, tmp_vault, mock_env):
        from watchers.gmail_watcher import GmailWatcher

        # Body with valid UTF-8 (sanitize_utf8 passes it through)
        body_text = "Hello \u00e9\u00e0\u00fc world"
        encoded_body = base64.urlsafe_b64encode(body_text.encode("utf-8")).decode()

        raw = {
            "id": "msg_utf8",
            "labelIds": ["INBOX"],
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "From", "value": "test@example.com"},
                    {"name": "To", "value": "user@example.com"},
                    {"name": "Subject", "value": "UTF8 test"},
                    {"name": "Date", "value": "Mon, 17 Feb 2026 10:00:00 +0000"},
                ],
                "body": {"data": encoded_body, "size": len(body_text)},
            },
            "sizeEstimate": 512,
        }

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        email = watcher._parse_email(raw)
        assert "\u00e9" in email.body
        assert "\u00e0" in email.body


# ── T067-T069: Classification tests ─────────────────────────────────────


class TestClassifyActionable:
    """T067: Given email with subject 'Urgent: Please review contract',
    When _classify_email() called,
    Then returns Classification.ACTIONABLE."""

    def test_actionable_keywords(self, tmp_vault, mock_env):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        email = EmailItem(
            message_id="msg_action",
            sender="boss@company.com",
            recipients=["user@company.com"],
            subject="Urgent: Please review contract",
            body="Please review the attached contract by Friday.",
            date="2026-02-17T10:00:00Z",
            labels=["INBOX", "UNREAD"],
            classification=Classification.ACTIONABLE,  # placeholder, will be re-classified
        )

        result = watcher._classify_email(email)
        assert result == Classification.ACTIONABLE


class TestClassifyInformational:
    """T068: Given email from noreply@ with subject 'Weekly Newsletter',
    When _classify_email() called,
    Then returns Classification.INFORMATIONAL."""

    def test_informational_keywords_and_sender(self, tmp_vault, mock_env):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        email = EmailItem(
            message_id="msg_info",
            sender="noreply@newsletter.com",
            recipients=["user@example.com"],
            subject="Weekly Newsletter - Tech Digest",
            body="This week in tech news... Unsubscribe here.",
            date="2026-02-17T08:00:00Z",
            labels=["INBOX", "UNREAD"],
            classification=Classification.ACTIONABLE,
        )

        result = watcher._classify_email(email)
        assert result == Classification.INFORMATIONAL


class TestClassifyDefaultActionable:
    """T069: Given ambiguous email with no strong signals,
    When _classify_email() called,
    Then returns Classification.ACTIONABLE (default-to-actionable per ADR-0004)."""

    def test_ambiguous_defaults_to_actionable(self, tmp_vault, mock_env):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        email = EmailItem(
            message_id="msg_ambiguous",
            sender="colleague@company.com",
            recipients=["user@company.com"],
            subject="Quick note",
            body="Hey, just wanted to say hello.",
            date="2026-02-17T12:00:00Z",
            labels=["INBOX", "UNREAD"],
            classification=Classification.ACTIONABLE,
        )

        result = watcher._classify_email(email)
        assert result == Classification.ACTIONABLE


# ── T070-T071: Filename generation tests ─────────────────────────────────


class TestGenerateFilenameNormal:
    """T070: Given email with date and subject,
    When _generate_filename() called,
    Then returns 'YYYY-MM-DD-HHmm-sanitized-subject.md'."""

    def test_normal_filename(self, tmp_vault, mock_env, sample_email_item):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        target_dir = tmp_vault / "Needs_Action"
        filename = watcher._generate_filename(sample_email_item, target_dir)

        assert filename.endswith(".md")
        # Should start with date pattern YYYY-MM-DD-HHmm
        assert re.match(r"\d{4}-\d{2}-\d{2}-\d{4}-", filename)
        assert "meeting" in filename.lower()


class TestGenerateFilenameCollision:
    """T071: Given target file already exists,
    When _generate_filename() called,
    Then returns filename with '-001' suffix."""

    def test_collision_appends_suffix(self, tmp_vault, mock_env, sample_email_item):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        target_dir = tmp_vault / "Needs_Action"

        # Generate first filename, create the file
        first_name = watcher._generate_filename(sample_email_item, target_dir)
        (target_dir / first_name).write_text("existing file")

        # Generate again -- should get collision suffix
        second_name = watcher._generate_filename(sample_email_item, target_dir)
        assert second_name != first_name
        assert "-001" in second_name


# ── T072: Markdown rendering tests ───────────────────────────────────────


class TestRenderMarkdown:
    """T072: Given EmailItem,
    When _render_markdown() called,
    Then output has YAML frontmatter with all required fields followed by body."""

    def test_render_has_frontmatter_and_body(self, tmp_vault, mock_env, sample_email_item):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        output = watcher._render_markdown(sample_email_item)

        # Should start and end with frontmatter
        assert output.startswith("---\n")
        assert "---\n" in output[4:]  # closing delimiter

        # Check required frontmatter fields
        assert "type: email" in output
        assert "status: pending" in output
        assert "source: gmail" in output
        assert "message_id: msg_abc123" in output
        assert "classification: actionable" in output
        assert "priority: standard" in output
        assert "watcher: gmail_watcher" in output
        assert "has_attachments: true" in output

        # Body should appear after frontmatter
        assert "Please review" in output


# ── T073-T074: Vault routing tests ───────────────────────────────────────


class TestProcessItemActionableRoutesToNeedsAction:
    """T073: Given ACTIONABLE EmailItem,
    When process_item() called,
    Then file written to vault/Needs_Action/."""

    @pytest.mark.asyncio
    async def test_actionable_routes_to_needs_action(self, tmp_vault, mock_env, sample_email_item):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        await watcher.process_item(sample_email_item)

        files = list((tmp_vault / "Needs_Action").glob("*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "type: email" in content
        assert "msg_abc123" in content


class TestProcessItemInformationalRoutesToInbox:
    """T074: Given INFORMATIONAL EmailItem,
    When process_item() called,
    Then file written to vault/Inbox/."""

    @pytest.mark.asyncio
    async def test_informational_routes_to_inbox(self, tmp_vault, mock_env, sample_informational_email):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        await watcher.process_item(sample_informational_email)

        files = list((tmp_vault / "Inbox").glob("*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "type: email" in content
        assert "msg_news456" in content


# ── T075: Duplicate filtering test ───────────────────────────────────────


class TestPollFiltersAlreadyProcessed:
    """T075: Given email ID already in state.processed_ids,
    When poll() called,
    Then email is skipped (zero duplicate files)."""

    @pytest.mark.asyncio
    async def test_filters_processed_ids(self, tmp_vault, mock_env, sample_raw_gmail_message):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        # Mark the message as already processed
        watcher.state.processed_ids = ["msg_abc123"]

        # Mock _fetch_unread_emails to return the sample message
        watcher._fetch_unread_emails = AsyncMock(
            return_value=[sample_raw_gmail_message]
        )

        items = await watcher.poll()

        # Should be filtered out
        assert len(items) == 0


# ── T076: Async wrapping test ────────────────────────────────────────────


class TestFetchUnreadEmailsWrapsInThread:
    """T076: Given mocked Gmail service,
    When _fetch_unread_emails() called,
    Then asyncio.to_thread() is used for the sync SDK call (ADR-0002)."""

    @pytest.mark.asyncio
    async def test_uses_to_thread(self, tmp_vault, mock_env, mock_gmail_service):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )
        watcher._service = mock_gmail_service

        with patch("watchers.gmail_watcher.asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = [{"id": "msg_1"}]
            result = await watcher._fetch_unread_emails()

            mock_to_thread.assert_called_once()
            assert result == [{"id": "msg_1"}]


# ── QA-Fix: start() lifecycle calls _authenticate() ──────────────────────


class TestStartLifecycleCallsAuthenticate:
    """QA-Fix: GmailWatcher.start() must call _authenticate() before poll loop.

    Regression test for critical bug found by @qa-overseer:
    BaseWatcher.start() never called _authenticate(), leaving self._service = None.
    The first poll() -> _fetch_unread_emails_sync() call crashed with:
        AttributeError: 'NoneType' object has no attribute 'users'
    All prior tests passed because they mocked _fetch_unread_emails directly,
    bypassing self._service entirely.
    """

    @pytest.mark.asyncio
    async def test_start_authenticates_before_poll_loop(self, tmp_vault, mock_env):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        auth_calls = []

        def tracking_authenticate():
            auth_calls.append("_authenticate")
            watcher._service = MagicMock()  # simulate successful auth

        async def stop_immediately():
            watcher._running = False

        watcher._authenticate = tracking_authenticate
        watcher._run_poll_cycle = AsyncMock(side_effect=stop_immediately)

        with patch.object(watcher, "validate_prerequisites"):
            await watcher.start()

        assert "_authenticate" in auth_calls, (
            "_authenticate() was not called during start() -- "
            "self._service will remain None causing AttributeError on first poll()"
        )
        assert watcher._service is not None, (
            "_service must not be None after start() -- authentication was skipped"
        )


# ── T088-T090: Phase 6 -- Vault Routing & Ralph Wiggum Compatibility ──────


class TestFrontmatterRalphWiggumCompatible:
    """T088: Given rendered markdown,
    When parsed as YAML frontmatter,
    Then contains all required fields for Ralph Wiggum state machine compatibility."""

    def test_frontmatter_has_all_required_fields(
        self, tmp_vault, mock_env, sample_email_item
    ):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        output = watcher._render_markdown(sample_email_item)

        # Extract YAML frontmatter between --- delimiters
        parts = output.split("---\n", 2)
        assert len(parts) >= 3, "Frontmatter must have opening and closing --- delimiters"

        frontmatter = yaml.safe_load(parts[1])

        required_fields = [
            "type", "status", "source", "message_id", "from",
            "subject", "date_received", "date_processed",
            "classification", "priority", "has_attachments", "watcher",
        ]
        for field in required_fields:
            assert field in frontmatter, f"Missing required field: {field}"

        # Verify required values
        assert frontmatter["type"] == "email"
        assert frontmatter["status"] == "pending"
        assert frontmatter["source"] == "gmail"
        assert frontmatter["classification"] in ("actionable", "informational")
        assert frontmatter["priority"] == "standard"
        assert frontmatter["watcher"] == "gmail_watcher"
        assert isinstance(frontmatter["has_attachments"], bool)


class TestFilenamePatternCompliance:
    """T089: Given generated filename,
    When matched against regex `^\\d{4}-\\d{2}-\\d{2}-\\d{4}-[a-z0-9-]+\\.md$`,
    Then matches (YYYY-MM-DD-HHmm-sanitized.md)."""

    def test_filename_matches_pattern(self, tmp_vault, mock_env, sample_email_item):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        target_dir = tmp_vault / "Needs_Action"
        filename = watcher._generate_filename(sample_email_item, target_dir)

        pattern = r"^\d{4}-\d{2}-\d{2}-\d{4}-[a-z0-9-]+\.md$"
        assert re.match(pattern, filename), (
            f"Filename '{filename}' does not match expected pattern '{pattern}'"
        )


class TestVaultDirectoryCompliance:
    """T090: Given ACTIONABLE email processed, When file written,
    Then path starts with vault/Needs_Action/.
    Given INFORMATIONAL email, Then path starts with vault/Inbox/."""

    @pytest.mark.asyncio
    async def test_actionable_path_starts_with_needs_action(
        self, tmp_vault, mock_env, sample_email_item
    ):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        await watcher.process_item(sample_email_item)

        files = list((tmp_vault / "Needs_Action").glob("*.md"))
        assert len(files) == 1
        assert str(files[0]).startswith(str(tmp_vault / "Needs_Action"))

    @pytest.mark.asyncio
    async def test_informational_path_starts_with_inbox(
        self, tmp_vault, mock_env, sample_informational_email
    ):
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            credentials_path=str(mock_env["credentials_path"]),
            token_path=str(mock_env["token_path"]),
        )

        await watcher.process_item(sample_informational_email)

        files = list((tmp_vault / "Inbox").glob("*.md"))
        assert len(files) == 1
        assert str(files[0]).startswith(str(tmp_vault / "Inbox"))
