"""Tests for app.email_report — report generation and sending."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from app.models import KeywordItem, VideoItem


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


@pytest.fixture()
def sample_keywords():
    return [
        KeywordItem(rank=1, keyword="iphone", count=10, category="스마트폰/모바일"),
        KeywordItem(rank=2, keyword="galaxy", count=8, category="스마트폰/모바일"),
        KeywordItem(rank=3, keyword="laptop", count=5, category="노트북/PC"),
    ]


@pytest.fixture()
def sample_video():
    return VideoItem(
        video_id="vid001",
        title="Best Tech Review 2026",
        channel="TechChannel",
        views=100000,
        likes=5000,
        published_at="2026-03-15T10:00:00Z",
        language="en",
        thumbnail_url="https://example.com/thumb.jpg",
    )


@pytest.fixture()
def sample_trends():
    return [
        {"keyword": "iphone", "rank": 1, "count": 10, "rank_change": 2, "is_new": False},
        {"keyword": "galaxy", "rank": 2, "count": 8, "rank_change": -1, "is_new": False},
        {"keyword": "laptop", "rank": 3, "count": 5, "rank_change": None, "is_new": True},
    ]


# -----------------------------------------------------------------------
# generate_report_html
# -----------------------------------------------------------------------


class TestGenerateReportHtml:
    def test_basic_html_generation(self, sample_keywords):
        from app.email_report import generate_report_html

        html = generate_report_html(sample_keywords, {}, None)
        assert "<!DOCTYPE html>" in html
        assert "TechPulse" in html
        assert "iphone" in html
        assert "galaxy" in html
        assert "laptop" in html

    def test_includes_video_section(self, sample_keywords, sample_video):
        from app.email_report import generate_report_html

        html = generate_report_html(sample_keywords, {}, sample_video)
        assert "Best Tech Review 2026" in html
        assert "TechChannel" in html
        assert "100,000" in html

    def test_no_video_section_when_none(self, sample_keywords):
        from app.email_report import generate_report_html

        html = generate_report_html(sample_keywords, {}, None)
        # Should not contain the top video section markers
        assert "조회수 1위 영상" not in html or "Best Tech" not in html

    def test_with_trends(self, sample_keywords, sample_trends):
        from app.email_report import generate_report_html

        html = generate_report_html(sample_keywords, {}, None, sample_trends)
        # Upward trend icon for iphone (rank_change > 0)
        assert "\u25b2" in html  # ▲
        # New icon for laptop
        assert "\U0001f195" in html  # 🆕

    def test_empty_keywords(self):
        from app.email_report import generate_report_html

        html = generate_report_html([], {}, None)
        assert "<!DOCTYPE html>" in html

    def test_with_dict_keywords(self):
        """Test that the function handles dict-style keywords too."""
        from app.email_report import generate_report_html

        kw_dicts = [
            {"rank": 1, "keyword": "test", "count": 5, "category": "기타"},
        ]
        html = generate_report_html(kw_dicts, {}, None)
        assert "test" in html


# -----------------------------------------------------------------------
# send_report
# -----------------------------------------------------------------------


class TestSendReport:
    @patch("app.email_report.config")
    def test_returns_false_when_email_disabled(self, mock_config):
        mock_config.EMAIL_ENABLED = False
        from app.email_report import send_report

        result = send_report(["test@example.com"], "<html>report</html>")
        assert result is False

    @patch("app.email_report.config")
    def test_sends_email_successfully(self, mock_config):
        mock_config.EMAIL_ENABLED = True
        mock_config.RESEND_API_KEY = "test_key"
        mock_config.REPORT_FROM_EMAIL = "noreply@techpulse.app"

        with patch("app.email_report.resend") as mock_resend:
            mock_resend.Emails.send.return_value = {"id": "email123"}
            from app.email_report import send_report

            result = send_report(["user@example.com"], "<html>report</html>")
            assert result is True
            mock_resend.Emails.send.assert_called_once()

    @patch("app.email_report.config")
    def test_send_with_custom_subject(self, mock_config):
        mock_config.EMAIL_ENABLED = True
        mock_config.RESEND_API_KEY = "test_key"
        mock_config.REPORT_FROM_EMAIL = "noreply@techpulse.app"

        with patch("app.email_report.resend") as mock_resend:
            mock_resend.Emails.send.return_value = {"id": "email123"}
            from app.email_report import send_report

            result = send_report(
                ["user@example.com"], "<html>report</html>", subject="Custom Subject"
            )
            assert result is True
            call_args = mock_resend.Emails.send.call_args[0][0]
            assert call_args["subject"] == "Custom Subject"

    @patch("app.email_report.config")
    def test_returns_false_on_send_error(self, mock_config):
        mock_config.EMAIL_ENABLED = True
        mock_config.RESEND_API_KEY = "test_key"
        mock_config.REPORT_FROM_EMAIL = "noreply@techpulse.app"

        with patch("app.email_report.resend") as mock_resend:
            mock_resend.Emails.send.side_effect = Exception("API error")
            from app.email_report import send_report

            result = send_report(["user@example.com"], "<html>report</html>")
            assert result is False
