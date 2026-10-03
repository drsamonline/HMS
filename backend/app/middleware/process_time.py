"""
HHMS Process-Time Middleware

Measures the processing time of each HTTP request and exposes
the duration through the X-Process-Time response header.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from time import perf_counter

from starlette.types import ASGIApp, Message, Receive, Scope, Send


PROCESS_TIME_HEADER = "X-Process-Time"


class ProcessTimeMiddleware:
    """
    ASGI middleware that measures HTTP request processing time.

    The measured duration is expressed in seconds with six
    decimal places and returned in the response header.
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

        start_time = perf_counter()

        async def send_with_process_time(message: Message) -> None:
            if message["type"] == "http.response.start":
                elapsed = perf_counter() - start_time

                headers = list(message.get("headers", []))
                headers.append(
                    (
                        PROCESS_TIME_HEADER.lower().encode("latin-1"),
                        f"{elapsed:.6f}".encode("latin-1"),
                    )
                )
                message["headers"] = headers

            await send(message)

        await self.app(
            scope,
            receive,
            send_with_process_time,
        )