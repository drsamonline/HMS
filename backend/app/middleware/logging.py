"""
HHMS Request Logging Middleware

Logs the completion of HTTP requests together with their method,
path, status code, request ID, and processing duration.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send


REQUEST_ID_STATE_KEY = "request_id"


class RequestLoggingMiddleware:
    """
    ASGI middleware for structured HTTP request logging.

    The middleware records one completion log for each HTTP request.
    """

    def __init__(
        self,
        app: ASGIApp,
        logger: logging.Logger | None = None,
    ) -> None:
        self.app = app
        self.logger = logger or logging.getLogger("HHMS")

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = perf_counter()
        status_code: int | None = None

        async def send_with_logging(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = int(message["status"])

            await send(message)

        try:
            await self.app(
                scope,
                receive,
                send_with_logging,
            )
        except Exception:
            elapsed = perf_counter() - start_time
            self._log_request(
                scope=scope,
                status_code=status_code or 500,
                elapsed=elapsed,
                failed=True,
            )
            raise

        elapsed = perf_counter() - start_time
        self._log_request(
            scope=scope,
            status_code=status_code or 500,
            elapsed=elapsed,
            failed=False,
        )

    def _log_request(
        self,
        *,
        scope: Scope,
        status_code: int,
        elapsed: float,
        failed: bool,
    ) -> None:
        """
        Write a request completion log entry.

        Parameters
        ----------
        scope : Scope
            ASGI request scope.

        status_code : int
            HTTP response status code.

        elapsed : float
            Request processing duration in seconds.

        failed : bool
            Whether request processing raised an exception.
        """

        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        request_id = self._get_request_id(scope)

        extra: dict[str, Any] = {
            "request_id": request_id,
            "http_method": method,
            "http_path": path,
            "status_code": status_code,
            "duration_seconds": round(elapsed, 6),
        }

        if failed:
            self.logger.error(
                "HTTP request failed",
                extra=extra,
            )
            return

        self.logger.info(
            "HTTP request completed",
            extra=extra,
        )

    @staticmethod
    def _get_request_id(scope: Scope) -> str:
        """
        Retrieve the request ID assigned by RequestIDMiddleware.

        Returns
        -------
        str
            Request ID or ``-`` when unavailable.
        """

        state = scope.get("state")

        if not isinstance(state, dict):
            return "-"

        request_id = state.get(REQUEST_ID_STATE_KEY)

        if request_id is None:
            return "-"

        return str(request_id)