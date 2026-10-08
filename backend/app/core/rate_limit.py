"""In-memory per-IP rate limiter for the login endpoint (section 6.2).

A sliding window of failure timestamps per key. Good enough for a single
process; a multi-worker/multi-instance production deployment would need a
shared store (Redis) instead — the interface here (`hit`/`is_blocked`) is
small enough to swap the backend later without touching callers.
"""

import threading
import time
from collections import defaultdict, deque


class InMemoryRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            self._prune(key, now)
            self._hits[key].append(now)

    def is_blocked(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            self._prune(key, now)
            return len(self._hits[key]) >= self.max_attempts

    def _prune(self, key: str, now: float) -> None:
        window_start = now - self.window_seconds
        bucket = self._hits[key]
        while bucket and bucket[0] < window_start:
            bucket.popleft()

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)


# 10 failed login attempts from one IP within 15 minutes blocks further
# attempts from that IP, independent of the per-account lock in app.models.user.
login_ip_rate_limiter = InMemoryRateLimiter(max_attempts=10, window_seconds=15 * 60)
