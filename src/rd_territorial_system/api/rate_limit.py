from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from typing import Protocol

from fastapi.responses import JSONResponse

from rd_territorial_system.api.settings import get_settings


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int


class RateLimiterBackend(Protocol):
    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        ...


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = self._requests[key]

            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            remaining = max_requests - len(timestamps)

            if remaining <= 0:
                return RateLimitDecision(allowed=False, remaining=0)

            timestamps.append(now)

            return RateLimitDecision(
                allowed=True,
                remaining=max_requests - len(timestamps),
            )


class RedisRateLimiter:
    def __init__(self, redis_url: str, fail_open: bool = True) -> None:
        self.redis_url = redis_url
        self.fail_open = fail_open
        self._client = self._build_client(redis_url)

    def _build_client(self, redis_url: str):
        try:
            import redis
        except ImportError as exc:
            if self.fail_open:
                return None

            raise RuntimeError(
                "Redis backend selected but redis package is not installed."
            ) from exc

        return redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        if self._client is None:
            return RateLimitDecision(
                allowed=True,
                remaining=max_requests,
            )

        now_ms = int(time.time() * 1000)
        window_ms = window_seconds * 1000

        redis_key = f"rdts:rate_limit:{key}"

        try:
            pipe = self._client.pipeline()
            pipe.zremrangebyscore(redis_key, 0, now_ms - window_ms)
            pipe.zcard(redis_key)
            pipe.zadd(redis_key, {str(now_ms): now_ms})
            pipe.expire(redis_key, window_seconds)
            results = pipe.execute()

            current_count = int(results[1])

            if current_count >= max_requests:
                self._client.zrem(redis_key, str(now_ms))
                return RateLimitDecision(allowed=False, remaining=0)

            remaining = max_requests - current_count - 1

            return RateLimitDecision(
                allowed=True,
                remaining=max(remaining, 0),
            )

        except Exception:
            if self.fail_open:
                return RateLimitDecision(
                    allowed=True,
                    remaining=max_requests,
                )

            return RateLimitDecision(allowed=False, remaining=0)


def build_rate_limiter() -> RateLimiterBackend:
    settings = get_settings()
    backend = settings.rate_limit_backend.lower()

    if backend == "redis":
        return RedisRateLimiter(
            redis_url=settings.redis_url,
            fail_open=settings.rate_limit_fail_open,
        )

    return InMemoryRateLimiter()


rate_limiter = build_rate_limiter()


def rate_limit_response(request_id: str | None) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": {
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
            },
            "request_id": request_id,
        },
    )