"""Global exception middleware."""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.responses import Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Convert unhandled exceptions into JSON responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Handle exceptions raised during request processing."""

        try:
            return await call_next(request)

        except Exception as exc:
            status_code = getattr(
                exc,
                "status_code",
                HTTP_500_INTERNAL_SERVER_ERROR,
            )

            detail = getattr(
                exc,
                "detail",
                "Internal Server Error",
            )

            error_code = getattr(
                exc,
                "error_code",
                None,
            )

            logger.exception(
                "Unhandled exception",
                extra={
                    "request_id": getattr(
                        request.state,
                        "request_id",
                        None,
                    ),
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": status_code,
                },
            )

            payload = {
                "detail": detail,
            }

            if error_code is not None:
                payload["error_code"] = error_code

            return JSONResponse(
                status_code=status_code,
                content=payload,
            )