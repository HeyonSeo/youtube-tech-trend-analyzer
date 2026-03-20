# TechPulse — YouTube 테크 리뷰 트렌드 분석기

YouTube '테크 리뷰' 영상의 키워드 트렌드와 시청자 관심사를 분석하는 웹 대시보드.

## 주요 기능

- YouTube Data API v3 기반 테크 리뷰 영상 자동 수집 (한국어 + 영어)
- 키워드 TOP 10 추출 및 8개 관심사 카테고리 분류
- 지역별(한국/글로벌/통합) 분석
- CSV/Excel 내보내기
- 반응형 다크 테마 대시보드

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS, Recharts |
| Backend | Python 3.11+, FastAPI, Pydantic |
| API | YouTube Data API v3 |

## 사전 준비

[Google Cloud Console](https://console.cloud.google.com/)에서 YouTube Data API v3를 활성화하고 API 키를 발급받으세요.

## 설치 및 실행

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# .env에 YOUTUBE_API_KEY 입력
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

http://localhost:3000 에서 대시보드에 접속할 수 있습니다.

## 프로젝트 구조

```
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 앱 + API 엔드포인트
│   │   ├── analyzer.py      # 분석 엔진 (TechTrendAnalyzer)
│   │   ├── models.py        # Pydantic 모델
│   │   └── config.py        # 설정 (검색어, 불용어, 카테고리)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/              # Next.js 페이지 (대시보드, 키워드, 영상)
│       ├── components/       # UI 컴포넌트 (차트, 테이블, 버튼)
│       └── lib/api.ts        # API 클라이언트
├── docs/
│   └── PRD.md               # 제품 요구사항 정의서
└── analyzer.py              # CLI 버전 (레거시)
```

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /api/health | 서버 상태 확인 |
| GET | /api/analyze | 전체 분석 실행 |
| GET | /api/keywords | 키워드 TOP N |
| GET | /api/interests | 관심사 카테고리 |
| GET | /api/videos | 조회수 상위 영상 |
| GET | /api/export/csv | CSV 다운로드 |
| GET | /api/export/xlsx | Excel 다운로드 |

## 라이선스

MIT
