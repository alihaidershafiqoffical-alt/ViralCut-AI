---
name: viralcut-phases
description: "Detailed phase-by-phase build plan for ViralCut AI Shorts Generator. Reference this skill when executing any of the 7 build phases."
---

# ViralCut — Phase-by-Phase Build Blueprint

## Phase 1: Foundation & Configuration
**Goal**: Set up all infrastructure, configs, and project scaffolding.

### Steps:
1. **Next.js Frontend Setup** — App Router, TypeScript, Tailwind CSS, Shadcn/UI
2. **FastAPI Backend Setup** — Project structure, CORS, health checks
3. **Redis Configuration** — Connection pooling, task state storage
4. **Celery Configuration** — Worker setup, task routing, result backend
5. **Cloudflare R2 Setup** — Boto3 S3-compatible client, presigned URL generation
6. **Environment Variables** — `.env` files for both frontend and backend
7. **Docker Compose** — Local dev stack (Redis, FastAPI, Celery worker)
8. **Monorepo Root Config** — Root-level scripts, shared configs

---

## Phase 2: Frontend MVP UI
**Goal**: Build the complete user-facing interface with upload and polling.

### Steps:
9. **Landing Page Hero** — Headline, animated background, upload CTA
10. **Direct Upload Flow** — Presigned URL fetch → direct-to-R2 upload with progress bar
11. **URL Paste Input** — Support for YouTube/direct video links
12. **Task Creation API Call** — POST to FastAPI with R2 key or URL
13. **Polling Hook** — `usePolling` for real-time task status updates
14. **Processing Status UI** — Step-by-step progress (Downloading → Transcribing → Analyzing → Rendering)
15. **Error States** — Network errors, invalid files, processing failures
16. **Responsive Design** — Mobile-first, all breakpoints

---

## Phase 3: Video Intake
**Goal**: Backend receives video and extracts metadata.

### Steps:
17. **FastAPI Task Endpoint** — POST `/api/tasks` creates Celery task, returns task ID
18. **Task Status Endpoint** — GET `/api/tasks/{id}` returns current status/progress
19. **Video Download Task** — Celery task to download from R2 or URL to worker temp dir
20. **FFprobe Metadata Extraction** — Duration, resolution, codec, frame rate, file size
21. **Validation** — Reject files >2h, unsupported codecs, audio-only files
22. **Progress Updates** — Write step progress to Redis for polling

---

## Phase 4: AI Pipeline
**Goal**: Transcribe audio and use Gemini to find viral segments.

### Steps:
23. **Audio Extraction** — FFmpeg extracts audio track to WAV/MP3
24. **Faster-Whisper STT** — Transcribe with word-level timestamps
25. **Transcript Formatting** — Structure as `[{word, start, end}]` JSON
26. **Gemini Prompt Engineering** — System prompt for viral segment detection
27. **Gemini API Call** — Send transcript + video context, get back segment timestamps
28. **Segment Validation** — Ensure timestamps are valid, within video bounds
29. **Subtitle Mapping** — Map word timestamps to selected segments for .ass generation
30. **Pipeline Error Handling** — Retry logic, fallback strategies

---

## Phase 5: Video Processing
**Goal**: FFmpeg renders final vertical shorts with subtitles.

### Steps:
31. **Video Trimming** — FFmpeg cuts source to each segment's start/end
32. **9:16 Cropping** — Smart crop (center or face-detect) to vertical
33. **ASS Subtitle Generation** — Generate .ass files with animated word-by-word highlighting
34. **Subtitle Burning** — FFmpeg hardcodes subtitles onto video
35. **Output Encoding** — H.264/AAC, optimized for web playback
36. **Multi-Clip Processing** — Handle multiple clips per source video
37. **R2 Upload** — Upload rendered clips back to R2 with presigned download URLs
38. **Cleanup** — Delete temp files from worker filesystem

---

## Phase 6: Basic Editor & Playback UI
**Goal**: User can preview clips and make basic adjustments.

### Steps:
39. **Video Player Component** — Custom player with clip preview
40. **Clip Selector** — Browse/select from generated clips
41. **Trim Adjustment** — Fine-tune start/end by ±5 seconds
42. **Subtitle Style Picker** — Font family, size, color, position presets
43. **Re-Render Flow** — Send adjustments back to backend for re-processing
44. **Download Individual Clips** — Direct R2 download links

---

## Phase 7: Polish & SEO
**Goal**: Production-ready polish, SEO perfection, deployment.

### Steps:
45. **Zip Download** — Package all clips into single .zip download
46. **R2 Auto-Delete Lifecycle** — 24-hour TTL policy on all objects
47. **JSON-LD Structured Data** — SoftwareApplication + HowTo schema
48. **Advanced SEO Metadata** — Dynamic OG images, Twitter Cards, sitemap.xml, robots.txt
49. **CI/CD Pipeline** — GitHub Actions for frontend (Vercel) and backend (VPS deploy)
50. **Performance Audit** — Lighthouse 100, Core Web Vitals optimization

---

## Key API Contracts

### POST `/api/tasks`
```json
// Request
{ "source_type": "upload" | "url", "source_key": "r2-key-or-url" }

// Response
{ "task_id": "uuid", "status": "pending" }
```

### GET `/api/tasks/{task_id}`
```json
// Response
{
  "task_id": "uuid",
  "status": "pending" | "downloading" | "transcribing" | "analyzing" | "rendering" | "completed" | "failed",
  "progress": 0-100,
  "current_step": "Transcribing audio...",
  "clips": [
    { "id": "clip-1", "title": "...", "duration": 45, "download_url": "...", "preview_url": "..." }
  ],
  "error": null
}
```

### GET `/api/upload/presigned`
```json
// Response
{ "upload_url": "https://r2.../presigned", "object_key": "uploads/uuid.mp4" }
```
