# ViralCut Background Worker & AI Processing Engine

The **Agent/Worker** is responsible for executing all compute-heavy, asynchronous video processing pipelines in ViralCut.

---

## Capabilities & Responsibilities

1. **Audio Extraction**: Isolating audio streams with FFmpeg.
2. **AI Transcription**: Generating word-level timestamped transcripts using **Faster-Whisper**.
3. **Viral Moment Selection**: Prompting **Google Gemini 1.5 Flash** with normalized transcripts to identify high-retention segments (hooks, value points, CTAs).
4. **Karaoke Subtitle Generation**: Creating ASS subtitle files with kinetic word-by-word highlight effects.
5. **Smart 9:16 Video Transformation**: Cropping and trimming video clips to vertical formats using FFmpeg.
6. **Hardcoded Subtitle Burning & Encoding**: Encoding H.264/AAC MP4 clips optimized for social media platforms (TikTok, YouTube Shorts, Instagram Reels).
7. **ZIP Packaging & Cleanup**: Creating zip archives and running 24-hour temporary file purge cycles.

---

## Local Development Execution

### Option A: Direct Python Execution
```powershell
# From the project root or backend folder with virtualenv activated:
cd backend
celery -A app.core.celery_app worker --loglevel=info --concurrency=2
```

Or run the agent entrypoint:
```powershell
python ../agent/worker.py
```

### Option B: Docker
```bash
docker build -t viralcut-worker -f agent/Dockerfile .
docker run --env-file .env viralcut-worker
```

---

## Production Worker Configuration

- **Platform**: Render Background Worker, Railway Service, DigitalOcean Droplet, AWS ECS, or bare-metal VPS.
- **Root Directory**: `.` or `agent/`
- **Build Command**: `pip install -r agent/requirements.txt`
- **Start Command**: `celery -A app.core.celery_app worker --loglevel=info -c 2`
- **System Requirements**:
  - `ffmpeg` & `ffprobe` installed in system PATH.
  - Python 3.10+ / 3.11 recommended.
  - Redis 6.0+ instance.
  - FreeType / standard fonts installed for ASS subtitle rendering.
