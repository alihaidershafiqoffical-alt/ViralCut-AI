# ViralCut — Project Rules

## Identity
- **Project**: ViralCut — AI Shorts Generator
- **Purpose**: Converts long videos/URLs into vertical 9:16 Shorts using AI
- **Role**: You are a Senior Full-Stack Architect. Follow the project blueprint strictly.

## Architecture Rules (NON-NEGOTIABLE)
1. **NO user accounts, NO auth, NO permanent storage.** The app is fully ephemeral.
2. **Infrastructure**: Next.js frontend (Vercel) + Python/FastAPI backend (VPS) + Celery/Redis for background jobs + Cloudflare R2 for temporary storage.
3. **Files auto-delete after 24 hours.** No data persistence beyond the R2 lifecycle policy.

## Code Quality Rules
- Write **clean, modular, production-ready, and highly commented** code.
- All code must be TypeScript (frontend) or Python with type hints (backend).
- Use proper error handling, input validation, and logging everywhere.

## SEO Rules (Frontend)
- SEO must be **flawless**. Use Next.js App Router with:
  - Dynamic `metadata` exports on every page
  - JSON-LD structured data schema
  - Semantic HTML5 (`<main>`, `<article>`, `<section>`, `<h1>` hierarchy)
  - Perfect Core Web Vitals (LCP, CLS, FID)
  - Proper `<title>`, `<meta description>`, Open Graph, and Twitter Card tags

## Tech Stack (DO NOT DEVIATE)
| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| Video Processing | FFmpeg, FFprobe |
| AI - Speech-to-Text | Faster-Whisper |
| AI - Content Analysis | Google Gemini API |
| Task Queue | Celery + Redis |
| Temp Storage | Cloudflare R2 (S3-compatible) |

## The Pipeline
1. User uploads video (Direct-to-R2 via presigned URL) or pastes a supported link
2. Frontend polls FastAPI for task status
3. FastAPI triggers Celery worker
4. Worker: Download video → Extract audio (FFmpeg) → Transcribe (Faster-Whisper) → Send transcript to Gemini API to find most viral segments
5. Worker: FFmpeg cuts video, crops to 9:16 vertical, burns custom animated subtitles (.ass format)
6. Upload final Shorts to R2. User previews/downloads. Files auto-delete after 24h.

## Build Phases (7 Phases, ~50 Steps)
- **Phase 1**: Foundation & Configuration (Next.js, FastAPI, R2, Redis setup)
- **Phase 2**: Frontend MVP UI (Hero section, direct uploads, polling, error states)
- **Phase 3**: Video Intake (FFprobe metadata, Celery download task)
- **Phase 4**: AI Pipeline (Whisper STT, Gemini JSON extraction, Subtitle mapping)
- **Phase 5**: Video Processing (FFmpeg cropping, trimming, subtitle burning)
- **Phase 6**: Basic Editor & Playback UI (Trim, Font/Style selection, Re-render)
- **Phase 7**: Polish & SEO (Zip downloads, Auto-delete lifecycles, CI/CD, Advanced SEO metadata)

## Monorepo Structure
```
viralcut-monorepo/
├── frontend/          # Next.js (Vercel)
│   ├── src/
│   │   ├── app/       # App Router pages, layouts, API routes
│   │   ├── components/# Reusable UI (Tailwind, Radix/Shadcn)
│   │   ├── hooks/     # Custom React hooks (usePolling, etc.)
│   │   ├── lib/       # Utilities (axios, formatters)
│   │   └── types/     # TypeScript interfaces
│   └── public/        # Static assets
│
├── backend/           # FastAPI + Celery (VPS)
│   ├── app/
│   │   ├── api/       # API Routers
│   │   ├── core/      # Config, settings, security, Redis client
│   │   ├── models/    # Pydantic schemas
│   │   ├── services/  # Business logic (R2, Gemini wrappers)
│   │   └── main.py    # FastAPI entry point
│   ├── worker/
│   │   ├── tasks.py   # Celery task definitions
│   │   ├── pipeline.py# Orchestration
│   │   ├── ml/        # Faster-Whisper inference
│   │   └── video/     # FFmpeg/FFprobe wrappers
│   ├── requirements.txt
│   └── celery_app.py
│
├── docker-compose.yml # Local dev (Redis, FastAPI, Celery worker)
└── .github/           # CI/CD workflows
```

## Preview Instructions
Whenever generating or updating Next.js code:
1. Always include the exact terminal command to run the dev server (e.g., `npm run dev`).
2. Provide a clickable localhost link (e.g., [http://localhost:3000](http://localhost:3000)) at the end of the response.
3. Ensure the code is structured so that it runs flawlessly on the local dev server without immediate crashes.
