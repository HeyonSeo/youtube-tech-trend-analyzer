"""Tests for app.database — Supabase integration with mocked client."""

from __future__ import annotations

from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from app.models import AnalysisMetadata, KeywordItem, VideoItem


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


@pytest.fixture()
def mock_supabase_client():
    """Return a MagicMock that mimics the Supabase client."""
    client = MagicMock()

    # Chain: client.table("x").insert({}).execute()
    # Chain: client.table("x").select("...").eq("...").order("...").limit(N).execute()
    table_mock = MagicMock()
    client.table.return_value = table_mock

    return client


@pytest.fixture()
def sample_metadata():
    return AnalysisMetadata(
        video_count=2,
        period_days=7,
        region="all",
        run_date="2026-03-20 00:00:00 UTC",
        queries_used=["tech review"],
        errors=[],
    )


@pytest.fixture()
def sample_keywords():
    return [
        KeywordItem(rank=1, keyword="iphone", count=10, category="스마트폰/모바일"),
        KeywordItem(rank=2, keyword="galaxy", count=8, category="스마트폰/모바일"),
    ]


@pytest.fixture()
def sample_videos():
    return [
        VideoItem(
            video_id="vid001",
            title="Test Video",
            channel="TestChannel",
            views=100000,
            likes=5000,
            published_at="2026-03-15T10:00:00Z",
            language="en",
            thumbnail_url="https://example.com/thumb.jpg",
        )
    ]


# -----------------------------------------------------------------------
# save_analysis_run
# -----------------------------------------------------------------------


class TestSaveAnalysisRun:
    @patch("app.database.get_client")
    def test_save_returns_run_id(
        self, mock_get_client, mock_supabase_client, sample_metadata, sample_keywords, sample_videos
    ):
        mock_get_client.return_value = mock_supabase_client
        from app.database import save_analysis_run

        run_id = save_analysis_run(sample_metadata, sample_keywords, sample_videos)
        assert run_id is not None
        assert isinstance(run_id, str)
        # Should have called table().insert().execute() for runs, keywords, videos
        assert mock_supabase_client.table.call_count == 3

    @patch("app.database.get_client")
    def test_save_with_no_client_returns_none(
        self, mock_get_client, sample_metadata, sample_keywords, sample_videos
    ):
        mock_get_client.return_value = None
        from app.database import save_analysis_run

        result = save_analysis_run(sample_metadata, sample_keywords, sample_videos)
        assert result is None

    @patch("app.database.get_client")
    def test_save_with_empty_keywords(
        self, mock_get_client, mock_supabase_client, sample_metadata, sample_videos
    ):
        mock_get_client.return_value = mock_supabase_client
        from app.database import save_analysis_run

        run_id = save_analysis_run(sample_metadata, [], sample_videos)
        assert run_id is not None
        # Should only insert runs + videos (not keywords)
        assert mock_supabase_client.table.call_count == 2

    @patch("app.database.get_client")
    def test_save_with_empty_videos(
        self, mock_get_client, mock_supabase_client, sample_metadata, sample_keywords
    ):
        mock_get_client.return_value = mock_supabase_client
        from app.database import save_analysis_run

        run_id = save_analysis_run(sample_metadata, sample_keywords, [])
        assert run_id is not None
        # Should only insert runs + keywords (not videos)
        assert mock_supabase_client.table.call_count == 2

    @patch("app.database.get_client")
    def test_save_handles_db_error(
        self, mock_get_client, mock_supabase_client, sample_metadata, sample_keywords, sample_videos
    ):
        mock_get_client.return_value = mock_supabase_client
        mock_supabase_client.table.return_value.insert.return_value.execute.side_effect = Exception(
            "DB connection error"
        )
        from app.database import save_analysis_run

        result = save_analysis_run(sample_metadata, sample_keywords, sample_videos)
        assert result is None


# -----------------------------------------------------------------------
# get_trend_comparison
# -----------------------------------------------------------------------


class TestGetTrendComparison:
    @patch("app.database.get_client")
    def test_returns_none_when_no_client(self, mock_get_client):
        mock_get_client.return_value = None
        from app.database import get_trend_comparison

        result = get_trend_comparison("all")
        assert result is None

    @patch("app.database.get_client")
    def test_returns_none_with_insufficient_runs(self, mock_get_client, mock_supabase_client):
        mock_get_client.return_value = mock_supabase_client

        # Only 1 run — need at least 2
        runs_result = MagicMock()
        runs_result.data = [{"id": "run1", "run_date": "2026-03-20"}]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = (
            runs_result
        )

        from app.database import get_trend_comparison

        result = get_trend_comparison("all")
        assert result is None

    @patch("app.database.get_client")
    def test_returns_trends_with_two_runs(self, mock_get_client, mock_supabase_client):
        mock_get_client.return_value = mock_supabase_client

        # Mock the runs query
        runs_result = MagicMock()
        runs_result.data = [
            {"id": "run2", "run_date": "2026-03-20"},
            {"id": "run1", "run_date": "2026-03-13"},
        ]

        # Mock the keywords queries
        current_kw_result = MagicMock()
        current_kw_result.data = [
            {"keyword": "iphone", "count": 15, "category": "스마트폰/모바일", "rank": 1},
            {"keyword": "galaxy", "count": 10, "category": "스마트폰/모바일", "rank": 2},
        ]

        previous_kw_result = MagicMock()
        previous_kw_result.data = [
            {"keyword": "iphone", "count": 12, "category": "스마트폰/모바일", "rank": 2},
            {"keyword": "laptop", "count": 8, "category": "노트북/PC", "rank": 1},
        ]

        # Set up chained calls — the table mock needs to handle multiple calls
        table_mock = MagicMock()
        mock_supabase_client.table.return_value = table_mock

        # First call: analysis_runs query
        runs_chain = MagicMock()
        runs_chain.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = runs_result

        # Keywords queries
        kw_chain_current = MagicMock()
        kw_chain_current.select.return_value.eq.return_value.order.return_value.execute.return_value = current_kw_result

        kw_chain_previous = MagicMock()
        kw_chain_previous.select.return_value.eq.return_value.order.return_value.execute.return_value = previous_kw_result

        mock_supabase_client.table.side_effect = [
            runs_chain,       # analysis_runs
            kw_chain_current, # keywords (current)
            kw_chain_previous, # keywords (previous)
        ]

        from app.database import get_trend_comparison

        result = get_trend_comparison("all", 2)
        assert result is not None
        assert "trends" in result
        assert "current_date" in result
        assert "previous_date" in result
        assert len(result["trends"]) == 2

        # iphone went from rank 2 to rank 1 => rank_change = 1
        iphone_trend = next(t for t in result["trends"] if t["keyword"] == "iphone")
        assert iphone_trend["rank_change"] == 1
        assert iphone_trend["is_new"] is False

        # galaxy is new (not in previous)
        galaxy_trend = next(t for t in result["trends"] if t["keyword"] == "galaxy")
        assert galaxy_trend["is_new"] is True
        assert galaxy_trend["rank_change"] is None

    @patch("app.database.get_client")
    def test_handles_db_error(self, mock_get_client, mock_supabase_client):
        mock_get_client.return_value = mock_supabase_client
        mock_supabase_client.table.side_effect = Exception("DB error")

        from app.database import get_trend_comparison

        result = get_trend_comparison("all")
        assert result is None


# -----------------------------------------------------------------------
# get_trend_history
# -----------------------------------------------------------------------


class TestGetTrendHistory:
    @patch("app.database.get_client")
    def test_returns_none_when_no_client(self, mock_get_client):
        mock_get_client.return_value = None
        from app.database import get_trend_history

        result = get_trend_history("iphone")
        assert result is None

    @patch("app.database.get_client")
    def test_returns_history_data(self, mock_get_client, mock_supabase_client):
        mock_get_client.return_value = mock_supabase_client

        history_result = MagicMock()
        history_result.data = [
            {"count": 15, "rank": 1, "run_id": "run2", "analysis_runs": {"run_date": "2026-03-20"}},
            {"count": 12, "rank": 2, "run_id": "run1", "analysis_runs": {"run_date": "2026-03-13"}},
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = (
            history_result
        )

        from app.database import get_trend_history

        result = get_trend_history("iphone", limit=12)
        assert result is not None
        assert len(result) == 2

    @patch("app.database.get_client")
    def test_handles_db_error(self, mock_get_client, mock_supabase_client):
        mock_get_client.return_value = mock_supabase_client
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.side_effect = Exception(
            "DB error"
        )

        from app.database import get_trend_history

        result = get_trend_history("iphone")
        assert result is None


# -----------------------------------------------------------------------
# get_client
# -----------------------------------------------------------------------


class TestGetClient:
    @patch("app.database.config")
    @patch("app.database._client", None)
    def test_returns_none_when_db_disabled(self, mock_config):
        mock_config.DB_ENABLED = False
        from app.database import get_client

        result = get_client()
        assert result is None
