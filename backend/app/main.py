from __future__ import annotations

import csv
import io
import logging
import time as _time
from typing import Annotated

from datetime import date, datetime, timezone

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from googleapiclient.errors import HttpError
from openpyxl import Workbook
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app import config
from app.analyzer import TechTrendAnalyzer, clear_cache, get_cache_info
from app.config import CORS_ORIGINS, INTEREST_CATEGORIES, load_search_queries
from app.database import save_analysis_run, get_trend_comparison, get_trend_history
from app.email_report import generate_report_html, send_report
from app.models import AnalysisResult, InterestItem, KeywordItem, PaginatedVideos, ReportSendRequest, VideoItem

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App & rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="YouTube Tech Trend Analyzer",
    description="Analyze trending tech-review videos on YouTube and extract keywords / viewer interests.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(HttpError)
async def youtube_api_error_handler(request: Request, exc: HttpError):
    logger.error("YouTube API error: %s", exc)
    return JSONResponse(
        status_code=502,
        content={
            "error": "YouTube API Error",
            "detail": str(exc),
            "status_code": 502,
        },
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
            "status_code": 500,
        },
    )


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = _time.time()
    response = await call_next(request)
    duration = _time.time() - start
    logger.info(
        "%s %s -> %s (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_analyzer() -> TechTrendAnalyzer:
    return TechTrendAnalyzer()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/api/health")
@limiter.limit("30/minute")
async def health_check(request: Request) -> dict:
    cache_info = get_cache_info()
    return {
        "status": "ok",
        "cache_entries": cache_info["entries"],
        "last_analysis_time": cache_info["last_analysis_time"],
    }


# ---------------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------------


@app.post("/api/cache/clear")
@limiter.limit("30/minute")
async def clear_analysis_cache(request: Request) -> dict:
    removed = clear_cache()
    return {"status": "ok", "entries_removed": removed}


# ---------------------------------------------------------------------------
# Full analysis
# ---------------------------------------------------------------------------


@app.get("/api/analyze", response_model=AnalysisResult)
@limiter.limit("10/minute")
async def analyze(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=30)] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$")] = "all",
    top_n: Annotated[int, Query(ge=1, le=50)] = 10,
) -> AnalysisResult:
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=period_days, region=region, top_n=top_n)
    # Auto-save to DB (non-blocking, errors are logged but not raised)
    save_analysis_run(result.metadata, result.keywords, result.videos)
    return result


# ---------------------------------------------------------------------------
# Keywords only
# ---------------------------------------------------------------------------


@app.get("/api/keywords", response_model=list[KeywordItem])
@limiter.limit("30/minute")
async def get_keywords(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=30)] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$")] = "all",
    top_n: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[KeywordItem]:
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=period_days, region=region, top_n=top_n)
    return result.keywords


# ---------------------------------------------------------------------------
# Interests only
# ---------------------------------------------------------------------------


@app.get("/api/interests", response_model=list[InterestItem])
@limiter.limit("30/minute")
async def get_interests(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=30)] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$")] = "all",
) -> list[InterestItem]:
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=period_days, region=region)
    return result.interests


# ---------------------------------------------------------------------------
# Top videos
# ---------------------------------------------------------------------------


@app.get("/api/videos", response_model=PaginatedVideos)
@limiter.limit("30/minute")
async def get_videos(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=30)] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$")] = "all",
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedVideos:
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=period_days, region=region)
    total = len(result.videos)
    paginated = result.videos[offset : offset + limit]
    return PaginatedVideos(total=total, offset=offset, limit=limit, videos=paginated)


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


@app.get("/api/export/csv")
@limiter.limit("30/minute")
async def export_csv(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=30)] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$")] = "all",
    top_n: Annotated[int, Query(ge=1, le=50)] = 10,
) -> StreamingResponse:
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=period_days, region=region, top_n=top_n)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["rank", "keyword", "count", "category"])
    for kw in result.keywords:
        writer.writerow([kw.rank, kw.keyword, kw.count, kw.category])
    buf.seek(0)

    filename = f"techpulse_keywords_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------------------
# XLSX export
# ---------------------------------------------------------------------------


@app.get("/api/export/xlsx")
@limiter.limit("30/minute")
async def export_xlsx(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=30)] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$")] = "all",
    top_n: Annotated[int, Query(ge=1, le=50)] = 10,
) -> StreamingResponse:
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=period_days, region=region, top_n=top_n)

    wb = Workbook()

    # Sheet 1 — Keywords
    ws_kw = wb.active
    assert ws_kw is not None
    ws_kw.title = "Keywords"
    ws_kw.append(["rank", "keyword", "count", "category"])
    for kw in result.keywords:
        ws_kw.append([kw.rank, kw.keyword, kw.count, kw.category])

    # Sheet 2 — Top Videos
    ws_vid = wb.create_sheet(title="Top Videos")
    ws_vid.append(["video_id", "title", "channel", "views", "likes", "published_at", "language"])
    for v in result.videos:
        ws_vid.append([v.video_id, v.title, v.channel, v.views, v.likes, v.published_at, v.language])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"techpulse_analysis_{date.today().isoformat()}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------------------
# Settings (read-only)
# ---------------------------------------------------------------------------


@app.get("/api/settings")
@limiter.limit("30/minute")
async def get_settings(request: Request):
    kr_queries, en_queries = load_search_queries()
    return {
        "search_queries": {"kr": kr_queries, "en": en_queries},
        "categories": list(INTEREST_CATEGORIES.keys()),
        "cache_ttl_seconds": config.CACHE_TTL_SECONDS,
    }


# ---------------------------------------------------------------------------
# Trend tracking
# ---------------------------------------------------------------------------


@app.get("/api/trends")
@limiter.limit("30/minute")
async def get_trends(
    request: Request,
    region: str = Query("all"),
    weeks: int = Query(2, ge=2, le=12),
):
    """Compare keyword trends between analysis runs."""
    result = get_trend_comparison(region, weeks)
    if result is None:
        return {"message": "트렌드 데이터가 부족합니다. 최소 2회 이상 분석을 실행해주세요.", "trends": []}
    return result


@app.get("/api/trends/{keyword}")
@limiter.limit("30/minute")
async def get_keyword_trend_history(
    request: Request,
    keyword: str,
    limit: int = Query(12, ge=1, le=52),
):
    """Get historical data for a specific keyword."""
    result = get_trend_history(keyword, limit)
    if result is None:
        return {"message": "키워드 이력이 없습니다.", "history": []}
    return {"keyword": keyword, "history": result}


# ---------------------------------------------------------------------------
# Email report
# ---------------------------------------------------------------------------


@app.post("/api/report/send")
@limiter.limit("5/minute")
async def send_email_report(request: Request, body: ReportSendRequest):
    """Send report email to specified recipients."""
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=7, region="all", top_n=10)

    trends_data = None
    if config.DB_ENABLED:
        comparison = get_trend_comparison("all")
        if comparison:
            trends_data = comparison.get("trends")

    top_video = result.videos[0] if result.videos else None
    html = generate_report_html(result.keywords, {}, top_video, trends_data)

    success = send_report(body.recipients, html)
    if not success:
        raise HTTPException(status_code=503, detail="이메일 발송에 실패했습니다. RESEND_API_KEY를 확인해주세요.")
    return {"message": f"{len(body.recipients)}명에게 리포트를 발송했습니다.", "success": True}


@app.get("/api/report/preview")
@limiter.limit("10/minute")
async def preview_report(request: Request):
    """Preview the report HTML."""
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=7, region="all", top_n=10)
    top_video = result.videos[0] if result.videos else None
    html = generate_report_html(result.keywords, {}, top_video)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {"html": html, "subject": f"[TechPulse] 주간 테크 트렌드 리포트 — {now}"}
