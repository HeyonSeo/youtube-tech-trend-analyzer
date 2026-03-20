# TechPulse — 아키텍처 문서

> YouTube 테크 리뷰 트렌드 분석기의 시스템 구조, 데이터 흐름, DB 스키마 설명서

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [기술 스택](#2-기술-스택)
3. [시스템 아키텍처](#3-시스템-아키텍처)
4. [데이터 흐름](#4-데이터-흐름)
5. [데이터베이스 스키마](#5-데이터베이스-스키마)
6. [API 레퍼런스](#6-api-레퍼런스)
7. [프론트엔드 컴포넌트](#7-프론트엔드-컴포넌트)
8. [핵심 모듈](#8-핵심-모듈)
9. [미들웨어 및 캐시](#9-미들웨어-및-캐시)
10. [배포 구조](#10-배포-구조)
11. [개발 환경 설정](#11-개발-환경-설정)

---

## 1. 시스템 개요

TechPulse는 YouTube Data API v3를 통해 테크 리뷰 영상을 수집·분석하고, 키워드 트렌드와 관심사 분포를 실시간 대시보드로 제공하는 풀스택 웹 애플리케이션입니다.

**핵심 흐름:**

```
사용자 → Next.js 대시보드 → FastAPI 백엔드 → YouTube Data API v3
                                           → Supabase (트렌드 저장)
```

**구성 레이어:**

| 레이어 | 역할 | 기술 |
|--------|------|------|
| Frontend | 대시보드 UI, 차트, 내보내기 | Next.js 14, React 18, TypeScript |
| Backend | 분석 엔진, REST API | FastAPI, Python 3.11+ |
| Database | 트렌드 이력 저장 | Supabase (PostgreSQL) |
| External | 영상 데이터 수집 | YouTube Data API v3 |
| Deployment | 호스팅, CI/CD | Vercel |

---

## 2. 기술 스택

### Backend

| 패키지 | 버전 | 용도 |
|--------|------|------|
| FastAPI | ≥0.100 | REST API 프레임워크 |
| Pydantic v2 | ≥2.0 | 데이터 모델 / 유효성 검사 |
| google-api-python-client | ≥2.0 | YouTube Data API v3 클라이언트 |
| httplib2 | - | HTTP 타임아웃 설정 |
| supabase | - | Supabase Python SDK |
| slowapi | - | Rate Limiting |
| openpyxl | - | XLSX 내보내기 |
| python-dotenv | ≥1.0 | 환경변수 로드 |
| uvicorn | - | ASGI 서버 |

### Frontend

| 패키지 | 버전 | 용도 |
|--------|------|------|
| Next.js | 14 (App Router) | React SSR 프레임워크 |
| React | 18 | UI 라이브러리 |
| TypeScript | 5 | 타입 안전성 |
| Tailwind CSS | 3 | 유틸리티 CSS |
| Recharts | - | 차트 (Bar, Radar, Line) |
| TanStack Query | - | 서버 상태 관리 / 캐시 |

---

## 3. 시스템 아키텍처

![System Architecture](./diagrams/system-architecture.svg)

### 레이어 설명

#### Frontend (Next.js 14, Vercel)

App Router 기반 SPA. 5개 페이지와 6개 핵심 컴포넌트로 구성됩니다.

- **페이지:** `/` (대시보드) · `/keywords` · `/videos` · `/trends` · `/settings`
- **상태 관리:** TanStack Query로 API 응답 캐싱 및 백그라운드 갱신
- **다크모드:** `ThemeToggle` 컴포넌트 + Tailwind `dark:` 클래스
- **에러 처리:** `ErrorBoundary` 전역 래퍼

#### Backend (FastAPI, Python 3.11+)

단일 FastAPI 앱 인스턴스. `TechTrendAnalyzer` 클래스가 분석 파이프라인 전체를 담당합니다.

- **분석 파이프라인:** 검색 → 중복 제거 → 상세 조회 → 키워드 추출 → 분류 → 캐시 저장
- **캐시:** 모듈 수준 `dict`에 `period:region:topN` 키로 TTL 캐싱
- **DB 저장:** 분석 완료 후 비동기(non-blocking) Supabase 저장 — 실패해도 응답에 영향 없음

#### External Services

| 서비스 | 역할 |
|--------|------|
| YouTube Data API v3 | `search.list` (영상 검색) + `videos.list` (통계/스니펫) |
| Supabase (PostgreSQL) | 분석 이력·키워드·영상 데이터 영구 저장 |
| Vercel | Next.js 호스팅, CDN, GitHub 연동 CI/CD |

---

## 4. 데이터 흐름

![Data Flow](./diagrams/data-flow.svg)

### 분석 요청 시나리오

**① 사용자가 필터 선택** — region (kr/global/all), period_days (1~30), top_n (1~50)

**② Frontend → Backend** — `GET /api/analyze?period_days=7&region=all&top_n=10`

**③ 캐시 조회**
- **HIT:** TTL 이내 결과 즉시 반환 (YouTube API 호출 없음)
- **MISS:** 이하 단계 진행

**④ YouTube API 검색** — KR 쿼리 6개 + EN 쿼리 6개, 각 최대 25개 결과 (`search.list`)

**⑤ 상세 정보 조회** — 신규 video_id에 대해서만 `videos.list` 호출 (중복 제거 후)

**⑥ 분석 처리**
- 제목 + 태그 + 설명(300자) → 정규식 토크나이징
- 불용어 필터링 → Counter 집계 → Top-N 추출
- 키워드 → 8개 관심사 카테고리 매핑
- 언어 감지 (한글 비율 15% 기준 ko/en 분류)

**⑦ Supabase 저장** — `analysis_runs`, `keywords`, 상위 20개 `videos` 비동기 저장

**⑧ 캐시 저장** — `_cache[key] = (now, result)`

**⑨ 응답 반환** — `AnalysisResult` JSON → Frontend 차트 렌더링

---

## 5. 데이터베이스 스키마

![DB Schema](./diagrams/db-schema.svg)

### analysis_runs

분석 실행 이력. 모든 하위 테이블의 루트.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | UUID | PK |
| `run_date` | TIMESTAMPTZ | 실행 시각 (UTC) |
| `region` | VARCHAR | `kr` / `global` / `all` |
| `period_days` | INT | 분석 기간 (일) |
| `video_count` | INT | 수집된 고유 영상 수 |
| `status` | VARCHAR | `running` / `completed` / `failed` |

**인덱스:** `(region, run_date DESC)` — 트렌드 비교 쿼리 최적화

### keywords

실행별 키워드 집계 결과.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | UUID | PK |
| `run_id` | UUID | FK → `analysis_runs.id` |
| `keyword` | VARCHAR | 추출된 키워드 |
| `count` | INT | 출현 빈도 |
| `rank` | INT | 순위 (1-based) |
| `category` | VARCHAR | 관심사 카테고리 |
| `language` | VARCHAR | `ko` / `en` |

**인덱스:** `(run_id)`, `(keyword, run_id)` — 트렌드 이력 조회 최적화

### videos

실행별 수집 영상 (상위 20개 저장).

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | UUID | PK |
| `run_id` | UUID | FK → `analysis_runs.id` |
| `video_id` | VARCHAR | YouTube 영상 ID |
| `title` | TEXT | 영상 제목 |
| `channel` | VARCHAR | 채널명 |
| `views` | BIGINT | 조회수 |
| `likes` | BIGINT | 좋아요 수 |
| `published_at` | TIMESTAMPTZ | 게시일 |
| `language` | VARCHAR | 감지된 언어 (`ko` / `en`) |

### trend_snapshots (Phase 2 예정)

주간 스냅샷 집계 테이블 (독립, FK 없음).

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `snapshot_date` | DATE | 스냅샷 날짜 |
| `keyword` | VARCHAR | 키워드 |
| `rank` | INT | 해당 주 순위 |
| `count` | INT | 빈도 |
| `rank_change` | INT | 전주 대비 순위 변동 |
| `is_new` | BOOLEAN | 신규 진입 여부 |

---

## 6. API 레퍼런스

베이스 URL: `http://localhost:8000` (개발) / `NEXT_PUBLIC_API_URL` 환경변수 (프로덕션)

### 공통 쿼리 파라미터

| 파라미터 | 타입 | 기본값 | 범위 | 설명 |
|----------|------|--------|------|------|
| `period_days` | int | `7` | 1–30 | 최근 N일 데이터 |
| `region` | string | `"all"` | `kr\|global\|all` | 검색 언어 필터 |
| `top_n` | int | `10` | 1–50 | 상위 키워드 수 |

### 엔드포인트

| 메서드 | 경로 | Rate Limit | 설명 |
|--------|------|------------|------|
| `GET` | `/api/analyze` | 10/min | 전체 분석 실행 + 결과 반환 |
| `GET` | `/api/keywords` | 30/min | 키워드 TOP N 목록 |
| `GET` | `/api/interests` | 30/min | 관심사 카테고리 점수 |
| `GET` | `/api/videos` | 30/min | 조회수 상위 영상 (페이지네이션) |
| `GET` | `/api/trends` | 30/min | 주간 키워드 순위 비교 |
| `GET` | `/api/trends/{keyword}` | 30/min | 특정 키워드 이력 |
| `GET` | `/api/export/csv` | 30/min | 키워드 CSV 다운로드 |
| `GET` | `/api/export/xlsx` | 30/min | 키워드 + 영상 XLSX 다운로드 |
| `GET` | `/api/settings` | 30/min | 현재 설정 조회 |
| `GET` | `/api/health` | 30/min | 헬스 체크 + 캐시 상태 |
| `POST` | `/api/cache/clear` | 30/min | 캐시 초기화 |

### 응답 모델

```typescript
// GET /api/analyze
interface AnalysisResult {
  metadata: {
    video_count: number;
    period_days: number;
    region: string;
    run_date: string;
    queries_used: string[];
    errors: string[];
    api_calls_used: number;
  };
  videos: VideoItem[];      // 조회수 내림차순
  keywords: KeywordItem[];  // 빈도 내림차순, Top-N
  interests: InterestItem[]; // 카테고리별 점수
}

interface KeywordItem  { rank: number; keyword: string; count: number; category: string; }
interface InterestItem { rank: number; category: string; score: number; ratio: number; }
interface VideoItem    { video_id: string; title: string; channel: string; views: number;
                        likes: number; published_at: string; language: string; thumbnail_url: string; }
```

---

## 7. 프론트엔드 컴포넌트

```
src/
├── app/
│   ├── layout.tsx          — RootLayout: nav, ThemeToggle, QueryProvider, ErrorBoundary
│   ├── page.tsx            — 대시보드 메인 (SummaryCards + 차트 + VideoTable)
│   ├── keywords/page.tsx   — 키워드 상세 (필터, 정렬, 언어별 분리)
│   ├── videos/page.tsx     — 영상 목록 (썸네일, 페이지네이션)
│   ├── trends/page.tsx     — 트렌드 비교 (순위 변동, 신규 진입)
│   └── settings/page.tsx   — 설정 (검색어, 캐시 TTL, 캐시 초기화)
├── components/
│   ├── KeywordRankingChart.tsx  — Recharts HorizontalBar
│   ├── InterestRadarChart.tsx   — Recharts RadarChart
│   ├── VideoTable.tsx           — 썸네일 테이블 + 페이지네이션
│   ├── SummaryCards.tsx         — 요약 지표 카드 4개
│   ├── ExportButton.tsx         — CSV/XLSX 드롭다운
│   ├── TrendModal.tsx           — 키워드 클릭 시 이력 모달
│   ├── ThemeToggle.tsx          — 다크/라이트 모드 토글
│   ├── RegionToggle.tsx         — 한국/글로벌/전체 전환
│   ├── LoadingSkeleton.tsx      — 로딩 스켈레톤
│   └── ErrorBoundary.tsx        — React 에러 경계
└── lib/
    ├── api.ts              — fetch 헬퍼 함수 + TypeScript 인터페이스
    └── QueryProvider.tsx   — TanStack Query 클라이언트 설정
```

---

## 8. 핵심 모듈

### TechTrendAnalyzer (`backend/app/analyzer.py`)

```
TechTrendAnalyzer
├── search_videos(query, published_after)     → YouTube search.list
├── get_video_details(video_ids)              → YouTube videos.list
├── extract_keywords(text)                    → List[str] (정규식 + 불용어 필터)
├── categorize_interests(counter)             → Dict[category, score]
├── _detect_language(text)                    → "ko" | "en"
├── _retry_api_call(func, max_retries=3)      → 지수 백오프 재시도
└── analyze(period_days, region, top_n)       → AnalysisResult
```

**캐시 키 전략:** `"{period_days}:{region}:{top_n}"` — 동일 파라미터 요청은 TTL 이내 YouTube API 미호출

**관심사 카테고리 (8개):**

| 카테고리 | 예시 키워드 |
|----------|------------|
| 스마트폰 | 갤럭시, 아이폰, 픽셀, 폴드 |
| 노트북/PC | 맥북, 레노버, 델, 인텔 |
| AI/소프트웨어 | chatgpt, copilot, gemini, llm |
| 오디오/웨어러블 | 에어팟, 갤버즈, 노이즈캔슬링 |
| 카메라/영상 | 소니, 캐논, 미러리스, 4k |
| 성능/벤치마크 | 벤치마크, 스냅드래곤, 쾌적 |
| 가격/가성비 | 가성비, 할인, 출시가 |
| 디스플레이/디자인 | amoled, oled, 베젤 |

### Database Layer (`backend/app/database.py`)

Supabase 클라이언트를 lazy initialization으로 관리합니다. `DB_ENABLED=false`이면 DB 관련 코드가 완전히 비활성화되어 로컬 개발 시 DB 없이 실행 가능합니다.

```python
save_analysis_run(metadata, keywords, videos)  # analysis_runs + keywords + videos[:20]
get_trend_comparison(region, weeks)             # 최근 N회 실행 비교
get_trend_history(keyword, limit)              # 키워드별 시계열 이력
```

---

## 9. 미들웨어 및 캐시

### 미들웨어 스택 (순서)

```
요청 수신
  → Rate Limiter (slowapi)         : IP 기반 요청 수 제한
  → Request Logger (middleware)    : 메서드, 경로, 상태코드, 소요시간 기록
  → GZip (GZipMiddleware)          : 응답 ≥1KB 자동 압축
  → CORS (CORSMiddleware)          : 허용 오리진 설정
  → 라우트 핸들러
응답 반환
```

### In-Memory 캐시

```python
_cache: dict[str, tuple[datetime, AnalysisResult]] = {}
# key: "7:all:10"
# value: (cached_at, result)
# TTL: config.CACHE_TTL_SECONDS (기본 300초)
```

YouTube API 할당량 보호가 주목적입니다. 캐시 히트 시 YouTube API 호출을 완전히 생략합니다.

### Rate Limiting

| 엔드포인트 | 제한 |
|------------|------|
| `GET /api/analyze` | 10 req/min |
| 그 외 모든 엔드포인트 | 30 req/min |

---

## 10. 배포 구조

```
GitHub (main branch push)
  └→ Vercel CI/CD
       ├→ Frontend: Next.js 빌드 → CDN 배포
       └→ Backend: FastAPI → Vercel Serverless Functions (예정)
            ※ 현재 로컬/별도 서버에서 uvicorn 실행
```

**환경변수:**

| 변수 | 위치 | 설명 |
|------|------|------|
| `YOUTUBE_API_KEY` | Backend `.env` | YouTube Data API v3 키 |
| `SUPABASE_URL` | Backend `.env` | Supabase 프로젝트 URL |
| `SUPABASE_KEY` | Backend `.env` | Supabase anon key |
| `DB_ENABLED` | Backend `.env` | `true` / `false` (기본 false) |
| `CORS_ORIGINS` | Backend `.env` | 허용 프론트엔드 URL |
| `CACHE_TTL_SECONDS` | Backend `.env` | 캐시 TTL (기본 300) |
| `NEXT_PUBLIC_API_URL` | Frontend `.env.local` | 백엔드 베이스 URL |

---

## 11. 개발 환경 설정

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env         # YOUTUBE_API_KEY 입력
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev                     # http://localhost:3000
```

### 테스트

```bash
# Backend
cd backend
pytest tests/ -v

# API 헬스 체크
curl http://localhost:8000/api/health
```

---

*최종 업데이트: 2026-03-20 | TechPulse v1.0*
