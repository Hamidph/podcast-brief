"""Tests for the email sender."""

import os
from unittest.mock import patch

from podcast_brief.send_email import send_briefing_email


def test_send_email_success():
    with patch.dict(os.environ, {"RESEND_API_KEY": "test_key"}):
        with patch("podcast_brief.send_email.resend") as mock_resend:
            mock_resend.Emails.send.return_value = {"id": "email_123"}

            result = send_briefing_email(
                subject="Test Subject",
                html="<h1>Test</h1>",
                to="test@example.com",
                from_addr="sender@example.com",
            )

    assert result["status"] == "ok"
    assert result["id"] == "email_123"


def test_send_email_failure():
    with patch.dict(os.environ, {"RESEND_API_KEY": "test_key"}):
        with patch("podcast_brief.send_email.resend") as mock_resend:
            mock_resend.Emails.send.side_effect = Exception("API error")

            result = send_briefing_email(
                subject="Test Subject",
                html="<h1>Test</h1>",
                to="test@example.com",
                from_addr="sender@example.com",
            )

    assert result["status"] == "error"
    assert "API error" in result["error"]
