from __future__ import annotations

from pydantic import BaseModel


class VideoItem(BaseModel):
    video_id: str
    title: str
    channel: str
    views: int
    likes: int
    published_at: str
    language: str
    thumbnail_url: str


class KeywordItem(BaseModel):
    rank: int
    keyword: str
    count: int
    category: str


class InterestItem(BaseModel):
    rank: int
    category: str
    score: int
    ratio: float  # 0.0 – 1.0


class PaginatedVideos(BaseModel):
    total: int
    offset: int
    limit: int
    videos: list[VideoItem]


class AnalysisMetadata(BaseModel):
    video_count: int
    period_days: int
    region: str
    run_date: str
    queries_used: list[str]
    errors: list[str] = []
    api_calls_used: int = 0


class AnalysisResult(BaseModel):
    metadata: AnalysisMetadata
    videos: list[VideoItem]
    keywords: list[KeywordItem]
    interests: list[InterestItem]


class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int


class TrendItem(BaseModel):
    keyword: str
    rank: int
    count: int
    category: str
    rank_change: int | None = None
    is_new: bool = False
    previous_rank: int | None = None


class TrendComparison(BaseModel):
    current_date: str
    previous_date: str
    trends: list[TrendItem]


class ReportRecipient(BaseModel):
    email: str


class ReportSendRequest(BaseModel):
    recipients: list[str]


class ReportPreviewResponse(BaseModel):
    html: str
    subject: str
