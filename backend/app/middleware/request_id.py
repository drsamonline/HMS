"""Request ID middleware for FastAPI using UUID4."""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.core.utils import generate_uuid

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that injects a unique request ID into each request.

    The request ID is:
    - Generated using UUID4
    - Added to request.state
    - Included in response headers
    - Available for logging and tracing
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Add request ID to the request state and response headers.

        Args:
            request: The incoming FastAPI request
            call_next: The next middleware or route handler

        Returns:
            Response: The response with X-Request-ID header added
        """
        request_id = str(generate_uuid())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
