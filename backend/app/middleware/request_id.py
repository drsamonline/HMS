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

from app.core.request_context import (
    RequestContext,
    reset_request_context,
    set_request_context,
)


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

        # Bind the facts an audit row needs. Services cannot see the Request,
        # and should not, so this is the only way the client address and user
        # agent reach the service layer without threading a request object
        # through every signature.
        token = set_request_context(
            RequestContext(
                request_id=request_id,
                ip_address=self._client_address(scope),
                user_agent=self._user_agent(scope),
            )
        )

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

        try:
            await self.app(
                scope,
                receive,
                send_with_request_id,
            )
        finally:
            # Reset even when the handler raised: a context that outlives its
            # request leaks one hospital's client address into the next.
            reset_request_context(token)

    @staticmethod
    def _client_address(scope: Scope) -> str | None:
        """The peer address, if the ASGI server supplied one."""

        client = scope.get("client")
        if not client:
            return None
        try:
            return str(client[0])
        except (IndexError, TypeError):
            return None

    @staticmethod
    def _user_agent(scope: Scope) -> str | None:
        """The User-Agent header, truncated to the column width."""

        for key, value in scope.get("headers", []):
            if key.lower() == b"user-agent":
                return value.decode("latin-1")[:255]
        return None

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