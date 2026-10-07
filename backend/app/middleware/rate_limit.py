"""
HHMS Rate-Limiting Middleware

Provides a lightweight in-memory sliding-window rate limiter used to
throttle high-value authentication endpoints (``POST /api/v1/auth/login``)
against brute-force credential attacks. The limiter is deliberately
dependency-free so it works identically in source, packaged, and frozen
(PyInstaller) runtimes.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import threading
import time
from collections import deque

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


RATE_LIMITED_PATHS = frozenset({"/api/v1/auth/login"})

RETRY_AFTER_SECONDS = 60


class SlidingWindowRateLimiter:
    """
    Thread-safe fixed-slot sliding-window counter.

    For each client key the limiter keeps the request timestamps of the
    current window in a deque; requests are allowed while the number of
    recorded hits stays below ``limit`` within the trailing
    ``window_seconds`` interval.
    """

    def __init__(
        self,
        *,
        limit: int = 10,
        window_seconds: float = 60.0,
    ) -> None:
        if limit < 1:
            raise ValueError("Rate-limit must be at least 1 request per window.")

        if window_seconds <= 0:
            raise ValueError("Rate-limit window must be positive.")

        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(
        self,
        key: str,
        *,
        now: float | None = None,
    ) -> tuple[bool, float]:
        """
        Record an attempt for ``key`` and decide whether it is allowed.

        Returns
        -------
        tuple[bool, float]
            ``(allowed, retry_after_seconds)`` — when allowed,
            ``retry_after_seconds`` is ``0.0``; otherwise it is the time
            until the oldest hit in the window expires.
        """
        timestamp = time.monotonic() if now is None else now
        cutoff = timestamp - self.window_seconds

        with self._lock:
            bucket = self._hits.get(key)

            if bucket is None:
                bucket = deque()
                self._hits[key] = bucket

            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self.limit:
                retry_after = bucket[0] + self.window_seconds - timestamp
                return False, max(retry_after, 0.0)

            bucket.append(timestamp)
            return True, 0.0

    def reset(self, key: str | None = None) -> None:
        """Clear one key's history (or all keys when ``key`` is ``None``)."""
        with self._lock:
            if key is None:
                self._hits.clear()
            else:
                self._hits.pop(key, None)


def _client_key(scope: Scope) -> str:
    """
    Derive the limiting identity for a request.

    Prefers the proxy-supplied ``X-Forwarded-For`` first hop, then the
    peer address reported by the server; falls back to ``"unknown"``.
    """
    for raw_name, raw_value in scope.get("headers", []):
        if raw_name.lower() == b"x-forwarded-for":
            first_hop = raw_value.decode("latin-1").split(",")[0].strip()

            if first_hop:
                return first_hop

    client = scope.get("client")

    if client and client[0]:
        return str(client[0])

    return "unknown"


class RateLimitMiddleware:
    """
    ASGI middleware enforcing the login brute-force throttle.

    Only paths listed in :data:`RATE_LIMITED_PATHS` are metered; every
    other request passes straight through with zero bookkeeping. When a
    client exceeds the configured budget the middleware short-circuits
    with a structured ``429 Too Many Requests`` JSON body mirroring the
    shape produced by the exception handlers.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        limiter: SlidingWindowRateLimiter | None = None,
        limit: int = 10,
        window_seconds: float = 60.0,
    ) -> None:
        self.app = app
        self.limiter = limiter or SlidingWindowRateLimiter(
            limit=limit,
            window_seconds=window_seconds,
        )

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if (
            scope["type"] != "http"
            or scope.get("method") != "POST"
            or scope.get("path") not in RATE_LIMITED_PATHS
        ):
            await self.app(scope, receive, send)
            return

        allowed, retry_after = self.limiter.allow(_client_key(scope))

        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "Too many login attempts. Please try again in "
                        f"{int(retry_after) + 1} seconds."
                    ),
                    "error": "rate_limited",
                },
                headers={
                    "Retry-After": str(int(retry_after) + 1),
                },
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


__all__ = [
    "RateLimitMiddleware",
    "SlidingWindowRateLimiter",
    "RATE_LIMITED_PATHS",
    "RETRY_AFTER_SECONDS",
]
