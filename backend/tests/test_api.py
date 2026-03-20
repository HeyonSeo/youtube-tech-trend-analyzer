from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models import (
    AnalysisMetadata,
    AnalysisResult,
    InterestItem,
    KeywordItem,
    VideoItem,
)


@pytest.fixture()
def fake_analysis_result() -> AnalysisResult:
    return AnalysisResult(
        metadata=AnalysisMetadata(
            video_count=1,
            period_days=7,
            region="all",
            run_date="2026-03-20 00:00:00 UTC",
            queries_used=["tech review"],
            errors=[],
        ),
        videos=[
            VideoItem(
                video_id="vid001",
                title="Test Video",
                channel="TestChannel",
                views=1000,
                likes=100,
                published_at="2026-03-19T00:00:00Z",
                language="en",
                thumbnail_url="https://example.com/thumb.jpg",
            )
        ],
        keywords=[
            KeywordItem(rank=1, keyword="test", count=10, category="기타")
        ],
        interests=[
            InterestItem(rank=1, category="스마트폰/모바일", score=10, ratio=1.0)
        ],
    )


# -----------------------------------------------------------------------
# /api/health
# -----------------------------------------------------------------------


@pytest.mark.anyio
async def test_health_returns_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


# -----------------------------------------------------------------------
# /api/analyze (mocked)
# -----------------------------------------------------------------------


@pytest.mark.anyio
async def test_analyze_with_mock(fake_analysis_result: AnalysisResult):
    mock_analyzer = MagicMock()
    mock_analyzer.analyze.return_value = fake_analysis_result

    with patch("app.main._get_analyzer", return_value=mock_analyzer):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/analyze", params={"period_days": 7, "region": "all"}
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["region"] == "all"
    assert len(data["videos"]) == 1


# -----------------------------------------------------------------------
# /api/export/csv
# -----------------------------------------------------------------------


@pytest.mark.anyio
async def test_export_csv_content_type(fake_analysis_result: AnalysisResult):
    mock_analyzer = MagicMock()
    mock_analyzer.analyze.return_value = fake_analysis_result

    with patch("app.main._get_analyzer", return_value=mock_analyzer):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/export/csv")

    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
