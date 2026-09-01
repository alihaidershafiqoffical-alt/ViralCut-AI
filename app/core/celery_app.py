"""
app/core/celery_app.py
----------------------
Celery instance configuration with resource exhaustion protections:
- Worker soft & hard time limits
- Worker process recycling (max tasks & max memory per child)
- Fair prefetch queue distribution
"""

from __future__ import annotations

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "viralcut_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    imports=["app.tasks"],
    # ── Resource Exhaustion Protections ─────────────────────────────────────────
    task_time_limit=settings.WORKER_TASK_TIME_LIMIT_SECONDS,           # 600s hard kill
    task_soft_time_limit=settings.WORKER_TASK_SOFT_TIME_LIMIT_SECONDS, # 540s soft timeout
    worker_max_tasks_per_child=20,                                     # Recycle worker process to prevent PyTorch/FFmpeg memory leaks
    worker_max_memory_per_child=500_000,                               # 500 MB memory threshold per worker child
    worker_prefetch_multiplier=1,                                      # Fair queue distribution preventing queue starvation
    task_acks_late=True,                                               # Ack after execution completes
    task_reject_on_worker_lost=True                                    # Requeue or reject if worker process drops
)
