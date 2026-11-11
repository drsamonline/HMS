"""
HHMS Security Headers Middleware
================================

Adds the HTTP response headers that protect a browser-rendered interface
from framing, MIME sniffing, referrer leakage and unexpected script or
style injection.

``docs/SECURITY_ARCHITECTURE.md`` section 8 has specified these headers
since v1.0 of the architecture, and until now no middleware set any of
them. This module makes the specification true.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


# The GUI in ``frontend/`` renders inline <style> and <script> blocks, so the
# content policy has to permit inline script and style for now. Tightening this
# to a nonce-based policy is part of the interface rebuild (build plan B27/B28);
# until then an inline-permitting policy is honest, and a policy the UI cannot
# satisfy would simply be removed again by the first person who hit a blank page.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach the security headers to every response, including errors."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            # ``setdefault`` semantics: never overwrite a header a route set
            # deliberately, for example a download that needs its own policy.
            if header not in response.headers:
                response.headers[header] = value
        return response


__all__ = [
    "CONTENT_SECURITY_POLICY",
    "SECURITY_HEADERS",
    "SecurityHeadersMiddleware",
]
