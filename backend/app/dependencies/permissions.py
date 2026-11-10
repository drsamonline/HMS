"""
The permission guard.

One dependency factory, used by every protected route:

    @router.get("", dependencies=[require("patients.read")])

It answers one question - does the authenticated user's role set hold this code -
and it answers it from the database rather than from the token, because a role can
be revoked and the next request should notice. The cost is one join per request;
the alternative is a permission change that takes effect at the next login, which
for an authorisation decision is the wrong trade.

Default deny
------------
A route with no guard is refused, not allowed. That is enforced by a router-level
dependency in ``api/v1/api.py``, which knows which routes declared a guard because
``require()`` stamps its dependency function with the code it demands.

The enforcement mode is staged. ``PERMISSION_ENFORCEMENT`` is one of:

``off``      no checks at all - only for a deliberate debugging session
``warn``     explicit guards apply; an unguarded route logs a warning and is allowed
``enforce``  explicit guards apply; an unguarded route returns 403

B13 ships ``warn`` so that the suite stays green while the 242 routes are being
guarded in B14, and B14 flips the default to ``enforce``. A batch that turned the
whole application off and called it progress would not be progress.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.permissions import ALL_ACCESS_ROLE_NAMES, CODES
from app.dependencies.auth import CurrentUser, CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole


#: Attribute stamped on the dependency function so the router-level check can
#: tell a guarded route from an unguarded one without re-reading the source.
PERMISSION_MARKER = "_hhms_permission"


async def permissions_for_user(db: AsyncSession, user_id: int) -> frozenset[str]:
    """Every code the user's active roles hold.

    An all-access role short-circuits to the whole catalogue, matching what the
    client has always done and what migration 0033 makes true in the data.
    """

    role_rows = await db.execute(
        select(Role.role_name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id, Role.is_active.is_(True))
    )
    role_names = {str(name).strip().lower() for (name,) in role_rows.all()}

    if role_names & ALL_ACCESS_ROLE_NAMES:
        return CODES

    if not role_names:
        return frozenset()

    rows = await db.execute(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            UserRole.user_id == user_id,
            Role.is_active.is_(True),
            Permission.is_active.is_(True),
        )
    )
    return frozenset(code for (code,) in rows.all())


def _subject_id(current_user: CurrentUser) -> int:
    try:
        return int(str(current_user.get("sub")))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        ) from exc


def require(code: str) -> Callable:
    """A dependency that refuses the request unless the user holds ``code``."""

    if code not in CODES:
        # A typo in a route guard must fail at import, not at 3 a.m.
        raise ValueError(
            f"unknown permission code {code!r}; declare it in app/core/permissions.py"
        )

    async def guard(
        request: Request,
        current_user: CurrentUserDependency,
        db: DatabaseSession,
    ) -> CurrentUser:
        if get_settings().PERMISSION_ENFORCEMENT == "off":
            return current_user

        subject = _subject_id(current_user)

        # Memoised on the request, not in a ContextVar: two guards on one route
        # are two sibling dependencies, and a value written to a context
        # variable inside one is not reliably visible to the other. The request
        # object is shared by definition, and is discarded with the request - so
        # a revoked role still stops working on the next one.
        cached = getattr(request.state, "permissions", None)
        cached_for = getattr(request.state, "permissions_actor", None)
        if cached is not None and cached_for == subject:
            held = cached
        else:
            held = await permissions_for_user(db, subject)
            request.state.permissions = held
            request.state.permissions_actor = subject
        if code not in held:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires the {code} permission.",
            )
        return current_user

    setattr(guard, PERMISSION_MARKER, code)
    guard.__name__ = f"require_{code.replace('.', '_')}"
    return guard


def route_permission(route) -> str | None:
    """The code a route demands, or ``None`` when it declares no guard."""

    for dependency in getattr(route, "dependencies", []) or []:
        code = getattr(getattr(dependency, "dependency", None), PERMISSION_MARKER, None)
        if code:
            return code

    dependant = getattr(route, "dependant", None)
    if dependant is not None:
        for sub in dependant.dependencies:
            code = getattr(sub.call, PERMISSION_MARKER, None)
            if code:
                return code
    return None


async def default_deny(request: Request) -> None:
    """Router-level check: a route with no guard is refused under ``enforce``.

    Attached once, to the v1 router, so that a route added tomorrow without a
    guard is closed rather than open. That is the whole point: the failure mode
    this prevents is a new endpoint that forgets, not an old one that was
    reviewed.
    """

    mode = get_settings().PERMISSION_ENFORCEMENT
    if mode == "off":
        return

    route = request.scope.get("route")
    if route is None or route_permission(route) is not None:
        return

    path = request.url.path
    if path in PUBLIC_PATHS or path in AUTHENTICATED_ONLY_PATHS:
        return
    if path.startswith(SETUP_PREFIX):
        return

    if mode == "warn":
        import logging

        logging.getLogger("hhms.permissions").warning(
            "route %s %s declares no permission guard", request.method, path
        )
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "This route declares no permission guard and is refused by default. "
            "Add require(<code>) to the route."
        ),
    )


#: Routes that require a login but no particular permission: they return
#: something about the caller themselves. Kept separate from PUBLIC_PATHS so that
#: "needs a token" and "needs no token" never get confused in review.
AUTHENTICATED_ONLY_PATHS = frozenset(
    {
        "/api/v1/navigation",
        "/api/v1/home",
    }
)


#: The setup wizard runs before any user exists, so it cannot be guarded by a
#: permission. It carries its own gate: the setup code, exchanged for a token with
#: ``scope: setup``. Listed here so default deny allows it deliberately.
#: A prefix rather than a set of exact paths: ``/setup/steps/{step}`` is a route
#: template, and the request carries a literal path that will never match it.
SETUP_PREFIX = "/api/v1/setup/"


#: Routes that must work before a user is authenticated, or that carry no
#: hospital data. Everything else needs a guard.
PUBLIC_PATHS = frozenset(
    {
        # Liveness and readiness probes: a load balancer or the CI smoke test
        # cannot present a token, and these return no hospital data.
        "/api/v1/health",
        "/api/v1/health/live",
        "/api/v1/health/ready",
        # Discovery tells a LAN client where the server is, before it has a
        # token. It exposes a name and a version, nothing more.
        "/api/v1/health/discovery",
        # Authentication itself, and the profile of the user just authenticated.
        "/api/v1/auth/login",
        "/api/v1/auth/me",
    }
)


DefaultDeny = Annotated[None, Depends(default_deny)]


__all__ = [
    "AUTHENTICATED_ONLY_PATHS",
    "DefaultDeny",
    "SETUP_PREFIX",
    "PERMISSION_MARKER",
    "PUBLIC_PATHS",
    "default_deny",
    "permissions_for_user",
    "require",
    "route_permission",
]
