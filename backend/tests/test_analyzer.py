from __future__ import annotations

from collections import Counter
from unittest.mock import patch, MagicMock

import pytest

from app.analyzer import TechTrendAnalyzer


# -----------------------------------------------------------------------
# extract_keywords
# -----------------------------------------------------------------------


class TestExtractKeywords:
    def test_basic_extraction(self):
        keywords = TechTrendAnalyzer.extract_keywords("Galaxy S25 Ultra Review")
        assert "galaxy" in keywords
        assert "s25" in keywords
        assert "ultra" in keywords
        assert "review" in keywords

    def test_stopword_filtering(self):
        keywords = TechTrendAnalyzer.extract_keywords(
            "This is a very good smartphone for the price"
        )
        for stopword in ("this", "is", "very", "for", "the"):
            assert stopword not in keywords
        assert "good" in keywords
        assert "smartphone" in keywords
        assert "price" in keywords

    def test_empty_string(self):
        keywords = TechTrendAnalyzer.extract_keywords("")
        assert keywords == []

    def test_special_characters(self):
        keywords = TechTrendAnalyzer.extract_keywords("iPhone!!! @#$% 15-Pro ***Max***")
        assert "iphone" in keywords
        assert "max" in keywords


# -----------------------------------------------------------------------
# categorize_interests
# -----------------------------------------------------------------------


class TestCategorizeInterests:
    def test_smartphone_category(self):
        counter = Counter({"iphone": 10, "galaxy": 5, "smartphone": 3})
        scores = TechTrendAnalyzer.categorize_interests(counter)
        assert "스마트폰/모바일" in scores
        assert scores["스마트폰/모바일"] == 18

    def test_empty_counter(self):
        scores = TechTrendAnalyzer.categorize_interests(Counter())
        assert scores == {}

    def test_sort_order(self):
        counter = Counter({"laptop": 5, "iphone": 20, "camera": 8})
        scores = TechTrendAnalyzer.categorize_interests(counter)
        score_values = list(scores.values())
        assert score_values == sorted(score_values, reverse=True)


# -----------------------------------------------------------------------
# analyze (with mocked YouTube build)
# -----------------------------------------------------------------------


class TestAnalyze:
    @patch("app.analyzer.build")
    @patch("app.analyzer.YOUTUBE_API_KEY", "fake_key_for_test")
    def test_analyze_returns_correct_result(self, mock_build, mock_youtube_service):
        """analyze() should return an AnalysisResult with correct region/period."""
        from app.analyzer import _cache
        _cache.clear()

        mock_build.return_value = mock_youtube_service

        analyzer = TechTrendAnalyzer()
        result = analyzer.analyze(period_days=7, region="global", top_n=5)

        assert result.metadata.period_days == 7
        assert result.metadata.region == "global"
        assert isinstance(result.videos, list)
        assert isinstance(result.keywords, list)
        assert isinstance(result.interests, list)
        assert result.metadata.video_count == 2
