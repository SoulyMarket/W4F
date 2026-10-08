import time

from app.core.rate_limit import InMemoryRateLimiter


def test_not_blocked_before_max_attempts():
    limiter = InMemoryRateLimiter(max_attempts=3, window_seconds=60)
    limiter.hit("1.2.3.4")
    limiter.hit("1.2.3.4")
    assert limiter.is_blocked("1.2.3.4") is False


def test_blocked_at_max_attempts():
    limiter = InMemoryRateLimiter(max_attempts=3, window_seconds=60)
    for _ in range(3):
        limiter.hit("1.2.3.4")
    assert limiter.is_blocked("1.2.3.4") is True


def test_keys_are_independent():
    limiter = InMemoryRateLimiter(max_attempts=2, window_seconds=60)
    limiter.hit("1.2.3.4")
    limiter.hit("1.2.3.4")
    assert limiter.is_blocked("1.2.3.4") is True
    assert limiter.is_blocked("5.6.7.8") is False


def test_reset_clears_attempts():
    limiter = InMemoryRateLimiter(max_attempts=2, window_seconds=60)
    limiter.hit("1.2.3.4")
    limiter.hit("1.2.3.4")
    assert limiter.is_blocked("1.2.3.4") is True
    limiter.reset("1.2.3.4")
    assert limiter.is_blocked("1.2.3.4") is False


def test_old_hits_outside_window_are_pruned():
    # A real sleep rather than window_seconds=0: on Windows, time.monotonic()
    # has coarse enough resolution that back-to-back calls can report the
    # exact same instant, making a zero-width window racy rather than a
    # reliable "already expired" case.
    limiter = InMemoryRateLimiter(max_attempts=2, window_seconds=0.05)
    limiter.hit("1.2.3.4")
    limiter.hit("1.2.3.4")
    assert limiter.is_blocked("1.2.3.4") is True
    time.sleep(0.1)
    assert limiter.is_blocked("1.2.3.4") is False
