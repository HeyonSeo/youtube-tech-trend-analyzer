# TechPulse Deployment Guide

This guide covers deploying the TechPulse application with:
- **Frontend** (Next.js) on **Vercel**
- **Backend** (FastAPI) on **Railway**

---

## Prerequisites

- GitHub repository with the project code
- [Vercel](https://vercel.com) account (free tier works)
- [Railway](https://railway.app) account (Starter plan or above recommended)
- YouTube Data API v3 key from [Google Cloud Console](https://console.cloud.google.com/)
- (Optional) [Supabase](https://supabase.com) project for data persistence
- (Optional) [Resend](https://resend.com) API key for email reports

---

## 1. Backend Deployment (Railway)

### 1.1 Create a New Railway Project

1. Go to [railway.app](https://railway.app) and sign in.
2. Click **"New Project"** > **"Deploy from GitHub Repo"**.
3. Select your repository and set the **Root Directory** to `backend`.

### 1.2 Configure Environment Variables

In the Railway dashboard, go to your service > **Variables** and add:

| Variable | Required | Description |
|---|---|---|
| `YOUTUBE_API_KEY` | Yes | YouTube Data API v3 key |
| `CORS_ORIGINS` | Yes | Your Vercel frontend URL (e.g., `https://techpulse.vercel.app`) |
| `SUPABASE_URL` | No | Supabase project URL (enables persistence) |
| `SUPABASE_KEY` | No | Supabase anon/service key |
| `RESEND_API_KEY` | No | Resend API key (enables email reports) |
| `REPORT_FROM_EMAIL` | No | Sender email address |
| `LOG_LEVEL` | No | `INFO` (default), `DEBUG`, `WARNING` |
| `CACHE_TTL_SECONDS` | No | Cache TTL in seconds (default: `3600`) |

> Railway automatically provides the `PORT` environment variable. The start command in `railway.json` uses `$PORT`.

### 1.3 Verify Deployment

Once deployed, Railway provides a public URL (e.g., `https://your-backend.up.railway.app`).

Test the health endpoint:

```bash
curl https://your-backend.up.railway.app/api/health
```

Expected response:
```json
{"status": "ok", "cache_entries": 0, "last_analysis_time": null}
```

### 1.4 Custom Domain (Optional)

In Railway > **Settings** > **Networking** > **Custom Domain**, add your domain and configure DNS.

---

## 2. Frontend Deployment (Vercel)

### 2.1 Import Project

1. Go to [vercel.com](https://vercel.com) and sign in.
2. Click **"Add New..."** > **"Project"**.
3. Import your GitHub repository.
4. Set **Root Directory** to `frontend`.
5. Framework Preset will auto-detect **Next.js**.

### 2.2 Configure Environment Variables

In the Vercel dashboard, go to **Settings** > **Environment Variables** and add:

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Yes | Backend Railway URL (e.g., `https://your-backend.up.railway.app`) |
| `BACKEND_URL` | Yes | Same as above (used server-side for rewrites) |
| `NEXTAUTH_SECRET` | Yes | Random secret (`openssl rand -base64 32`) |
| `NEXTAUTH_URL` | Yes | Your Vercel URL (e.g., `https://techpulse.vercel.app`) |
| `GOOGLE_CLIENT_ID` | Yes | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Yes | Google OAuth client secret |
| `CRON_SECRET` | Recommended | Secret to protect the cron endpoint (`openssl rand -hex 32`) |

### 2.3 Build Settings

The `vercel.json` file configures:
- **Build command**: `npm run build`
- **Install command**: `npm ci`
- **Output**: standalone mode (configured in `next.config.mjs`)
- **Region**: `icn1` (Seoul, for lowest latency to Korean users)

### 2.4 API Proxy

The `vercel.json` rewrites configuration proxies `/backend-api/*` requests to the backend. This avoids CORS issues for client-side requests.

Example: A frontend request to `/backend-api/analyze` is proxied to `${BACKEND_URL}/api/analyze`.

### 2.5 Verify Deployment

After deployment, visit your Vercel URL and confirm:
- The dashboard loads correctly
- API calls to the backend succeed (check the keywords/videos pages)

---

## 3. Cron Job (Automated Daily Analysis)

### 3.1 How It Works

Vercel Cron is configured in `vercel.json` to call `/api/cron/analyze` at **21:00 UTC daily** (06:00 KST).

This endpoint triggers the backend's `/api/analyze` for both `kr` and `global` regions, keeping cached data fresh.

### 3.2 Security

The cron endpoint checks for a `CRON_SECRET` bearer token. Vercel automatically includes this header for its own cron invocations when the `CRON_SECRET` environment variable is set.

### 3.3 Monitoring

Check cron execution logs in the Vercel dashboard:
**Project** > **Settings** > **Cron Jobs**

You can also manually test the cron endpoint:
```bash
curl -H "Authorization: Bearer YOUR_CRON_SECRET" \
  https://techpulse.vercel.app/api/cron/analyze
```

---

## 4. Alternative: Backend on Render

If you prefer Render over Railway:

### 4.1 Create a Web Service

1. Go to [render.com](https://render.com) and sign in.
2. Click **"New"** > **"Web Service"**.
3. Connect your GitHub repo, set **Root Directory** to `backend`.

### 4.2 Configure

- **Runtime**: Docker
- **Region**: Singapore or Tokyo (closest to Korean users)
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/api/health`

### 4.3 Environment Variables

Same as the Railway section above.

> Note: Render's free tier spins down after inactivity. Use the Starter plan ($7/mo) for always-on deployments.

---

## 5. Post-Deployment Checklist

- [ ] Backend health check returns `{"status": "ok"}`
- [ ] Frontend loads and displays data
- [ ] Google OAuth login works
- [ ] API proxy (`/backend-api/*`) returns data correctly
- [ ] Cron job appears in Vercel Cron Jobs dashboard
- [ ] CORS is correctly configured (no browser console errors)
- [ ] (Optional) Supabase connection verified — trend data persists
- [ ] (Optional) Email report sends successfully

---

## 6. Troubleshooting

### CORS Errors
Ensure `CORS_ORIGINS` on the backend includes your exact Vercel URL (with `https://`, no trailing slash).

### Cron Not Firing
- Cron jobs only run on the **production** deployment (not preview).
- Verify `CRON_SECRET` is set in Vercel environment variables.
- Check Vercel Functions logs for errors.

### Backend Connection Timeout
- Railway/Render might sleep on free tiers. Upgrade or use the cron job to keep the service warm.
- Increase `YOUTUBE_API_TIMEOUT` if YouTube API calls are slow.

### Build Failures
- Ensure `next.config.mjs` has `output: "standalone"` for Vercel compatibility.
- Check that all dependencies are in `package.json` (not just `devDependencies`).
