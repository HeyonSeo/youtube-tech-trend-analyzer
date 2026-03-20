from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def mock_youtube_service():
    """Return a MagicMock that mimics the YouTube Data API v3 service object."""
    service = MagicMock()

    # --- search().list().execute() ---
    search_response = {
        "items": [
            {
                "id": {"videoId": "vid001"},
                "snippet": {"title": "Test Tech Review"},
            },
            {
                "id": {"videoId": "vid002"},
                "snippet": {"title": "Smartphone Unboxing"},
            },
        ]
    }
    service.search.return_value.list.return_value.execute.return_value = (
        search_response
    )

    # --- videos().list().execute() ---
    video_details_response = {
        "items": [
            {
                "id": "vid001",
                "snippet": {
                    "title": "Test Tech Review",
                    "channelTitle": "TechChannel",
                    "description": "A review of the latest smartphone galaxy phone.",
                    "tags": ["tech", "review", "smartphone"],
                    "publishedAt": "2026-03-15T10:00:00Z",
                    "thumbnails": {
                        "high": {"url": "https://img.youtube.com/vi/vid001/hq.jpg"}
                    },
                },
                "statistics": {
                    "viewCount": "100000",
                    "likeCount": "5000",
                },
            },
            {
                "id": "vid002",
                "snippet": {
                    "title": "Smartphone Unboxing",
                    "channelTitle": "UnboxChannel",
                    "description": "Unboxing the new iphone 16 pro max.",
                    "tags": ["smartphone", "iphone", "unboxing"],
                    "publishedAt": "2026-03-14T08:00:00Z",
                    "thumbnails": {
                        "medium": {"url": "https://img.youtube.com/vi/vid002/mq.jpg"}
                    },
                },
                "statistics": {
                    "viewCount": "50000",
                    "likeCount": "2500",
                },
            },
        ]
    }
    service.videos.return_value.list.return_value.execute.return_value = (
        video_details_response
    )

    return service
