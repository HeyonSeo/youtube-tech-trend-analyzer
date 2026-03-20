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
# OpenAPI tag metadata
# ---------------------------------------------------------------------------
tags_metadata = [
    {
        "name": "분석",
        "description": "YouTube 테크 영상 분석 — 키워드, 관심사, 영상 데이터를 조회합니다.",
    },
    {
        "name": "내보내기",
        "description": "분석 결과를 CSV 또는 XLSX 파일로 다운로드합니다.",
    },
    {
        "name": "트렌드",
        "description": "키워드 순위 변동 및 이력 추적 (Supabase 연동 필요).",
    },
    {
        "name": "설정",
        "description": "현재 검색 쿼리, 카테고리, 캐시 설정을 조회합니다.",
    },
    {
        "name": "리포트",
        "description": "이메일 리포트 미리보기 및 발송 (Resend 연동 필요).",
    },
    {
        "name": "시스템",
        "description": "헬스 체크, 캐시 관리 등 시스템 운영 엔드포인트.",
    },
]

# ---------------------------------------------------------------------------
# App & rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="YouTube Tech Trend Analyzer",
    description=(
        "YouTube Data API v3 기반 테크 리뷰 트렌드 분석 API.\n\n"
        "주요 기능:\n"
        "- **키워드 분석**: 영상 제목/태그/설명에서 키워드 추출 및 빈도 랭킹\n"
        "- **관심사 분류**: 8개 테크 카테고리 자동 분류\n"
        "- **트렌드 추적**: 주간 순위 변동 비교 (Supabase 연동)\n"
        "- **내보내기**: CSV / XLSX 다운로드\n"
        "- **이메일 리포트**: 주간 리포트 발송 (Resend 연동)\n\n"
        "Rate Limit은 IP 기반으로 적용됩니다."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
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


@app.get(
    "/api/health",
    tags=["시스템"],
    summary="헬스 체크",
    description="서버 상태 및 캐시 정보를 반환합니다. 모니터링 도구나 로드밸런서에서 사용합니다.",
    responses={
        200: {
            "description": "서버 정상 동작",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "cache_entries": 3,
                        "last_analysis_time": "2025-01-15T10:30:00Z",
                    }
                }
            },
        }
    },
)
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


@app.post(
    "/api/cache/clear",
    tags=["시스템"],
    summary="캐시 초기화",
    description="모든 분석 캐시를 삭제합니다. 새로운 분석 요청 시 YouTube API를 다시 호출합니다.",
    responses={
        200: {
            "description": "캐시 초기화 성공",
            "content": {
                "application/json": {
                    "example": {"status": "ok", "entries_removed": 3}
                }
            },
        }
    },
)
@limiter.limit("30/minute")
async def clear_analysis_cache(request: Request) -> dict:
    removed = clear_cache()
    return {"status": "ok", "entries_removed": removed}


# ---------------------------------------------------------------------------
# Full analysis
# ---------------------------------------------------------------------------


@app.get(
    "/api/analyze",
    response_model=AnalysisResult,
    tags=["분석"],
    summary="전체 분석 실행",
    description=(
        "YouTube 테크 리뷰 영상을 검색하고 키워드, 관심사, 영상 목록을 포함한 "
        "전체 분석 결과를 반환합니다. 결과는 TTL 기반으로 캐시되며, "
        "Supabase가 연결된 경우 분석 이력이 자동 저장됩니다."
    ),
    responses={
        200: {
            "description": "분석 성공",
            "content": {
                "application/json": {
                    "example": {
                        "metadata": {
                            "video_count": 120,
                            "period_days": 7,
                            "region": "all",
                            "run_date": "2025-01-15",
                            "queries_used": ["테크 리뷰", "tech review"],
                            "errors": [],
                            "api_calls_used": 12,
                        },
                        "videos": [
                            {
                                "video_id": "abc123",
                                "title": "갤럭시 S25 울트라 리뷰",
                                "channel": "테크채널",
                                "views": 500000,
                                "likes": 15000,
                                "published_at": "2025-01-14",
                                "language": "kr",
                                "thumbnail_url": "https://i.ytimg.com/vi/abc123/mqdefault.jpg",
                            }
                        ],
                        "keywords": [
                            {"rank": 1, "keyword": "갤럭시", "count": 45, "category": "스마트폰/모바일"}
                        ],
                        "interests": [
                            {"rank": 1, "category": "스마트폰/모바일", "score": 120, "ratio": 0.35}
                        ],
                    }
                }
            },
        },
        502: {
            "description": "YouTube API 오류",
            "content": {
                "application/json": {
                    "example": {
                        "error": "YouTube API Error",
                        "detail": "quotaExceeded",
                        "status_code": 502,
                    }
                }
            },
        },
    },
)
@limiter.limit("10/minute")
async def analyze(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=30, description="분석 기간 (일). 기본값 7일.")] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$", description="지역 필터: kr(한국), global(글로벌), all(전체).")] = "all",
    top_n: Annotated[int, Query(ge=1, le=50, description="반환할 키워드 개수. 기본값 10.")] = 10,
) -> AnalysisResult:
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=period_days, region=region, top_n=top_n)
    # Auto-save to DB (non-blocking, errors are logged but not raised)
    save_analysis_run(result.metadata, result.keywords, result.videos)
    return result


# ---------------------------------------------------------------------------
# Keywords only
# ---------------------------------------------------------------------------


@app.get(
    "/api/keywords",
    response_model=list[KeywordItem],
    tags=["분석"],
    summary="키워드 TOP N 조회",
    description="분석 결과에서 키워드 랭킹만 반환합니다. 경량 요청이 필요할 때 사용합니다.",
    responses={
        200: {
            "description": "키워드 목록",
            "content": {
                "application/json": {
                    "example": [
                        {"rank": 1, "keyword": "갤럭시", "count": 45, "category": "스마트폰/모바일"},
                        {"rank": 2, "keyword": "아이폰", "count": 38, "category": "스마트폰/모바일"},
                        {"rank": 3, "keyword": "ai", "count": 32, "category": "AI/소프트웨어"},
                    ]
                }
            },
        }
    },
)
@limiter.limit("30/minute")
async def get_keywords(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=30, description="분석 기간 (일). 기본값 7일.")] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$", description="지역 필터: kr, global, all.")] = "all",
    top_n: Annotated[int, Query(ge=1, le=50, description="반환할 키워드 개수. 기본값 10.")] = 10,
) -> list[KeywordItem]:
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=period_days, region=region, top_n=top_n)
    return result.keywords


# ---------------------------------------------------------------------------
# Interests only
# ---------------------------------------------------------------------------


@app.get(
    "/api/interests",
    response_model=list[InterestItem],
    tags=["분석"],
    summary="관심사 카테고리 조회",
    description=(
        "8개 테크 카테고리(스마트폰/모바일, 노트북/PC, AI/소프트웨어 등)별 "
        "관심도 점수와 비율을 반환합니다."
    ),
    responses={
        200: {
            "description": "관심사 목록",
            "content": {
                "application/json": {
                    "example": [
                        {"rank": 1, "category": "스마트폰/모바일", "score": 120, "ratio": 0.35},
                        {"rank": 2, "category": "AI/소프트웨어", "score": 85, "ratio": 0.25},
                    ]
                }
            },
        }
    },
)
@limiter.limit("30/minute")
async def get_interests(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=30, description="분석 기간 (일). 기본값 7일.")] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$", description="지역 필터: kr, global, all.")] = "all",
) -> list[InterestItem]:
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=period_days, region=region)
    return result.interests


# ---------------------------------------------------------------------------
# Top videos
# ---------------------------------------------------------------------------


@app.get(
    "/api/videos",
    response_model=PaginatedVideos,
    tags=["분석"],
    summary="상위 영상 목록 조회",
    description="조회수 기준 상위 영상을 페이지네이션으로 반환합니다.",
    responses={
        200: {
            "description": "페이지네이션된 영상 목록",
            "content": {
                "application/json": {
                    "example": {
                        "total": 120,
                        "offset": 0,
                        "limit": 20,
                        "videos": [
                            {
                                "video_id": "abc123",
                                "title": "갤럭시 S25 울트라 리뷰",
                                "channel": "테크채널",
                                "views": 500000,
                                "likes": 15000,
                                "published_at": "2025-01-14",
                                "language": "kr",
                                "thumbnail_url": "https://i.ytimg.com/vi/abc123/mqdefault.jpg",
                            }
                        ],
                    }
                }
            },
        }
    },
)
@limiter.limit("30/minute")
async def get_videos(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=30, description="분석 기간 (일). 기본값 7일.")] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$", description="지역 필터: kr, global, all.")] = "all",
    offset: Annotated[int, Query(ge=0, description="건너뛸 항목 수. 기본값 0.")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="반환할 항목 수. 기본값 20, 최대 100.")] = 20,
) -> PaginatedVideos:
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=period_days, region=region)
    total = len(result.videos)
    paginated = result.videos[offset : offset + limit]
    return PaginatedVideos(total=total, offset=offset, limit=limit, videos=paginated)


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


@app.get(
    "/api/export/csv",
    tags=["내보내기"],
    summary="CSV 파일 다운로드",
    description="키워드 분석 결과를 CSV 파일로 다운로드합니다. 파일명에 날짜가 포함됩니다.",
    responses={
        200: {
            "description": "CSV 파일 (text/csv)",
            "content": {
                "text/csv": {
                    "example": "rank,keyword,count,category\n1,갤럭시,45,스마트폰/모바일\n2,아이폰,38,스마트폰/모바일"
                }
            },
        }
    },
)
@limiter.limit("30/minute")
async def export_csv(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=30, description="분석 기간 (일). 기본값 7일.")] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$", description="지역 필터: kr, global, all.")] = "all",
    top_n: Annotated[int, Query(ge=1, le=50, description="반환할 키워드 개수. 기본값 10.")] = 10,
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


@app.get(
    "/api/export/xlsx",
    tags=["내보내기"],
    summary="XLSX 파일 다운로드",
    description=(
        "키워드 및 영상 데이터를 XLSX 파일로 다운로드합니다. "
        "Keywords, Top Videos 두 개의 시트가 포함됩니다."
    ),
    responses={
        200: {
            "description": "XLSX 파일 (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)",
        }
    },
)
@limiter.limit("30/minute")
async def export_xlsx(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=30, description="분석 기간 (일). 기본값 7일.")] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$", description="지역 필터: kr, global, all.")] = "all",
    top_n: Annotated[int, Query(ge=1, le=50, description="반환할 키워드 개수. 기본값 10.")] = 10,
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


@app.get(
    "/api/settings",
    tags=["설정"],
    summary="현재 설정 조회",
    description="검색 쿼리 목록, 관심사 카테고리, 캐시 TTL 등 현재 설정을 반환합니다.",
    responses={
        200: {
            "description": "현재 설정",
            "content": {
                "application/json": {
                    "example": {
                        "search_queries": {
                            "kr": ["테크 리뷰", "IT 리뷰", "가젯 리뷰"],
                            "en": ["tech review", "gadget review"],
                        },
                        "categories": [
                            "스마트폰/모바일",
                            "노트북/PC",
                            "AI/소프트웨어",
                        ],
                        "cache_ttl_seconds": 3600,
                    }
                }
            },
        }
    },
)
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


@app.get(
    "/api/trends",
    tags=["트렌드"],
    summary="키워드 순위 변동 비교",
    description=(
        "최근 분석 실행 간의 키워드 순위 변동을 비교합니다. "
        "Supabase 연동(DB_ENABLED=true)이 필요하며, 최소 2회 이상 분석이 실행되어야 합니다."
    ),
    responses={
        200: {
            "description": "트렌드 비교 결과",
            "content": {
                "application/json": {
                    "example": {
                        "current_date": "2025-01-15T10:30:00Z",
                        "previous_date": "2025-01-08T10:30:00Z",
                        "trends": [
                            {
                                "keyword": "갤럭시",
                                "rank": 1,
                                "count": 45,
                                "category": "스마트폰/모바일",
                                "rank_change": 2,
                                "is_new": False,
                                "previous_rank": 3,
                            },
                            {
                                "keyword": "claude",
                                "rank": 5,
                                "count": 20,
                                "category": "AI/소프트웨어",
                                "rank_change": None,
                                "is_new": True,
                                "previous_rank": None,
                            },
                        ],
                    }
                }
            },
        }
    },
)
@limiter.limit("30/minute")
async def get_trends(
    request: Request,
    region: str = Query("all", description="지역 필터: kr, global, all."),
    weeks: int = Query(2, ge=2, le=12, description="비교할 주 수. 기본값 2, 최대 12."),
):
    """Compare keyword trends between analysis runs."""
    result = get_trend_comparison(region, weeks)
    if result is None:
        return {"message": "트렌드 데이터가 부족합니다. 최소 2회 이상 분석을 실행해주세요.", "trends": []}
    return result


@app.get(
    "/api/trends/{keyword}",
    tags=["트렌드"],
    summary="키워드 이력 조회",
    description="특정 키워드의 과거 순위 및 빈도 이력을 조회합니다. Supabase 연동이 필요합니다.",
    responses={
        200: {
            "description": "키워드 이력",
            "content": {
                "application/json": {
                    "example": {
                        "keyword": "갤럭시",
                        "history": [
                            {"count": 45, "rank": 1, "run_id": "uuid-1", "analysis_runs": {"run_date": "2025-01-15"}},
                            {"count": 38, "rank": 3, "run_id": "uuid-2", "analysis_runs": {"run_date": "2025-01-08"}},
                        ],
                    }
                }
            },
        }
    },
)
@limiter.limit("30/minute")
async def get_keyword_trend_history(
    request: Request,
    keyword: str,
    limit: int = Query(12, ge=1, le=52, description="반환할 이력 개수. 기본값 12, 최대 52."),
):
    """Get historical data for a specific keyword."""
    result = get_trend_history(keyword, limit)
    if result is None:
        return {"message": "키워드 이력이 없습니다.", "history": []}
    return {"keyword": keyword, "history": result}


# ---------------------------------------------------------------------------
# Email report
# ---------------------------------------------------------------------------


@app.post(
    "/api/report/send",
    tags=["리포트"],
    summary="이메일 리포트 발송",
    description=(
        "지정된 수신자에게 주간 테크 트렌드 리포트를 이메일로 발송합니다. "
        "RESEND_API_KEY 환경변수 설정이 필요합니다."
    ),
    responses={
        200: {
            "description": "발송 성공",
            "content": {
                "application/json": {
                    "example": {
                        "message": "3명에게 리포트를 발송했습니다.",
                        "success": True,
                    }
                }
            },
        },
        503: {
            "description": "이메일 발송 실패",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "이메일 발송에 실패했습니다. RESEND_API_KEY를 확인해주세요."
                    }
                }
            },
        },
    },
)
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


@app.get(
    "/api/report/preview",
    tags=["리포트"],
    summary="리포트 미리보기",
    description="이메일로 발송될 리포트의 HTML 미리보기를 반환합니다.",
    responses={
        200: {
            "description": "리포트 HTML",
            "content": {
                "application/json": {
                    "example": {
                        "html": "<html>...</html>",
                        "subject": "[TechPulse] 주간 테크 트렌드 리포트 -- 2025-01-15",
                    }
                }
            },
        }
    },
)
@limiter.limit("10/minute")
async def preview_report(request: Request):
    """Preview the report HTML."""
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=7, region="all", top_n=10)
    top_video = result.videos[0] if result.videos else None
    html = generate_report_html(result.keywords, {}, top_video)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {"html": html, "subject": f"[TechPulse] 주간 테크 트렌드 리포트 — {now}"}
