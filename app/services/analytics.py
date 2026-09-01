from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

# Global in-memory analytics storage fallback
_in_memory_daily_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
_in_memory_lifetime_counters: Dict[str, int] = defaultdict(int)


class AnalyticsService:
    """
    Saves anonymized, privacy-conscious event counters in Redis with an in-memory fallback.
    Compliant with GDPR, CCPA, and Google AdSense policies.
    """

    @classmethod
    def track_event(cls, event_name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """
        Increments daily counts in Redis or in-memory for a given event name.
        Absolutely no PII (IPs, user identifiers, video details) is collected.
        """
        from app.services.job_manager import JobManagerService
        
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Try to use Redis first
        redis_client = None
        try:
            redis_client = JobManagerService.get_redis_client()
        except Exception:
            pass

        if redis_client:
            try:
                counter_key = f"viralcut:analytics:daily:{today_str}"
                # Redis client connection check by execution
                redis_client.hincrby(counter_key, event_name, 1)
                redis_client.expire(counter_key, 90 * 24 * 60 * 60)
                
                lifetime_key = "viralcut:analytics:lifetime"
                redis_client.hincrby(lifetime_key, event_name, 1)
                
                logger.info("Analytics Event (Redis): %s", event_name)
                return
            except Exception as e:
                logger.debug("Redis analytics failed, falling back to in-memory: %s", e)

        # Fallback to in-memory
        _in_memory_daily_counters[today_str][event_name] += 1
        _in_memory_lifetime_counters[event_name] += 1
        logger.info("Analytics Event (In-Memory): %s", event_name)

    @classmethod
    def get_stats(cls, date_str: Optional[str] = None) -> Dict[str, int]:
        """
        Retrieves counters for a specific date (YYYY-MM-DD), or lifetime stats if date is omitted.
        """
        from app.services.job_manager import JobManagerService
        
        redis_client = None
        try:
            redis_client = JobManagerService.get_redis_client()
        except Exception:
            pass

        if redis_client:
            try:
                if date_str:
                    key = f"viralcut:analytics:daily:{date_str}"
                else:
                    key = "viralcut:analytics:lifetime"
                    
                raw_data = redis_client.hgetall(key)
                if raw_data:
                    return {k: int(v) for k, v in raw_data.items()}
            except Exception as e:
                logger.debug("Redis analytics stats read failed, using in-memory: %s", e)

        # Fallback to in-memory
        if date_str:
            return dict(_in_memory_daily_counters[date_str])
        else:
            return dict(_in_memory_lifetime_counters)

    @classmethod
    def clear_test_data(cls, date_str: str) -> None:
        """Clears local and Redis test data (only used during testing)."""
        from app.services.job_manager import JobManagerService
        
        # Clear in-memory
        _in_memory_daily_counters.pop(date_str, None)
        _in_memory_lifetime_counters.clear()
        
        # Clear Redis
        try:
            redis_client = JobManagerService.get_redis_client()
            if redis_client:
                redis_client.delete(f"viralcut:analytics:daily:{date_str}")
                redis_client.delete("viralcut:analytics:lifetime")
        except Exception:
            pass
