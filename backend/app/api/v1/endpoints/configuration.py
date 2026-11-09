"""Configuration API.

Separate from ``/settings``, which manages the older ``SystemSetting`` key/value
pairs. This endpoint is the one the setup wizard drives: it exposes the catalogue
from B19, the effective value and where it came from, and a validated write path.

Two behaviours matter more than the shape of the JSON:

* a batch write is all-or-nothing. One bad value rejects the whole request, so a
  wizard step that sets six things either lands or does not - never half.
* a bootstrap value is refused here with a message that says where it *can* be
  set, because the server reads it before the database is open (D-032).

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.exceptions import BusinessRuleException, ResourceNotFoundException
from app.core.settings_catalogue import GROUPS, SOURCE_DATABASE, in_group
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.dependencies.permissions import require
from app.services import audit, settings_store

router = APIRouter(prefix="/configuration", tags=["Configuration"])


class SettingRead(BaseModel):
    key: str
    group: str
    label: str
    description: str
    type: str
    value: Any = None
    default: Any = None
    source: str
    restart_required: bool
    bootstrap: bool
    choices: list[str] = Field(default_factory=list)


class SettingPatch(BaseModel):
    values: dict[str, Any]


class SettingReset(BaseModel):
    key: str


def _actor_id(current_user) -> int | None:
    try:
        return int(str(current_user.get("sub")))
    except (TypeError, ValueError):
        return None


def _read(spec, effective) -> SettingRead:
    value = effective.value
    if spec.type == "secret" and value:
        # A secret is never echoed back, only its existence.
        value = "********"
    return SettingRead(
        key=spec.key,
        group=spec.group,
        label=spec.label,
        description=spec.description,
        type=spec.type,
        value=value,
        default=None if spec.type == "secret" else spec.default,
        source=effective.source,
        restart_required=spec.restart_required,
        bootstrap=spec.bootstrap,
        choices=list(spec.choices),
    )


@router.get(
    "",
    response_model=list[SettingRead],
    dependencies=[Depends(require("settings.read"))],
)
async def list_settings(db: DatabaseSession) -> list[SettingRead]:
    """Every setting, in group order, with its value and its source."""

    effective = await settings_store.effective_all(db)
    return [
        _read(spec, effective[spec.key])
        for group in GROUPS
        for spec in in_group(group)
    ]


@router.patch(
    "",
    response_model=list[SettingRead],
    dependencies=[Depends(require("settings.write"))],
)
async def patch_settings(
    payload: SettingPatch,
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> list[SettingRead]:
    """Set several settings at once. One invalid value rejects the batch."""

    if not payload.values:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No settings were supplied.",
        )

    # Validate the whole batch before writing any of it: a wizard step that sets
    # six values must land or fail together.
    staged: list[tuple[str, Any]] = []
    for key, value in payload.values.items():
        try:
            await settings_store.validate(db, key, value)
        except (BusinessRuleException, ResourceNotFoundException) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        staged.append((key, value))

    actor = _actor_id(current_user)
    for key, value in staged:
        await settings_store.set_value(db, key, value, actor_id=actor)

    await db.commit()

    effective = await settings_store.effective_all(db)
    return [_read(effective[key].spec, effective[key]) for key, _ in staged]


@router.post(
    "/reset",
    response_model=SettingRead,
    dependencies=[Depends(require("settings.write"))],
)
async def reset_setting(
    payload: SettingReset,
    db: DatabaseSession,
) -> SettingRead:
    """Remove an override, returning the setting to the environment or default."""

    try:
        result = await settings_store.reset_value(db, payload.key)
    except ResourceNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    await db.commit()
    return _read(result.spec, result)


@router.get(
    "/export",
    dependencies=[Depends(require("settings.read"))],
)
async def export_settings(db: DatabaseSession) -> dict:
    """The overrides only - what makes this installation different from a default.

    Exporting all forty-four values would make a provisioning file that silently
    pins today's defaults forever.
    """

    effective = await settings_store.effective_all(db)
    return {
        "schema": 1,
        "values": {
            key: result.value
            for key, result in effective.items()
            if result.source == SOURCE_DATABASE
        },
    }


@router.post(
    "/import",
    response_model=list[SettingRead],
    dependencies=[Depends(require("settings.write"))],
)
async def import_settings(
    payload: SettingPatch,
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> list[SettingRead]:
    """Apply an exported file to this installation. Same all-or-nothing rule."""

    return await patch_settings(payload, db, current_user)


__all__ = ["router"]
