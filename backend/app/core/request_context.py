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
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class RequestContext:
    """The request facts an audit row needs, and nothing else."""

    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    actor_id: int | None = None
    actor_username: str | None = None
    actor_role: str | None = None


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


def bind_actor(
    *,
    actor_id: int | None,
    username: str | None,
    roles: list[str] | tuple[str, ...] | None,
) -> None:
    """Record who the request is authenticated as, for the audit trail.

    Called by the authentication dependency once the token has been validated.
    Services then read the actor from here instead of taking it as a parameter,
    which is what keeps the audit call to one line in every service rather than
    a signature change in every service and every endpoint that calls it.
    """

    role_text = ", ".join(str(role) for role in roles) if roles else None
    _current.set(
        replace(
            _current.get(),
            actor_id=actor_id,
            actor_username=username,
            actor_role=role_text,
        )
    )


__all__ = [
    "RequestContext",
    "bind_actor",
    "current_request_context",
    "reset_request_context",
    "set_request_context",
]
