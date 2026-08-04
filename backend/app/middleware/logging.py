"""Structured request logging middleware for FastAPI."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)

logger = logging.getLogger(__name__)

_ALLOWED_HEADERS = {
    "host",
    "user-agent",
    "accept",
    "accept-encoding",
    "content-type",
    "content-length",
}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs request and response information."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Log request processing."""

        start = time.perf_counter()

        safe_headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() in _ALLOWED_HEADERS
        }

        request_data: dict[str, Any] = {
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": safe_headers,
        }

        try:
            response = await call_next(request)
        except Exception:
            request_data["process_time"] = time.perf_counter() - start

            logger.exception(
                "Request failed",
                extra={"http": request_data},
            )

            raise

        request_data.update(
            {
                "status_code": response.status_code,
                "process_time": time.perf_counter() - start,
            }
        )

        logger.info(
            "Request completed",
            extra={"http": request_data},
        )

        return response