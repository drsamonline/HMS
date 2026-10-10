"""
HHMS Request ID Middleware

Provides a unique request identifier for every HTTP request.
The identifier is returned to the client and made available
through the request state for logging and tracing.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from uuid import UUID, uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send


REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_STATE_KEY = "request_id"


class RequestIDMiddleware:
    """
    ASGI middleware that assigns a unique identifier to each request.

    A client-supplied request ID is accepted when present and valid;
    otherwise, a new UUID4 identifier is generated.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = self._get_request_id(scope)

        scope.setdefault("state", {})
        scope["state"][REQUEST_ID_STATE_KEY] = request_id

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append(
                    (
                        REQUEST_ID_HEADER.lower().encode("latin-1"),
                        request_id.encode("latin-1"),
                    )
                )
                message["headers"] = headers

            await send(message)

        await self.app(
            scope,
            receive,
            send_with_request_id,
        )

    @staticmethod
    def _get_request_id(scope: Scope) -> str:
        """
        Extract a valid client request ID or generate a new UUID4.

        Parameters
        ----------
        scope : Scope
            ASGI request scope.

        Returns
        -------
        str
            Request identifier.
        """

        for key, value in scope.get("headers", []):
            if key.lower() == REQUEST_ID_HEADER.lower().encode("latin-1"):
                candidate = value.decode("latin-1").strip()

                try:
                    UUID(candidate)
                except (ValueError, AttributeError):
                    break

                return candidate

        return str(uuid4())