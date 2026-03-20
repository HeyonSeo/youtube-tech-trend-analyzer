# TechPulse 환경변수 설정 가이드

이 문서는 TechPulse 프로젝트의 모든 환경변수를 설명합니다.

## 목차

- [Backend 환경변수](#backend-환경변수)
- [Frontend 환경변수](#frontend-환경변수)
- [환경별 설정 파일](#환경별-설정-파일)
- [설정 예시](#설정-예시)

---

## Backend 환경변수

설정 파일: `backend/.env` (개발) / `backend/.env.production.local` (프로덕션)

### YouTube API

| 변수 | 필수 | 기본값 | 설명 |
|-----|------|--------|------|
| `YOUTUBE_API_KEY` | **필수** | _(없음)_ | YouTube Data API v3 키. [Google Cloud Console](https://console.cloud.google.com/)에서 발급. |
| `YOUTUBE_API_TIMEOUT` | 선택 | `15` | YouTube API 요청 타임아웃 (초). |

### 데이터베이스 (Supabase)

| 변수 | 필수 | 기본값 | 설명 |
|-----|------|--------|------|
| `SUPABASE_URL` | 선택 | `""` | Supabase 프로젝트 URL. 예: `https://your-project.supabase.co` |
| `SUPABASE_KEY` | 선택 | `""` | Supabase anon key. |
| `DB_ENABLED` | 자동 | _(자동 산출)_ | `SUPABASE_URL`과 `SUPABASE_KEY`가 모두 설정되면 자동으로 `true`. 직접 설정 불필요. |

> 트렌드 추적 기능(주간 순위 변동 비교)을 사용하려면 Supabase 연결이 필요합니다.

### 이메일 (Resend)

| 변수 | 필수 | 기본값 | 설명 |
|-----|------|--------|------|
| `RESEND_API_KEY` | 선택 | `""` | [Resend](https://resend.com/) API 키. 이메일 리포트 기능에 필요. |
| `REPORT_FROM_EMAIL` | 선택 | `noreply@techpulse.app` | 리포트 발신자 이메일 주소. Resend에서 인증된 도메인 필요. |
| `EMAIL_ENABLED` | 자동 | _(자동 산출)_ | `RESEND_API_KEY`가 설정되면 자동으로 `true`. 직접 설정 불필요. |

### 서버 설정

| 변수 | 필수 | 기본값 | 설명 |
|-----|------|--------|------|
| `CORS_ORIGINS` | 선택 | `http://localhost:3000` | 허용된 CORS 오리진. 쉼표로 구분. 예: `https://app.vercel.app,http://localhost:3000` |
| `LOG_LEVEL` | 선택 | `INFO` | 로그 레벨. `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `CACHE_TTL_SECONDS` | 선택 | `3600` | 분석 결과 캐시 유지 시간 (초). 기본 1시간. |

### 검색 쿼리 커스터마이징

| 변수 | 필수 | 기본값 | 설명 |
|-----|------|--------|------|
| `CUSTOM_QUERIES_FILE` | 선택 | `""` | 커스텀 검색 쿼리 JSON 파일 경로. |

커스텀 검색 쿼리 JSON 형식:

```json
{
  "kr": ["테크 리뷰", "IT 리뷰", "가젯 리뷰"],
  "en": ["tech review", "gadget review", "best tech"]
}
```

---

## Frontend 환경변수

설정 파일: `frontend/.env.local` (개발) / Vercel Dashboard (프로덕션)

### API 연결

| 변수 | 필수 | 기본값 | 설명 |
|-----|------|--------|------|
| `NEXT_PUBLIC_API_URL` | **필수** | _(없음)_ | Backend API URL. 개발: `http://localhost:8000`, 프로덕션: 배포된 백엔드 URL. |
| `BACKEND_URL` | 선택 | _(없음)_ | 서버 사이드 요청 및 Vercel rewrites용 백엔드 URL. 프로덕션에서 사용. |

### 인증 (NextAuth.js)

| 변수 | 필수 | 기본값 | 설명 |
|-----|------|--------|------|
| `NEXTAUTH_SECRET` | **필수*** | _(없음)_ | JWT 서명 시크릿. `openssl rand -base64 32`로 생성. |
| `NEXTAUTH_URL` | **필수*** | _(없음)_ | 프론트엔드 정규 URL. 개발: `http://localhost:3000`, 프로덕션: `https://your-app.vercel.app` |
| `GOOGLE_CLIENT_ID` | 선택 | _(없음)_ | Google OAuth 클라이언트 ID. [Google Cloud Console](https://console.cloud.google.com/)에서 발급. |
| `GOOGLE_CLIENT_SECRET` | 선택 | _(없음)_ | Google OAuth 클라이언트 시크릿. |

> *인증 기능을 사용하는 경우에만 필수

### 스케줄링

| 변수 | 필수 | 기본값 | 설명 |
|-----|------|--------|------|
| `CRON_SECRET` | 권장 | _(없음)_ | Vercel Cron Job의 `/api/cron/analyze` 엔드포인트 보호용 시크릿. `openssl rand -hex 32`로 생성. |

---

## 환경별 설정 파일

```
youtube-tech-trend-analyzer/
├── .env.example                     # 루트 환경변수 예시 (최소)
├── backend/
│   ├── .env.example                 # Backend 개발 환경변수 예시
│   └── .env.production.example      # Backend 프로덕션 환경변수 예시
└── frontend/
    ├── .env.local.example           # Frontend 개발 환경변수 예시
    └── .env.production.example      # Frontend 프로덕션 환경변수 예시
```

### 개발 환경 (최소 설정)

```bash
# backend/.env
YOUTUBE_API_KEY=your_youtube_api_key

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 프로덕션 환경 (전체 설정)

```bash
# backend 환경변수 (Railway/Render Dashboard)
YOUTUBE_API_KEY=your_youtube_api_key
CORS_ORIGINS=https://your-app.vercel.app
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
RESEND_API_KEY=re_your_resend_api_key
REPORT_FROM_EMAIL=noreply@yourdomain.com
LOG_LEVEL=INFO
CACHE_TTL_SECONDS=3600
YOUTUBE_API_TIMEOUT=15

# frontend 환경변수 (Vercel Dashboard)
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
BACKEND_URL=https://your-backend.up.railway.app
NEXTAUTH_SECRET=your_generated_secret
NEXTAUTH_URL=https://your-app.vercel.app
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
CRON_SECRET=your_cron_secret
```

---

## 설정 예시

### 1. 기본 개발 환경 (API 분석만)

```bash
# backend/.env
YOUTUBE_API_KEY=AIzaSy...

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. 트렌드 추적 포함

```bash
# backend/.env
YOUTUBE_API_KEY=AIzaSy...
SUPABASE_URL=https://abc123.supabase.co
SUPABASE_KEY=eyJhbGciOi...
```

### 3. 이메일 리포트 포함

```bash
# backend/.env
YOUTUBE_API_KEY=AIzaSy...
RESEND_API_KEY=re_abc123...
REPORT_FROM_EMAIL=reports@yourdomain.com
```

### 4. 캐시 조정

```bash
# 캐시 비활성화 (매 요청마다 API 호출, 개발 시)
CACHE_TTL_SECONDS=0

# 캐시를 6시간으로 설정 (API 쿼터 절약)
CACHE_TTL_SECONDS=21600
```
