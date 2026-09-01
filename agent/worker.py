"""
agent/worker.py
---------------
Standalone Celery worker entrypoint for the ViralCut AI Background Processing Engine.
Handles audio extraction, Faster-Whisper STT, Gemini AI viral clipping, ASS karaoke subtitle styling,
FFmpeg 9:16 vertical crop rendering, and zip archiving.
"""

from __future__ import annotations

import sys
import os
import logging

# Ensure the backend directory is in the Python sys.path so modules and tasks can be discovered seamlessly
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.celery_app import celery_app
from app.core.config import settings

# Import tasks to ensure worker registration
import app.tasks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("viralcut.worker")

if __name__ == "__main__":
    logger.info("Initializing ViralCut AI Background Worker...")
    logger.info("Connecting to Redis Broker: %s", settings.CELERY_BROKER_URL)
    logger.info("Gemini Model: %s", settings.GEMINI_MODEL)
    logger.info("Whisper Model Size: %s (device=%s)", settings.WHISPER_MODEL_SIZE, settings.WHISPER_DEVICE)

    # Start Celery worker programmatically
    celery_app.worker_main(
        argv=[
            "worker",
            "--loglevel=info",
            "--concurrency=2",
            "-n", "viralcut_worker@%h"
        ]
    )
