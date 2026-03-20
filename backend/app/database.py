"""Supabase database integration for trend tracking."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app import config

logger = logging.getLogger(__name__)

_client = None


def get_client():
    global _client
    if _client is None and config.DB_ENABLED:
        from supabase import create_client
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


def save_analysis_run(metadata, keywords, videos):
    """Save analysis results to Supabase."""
    client = get_client()
    if not client:
        logger.info("DB not configured, skipping save")
        return None

    run_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    try:
        # Save run metadata
        client.table("analysis_runs").insert({
            "id": run_id,
            "run_date": now,
            "region": metadata.region,
            "period_days": metadata.period_days,
            "video_count": metadata.video_count,
            "status": "completed",
        }).execute()

        # Save keywords
        if keywords:
            keyword_rows = [
                {
                    "id": str(uuid4()),
                    "run_id": run_id,
                    "keyword": kw.keyword,
                    "count": kw.count,
                    "category": kw.category,
                    "rank": kw.rank,
                }
                for kw in keywords
            ]
            client.table("keywords").insert(keyword_rows).execute()

        # Save top videos (limit to 20)
        if videos:
            video_rows = [
                {
                    "id": str(uuid4()),
                    "run_id": run_id,
                    "video_id": v.video_id,
                    "title": v.title,
                    "channel": v.channel,
                    "views": v.views,
                    "likes": v.likes,
                    "published_at": v.published_at,
                    "language": v.language,
                }
                for v in videos[:20]
            ]
            client.table("videos").insert(video_rows).execute()

        logger.info(f"Saved analysis run {run_id} to database")
        return run_id
    except Exception as e:
        logger.error(f"Failed to save to database: {e}")
        return None


def get_trend_comparison(region: str = "all", weeks: int = 2):
    """Compare keyword rankings between recent analysis runs."""
    client = get_client()
    if not client:
        return None

    try:
        # Get the last N completed runs
        runs = (
            client.table("analysis_runs")
            .select("id, run_date")
            .eq("status", "completed")
            .eq("region", region)
            .order("run_date", desc=True)
            .limit(weeks)
            .execute()
        )

        if not runs.data or len(runs.data) < 2:
            return None

        current_run_id = runs.data[0]["id"]
        previous_run_id = runs.data[1]["id"]

        # Get keywords for both runs
        current_kw = (
            client.table("keywords")
            .select("keyword, count, category, rank")
            .eq("run_id", current_run_id)
            .order("rank")
            .execute()
        )

        previous_kw = (
            client.table("keywords")
            .select("keyword, count, category, rank")
            .eq("run_id", previous_run_id)
            .order("rank")
            .execute()
        )

        # Build comparison
        prev_map = {kw["keyword"]: kw for kw in (previous_kw.data or [])}
        trends = []
        for kw in (current_kw.data or []):
            prev = prev_map.get(kw["keyword"])
            rank_change = (prev["rank"] - kw["rank"]) if prev else None
            is_new = prev is None
            trends.append({
                "keyword": kw["keyword"],
                "rank": kw["rank"],
                "count": kw["count"],
                "category": kw["category"],
                "rank_change": rank_change,
                "is_new": is_new,
                "previous_rank": prev["rank"] if prev else None,
            })

        return {
            "current_date": runs.data[0]["run_date"],
            "previous_date": runs.data[1]["run_date"],
            "trends": trends,
        }
    except Exception as e:
        logger.error(f"Failed to fetch trends: {e}")
        return None


def get_trend_history(keyword: str, limit: int = 12):
    """Get historical rank/count data for a specific keyword."""
    client = get_client()
    if not client:
        return None

    try:
        result = (
            client.table("keywords")
            .select("count, rank, run_id, analysis_runs!inner(run_date)")
            .eq("keyword", keyword)
            .order("analysis_runs.run_date", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data
    except Exception as e:
        logger.error(f"Failed to fetch keyword history: {e}")
        return None
