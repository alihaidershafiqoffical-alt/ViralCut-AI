"""
app/core/rate_limiter.py
------------------------
Redis-backed Sliding-Window Rate Limiter & Abuse Protection for Anonymous Users.

Enforces resource protection for:
- Upload requests
- URL processing
- Job creation
- Status polling
- Download requests

Features:
- IP extraction with proxy support (X-Forwarded-For)
- Redis sorted set atomic sliding-window algorithm
- In-memory fallback for high-availability / test environments
- Standard rate limit response headers (Retry-After, X-RateLimit-Limit, etc.)
- User-friendly error messages (no technical stack traces)
"""

from __future__ import annotations

import time
import logging
from typing import Optional, Dict, Any, Tuple, List
from collections import defaultdict
from fastapi import Request, HTTPException, status
from redis import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitRule:
    def __init__(
        self,
        name: str,
        max_requests: int,
        window_seconds: int,
        friendly_message: str
    ):
        self.name = name
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.friendly_message = friendly_message

    # Pre-configured rules for anonymous abuse protection
    UPLOAD = None
    URL_INGEST = None
    JOB_CREATE = None
    STATUS_POLL = None
    DOWNLOAD = None


RateLimitRule.UPLOAD = RateLimitRule(
    name="upload",
    max_requests=5,
    window_seconds=600,  # 5 uploads per 10 minutes
    friendly_message="You have reached the upload limit of 5 videos per 10 minutes. Please wait before uploading another video."
)

RateLimitRule.URL_INGEST = RateLimitRule(
    name="url_ingest",
    max_requests=5,
    window_seconds=600,  # 5 URL ingestions per 10 minutes
    friendly_message="You have reached the URL processing limit of 5 links per 10 minutes. Please wait before processing more video URLs."
)

RateLimitRule.JOB_CREATE = RateLimitRule(
    name="job_create",
    max_requests=10,
    window_seconds=900,  # 10 jobs per 15 minutes
    friendly_message="You have reached the job generation limit. Please wait a few minutes before queuing more Short renderings."
)

RateLimitRule.STATUS_POLL = RateLimitRule(
    name="status_poll",
    max_requests=60,
    window_seconds=60,  # 60 poll requests per minute (1 per second max)
    friendly_message="Status polling limit reached. Please reduce polling frequency to once every 2 seconds."
)

RateLimitRule.DOWNLOAD = RateLimitRule(
    name="download",
    max_requests=20,
    window_seconds=300,  # 20 downloads per 5 minutes
    friendly_message="Download rate limit exceeded. Please wait a few moments before requesting more video downloads."
)


# Global in-memory storage fallback
_in_memory_sliding_windows: Dict[str, List[float]] = defaultdict(list)


class RateLimiterService:
    """
    Evaluates and records request timestamps per client IP.
    """

    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Extracts client IP address safely considering reverse proxies."""
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # First IP in the comma-separated list is the original client
            client_ip = x_forwarded_for.split(",")[0].strip()
            if client_ip:
                return client_ip

        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip.strip()

        if request.client and request.client.host:
            return request.client.host

        return "127.0.0.1"

    @classmethod
    def get_redis(cls) -> Optional[Redis]:
        """Returns Redis client instance or None if unavailable."""
        try:
            from app.services.job_manager import JobManagerService
            return JobManagerService.get_redis_client()
        except Exception as e:
            logger.debug("Redis unavailable for rate limiter, using in-memory fallback: %s", e)
            return None

    @classmethod
    def check_rate_limit(
        cls,
        request: Request,
        rule: RateLimitRule
    ) -> Tuple[bool, int, int, int]:
        """
        Executes sliding window rate limit evaluation.
        Returns: (is_allowed, remaining_requests, reset_time_epoch, retry_after_seconds)
        """
        client_ip = cls.get_client_ip(request)
        now = time.time()
        window_start = now - rule.window_seconds
        key = f"viralcut:ratelimit:{rule.name}:{client_ip}"

        redis_client = cls.get_redis()

        # ── 1. Redis Sliding Window Evaluation ──────────────────────────────
        if redis_client:
            try:
                pipe = redis_client.pipeline()
                # Remove timestamps older than current window
                pipe.zremrangebyscore(key, 0, window_start)
                # Count remaining requests in current window
                pipe.zcard(key)
                # Get the oldest timestamp in the current window for accurate retry-after calculation
                pipe.zrange(key, 0, 0, withscores=True)
                # Set TTL on key
                pipe.expire(key, rule.window_seconds + 5)
                results = pipe.execute()

                current_count = results[1]
                oldest_entry = results[2]

                if current_count >= rule.max_requests:
                    oldest_ts = oldest_entry[0][1] if oldest_entry else window_start
                    retry_after = max(1, int(oldest_ts + rule.window_seconds - now))
                    reset_epoch = int(now + retry_after)
                    return False, 0, reset_epoch, retry_after

                # Allow and record current request timestamp
                redis_client.zadd(key, {f"{now}_{current_count}": now})
                remaining = max(0, rule.max_requests - (current_count + 1))
                reset_epoch = int(now + rule.window_seconds)
                return True, remaining, reset_epoch, 0

            except Exception as redis_err:
                logger.debug("Redis rate limit check error (%s), using in-memory fallback", redis_err)

        # ── 2. In-Memory Fallback Evaluation ────────────────────────────────
        timestamps = _in_memory_sliding_windows[key]
        # Purge expired timestamps
        _in_memory_sliding_windows[key] = [t for t in timestamps if t > window_start]
        active_timestamps = _in_memory_sliding_windows[key]

        if len(active_timestamps) >= rule.max_requests:
            oldest_ts = active_timestamps[0]
            retry_after = max(1, int(oldest_ts + rule.window_seconds - now))
            reset_epoch = int(now + retry_after)
            return False, 0, reset_epoch, retry_after

        # Record this request
        active_timestamps.append(now)
        remaining = max(0, rule.max_requests - len(active_timestamps))
        reset_epoch = int(now + rule.window_seconds)
        return True, remaining, reset_epoch, 0


def rate_limit(rule: RateLimitRule):
    """
    FastAPI dependency factory enforcing rate limits on endpoints.
    """
    async def dependency(request: Request):
        allowed, remaining, reset_epoch, retry_after = RateLimiterService.check_rate_limit(request, rule)

        if not allowed:
            logger.warning(
                "Rate limit exceeded for IP %s on '%s' (limit=%d/%ds, retry_after=%ds)",
                RateLimiterService.get_client_ip(request),
                rule.name,
                rule.max_requests,
                rule.window_seconds,
                retry_after
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": rule.friendly_message,
                    "action": rule.name,
                    "retry_after_seconds": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rule.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_epoch)
                }
            )

    return dependency
