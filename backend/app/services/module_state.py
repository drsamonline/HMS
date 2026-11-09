"""
Reading and changing which modules this hospital has enabled.

The rules live here rather than in the endpoint, because they are the rules an
assessment asks about: enabling a module brings its prerequisites with it,
disabling refuses if something depends on it, and disabling never deletes a
record.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleException, ResourceNotFoundException
from app.services import audit
from app.models.module_state import ModuleState
from app.modules.registry import BY_CODE, dependents, resolve


async def enabled_codes(db: AsyncSession) -> set[str]:
    """The module codes switched on for this installation."""

    rows = await db.execute(
        select(ModuleState.module_code).where(ModuleState.is_enabled.is_(True))
    )
    codes = {code for (code,) in rows.all()}
    # Core is not switchable, so it is always on whatever the table says.
    return codes | {module.code for module in BY_CODE.values() if module.is_core}


async def is_enabled(db: AsyncSession, code: str) -> bool:
    return code in await enabled_codes(db)


async def enable(
    db: AsyncSession, code: str, *, actor_id: int | None = None
) -> set[str]:
    """Switch a module on, with its prerequisites. Returns the modules changed."""

    if code not in BY_CODE:
        raise ResourceNotFoundException(f"Unknown module: {code}")

    current = await enabled_codes(db)
    wanted = resolve(code, current)
    changed = wanted - current

    now = datetime.now(UTC)
    for module_code in sorted(wanted):
        state = await _get_or_create(db, module_code)
        if state.is_enabled:
            continue
        state.is_enabled = True
        state.enabled_at = now
        state.enabled_by = actor_id
        state.disabled_at = None
        state.disabled_by = None

    # Switching a module on or off is an administrative act an assessor asks
    # about, so it goes in the trail like any other change.
    for module_code in sorted(changed):
        await audit.record(
            db,
            activity="module.enable",
            entity_name="ModuleState",
            entity_id=None,
            after={"module_code": module_code, "is_enabled": True},
            reason=f"Enabled by request for {code}",
        )

    await db.flush()
    return changed


async def disable(
    db: AsyncSession, code: str, *, actor_id: int | None = None
) -> None:
    """Switch a module off. Refuses if another enabled module depends on it."""

    if code not in BY_CODE:
        raise ResourceNotFoundException(f"Unknown module: {code}")

    module = BY_CODE[code]
    if module.is_core:
        raise BusinessRuleException(
            f"{module.name} is the core module and cannot be disabled."
        )

    current = await enabled_codes(db)
    blocking = [name for name in dependents(code) if name in current]
    if blocking:
        raise BusinessRuleException(
            f"Cannot disable {module.name}: "
            f"{', '.join(sorted(blocking))} depend on it."
        )

    state = await _get_or_create(db, code)
    state.is_enabled = False
    state.disabled_at = datetime.now(UTC)
    state.disabled_by = actor_id

    # No cascade, no delete, no touch of any clinical table: the whole point of
    # 7.3 is that switching a module off preserves its records.
    await audit.record(
        db,
        activity="module.disable",
        entity_name="ModuleState",
        entity_id=None,
        before={"module_code": code, "is_enabled": True},
        after={"module_code": code, "is_enabled": False},
    )
    await db.flush()


async def _get_or_create(db: AsyncSession, code: str) -> ModuleState:
    result = await db.execute(
        select(ModuleState).where(ModuleState.module_code == code)
    )
    state = result.scalar_one_or_none()
    if state is None:
        state = ModuleState(module_code=code, is_enabled=False)
        db.add(state)
        await db.flush()
    return state


__all__ = ["disable", "enable", "enabled_codes", "is_enabled"]
