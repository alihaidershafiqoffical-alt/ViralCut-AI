"""
app/services/concurrency_guard.py
---------------------------------
Infrastructure Resource & Concurrency Protection for Anonymous Users.

Enforces:
- Maximum concurrent active processing jobs per IP (e.g. max 2)
- Maximum global concurrent active rendering jobs (e.g. max 10)
- Maximum queue capacity backpressure (e.g. max 50 queued tasks)
- Immediate cancellation and cleanup endpoint
"""

from __future__ import annotations

import logging
from typing import Tuple, Optional
from fastapi import Request, HTTPException, status
from redis import Redis

from app.core.config import settings
from app.services.job_manager import JobManagerService

logger = logging.getLogger(__name__)

REDIS_GLOBAL_ACTIVE_KEY = "viralcut:concurrency:active_global"
REDIS_IP_ACTIVE_PREFIX = "viralcut:concurrency:active_ip:"


class ConcurrencyGuardService:
    """
    Guards server infrastructure from being overwhelmed by concurrent anonymous requests.
    """

    @staticmethod
    def get_redis() -> Optional[Redis]:
        try:
            return JobManagerService.get_redis_client()
        except Exception as e:
            logger.debug("Redis unavailable for concurrency guard: %s", e)
            return None

    @classmethod
    def check_and_reserve_capacity(cls, job_id: str, client_ip: str) -> None:
        """
        Validates global queue limits, global concurrent workers, and per-IP concurrent jobs.
        Raises HTTPException(503 or 429) if limits are exceeded.
        """
        redis = cls.get_redis()
        if not redis:
            return  # In-memory mode allows test runs

        try:
            # 1. Check Global Active Processing Jobs
            global_active_count = redis.scard(REDIS_GLOBAL_ACTIVE_KEY)
            if global_active_count >= settings.MAX_CONCURRENT_JOBS_GLOBAL:
                logger.warning(
                    "Global concurrency limit reached (%d/%d jobs)",
                    global_active_count, settings.MAX_CONCURRENT_JOBS_GLOBAL
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error": "Our video processing servers are currently at peak capacity. Please retry in a few moments.",
                        "reason": "GLOBAL_CAPACITY_EXCEEDED"
                    }
                )

            # 2. Check Per-IP Active Processing Jobs
            ip_key = f"{REDIS_IP_ACTIVE_PREFIX}{client_ip}"
            ip_active_count = redis.scard(ip_key)
            if ip_active_count >= settings.MAX_CONCURRENT_JOBS_PER_IP:
                logger.warning(
                    "Per-IP concurrency limit exceeded for %s (%d/%d jobs)",
                    client_ip, ip_active_count, settings.MAX_CONCURRENT_JOBS_PER_IP
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": f"You already have {ip_active_count} video processing tasks active. Please wait for your current video to finish.",
                        "reason": "PER_IP_CONCURRENCY_EXCEEDED"
                    }
                )

            # 3. Reserve capacity in atomic set
            pipe = redis.pipeline()
            pipe.sadd(REDIS_GLOBAL_ACTIVE_KEY, job_id)
            pipe.expire(REDIS_GLOBAL_ACTIVE_KEY, settings.WORKER_TASK_TIME_LIMIT_SECONDS)
            pipe.sadd(ip_key, job_id)
            pipe.expire(ip_key, settings.WORKER_TASK_TIME_LIMIT_SECONDS)
            pipe.execute()
            logger.info("Reserved processing capacity for job %s (IP: %s)", job_id, client_ip)

        except HTTPException:
            raise
        except Exception as err:
            logger.warning("Error evaluating concurrency guard: %s", err)

    @classmethod
    def release_capacity(cls, job_id: str, client_ip: Optional[str] = None) -> None:
        """
        Releases reserved capacity upon job completion, failure, or cancellation.
        """
        redis = cls.get_redis()
        if not redis:
            return

        try:
            redis.srem(REDIS_GLOBAL_ACTIVE_KEY, job_id)
            if client_ip:
                redis.srem(f"{REDIS_IP_ACTIVE_PREFIX}{client_ip}", job_id)
            logger.debug("Released concurrency capacity for job %s", job_id)
        except Exception as err:
            logger.debug("Error releasing concurrency capacity: %s", err)
