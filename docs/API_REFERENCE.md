# TechPulse API Reference

> 베이스 URL: `http://localhost:8000` (개발) / `https://your-backend.up.railway.app` (프로덕션)

## 목차

- [공통 사항](#공통-사항)
- [분석 API](#분석-api)
  - [GET /api/analyze](#get-apianalyze)
  - [GET /api/keywords](#get-apikeywords)
  - [GET /api/interests](#get-apiinterests)
  - [GET /api/videos](#get-apivideos)
- [내보내기 API](#내보내기-api)
  - [GET /api/export/csv](#get-apiexportcsv)
  - [GET /api/export/xlsx](#get-apiexportxlsx)
- [트렌드 API](#트렌드-api)
  - [GET /api/trends](#get-apitrends)
  - [GET /api/trends/{keyword}](#get-apitrendskeyword)
- [설정 API](#설정-api)
  - [GET /api/settings](#get-apisettings)
- [리포트 API](#리포트-api)
  - [POST /api/report/send](#post-apireportsend)
  - [GET /api/report/preview](#get-apireportpreview)
- [시스템 API](#시스템-api)
  - [GET /api/health](#get-apihealth)
  - [POST /api/cache/clear](#post-apicacheclear)

---

## 공통 사항

### Rate Limiting

모든 엔드포인트에 IP 기반 rate limiting이 적용됩니다.

| 엔드포인트 | 제한 |
|-----------|------|
| `GET /api/analyze` | 10회/분 |
| `POST /api/report/send` | 5회/분 |
| `GET /api/report/preview` | 10회/분 |
| 기타 모든 엔드포인트 | 30회/분 |

Rate limit 초과 시 `429 Too Many Requests` 응답이 반환됩니다.

### 공통 쿼리 파라미터

대부분의 분석 관련 엔드포인트에서 아래 파라미터를 지원합니다.

| 파라미터 | 타입 | 기본값 | 범위 | 설명 |
|---------|------|--------|------|------|
| `period_days` | int | `7` | 1~30 | 분석 기간 (일) |
| `region` | string | `"all"` | `kr`, `global`, `all` | 지역 필터 |
| `top_n` | int | `10` | 1~50 | 반환할 키워드 수 |

### 공통 에러 응답

```json
{
  "error": "에러 유형",
  "detail": "상세 메시지",
  "status_code": 500
}
```

| 상태 코드 | 설명 |
|----------|------|
| `429` | Rate limit 초과 |
| `500` | 내부 서버 오류 |
| `502` | YouTube API 오류 (quota 초과, 네트워크 등) |
| `503` | 외부 서비스 오류 (이메일 발송 실패 등) |

---

## 분석 API

### GET /api/analyze

전체 분석을 실행하고 키워드, 관심사, 영상 데이터를 모두 반환합니다.

**Rate Limit:** 10회/분

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `period_days` | int | X | `7` | 분석 기간 (1~30일) |
| `region` | string | X | `"all"` | 지역 필터 (`kr`, `global`, `all`) |
| `top_n` | int | X | `10` | 키워드 수 (1~50) |

#### 응답 (200 OK)

```json
{
  "metadata": {
    "video_count": 120,
    "period_days": 7,
    "region": "all",
    "run_date": "2025-01-15",
    "queries_used": ["테크 리뷰", "IT 리뷰", "tech review", "gadget review"],
    "errors": [],
    "api_calls_used": 12
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
      "thumbnail_url": "https://i.ytimg.com/vi/abc123/mqdefault.jpg"
    }
  ],
  "keywords": [
    {
      "rank": 1,
      "keyword": "갤럭시",
      "count": 45,
      "category": "스마트폰/모바일"
    }
  ],
  "interests": [
    {
      "rank": 1,
      "category": "스마트폰/모바일",
      "score": 120,
      "ratio": 0.35
    }
  ]
}
```

#### 에러 응답

| 상태 코드 | 원인 |
|----------|------|
| `502` | YouTube API quota 초과 또는 API 오류 |

```json
{
  "error": "YouTube API Error",
  "detail": "HttpError 403 ... quotaExceeded",
  "status_code": 502
}
```

---

### GET /api/keywords

키워드 랭킹만 반환합니다 (경량 응답).

**Rate Limit:** 30회/분

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `period_days` | int | X | `7` | 분석 기간 (1~30일) |
| `region` | string | X | `"all"` | 지역 필터 |
| `top_n` | int | X | `10` | 키워드 수 (1~50) |

#### 응답 (200 OK)

```json
[
  { "rank": 1, "keyword": "갤럭시", "count": 45, "category": "스마트폰/모바일" },
  { "rank": 2, "keyword": "아이폰", "count": 38, "category": "스마트폰/모바일" },
  { "rank": 3, "keyword": "ai", "count": 32, "category": "AI/소프트웨어" }
]
```

---

### GET /api/interests

관심사 카테고리별 점수와 비율을 반환합니다.

**Rate Limit:** 30회/분

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `period_days` | int | X | `7` | 분석 기간 (1~30일) |
| `region` | string | X | `"all"` | 지역 필터 |

> `top_n` 파라미터는 이 엔드포인트에서 사용되지 않습니다.

#### 응답 (200 OK)

```json
[
  { "rank": 1, "category": "스마트폰/모바일", "score": 120, "ratio": 0.35 },
  { "rank": 2, "category": "AI/소프트웨어", "score": 85, "ratio": 0.25 },
  { "rank": 3, "category": "노트북/PC", "score": 60, "ratio": 0.18 },
  { "rank": 4, "category": "오디오/웨어러블", "score": 30, "ratio": 0.09 },
  { "rank": 5, "category": "카메라/영상", "score": 22, "ratio": 0.06 },
  { "rank": 6, "category": "성능/벤치마크", "score": 18, "ratio": 0.05 },
  { "rank": 7, "category": "가격/가성비", "score": 10, "ratio": 0.03 },
  { "rank": 8, "category": "디스플레이/디자인", "score": 5, "ratio": 0.01 }
]
```

---

### GET /api/videos

조회수 기준 상위 영상 목록을 페이지네이션으로 반환합니다.

**Rate Limit:** 30회/분

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `period_days` | int | X | `7` | 분석 기간 (1~30일) |
| `region` | string | X | `"all"` | 지역 필터 |
| `offset` | int | X | `0` | 건너뛸 항목 수 |
| `limit` | int | X | `20` | 반환할 항목 수 (1~100) |

#### 응답 (200 OK)

```json
{
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
      "thumbnail_url": "https://i.ytimg.com/vi/abc123/mqdefault.jpg"
    }
  ]
}
```

---

## 내보내기 API

### GET /api/export/csv

키워드 분석 결과를 CSV 파일로 다운로드합니다.

**Rate Limit:** 30회/분

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `period_days` | int | X | `7` | 분석 기간 (1~30일) |
| `region` | string | X | `"all"` | 지역 필터 |
| `top_n` | int | X | `10` | 키워드 수 (1~50) |

#### 응답 (200 OK)

- **Content-Type:** `text/csv`
- **Content-Disposition:** `attachment; filename=techpulse_keywords_2025-01-15.csv`

```csv
rank,keyword,count,category
1,갤럭시,45,스마트폰/모바일
2,아이폰,38,스마트폰/모바일
3,ai,32,AI/소프트웨어
```

---

### GET /api/export/xlsx

키워드 및 영상 데이터를 XLSX 파일로 다운로드합니다. 두 개의 시트(Keywords, Top Videos)가 포함됩니다.

**Rate Limit:** 30회/분

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `period_days` | int | X | `7` | 분석 기간 (1~30일) |
| `region` | string | X | `"all"` | 지역 필터 |
| `top_n` | int | X | `10` | 키워드 수 (1~50) |

#### 응답 (200 OK)

- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Content-Disposition:** `attachment; filename=techpulse_analysis_2025-01-15.xlsx`

**Sheet 1 — Keywords:** rank, keyword, count, category

**Sheet 2 — Top Videos:** video_id, title, channel, views, likes, published_at, language

---

## 트렌드 API

> Supabase 연동(`DB_ENABLED=true`)이 필요합니다.

### GET /api/trends

최근 분석 실행 간의 키워드 순위 변동을 비교합니다.

**Rate Limit:** 30회/분

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `region` | string | X | `"all"` | 지역 필터 |
| `weeks` | int | X | `2` | 비교할 주 수 (2~12) |

#### 응답 (200 OK) -- 데이터 충분 시

```json
{
  "current_date": "2025-01-15T10:30:00Z",
  "previous_date": "2025-01-08T10:30:00Z",
  "trends": [
    {
      "keyword": "갤럭시",
      "rank": 1,
      "count": 45,
      "category": "스마트폰/모바일",
      "rank_change": 2,
      "is_new": false,
      "previous_rank": 3
    },
    {
      "keyword": "claude",
      "rank": 5,
      "count": 20,
      "category": "AI/소프트웨어",
      "rank_change": null,
      "is_new": true,
      "previous_rank": null
    }
  ]
}
```

#### 응답 (200 OK) -- 데이터 부족 시

```json
{
  "message": "트렌드 데이터가 부족합니다. 최소 2회 이상 분석을 실행해주세요.",
  "trends": []
}
```

> **`rank_change` 해석:** 양수 = 순위 상승 (예: 3위 -> 1위 = +2), 음수 = 순위 하락, `null` = 신규 진입

---

### GET /api/trends/{keyword}

특정 키워드의 과거 순위 및 빈도 이력을 조회합니다.

**Rate Limit:** 30회/분

#### 경로 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `keyword` | string | O | 조회할 키워드 |

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `limit` | int | X | `12` | 이력 개수 (1~52) |

#### 응답 (200 OK)

```json
{
  "keyword": "갤럭시",
  "history": [
    {
      "count": 45,
      "rank": 1,
      "run_id": "550e8400-e29b-41d4-a716-446655440000",
      "analysis_runs": {
        "run_date": "2025-01-15T10:30:00Z"
      }
    },
    {
      "count": 38,
      "rank": 3,
      "run_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "analysis_runs": {
        "run_date": "2025-01-08T10:30:00Z"
      }
    }
  ]
}
```

#### 응답 (200 OK) -- 이력 없음

```json
{
  "message": "키워드 이력이 없습니다.",
  "history": []
}
```

---

## 설정 API

### GET /api/settings

현재 검색 쿼리, 관심사 카테고리, 캐시 TTL 설정을 반환합니다 (읽기 전용).

**Rate Limit:** 30회/분

#### 응답 (200 OK)

```json
{
  "search_queries": {
    "kr": ["테크 리뷰", "IT 리뷰", "가젯 리뷰", "스마트폰 리뷰", "노트북 리뷰"],
    "en": ["tech review", "gadget review", "smartphone review", "laptop review", "best tech"]
  },
  "categories": [
    "스마트폰/모바일",
    "노트북/PC",
    "AI/소프트웨어",
    "오디오/웨어러블",
    "카메라/영상",
    "성능/벤치마크",
    "가격/가성비",
    "디스플레이/디자인"
  ],
  "cache_ttl_seconds": 3600
}
```

---

## 리포트 API

> Resend 연동(`RESEND_API_KEY` 설정)이 필요합니다.

### POST /api/report/send

지정된 수신자에게 주간 테크 트렌드 리포트를 이메일로 발송합니다.

**Rate Limit:** 5회/분

#### 요청 본문 (JSON)

```json
{
  "recipients": ["user1@example.com", "user2@example.com"]
}
```

| 필드 | 타입 | 필수 | 설명 |
|-----|------|------|------|
| `recipients` | string[] | O | 수신자 이메일 주소 목록 |

#### 응답 (200 OK)

```json
{
  "message": "2명에게 리포트를 발송했습니다.",
  "success": true
}
```

#### 에러 응답

| 상태 코드 | 원인 |
|----------|------|
| `422` | 요청 본문 검증 실패 (recipients 누락 등) |
| `503` | RESEND_API_KEY 미설정 또는 이메일 발송 실패 |

```json
{
  "detail": "이메일 발송에 실패했습니다. RESEND_API_KEY를 확인해주세요."
}
```

---

### GET /api/report/preview

이메일로 발송될 리포트의 HTML 미리보기를 반환합니다.

**Rate Limit:** 10회/분

#### 응답 (200 OK)

```json
{
  "html": "<!DOCTYPE html><html>...</html>",
  "subject": "[TechPulse] 주간 테크 트렌드 리포트 — 2025-01-15"
}
```

---

## 시스템 API

### GET /api/health

서버 상태 및 캐시 정보를 반환합니다. 모니터링 도구나 로드밸런서에서 사용합니다.

**Rate Limit:** 30회/분

#### 응답 (200 OK)

```json
{
  "status": "ok",
  "cache_entries": 3,
  "last_analysis_time": "2025-01-15T10:30:00Z"
}
```

---

### POST /api/cache/clear

모든 분석 캐시를 삭제합니다. 다음 분석 요청 시 YouTube API가 새로 호출됩니다.

**Rate Limit:** 30회/분

#### 응답 (200 OK)

```json
{
  "status": "ok",
  "entries_removed": 3
}
```

---

## Swagger UI

개발 환경에서 대화형 API 문서를 사용할 수 있습니다:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
