"""
The module gate: a route belonging to a disabled module does not exist.

`MASTER_SPECIFICATION` 7.3 says a disabled module's menus and workflows disappear
while its records are preserved. This is the workflow half: the router is still in
the process, but every request to it answers 404 - the honest answer for a hospital
that does not have the module, and better than 403, which would tell the caller the
route exists and they merely lack a permission.

Why the routers stay mounted rather than being omitted at startup: module state is
data, and it changes while the server runs. Omitting at startup would mean a
restart after every switch, and a hospital administrator who toggles pharmacy off
and sees it still working until Tuesday.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundException
from app.dependencies.database import DatabaseSession
from app.models.module_state import ModuleState
from app.modules.registry import BY_CODE

#: Set on the request once per request, so a page that loads six endpoints of the
#: same module does not run the same query six times.
_MODULE_CACHE_ATTR = "enabled_modules"


CORE_ONLY = frozenset(code for code, spec in BY_CODE.items() if spec.is_core)


async def enabled_modules(db: AsyncSession) -> frozenset[str]:
    """The modules switched on for this installation, core always included.

    A database without the ``ModuleState`` table has not been migrated. That is a
    broken installation rather than a hospital with no modules, and the least
    surprising behaviour is to serve core and nothing else - not to raise a 500 on
    every request, and not to switch everything on.
    """

    from sqlalchemy.exc import OperationalError

    try:
        rows = await db.execute(
            select(ModuleState.module_code).where(ModuleState.is_enabled.is_(True))
        )
    except OperationalError:
        import logging

        logging.getLogger("hhms.modules").error(
            "ModuleState is missing: the database has not been migrated. "
            "Serving core only."
        )
        return CORE_ONLY

    codes = {code for (code,) in rows.all()}
    return frozenset(codes | CORE_ONLY)


async def _modules_for_request(request: Request, db: AsyncSession) -> frozenset[str]:
    cached = getattr(request.state, _MODULE_CACHE_ATTR, None)
    if cached is not None:
        return cached
    codes = await enabled_modules(db)
    setattr(request.state, _MODULE_CACHE_ATTR, codes)
    return codes


def require_module(code: str) -> Callable:
    """A dependency that answers 404 when ``code`` is not enabled."""

    if code not in BY_CODE:
        raise ValueError(f"unknown module {code!r}; declare it in app/modules/registry.py")

    async def gate(request: Request, db: DatabaseSession) -> None:
        enabled = await _modules_for_request(request, db)
        if code not in enabled:
            raise ResourceNotFoundException(
                f"The {BY_CODE[code].name} module is not enabled for this hospital."
            )

    gate.__name__ = f"require_module_{code}"
    return gate


ModuleGate = Annotated[None, Depends(lambda: None)]


__all__ = ["ModuleGate", "enabled_modules", "require_module"]
