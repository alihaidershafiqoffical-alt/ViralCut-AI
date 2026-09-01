# Local Development Guide

This guide walks you through setting up and running the complete **ViralCut** development environment on your local machine.

---

## Prerequisites

Before starting, ensure you have the following installed:

1. **Node.js**: v18.17+ or v20+ (`node --version`)
2. **Python**: v3.10+ or v3.11+ (`python --version`)
3. **FFmpeg & FFprobe**: Required for audio extraction, video cropping, and subtitle burning (`ffmpeg -version`)
   - *Windows*: Install via Winget `winget install Gyan.FFmpeg` or download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add to PATH.
   - *macOS*: `brew install ffmpeg`
   - *Linux*: `sudo apt-get install -y ffmpeg`
4. **Redis**: Redis 6.0+ server (`redis-cli ping`)
   - *Docker*: `docker run -d -p 6379:6379 --name redis redis:alpine`
   - *Windows WSL / Native*: `wsl redis-server` or Memurai / Redis Windows port.
5. **Google Gemini API Key**: Free tier or paid API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

---

## Quick Start Option 1: Docker Compose (Recommended)

Run the backend, Redis, and Celery worker inside isolated containers:

```bash
# 1. Create .env from the master template
cp .env.example .env
# Edit .env and paste your GEMINI_API_KEY

# 2. Launch Redis, Backend API, and Celery Worker:
docker-compose up --build

# 3. In another terminal, start the Next.js frontend:
cd frontend
npm install
npm run dev
```

- **Frontend App**: `http://localhost:3000`
- **FastAPI Backend**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`

---

## Quick Start Option 2: 4-Terminal Manual Setup

### Step 1: Configure Environment Files
Copy the environment examples:

```powershell
# In the repository root:
cp .env.example .env

# In frontend:
cp frontend/.env.example frontend/.env.local

# In backend:
cp backend/.env.example backend/.env
```

Open `backend/.env` and enter your `GEMINI_API_KEY=AIzaSy...`.

---

### Step 2: Open 4 Terminals

#### Terminal 1: Redis Server
Start your local Redis instance:
```powershell
# Via Docker:
docker run -p 6379:6379 --rm --name local-redis redis:alpine

# Or if installed natively on Windows/Linux:
redis-server
```

#### Terminal 2: FastAPI Backend API
```powershell
cd "d:\Viral Cut\backend"

# Create and activate virtual environment (if not already created)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt

# Start the FastAPI server
python run.py
```
> FastAPI will start at `http://localhost:8000` with Swagger UI at `http://localhost:8000/docs`.

#### Terminal 3: Celery Background Worker & AI Pipeline
```powershell
cd "d:\Viral Cut\backend"

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# Run the Celery worker process
celery -A app.core.celery_app worker --loglevel=info --concurrency=2
```
> On Windows, if Celery pool errors occur, add `--pool=solo`:  
> `celery -A app.core.celery_app worker --loglevel=info --pool=solo`

#### Terminal 4: Next.js Frontend
```powershell
cd "d:\Viral Cut\frontend"

# Install node dependencies
npm install

# Start Next.js development server
npm run dev
```
> The web interface will open at `http://localhost:3000`.

---

## Verifying Local Setup

1. Open `http://localhost:3000` in your web browser.
2. In the hero section, enter a YouTube URL or upload a short MP4 test video.
3. Click **Generate Viral Shorts**.
4. Observe the 9-stage progress tracker:
   - Stage 1: Uploading / Ingestion
   - Stage 2: Video validation
   - Stage 3: Audio extraction (FFmpeg)
   - Stage 4: Transcription (Faster-Whisper)
   - Stage 5: AI analysis (Gemini 1.5 Flash)
   - Stage 6: Clip selection
   - Stage 7: 9:16 Crop generation (FFmpeg)
   - Stage 8: Kinetic karaoke subtitles burn-in
   - Stage 9: Finalizing & ZIP bundling
5. Preview the generated vertical Shorts and download individual clips or the complete `.zip` archive.
