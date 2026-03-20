from __future__ import annotations

import logging
import re
import time
from collections import Counter
from datetime import datetime, timedelta, timezone

import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app import config
from app.config import (
    INTEREST_CATEGORIES,
    SEARCH_QUERIES_EN,
    SEARCH_QUERIES_KR,
    STOPWORDS,
    YOUTUBE_API_KEY,
)
from app.models import (
    AnalysisMetadata,
    AnalysisResult,
    InterestItem,
    KeywordItem,
    VideoItem,
)

logger = logging.getLogger(__name__)

# Module-level cache: key -> (timestamp, result)
_cache: dict[str, tuple[datetime, AnalysisResult]] = {}
_last_analysis_time: datetime | None = None


def get_cache_info() -> dict:
    """Return cache status information."""
    return {
        "entries": len(_cache),
        "keys": list(_cache.keys()),
        "last_analysis_time": (
            _last_analysis_time.isoformat() if _last_analysis_time else None
        ),
    }


def clear_cache() -> int:
    """Clear the analysis cache. Returns the number of entries removed."""
    global _last_analysis_time
    count = len(_cache)
    _cache.clear()
    _last_analysis_time = None
    logger.info("Cache cleared (%d entries removed)", count)
    return count


class TechTrendAnalyzer:
    """YouTube tech-review trend analyzer backed by the YouTube Data API v3."""

    def __init__(self) -> None:
        if not YOUTUBE_API_KEY:
            raise RuntimeError(
                "YOUTUBE_API_KEY is not set. "
                "Add it to your .env file or export it as an environment variable."
            )
        http = httplib2.Http(timeout=config.YOUTUBE_API_TIMEOUT)
        self._youtube = build(
            "youtube", "v3", developerKey=YOUTUBE_API_KEY, http=http
        )

    # ------------------------------------------------------------------
    # Retry helper
    # ------------------------------------------------------------------

    @staticmethod
    def _retry_api_call(func, max_retries: int = 3):
        """Execute *func* with exponential backoff on transient errors."""
        for attempt in range(max_retries):
            try:
                return func()
            except HttpError as e:
                if e.resp.status in (429, 500, 503) and attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        "API error %s, retrying in %ds (attempt %d/%d)...",
                        e.resp.status,
                        wait,
                        attempt + 1,
                        max_retries,
                    )
                    time.sleep(wait)
                else:
                    raise

    # ------------------------------------------------------------------
    # YouTube helpers
    # ------------------------------------------------------------------

    def search_videos(
        self,
        query: str,
        published_after: str,
        max_results: int = 25,
    ) -> dict:
        """Search YouTube for videos matching *query* published after *published_after* (ISO-8601)."""
        request = self._youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            order="viewCount",
            publishedAfter=published_after,
            maxResults=max_results,
        )
        return self._retry_api_call(request.execute)

    def get_video_details(self, video_ids: list[str]) -> dict:
        """Fetch statistics and snippet for the given *video_ids*."""
        request = self._youtube.videos().list(
            part="statistics,snippet",
            id=",".join(video_ids),
        )
        return self._retry_api_call(request.execute)

    # ------------------------------------------------------------------
    # NLP helpers
    # ------------------------------------------------------------------

    @staticmethod
    def extract_keywords(text: str) -> list[str]:
        """Return keywords from *text*, filtering stopwords and short tokens."""
        text = re.sub(r"[^\w\s가-힣]", " ", text.lower())
        words = text.split()
        return [w for w in words if len(w) >= 2 and w not in STOPWORDS]

    @staticmethod
    def categorize_interests(keyword_counter: Counter) -> dict[str, int]:
        """Map aggregated keywords to interest-category scores."""
        scores: dict[str, int] = {}
        for category, terms in INTEREST_CATEGORIES.items():
            score = sum(keyword_counter.get(term, 0) for term in terms)
            if score > 0:
                scores[category] = score
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))

    # ------------------------------------------------------------------
    # Detect language heuristic
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_language(text: str) -> str:
        """Return ``'ko'`` if Korean characters dominate, else ``'en'``."""
        korean_chars = len(re.findall(r"[가-힣]", text))
        return "ko" if korean_chars > len(text) * 0.15 else "en"

    # ------------------------------------------------------------------
    # Main analysis
    # ------------------------------------------------------------------

    def analyze(
        self,
        period_days: int = 7,
        region: str = "all",
        top_n: int = 10,
    ) -> AnalysisResult:
        """Run the full analysis pipeline and return a structured result.

        Parameters
        ----------
        period_days:
            Number of days to look back from now.
        region:
            ``"kr"`` for Korean queries only, ``"global"`` for English only,
            ``"all"`` for both.
        top_n:
            Number of top keywords to include in the result.
        """
        global _last_analysis_time

        # -- Check cache --
        cache_key = f"{period_days}:{region}:{top_n}"
        if cache_key in _cache:
            cached_time, cached_result = _cache[cache_key]
            if (datetime.now(timezone.utc) - cached_time).seconds < config.CACHE_TTL_SECONDS:
                logger.info("Cache hit for %s", cache_key)
                return cached_result

        now = datetime.now(timezone.utc)
        published_after = (now - timedelta(days=period_days)).isoformat()

        # Select queries based on region
        if region == "kr":
            queries = SEARCH_QUERIES_KR
        elif region == "global":
            queries = SEARCH_QUERIES_EN
        else:
            queries = SEARCH_QUERIES_KR + SEARCH_QUERIES_EN

        all_videos: dict[str, dict] = {}
        keyword_counter: Counter = Counter()
        errors: list[str] = []
        api_calls_used: int = 0

        for query in queries:
            try:
                results = self.search_videos(query, published_after)
                api_calls_used += 1
            except HttpError as e:
                msg = f"Search failed for query '{query}': HTTP {e.resp.status} - {e}"
                logger.error(msg)
                errors.append(msg)
                continue
            except Exception as e:
                msg = f"Search failed for query '{query}': {type(e).__name__}: {e}"
                logger.error(msg)
                errors.append(msg)
                continue

            video_ids = [
                item["id"]["videoId"]
                for item in results.get("items", [])
                if item["id"].get("videoId")
            ]
            if not video_ids:
                continue

            # Deduplicate: only fetch details for video IDs we haven't seen yet
            new_video_ids = [vid for vid in video_ids if vid not in all_videos]
            if not new_video_ids:
                continue

            try:
                details = self.get_video_details(new_video_ids)
                api_calls_used += 1
            except HttpError as e:
                msg = f"Video details failed for IDs {new_video_ids[:5]}...: HTTP {e.resp.status} - {e}"
                logger.error(msg)
                errors.append(msg)
                continue
            except Exception as e:
                msg = f"Video details failed for IDs {new_video_ids[:5]}...: {type(e).__name__}: {e}"
                logger.error(msg)
                errors.append(msg)
                continue

            for item in details.get("items", []):
                vid: str = item["id"]
                if vid in all_videos:
                    continue

                snippet = item["snippet"]
                stats = item["statistics"]
                title: str = snippet["title"]
                description: str = snippet.get("description", "")
                tags: list[str] = snippet.get("tags", [])
                thumbnails = snippet.get("thumbnails", {})
                thumbnail_url: str = (
                    thumbnails.get("high", {}).get("url")
                    or thumbnails.get("medium", {}).get("url")
                    or thumbnails.get("default", {}).get("url", "")
                )

                all_videos[vid] = {
                    "video_id": vid,
                    "title": title,
                    "channel": snippet["channelTitle"],
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "published_at": snippet.get("publishedAt", ""),
                    "language": self._detect_language(title),
                    "thumbnail_url": thumbnail_url,
                }

                # Extract keywords from title + tags + first 300 chars of description
                text = f"{title} {' '.join(tags)} {description[:300]}"
                for kw in self.extract_keywords(text):
                    keyword_counter[kw] += 1

        # -- Build result models --

        # Videos sorted by views descending
        sorted_videos = sorted(
            all_videos.values(), key=lambda v: v["views"], reverse=True
        )
        video_items = [VideoItem(**v) for v in sorted_videos]

        # Top-N keywords with category tagging
        keyword_items: list[KeywordItem] = []
        for rank, (kw, count) in enumerate(keyword_counter.most_common(top_n), start=1):
            matched_category = "기타"
            for cat, terms in INTEREST_CATEGORIES.items():
                if kw in terms:
                    matched_category = cat
                    break
            keyword_items.append(
                KeywordItem(rank=rank, keyword=kw, count=count, category=matched_category)
            )

        # Interest scores
        interest_scores = self.categorize_interests(keyword_counter)
        max_score = max(interest_scores.values()) if interest_scores else 1
        interest_items: list[InterestItem] = []
        for rank, (cat, score) in enumerate(interest_scores.items(), start=1):
            interest_items.append(
                InterestItem(
                    rank=rank,
                    category=cat,
                    score=score,
                    ratio=round(score / max_score, 4),
                )
            )

        metadata = AnalysisMetadata(
            video_count=len(all_videos),
            period_days=period_days,
            region=region,
            run_date=now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            queries_used=queries,
            errors=errors,
            api_calls_used=api_calls_used,
        )

        result = AnalysisResult(
            metadata=metadata,
            videos=video_items,
            keywords=keyword_items,
            interests=interest_items,
        )

        # Store in cache
        _cache[cache_key] = (datetime.now(timezone.utc), result)
        _last_analysis_time = datetime.now(timezone.utc)
        logger.info(
            "Analysis complete: %d videos, %d errors, cached as '%s'",
            len(all_videos),
            len(errors),
            cache_key,
        )

        return result
