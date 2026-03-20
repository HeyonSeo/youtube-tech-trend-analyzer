"""YouTube 테크 리뷰 트렌드 분석기

최근 7일간 '테크 리뷰' 분야에서 높은 조회수를 기록한 영상들의
공통 키워드 10개와 시청자 주요 관심사를 분석합니다.
"""

import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise SystemExit("YOUTUBE_API_KEY 환경변수를 .env 파일에 설정해주세요.")

SEARCH_QUERIES = [
    "테크 리뷰",
    "tech review",
    "IT 리뷰",
    "가젯 리뷰",
    "스마트폰 리뷰",
    "노트북 리뷰",
]

# 키워드 추출 시 제외할 불용어
STOPWORDS = {
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
    # 한국어 불용어
    "그", "이", "저", "것", "수", "등", "및", "더", "를", "을", "의",
    "에", "에서", "로", "으로", "와", "과", "은", "는", "이", "가",
    "도", "만", "까지", "부터", "에게", "한테", "께", "보다", "처럼",
    "같이", "대로", "밖에", "뿐", "요", "네", "거", "좀", "잘",
    "안", "못", "다", "해", "합니다", "있는", "하는", "되는", "있다",
    "없다", "하다", "되다", "나", "내", "제", "우리", "너", "당신",
}

# 관심사 카테고리 매핑
INTEREST_CATEGORIES = {
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


def get_youtube_service():
    return build("youtube", "v3", developerKey=API_KEY)


def search_videos(youtube, query: str, published_after: str, max_results: int = 50):
    """YouTube 검색 API로 영상 목록 조회."""
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        order="viewCount",
        publishedAfter=published_after,
        maxResults=max_results,
        relevanceLanguage="ko",
        regionCode="KR",
    )
    return request.execute()


def get_video_details(youtube, video_ids: list[str]):
    """영상 상세 정보(조회수, 좋아요 등) 조회."""
    request = youtube.videos().list(
        part="statistics,snippet",
        id=",".join(video_ids),
    )
    return request.execute()


def extract_keywords(text: str) -> list[str]:
    """텍스트에서 키워드를 추출."""
    text = re.sub(r"[^\w\s가-힣]", " ", text.lower())
    words = text.split()
    return [w for w in words if len(w) >= 2 and w not in STOPWORDS]


def categorize_interests(keyword_counter: Counter) -> dict[str, int]:
    """키워드를 관심사 카테고리로 분류하고 점수를 매김."""
    scores: dict[str, int] = {}
    for category, terms in INTEREST_CATEGORIES.items():
        score = sum(keyword_counter.get(term, 0) for term in terms)
        if score > 0:
            scores[category] = score
    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


def print_table(headers: list[str], rows: list[list[str]]):
    """간단한 마크다운 스타일 테이블 출력."""
    col_widths = [
        max(len(str(h)), *(len(str(row[i])) for row in rows))
        for i, h in enumerate(headers)
    ]

    def fmt_row(vals):
        return "| " + " | ".join(
            str(v).ljust(w) for v, w in zip(vals, col_widths)
        ) + " |"

    print(fmt_row(headers))
    print("|" + "|".join("-" * (w + 2) for w in col_widths) + "|")
    for row in rows:
        print(fmt_row(row))


def main():
    youtube = get_youtube_service()
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()

    all_videos = {}
    keyword_counter: Counter = Counter()

    print(f"[*] 분석 기간: {(now - timedelta(days=7)).strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}")
    print(f"[*] 검색 쿼리: {', '.join(SEARCH_QUERIES)}\n")

    # 1. 여러 검색어로 영상 수집
    for query in SEARCH_QUERIES:
        print(f"  검색 중: '{query}'...")
        try:
            results = search_videos(youtube, query, week_ago)
        except Exception as e:
            print(f"  ⚠ 검색 실패 ({query}): {e}")
            continue

        video_ids = [
            item["id"]["videoId"]
            for item in results.get("items", [])
            if item["id"].get("videoId")
        ]
        if not video_ids:
            continue

        details = get_video_details(youtube, video_ids)
        for item in details.get("items", []):
            vid = item["id"]
            if vid in all_videos:
                continue
            title = item["snippet"]["title"]
            description = item["snippet"].get("description", "")
            tags = item["snippet"].get("tags", [])
            view_count = int(item["statistics"].get("viewCount", 0))
            like_count = int(item["statistics"].get("likeCount", 0))

            all_videos[vid] = {
                "title": title,
                "views": view_count,
                "likes": like_count,
                "channel": item["snippet"]["channelTitle"],
            }

            # 키워드 추출: 제목 + 태그 + 설명 앞부분
            text = f"{title} {' '.join(tags)} {description[:300]}"
            for kw in extract_keywords(text):
                keyword_counter[kw] += 1

    if not all_videos:
        print("\n검색 결과가 없습니다. API 키와 네트워크를 확인해주세요.")
        return

    # 2. 조회수 기준 상위 영상 정렬
    sorted_videos = sorted(all_videos.values(), key=lambda v: v["views"], reverse=True)

    print(f"\n{'='*70}")
    print(f"  수집된 영상 수: {len(all_videos)}개")
    print(f"{'='*70}\n")

    # 3. 상위 10개 영상
    print("▶ 조회수 상위 10개 영상\n")
    top_rows = []
    for i, v in enumerate(sorted_videos[:10], 1):
        top_rows.append([
            str(i),
            v["title"][:40],
            v["channel"][:15],
            f"{v['views']:,}",
            f"{v['likes']:,}",
        ])
    print_table(["순위", "제목", "채널", "조회수", "좋아요"], top_rows)

    # 4. 공통 키워드 TOP 10
    print(f"\n{'='*70}")
    print("▶ 공통 키워드 TOP 10\n")
    top_keywords = keyword_counter.most_common(10)
    kw_rows = []
    for i, (kw, count) in enumerate(top_keywords, 1):
        kw_rows.append([str(i), kw, str(count)])
    print_table(["순위", "키워드", "출현 빈도"], kw_rows)

    # 5. 시청자 주요 관심사
    print(f"\n{'='*70}")
    print("▶ 시청자 주요 관심사 분석\n")
    interests = categorize_interests(keyword_counter)
    if interests:
        max_score = max(interests.values())
        int_rows = []
        for i, (cat, score) in enumerate(interests.items(), 1):
            bar_len = int((score / max_score) * 20)
            bar = "█" * bar_len
            int_rows.append([str(i), cat, str(score), bar])
        print_table(["순위", "관심사 분야", "관련도 점수", "비중"], int_rows)
    else:
        print("  관심사 분류 데이터가 부족합니다.")

    # 6. 종합 요약 테이블
    print(f"\n{'='*70}")
    print("▶ 종합 요약: 키워드 + 관심사\n")
    summary_rows = []
    for i, (kw, count) in enumerate(top_keywords, 1):
        # 키워드가 어떤 관심사에 해당하는지 찾기
        matched = "기타"
        for cat, terms in INTEREST_CATEGORIES.items():
            if kw in terms:
                matched = cat
                break
        summary_rows.append([str(i), kw, str(count), matched])
    print_table(["순위", "키워드", "빈도", "관련 관심사"], summary_rows)

    print(f"\n[*] 분석 완료!")


if __name__ == "__main__":
    main()
