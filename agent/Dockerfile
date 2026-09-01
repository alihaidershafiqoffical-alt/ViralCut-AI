# =============================================================================
# ViralCut AI Background Worker — Production Dockerfile
# Includes FFmpeg, FFprobe, FreeType font rendering, Faster-Whisper, and Celery
# =============================================================================

FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies: FFmpeg, FFprobe, libass, fonts, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-freefont-ttf \
    fonts-dejavu-core \
    fontconfig \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY agent/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend /app/backend
COPY agent /app/agent

# Set working directory to backend root so Celery module paths resolve cleanly
WORKDIR /app/backend

# Create temporary upload & processing storage directory
RUN mkdir -p /app/backend/temp_uploads

# Run Celery worker
CMD ["celery", "-A", "app.core.celery_app", "worker", "--loglevel=info", "--concurrency=2", "-n", "viralcut_worker@%h"]
