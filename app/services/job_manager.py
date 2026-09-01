"""
app/services/job_manager.py
---------------------------
Job and Task Progress Manager using Redis.
Provides safe retrieval, schema updates, sanitized error management, and progression tracking for background workers.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Dict, Optional, Any, List
from enum import Enum
from redis import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

    # Backward-compatible aliases
    PENDING = "queued"


# Job TTL in seconds (12 hours by default for anonymous users)
DEFAULT_JOB_TTL_SECONDS = 43200

# Global in-memory storage fallback when Redis is offline
_in_memory_jobs: Dict[str, str] = {}


class JobManagerService:
    """
    Manages job states, steps, and progress percentages in Redis safely for anonymous users.
    Falls back to in-memory dictionary storage if Redis is unreachable.
    """

    @classmethod
    def get_redis_client(cls) -> Optional[Redis]:
        """Returns a configured thread-safe Redis client instance or None if unreachable."""
        try:
            client = Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=0.5)
            client.ping()
            return client
        except Exception:
            return None

    @staticmethod
    def sanitize_error(raw_error: Optional[str]) -> Optional[str]:
        """
        Sanitizes error messages to protect internal system paths,
        stack traces, database details, or sensitive server internals.
        """
        if not raw_error:
            return None

        # If it looks like a python traceback or contains file paths, sanitize it
        if "Traceback" in raw_error or "File \"" in raw_error or ".py" in raw_error:
            # Extract only the last exception message if possible
            lines = raw_error.strip().split("\n")
            last_line = lines[-1] if lines else "An error occurred during processing."
            if ":" in last_line:
                raw_error = last_line.split(":", 1)[1].strip()
            else:
                raw_error = last_line

        # Remove local disk paths (Windows and Unix)
        raw_error = re.sub(r"[a-zA-Z]:\\[\w\s\\.-]+", "[internal file]", raw_error)
        raw_error = re.sub(r"/(?:[\w.-]+/)+[\w.-]+", "[internal file]", raw_error)

        # Standard customer-friendly fallback mappings
        lower = raw_error.lower()
        if "timeout" in lower or "timed out" in lower:
            return "The operation timed out while processing your video. Please try again with a shorter clip."
        if "memory" in lower or "oom" in lower:
            return "Video resolution or size exceeded processing memory limits."
        if "not found" in lower or "no such file" in lower:
            return "The source video file could not be found or has expired."
        if "codec" in lower or "unsupported" in lower:
            return "The video format or codec is unsupported. Please try standard MP4 format."
        if "quota" in lower or "rate limit" in lower:
            return "AI service is currently experiencing high demand. Please retry in a few moments."

        # Truncate overly long error messages
        if len(raw_error) > 200:
            raw_error = raw_error[:197] + "..."

        return raw_error

    @classmethod
    def create_job(cls, job_id: str, video_title: str, token_hash: Optional[str] = None, target_count: int = 3) -> Dict[str, Any]:
        """Initializes a new job entry inside Redis with a queued state and secure access token hash."""
        now = time.time()
        job_data = {
            "id": job_id,
            "jobId": job_id,
            "tokenHash": token_hash,
            "status": JobStatus.QUEUED.value,
            "stage": "Uploading",
            "progress": 0,
            "currentStep": "Waiting in queue...",
            "statusMessage": "Waiting in queue to begin processing…",
            "videoTitle": video_title,
            "targetCount": target_count,
            "clips": [],
            "error": None,
            "createdAt": now,
            "updatedAt": now,
            "expiresAt": now + DEFAULT_JOB_TTL_SECONDS
        }
        
        serialized = json.dumps(job_data)
        key = f"viralcut:job:{job_id}"
        
        redis = cls.get_redis_client()
        if redis:
            try:
                redis.set(key, serialized, ex=DEFAULT_JOB_TTL_SECONDS)
            except Exception:
                _in_memory_jobs[key] = serialized
        else:
            _in_memory_jobs[key] = serialized
            
        logger.info("Created background job entry: %s", job_id)
        
        from app.services.analytics import AnalyticsService
        AnalyticsService.track_event("job_created")
        
        return job_data

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves current state dictionary for a specific job from Redis or memory fallback."""
        key = f"viralcut:job:{job_id}"
        raw = None
        
        redis = cls.get_redis_client()
        if redis:
            try:
                raw = redis.get(key)
            except Exception:
                raw = _in_memory_jobs.get(key)
        else:
            raw = _in_memory_jobs.get(key)
            
        if not raw:
            return None
        
        job_data = json.loads(raw)
        
        # Check if job has expired according to timestamp
        expires_at = job_data.get("expiresAt")
        if expires_at and time.time() > expires_at:
            job_data["status"] = JobStatus.EXPIRED.value
            job_data["statusMessage"] = "This job has expired and its temporary assets were cleaned up."

        # Normalize old "pending" status to "queued"
        if job_data.get("status") == "pending":
            job_data["status"] = JobStatus.QUEUED.value

        return job_data

    @classmethod
    def verify_job_access(cls, job_id: str, access_token: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Retrieves the job and performs constant-time validation of the caller's access token.
        Returns None if job is not found OR if token is invalid (avoids user/job enumeration).
        """
        from app.core.security import AnonymousSecurityService

        job_data = cls.get_job(job_id)
        if not job_data:
            return None

        stored_hash = job_data.get("tokenHash")
        # If job was secured with a token hash, require valid token
        if stored_hash:
            if not AnonymousSecurityService.verify_token(access_token, stored_hash):
                logger.warning("Unauthorized access attempt to job %s (invalid or missing token)", job_id)
                return None

        return job_data

    @classmethod
    def update_progress(
        cls,
        job_id: str,
        progress: int,
        step_label: str,
        status: str = JobStatus.PROCESSING.value,
        error: Optional[str] = None,
        clips: Optional[list] = None,
        stage: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Updates the status, progress percentage, step label, stage, and output clips."""
        job_data = cls.get_job(job_id)
        if not job_data:
            logger.warning("Attempted to update non-existent job: %s", job_id)
            return None
            
        key = f"viralcut:job:{job_id}"
        
        # Normalize status
        if isinstance(status, JobStatus):
            status_val = status.value
        else:
            status_val = JobStatus.QUEUED.value if status == "pending" else str(status)

        job_data["status"] = status_val
        job_data["progress"] = min(100, max(0, progress))
        job_data["currentStep"] = step_label
        job_data["statusMessage"] = step_label
        job_data["updatedAt"] = time.time()
        
        if stage is not None:
            job_data["stage"] = stage
        if error is not None:
            job_data["error"] = cls.sanitize_error(error)
        if clips is not None:
            job_data["clips"] = clips

        serialized = json.dumps(job_data)
        redis = cls.get_redis_client()
        if redis:
            try:
                redis.set(key, serialized, ex=DEFAULT_JOB_TTL_SECONDS)
            except Exception:
                _in_memory_jobs[key] = serialized
        else:
            _in_memory_jobs[key] = serialized
            
        logger.debug("Updated job %s progress to %d%% in stage '%s' (%s)", job_id, progress, job_data.get("stage"), step_label)
        return job_data

    @classmethod
    def mark_complete(cls, job_id: str, clips: list) -> Optional[Dict[str, Any]]:
        """Marks the job status as completed and registers output clips urls."""
        from app.services.analytics import AnalyticsService
        AnalyticsService.track_event("job_completed")
        return cls.update_progress(
            job_id=job_id,
            progress=100,
            step_label="Process complete! Your Shorts are ready.",
            status=JobStatus.COMPLETED.value,
            clips=clips,
            stage="Finalizing"
        )

    @classmethod
    def mark_failed(cls, job_id: str, error_message: str) -> Optional[Dict[str, Any]]:
        """Marks the job status as failed and records sanitized error details."""
        from app.services.analytics import AnalyticsService
        AnalyticsService.track_event("job_failed")
        return cls.update_progress(
            job_id=job_id,
            progress=0,
            step_label="Video processing could not be completed.",
            status=JobStatus.FAILED.value,
            error=error_message,
            stage="Finalizing"
        )

    @classmethod
    def mark_expired(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Marks the job status as expired."""
        return cls.update_progress(
            job_id=job_id,
            progress=0,
            step_label="Job expired.",
            status=JobStatus.EXPIRED.value
        )
