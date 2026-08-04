"""Request processing time middleware for FastAPI."""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """Middleware that measures and reports request processing time.

    The processing time is:
    - Measured in seconds with high precision
    - Added to response headers as X-Process-Time
    - Available for logging and monitoring
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Measure request processing time and add to response headers.

        Args:
            request: The incoming FastAPI request
            call_next: The next middleware or route handler

        Returns:
            Response: The response with X-Process-Time header added
        """
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        request.state.process_time = process_time
        response.headers["X-Process-Time"] = f"{process_time:.6f}"
        return response