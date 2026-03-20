from __future__ import annotations

import csv
import io
from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

from app.analyzer import TechTrendAnalyzer
from app.config import CORS_ORIGINS
from app.models import AnalysisResult, InterestItem, KeywordItem, VideoItem

app = FastAPI(
    title="YouTube Tech Trend Analyzer",
    description="Analyze trending tech-review videos on YouTube and extract keywords / viewer interests.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_analyzer() -> TechTrendAnalyzer:
    return TechTrendAnalyzer()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Full analysis
# ---------------------------------------------------------------------------

@app.get("/api/analyze", response_model=AnalysisResult)
async def analyze(
    period_days: Annotated[int, Query(ge=1, le=30)] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$")] = "all",
    top_n: Annotated[int, Query(ge=1, le=50)] = 10,
) -> AnalysisResult:
    analyzer = _get_analyzer()
    return analyzer.analyze(period_days=period_days, region=region, top_n=top_n)


# ---------------------------------------------------------------------------
# Keywords only
# ---------------------------------------------------------------------------

@app.get("/api/keywords", response_model=list[KeywordItem])
async def get_keywords(
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
async def get_interests(
    period_days: Annotated[int, Query(ge=1, le=30)] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$")] = "all",
) -> list[InterestItem]:
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=period_days, region=region)
    return result.interests


# ---------------------------------------------------------------------------
# Top videos
# ---------------------------------------------------------------------------

@app.get("/api/videos", response_model=list[VideoItem])
async def get_videos(
    period_days: Annotated[int, Query(ge=1, le=30)] = 7,
    region: Annotated[str, Query(pattern=r"^(kr|global|all)$")] = "all",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[VideoItem]:
    analyzer = _get_analyzer()
    result = analyzer.analyze(period_days=period_days, region=region)
    return result.videos[:limit]


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

@app.get("/api/export/csv")
async def export_csv(
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

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=keywords.csv"},
    )


# ---------------------------------------------------------------------------
# XLSX export
# ---------------------------------------------------------------------------

@app.get("/api/export/xlsx")
async def export_xlsx(
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

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=analysis.xlsx"},
    )
