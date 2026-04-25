import sys

from rd_territorial_system.api.rate_limit import (
    InMemoryRateLimiter,
    RedisRateLimiter,
)


def test_in_memory_rate_limiter_blocks_after_limit():
    limiter = InMemoryRateLimiter()

    d1 = limiter.is_allowed("client:test", max_requests=2, window_seconds=60)
    d2 = limiter.is_allowed("client:test", max_requests=2, window_seconds=60)
    d3 = limiter.is_allowed("client:test", max_requests=2, window_seconds=60)

    assert d1.allowed is True
    assert d2.allowed is True
    assert d3.allowed is False
    assert d3.remaining == 0


def test_redis_rate_limiter_fail_open_when_client_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "redis", None)

    limiter = RedisRateLimiter(
        redis_url="redis://localhost:6379/0",
        fail_open=True,
    )

    decision = limiter.is_allowed(
        key="client:test",
        max_requests=10,
        window_seconds=60,
    )

    assert decision.allowed is True
    assert decision.remaining == 10


def test_redis_rate_limiter_fail_closed_when_client_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "redis", None)

    try:
        RedisRateLimiter(
            redis_url="redis://localhost:6379/0",
            fail_open=False,
        )
    except RuntimeError as exc:
        assert "redis package is not installed" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")