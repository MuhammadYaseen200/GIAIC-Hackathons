"""Tests for watchers/privacy_gate.py — ADR-0010, SC-009, SC-010"""
import pytest
from watchers.privacy_gate import run_privacy_gate, PrivacyGateResult, PrivacyLogEntry


class TestMediaBlock:
    def test_image_blocked(self):
        result = run_privacy_gate("hello", media_type="image")
        assert result.media_blocked is True
        assert result.body == "[MEDIA — content not stored]"
        assert result.redaction_applied is False

    def test_video_blocked(self):
        result = run_privacy_gate("some caption", media_type="video")
        assert result.media_blocked is True

    def test_audio_blocked(self):
        result = run_privacy_gate("", media_type="audio")
        assert result.media_blocked is True

    def test_text_not_blocked(self):
        result = run_privacy_gate("hello world", media_type="text")
        assert result.media_blocked is False


class TestOTPRedaction:
    def test_otp_keyword(self):
        result = run_privacy_gate("otp: 123456", media_type="text")
        assert "[REDACTED-OTP]" in result.body
        assert "123456" not in result.body
        assert result.redaction_applied is True

    def test_standalone_6digit_code(self):
        result = run_privacy_gate("Your code: 847291", media_type="text")
        assert "[REDACTED-OTP]" in result.body
        assert "847291" not in result.body

    def test_one_time_password(self):
        result = run_privacy_gate("one-time password: 993847", media_type="text")
        assert "[REDACTED-OTP]" in result.body


class TestPasswordPINRedaction:
    def test_password_pattern(self):
        result = run_privacy_gate("password: myS3cr3t!", media_type="text")
        assert "[REDACTED-PASSWORD]" in result.body
        assert "myS3cr3t!" not in result.body

    def test_pin_pattern(self):
        result = run_privacy_gate("pin: 4829", media_type="text")
        assert "[REDACTED-PIN]" in result.body
        assert "4829" not in result.body


class TestCardRedaction:
    def test_16digit_card(self):
        result = run_privacy_gate("card: 4111111111111111", media_type="text")
        assert "[REDACTED-CARD]" in result.body
        assert "4111111111111111" not in result.body


class TestSecretRedaction:
    def test_api_key_pattern(self):
        result = run_privacy_gate("api_key: sk-abc123xyz", media_type="text")
        assert "[REDACTED-SECRET]" in result.body


class TestCleanText:
    def test_clean_text_unchanged(self):
        result = run_privacy_gate("Hi, how are you?", media_type="text")
        assert result.body == "Hi, how are you?"
        assert result.redaction_applied is False
        assert result.media_blocked is False
        assert result.alert_message == ""

    def test_alert_contains_no_original_content(self):
        result = run_privacy_gate("password: secret123", media_type="text")
        assert "secret123" not in result.alert_message

    def test_double_redaction(self):
        result = run_privacy_gate("password: abc otp: 123456", media_type="text")
        assert "[REDACTED-PASSWORD]" in result.body
        assert "[REDACTED-OTP]" in result.body

    def test_returns_privacy_gate_result(self):
        result = run_privacy_gate("hello", media_type="text")
        assert isinstance(result, PrivacyGateResult)


class TestDataclasses:
    def test_privacy_log_entry_to_dict(self):
        entry = PrivacyLogEntry(
            timestamp="2026-03-03T00:00:00Z",
            media_blocked=False,
            redaction_applied=True,
            patterns_matched=["[REDACTED-OTP]"],
        )
        d = entry.to_dict()
        assert d["redaction_applied"] is True
        assert d["patterns_matched"] == ["[REDACTED-OTP]"]
