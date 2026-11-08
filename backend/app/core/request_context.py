"""
Per-request context available to the service layer.

A service cannot see the Starlette ``Request``, and it should not: passing the
request object into business logic couples every service to HTTP. What a service
does need, for the audit trail, is the handful of facts that describe *where the
call came from* - the request id, the client address and the user agent.

Those are set once per request by ``RequestIDMiddleware`` into a
``ContextVar`` and read back here. A context variable rather than a module global
because the server handles concurrent requests in one process, and a global would
hand one hospital's client address to another hospital's audit row.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass


@dataclass(frozen=True)
class RequestContext:
    """The request facts an audit row needs, and nothing else."""

    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


_EMPTY = RequestContext()

_current: ContextVar[RequestContext] = ContextVar(
    "hhms_request_context",
    default=_EMPTY,
)


def set_request_context(context: RequestContext) -> Token:
    """Bind a context to the current request. Returns a reset token."""

    return _current.set(context)


def reset_request_context(token: Token) -> None:
    """Restore the previous context. Called in the middleware's ``finally``."""

    _current.reset(token)


def current_request_context() -> RequestContext:
    """The context for the request being served, or an empty one."""

    return _current.get()


__all__ = [
    "RequestContext",
    "current_request_context",
    "reset_request_context",
    "set_request_context",
]
