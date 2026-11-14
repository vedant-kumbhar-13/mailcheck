"""
Per-IP sliding-window rate limiter, stored in process memory.
No Redis. Thread-safe for asyncio (single-threaded event loop).
"""

from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque

from app.config import settings


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window = window_seconds
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def _key(self, raw_ip: str) -> str:
        """Hash the IP so we don't store PII in memory."""
        return hashlib.sha256(raw_ip.encode()).hexdigest()[:16]

    def hit(self, raw_ip: str) -> bool:
        """
        Returns True if the request is allowed, False if rate-limited.
        Records the hit only when allowed.
        """
        key = self._key(raw_ip)
        now = time.monotonic()
        bucket = self._buckets[key]
        cutoff = now - self._window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self._limit:
            return False
        bucket.append(now)
        return True


# Singletons — created once at import time
single_limiter = RateLimiter(limit=settings.rate_single_per_min, window_seconds=60)
