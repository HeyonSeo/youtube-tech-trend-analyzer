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


class AnalysisMetadata(BaseModel):
    video_count: int
    period_days: int
    region: str
    run_date: str
    queries_used: list[str]


class AnalysisResult(BaseModel):
    metadata: AnalysisMetadata
    videos: list[VideoItem]
    keywords: list[KeywordItem]
    interests: list[InterestItem]
