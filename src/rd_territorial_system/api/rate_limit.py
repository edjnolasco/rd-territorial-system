from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse


@dataclass(frozen=True)
class RateLimitConfig:
    enabled: bool
    max_requests: int
    window_seconds: int


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = self._requests[key]

            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            remaining = max_requests - len(timestamps)

            if remaining <= 0:
                return False, 0

            timestamps.append(now)
            return True, remaining - 1


rate_limiter = InMemoryRateLimiter()


def get_client_key(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "unknown"


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