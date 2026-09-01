# ViralCut Production Deployment Guide

This guide details how to deploy each component of the ViralCut monorepo to production from a single GitHub repository.

---

## Deployment Architecture Overview

```
GitHub Repository: [username]/ViralCut
 │
 ├── Root Directory: frontend/  ─────────► Vercel (Frontend Web UI)
 │
 ├── Root Directory: backend/   ─────────► Render / Railway Web Service (FastAPI API)
 │
 ├── Root Directory: . or agent/ ────────► Render / Railway Background Worker (Celery + FFmpeg + Whisper)
 │
 └── External Cloud Services:
      ├── Redis (Upstash / Redis Cloud) ──► Message Broker & Rate Limiting
      ├── Google Gemini AI API ──────────► Viral Intelligence Scoring
      └── Cloudflare R2 ─────────────────► Object Storage for Rendered Shorts
```

---

## 1. Frontend Deployment (Vercel)

1. Connect your GitHub repository in the [Vercel Dashboard](https://vercel.com).
2. Configure project settings:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (or Next.js default)
   - **Install Command**: `npm install`
   - **Output Directory**: `.next`
3. Add Environment Variables:
   - `NEXT_PUBLIC_API_URL`: URL of your deployed backend (e.g. `https://api.viralcut.ai` or `https://viralcut-backend.onrender.com`).
4. Click **Deploy**.

---

## 2. Redis Cloud Setup

ViralCut requires a Redis instance for Celery task queuing and job state tracking.

1. Create a free/paid managed Redis database at [Upstash](https://upstash.com) or [Redis Cloud](https://redis.io/cloud/).
2. Copy your connection URL (format: `rediss://default:YOUR_PASSWORD@your-redis-host:6379/0`).
3. Note this URL for configuring both the Backend API and the Background Worker.

---

## 3. Backend API Deployment (Render / Railway / VPS)

### Option A: Render (Web Service)
1. In Render, select **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure settings:
   - **Name**: `viralcut-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables:
   - `PROJECT_NAME`: `ViralCut Backend`
   - `API_V1_STR`: `/api/v1`
   - `REDIS_URL`: `<Your Redis Connection URL>`
   - `CELERY_BROKER_URL`: `<Your Redis Connection URL>`
   - `CELERY_RESULT_BACKEND`: `<Your Redis Connection URL>`
   - `GEMINI_API_KEY`: `<Your Google Gemini API Key>`
   - `GEMINI_MODEL`: `gemini-1.5-flash`
   - `ALLOWED_CORS_ORIGINS`: `["https://your-vercel-app.vercel.app","https://viralcut.ai"]`
   - `TEMP_STORAGE_DIR`: `/tmp/temp_uploads`

---

## 4. Background Worker Deployment (Render / Railway / Docker)

The worker executes FFmpeg transformations, Faster-Whisper, and Gemini AI tasks.

### Option A: Docker Deployment on Render / Railway
Because the worker requires `ffmpeg` and `ffprobe` system packages, Docker deployment is the most reliable:

1. Create a **New Background Worker** in Render or **New Service** in Railway.
2. Select **Docker** environment.
3. Configure settings:
   - **Dockerfile Path**: `agent/Dockerfile`
   - **Docker Context**: `.`
4. Add Environment Variables:
   - `REDIS_URL`: `<Your Redis Connection URL>`
   - `CELERY_BROKER_URL`: `<Your Redis Connection URL>`
   - `CELERY_RESULT_BACKEND`: `<Your Redis Connection URL>`
   - `GEMINI_API_KEY`: `<Your Google Gemini API Key>`
   - `GEMINI_MODEL`: `gemini-1.5-flash`
   - `WHISPER_MODEL_SIZE`: `base`
   - `WHISPER_DEVICE`: `cpu` (or `cuda` if using GPU instance)
   - `WORKER_TASK_TIME_LIMIT_SECONDS`: `600`
   - `TEMP_STORAGE_DIR`: `/tmp/temp_uploads`

---

## 5. Cloudflare R2 Storage (Optional / Production Scale)

To store rendered videos persistently or serve high-bandwidth video downloads:

1. Create a Bucket in [Cloudflare R2](https://dash.cloudflare.com): `viralcut-storage`.
2. Generate an API token with read/write permissions for R2.
3. Add the following variables to Backend & Worker:
   - `CLOUDFLARE_ACCOUNT_ID`: Your Cloudflare Account ID
   - `R2_ACCESS_KEY_ID`: R2 Access Key
   - `R2_SECRET_ACCESS_KEY`: R2 Secret Key
   - `R2_BUCKET_NAME`: `viralcut-storage`
   - `R2_ENDPOINT_URL`: `https://<account_id>.r2.cloudflarestorage.com`
   - `R2_PUBLIC_DOMAIN`: `https://pub-viralcut.r2.dev` (or your custom domain)

---

## 6. Pre-Launch Production Checklist

- [ ] Vercel frontend builds and renders properly without runtime errors.
- [ ] CORS on the backend explicitly allows your production frontend domain.
- [ ] Redis broker connection string uses TLS (`rediss://`) for secure cloud Redis instances.
- [ ] Worker container has FFmpeg and font libraries installed.
- [ ] Google Gemini API key is valid and has sufficient quota.
- [ ] No secrets or real `.env` files are tracked in the Git repository.
- [ ] 24-hour cleanup cron/service is enabled for temporary storage disks.
