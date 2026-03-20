from __future__ import annotations

import json
import os

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Custom search queries from JSON file
# ---------------------------------------------------------------------------
CUSTOM_QUERIES_FILE: str = os.getenv("CUSTOM_QUERIES_FILE", "")

# ---------------------------------------------------------------------------
# YouTube API
# ---------------------------------------------------------------------------
YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")

# ---------------------------------------------------------------------------
# Search queries (split by language)
# ---------------------------------------------------------------------------
SEARCH_QUERIES_KR: list[str] = [
    "테크 리뷰",
    "IT 리뷰",
    "가젯 리뷰",
    "스마트폰 리뷰",
    "노트북 리뷰",
]

SEARCH_QUERIES_EN: list[str] = [
    "tech review",
    "gadget review",
    "smartphone review",
    "laptop review",
    "best tech",
]

# ---------------------------------------------------------------------------
# Stopwords (Korean + English)
# ---------------------------------------------------------------------------
STOPWORDS: set[str] = {
    # English
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "must", "and", "or",
    "but", "if", "for", "with", "about", "from", "into", "of", "to", "in",
    "on", "at", "by", "it", "its", "this", "that", "these", "those", "not",
    "no", "so", "vs", "how", "what", "why", "when", "where", "which", "who",
    "i", "you", "he", "she", "we", "they", "my", "your", "his", "her", "our",
    "their", "me", "him", "us", "them", "all", "just", "very", "too", "also",
    "more", "most", "much", "many", "some", "any", "each", "every", "both",
    "few", "other", "such", "than", "then", "only", "own", "same", "up",
    "out", "off", "over", "under", "again", "once", "here", "there", "new",
    "one", "two", "first", "get", "got", "go", "went", "come", "make",
    # Korean
    "그", "이", "저", "것", "수", "등", "및", "더", "를", "을", "의",
    "에", "에서", "로", "으로", "와", "과", "은", "는", "이", "가",
    "도", "만", "까지", "부터", "에게", "한테", "께", "보다", "처럼",
    "같이", "대로", "밖에", "뿐", "요", "네", "거", "좀", "잘",
    "안", "못", "다", "해", "합니다", "있는", "하는", "되는", "있다",
    "없다", "하다", "되다", "나", "내", "제", "우리", "너", "당신",
}

# ---------------------------------------------------------------------------
# Interest categories — each with Korean AND English terms
# ---------------------------------------------------------------------------
INTEREST_CATEGORIES: dict[str, list[str]] = {
    "스마트폰/모바일": [
        "아이폰", "iphone", "갤럭시", "galaxy", "삼성", "samsung", "픽셀",
        "pixel", "스마트폰", "smartphone", "phone", "폰", "android", "안드로이드",
        "ios", "폴드", "fold", "플립", "flip",
    ],
    "노트북/PC": [
        "노트북", "laptop", "맥북", "macbook", "데스크톱", "desktop", "pc",
        "컴퓨터", "computer", "그램", "gram", "씽크패드", "thinkpad",
        "윈도우", "windows", "mac", "맥",
    ],
    "AI/소프트웨어": [
        "ai", "인공지능", "챗gpt", "chatgpt", "gpt", "gemini", "제미나이",
        "copilot", "코파일럿", "llm", "머신러닝", "딥러닝", "앱", "app",
        "소프트웨어", "software", "업데이트", "update",
    ],
    "오디오/웨어러블": [
        "이어폰", "earphone", "earbuds", "헤드폰", "headphone", "에어팟",
        "airpods", "스피커", "speaker", "워치", "watch", "웨어러블", "wearable",
        "버즈", "buds", "갤럭시워치", "애플워치",
    ],
    "카메라/영상": [
        "카메라", "camera", "렌즈", "lens", "촬영", "사진", "photo", "영상",
        "video", "4k", "8k", "짐벌", "gimbal", "gopro", "고프로", "드론", "drone",
    ],
    "성능/벤치마크": [
        "성능", "performance", "벤치마크", "benchmark", "속도", "speed", "배터리",
        "battery", "발열", "칩", "chip", "프로세서", "processor", "cpu", "gpu",
        "ram", "메모리", "memory", "스냅드래곤", "snapdragon", "바이오닉", "bionic",
    ],
    "가격/가성비": [
        "가격", "price", "가성비", "저렴", "cheap", "비싼", "expensive", "할인",
        "discount", "세일", "sale", "비교", "comparison", "추천", "best",
        "worth", "구매", "buy", "구입",
    ],
    "디스플레이/디자인": [
        "디스플레이", "display", "화면", "screen", "oled", "amoled", "lcd",
        "디자인", "design", "색감", "해상도", "resolution", "베젤", "bezel",
    ],
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ---------------------------------------------------------------------------
# YouTube API
# ---------------------------------------------------------------------------
YOUTUBE_API_TIMEOUT: int = int(os.getenv("YOUTUBE_API_TIMEOUT", "15"))

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
_cors_env = os.getenv("CORS_ORIGINS", "")
CORS_ORIGINS: list[str] = (
    [origin.strip() for origin in _cors_env.split(",") if origin.strip()]
    if _cors_env
    else ["http://localhost:3000"]
)

# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
DB_ENABLED: bool = bool(SUPABASE_URL and SUPABASE_KEY)


# ---------------------------------------------------------------------------
# Load custom search queries
# ---------------------------------------------------------------------------
def load_search_queries() -> tuple[list[str], list[str]]:
    """Load search queries from a custom JSON file if configured, otherwise use defaults."""
    if CUSTOM_QUERIES_FILE and os.path.exists(CUSTOM_QUERIES_FILE):
        with open(CUSTOM_QUERIES_FILE) as f:
            data = json.load(f)
            return data.get("kr", SEARCH_QUERIES_KR), data.get("en", SEARCH_QUERIES_EN)
    return SEARCH_QUERIES_KR, SEARCH_QUERIES_EN
