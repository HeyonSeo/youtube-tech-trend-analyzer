# TechPulse 문제 해결 가이드

개발 및 운영 중 발생할 수 있는 일반적인 문제와 해결 방법을 정리합니다.

## 목차

- [YouTube API 관련](#youtube-api-관련)
- [CORS 관련](#cors-관련)
- [Supabase 관련](#supabase-관련)
- [빌드/배포 관련](#빌드배포-관련)
- [개발 환경 설정](#개발-환경-설정)
- [캐시 관련](#캐시-관련)
- [이메일 리포트 관련](#이메일-리포트-관련)

---

## YouTube API 관련

### Q: `502 YouTube API Error — quotaExceeded` 오류가 발생합니다

YouTube Data API v3는 일일 쿼터 제한이 있습니다 (기본 10,000 units/day).

**해결 방법:**

1. [Google Cloud Console > APIs & Services > Dashboard](https://console.cloud.google.com/apis/dashboard)에서 현재 쿼터 사용량을 확인합니다.
2. 쿼터가 소진된 경우, 태평양 시간(PT) 자정에 리셋됩니다.
3. 캐시 TTL을 늘려 API 호출 빈도를 줄입니다:
   ```bash
   CACHE_TTL_SECONDS=21600  # 6시간
   ```
4. 장기적으로 [쿼터 증가 요청](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)을 제출합니다.

**쿼터 소비 참고:**

| API 호출 | 비용 (units) |
|----------|-------------|
| search.list | 100 |
| videos.list | 1 |

한 번의 전체 분석(`/api/analyze`)은 대략 1,000~1,200 units를 소비합니다.

---

### Q: `YOUTUBE_API_KEY`를 설정했는데 `403 Forbidden` 오류가 발생합니다

**확인 사항:**

1. API 키가 올바른지 확인합니다 (앞뒤 공백, 줄바꿈 주의).
2. Google Cloud Console에서 YouTube Data API v3가 **활성화**되어 있는지 확인합니다.
3. API 키에 IP 제한이 걸려 있다면 서버 IP를 허용 목록에 추가합니다.
4. 프로젝트의 결제 계정이 활성 상태인지 확인합니다.

---

### Q: 분석 결과에 영상이 0개로 나옵니다

**확인 사항:**

1. `period_days`가 너무 작지 않은지 확인합니다 (1일은 결과가 적을 수 있음).
2. `region=kr`이면 한국어 영상만, `region=global`이면 영어 영상만 검색됩니다. `region=all`을 사용해 보세요.
3. 네트워크 연결 상태를 확인합니다.
4. `YOUTUBE_API_TIMEOUT` 값을 늘려봅니다 (기본 15초):
   ```bash
   YOUTUBE_API_TIMEOUT=30
   ```

---

## CORS 관련

### Q: 프론트엔드에서 `CORS error: No 'Access-Control-Allow-Origin'` 오류가 발생합니다

**해결 방법:**

1. Backend의 `CORS_ORIGINS`에 프론트엔드 URL이 포함되어 있는지 확인합니다:
   ```bash
   # 개발 환경
   CORS_ORIGINS=http://localhost:3000

   # 프로덕션 — 여러 오리진은 쉼표로 구분
   CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
   ```

2. URL 끝에 슬래시(`/`)가 없어야 합니다:
   ```bash
   # 올바름
   CORS_ORIGINS=http://localhost:3000

   # 잘못됨
   CORS_ORIGINS=http://localhost:3000/
   ```

3. 프로토콜(`http` vs `https`)과 포트 번호가 정확히 일치하는지 확인합니다.

4. Backend를 재시작합니다 (환경변수 변경 후 서버 재시작 필요).

---

### Q: Vercel 배포 후 API 호출이 실패합니다

**확인 사항:**

1. `NEXT_PUBLIC_API_URL`이 배포된 Backend URL로 설정되어 있는지 확인합니다.
2. Backend의 `CORS_ORIGINS`에 Vercel 도메인이 포함되어 있는지 확인합니다.
3. Vercel의 Preview 배포는 URL이 매번 바뀝니다. 와일드카드가 필요하면 Backend CORS 설정을 조정합니다.

---

## Supabase 관련

### Q: 트렌드 데이터가 저장되지 않습니다

**확인 사항:**

1. `SUPABASE_URL`과 `SUPABASE_KEY`가 모두 설정되어 있는지 확인합니다.
2. Supabase 대시보드에서 테이블이 생성되어 있는지 확인합니다:
   - `analysis_runs`
   - `keywords`
   - `videos`
   - `trend_snapshots`
3. RLS (Row Level Security) 정책이 `INSERT`, `SELECT`를 허용하는지 확인합니다.
4. Backend 로그에서 `Failed to save to database` 오류를 확인합니다.

---

### Q: `트렌드 데이터가 부족합니다` 메시지가 표시됩니다

이 메시지는 정상입니다. 트렌드 비교를 위해 최소 2회의 분석 실행이 필요합니다.

**해결 방법:**

1. `/api/analyze`를 2회 이상 실행합니다 (다른 시간대에).
2. 동일한 `region` 설정으로 분석해야 비교가 가능합니다.

---

### Q: Supabase 연결 타임아웃이 발생합니다

**해결 방법:**

1. Supabase 프로젝트가 일시 중지(paused) 상태가 아닌지 확인합니다 (무료 플랜은 1주일 비활성 시 자동 일시 중지).
2. `SUPABASE_URL`이 올바른 형식인지 확인합니다: `https://your-project-id.supabase.co`
3. Supabase 대시보드에서 프로젝트 상태를 확인합니다.

---

## 빌드/배포 관련

### Q: Backend `pip install` 중 패키지 설치 실패

**해결 방법:**

1. Python 3.11 이상인지 확인합니다:
   ```bash
   python --version
   ```
2. 가상 환경을 새로 만듭니다:
   ```bash
   cd backend
   rm -rf venv
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. `openpyxl` 설치 오류 시 C 컴파일러가 필요할 수 있습니다 (특히 Linux).

---

### Q: Frontend `npm install` 중 오류 발생

**해결 방법:**

1. Node.js 18 이상인지 확인합니다:
   ```bash
   node --version
   ```
2. 캐시를 정리하고 재설치합니다:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

---

### Q: Frontend 빌드 시 타입 오류 발생

**해결 방법:**

1. `NEXT_PUBLIC_API_URL`이 `.env.local`에 설정되어 있는지 확인합니다.
2. 타입 정의가 최신인지 확인합니다:
   ```bash
   cd frontend
   npx tsc --noEmit
   ```

---

### Q: Vercel 배포가 실패합니다

**확인 사항:**

1. Vercel Dashboard > Settings > Environment Variables에 모든 필수 환경변수가 설정되어 있는지 확인합니다.
2. Build 로그에서 구체적인 오류 메시지를 확인합니다.
3. `next.config.mjs`의 rewrites 설정에서 Backend URL이 올바른지 확인합니다.

---

## 개발 환경 설정

### Q: Backend 실행 시 `ModuleNotFoundError` 발생

**해결 방법:**

1. 가상 환경이 활성화되어 있는지 확인합니다:
   ```bash
   # 활성화 확인 (프롬프트에 (venv) 표시)
   which python  # 또는 Windows: where python
   ```
2. `backend/` 디렉토리에서 실행하고 있는지 확인합니다:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

---

### Q: `uvicorn`이 설치되어 있지 않다고 나옵니다

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

### Q: Frontend에서 API 호출 시 `ERR_CONNECTION_REFUSED`

**확인 사항:**

1. Backend가 실행 중인지 확인합니다 (`http://localhost:8000/api/health`).
2. `NEXT_PUBLIC_API_URL`이 `http://localhost:8000`으로 설정되어 있는지 확인합니다.
3. Backend의 포트 번호가 8000인지 확인합니다.

---

## 캐시 관련

### Q: 분석 결과가 업데이트되지 않습니다

분석 결과는 `CACHE_TTL_SECONDS` (기본 3600초 = 1시간) 동안 캐시됩니다.

**해결 방법:**

1. 캐시를 수동으로 초기화합니다:
   ```bash
   curl -X POST http://localhost:8000/api/cache/clear
   ```
2. 또는 대시보드의 설정 페이지에서 캐시 초기화를 클릭합니다.
3. 개발 중에는 캐시를 비활성화할 수 있습니다:
   ```bash
   CACHE_TTL_SECONDS=0
   ```

---

### Q: 메모리 사용량이 계속 증가합니다

인메모리 캐시를 사용하므로, 다양한 파라미터 조합으로 분석 시 메모리가 증가할 수 있습니다.

**해결 방법:**

1. 주기적으로 캐시를 초기화합니다.
2. `CACHE_TTL_SECONDS` 값을 줄여 캐시가 자동으로 만료되게 합니다.

---

## 이메일 리포트 관련

### Q: 이메일 발송 시 `503` 오류가 발생합니다

**확인 사항:**

1. `RESEND_API_KEY`가 설정되어 있는지 확인합니다.
2. Resend 대시보드에서 API 키가 유효한지 확인합니다.
3. `REPORT_FROM_EMAIL`의 도메인이 Resend에서 인증되어 있는지 확인합니다.
4. Resend 무료 플랜의 일일 발송 한도(100통/일)를 초과하지 않았는지 확인합니다.

---

### Q: 이메일이 스팸함으로 들어갑니다

**해결 방법:**

1. Resend에서 커스텀 도메인을 설정하고 DNS 레코드(SPF, DKIM, DMARC)를 추가합니다.
2. `REPORT_FROM_EMAIL`을 인증된 도메인의 주소로 설정합니다.

---

## 도움이 필요하신가요?

위 가이드로 해결되지 않는 문제가 있다면:

1. Backend 로그를 확인합니다 (`LOG_LEVEL=DEBUG`로 상세 로그 활성화).
2. Browser DevTools > Network 탭에서 API 요청/응답을 확인합니다.
3. GitHub Issues에 문제를 보고합니다.
