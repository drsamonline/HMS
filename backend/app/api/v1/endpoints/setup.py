"""First-run setup API.

Everything here answers before a user exists, so none of it can be permission
guarded. What replaces the permission is the setup code: the status endpoint hands
out a code to the server log, and every write requires a token minted from it.

Scope is a claim on the token rather than a table of sessions, so a setup token
cannot be used as a login and a login cannot be used to finish setup.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.jwt import create_access_token
from app.core.exceptions import BusinessRuleException, ResourceNotFoundException
from app.core.settings_catalogue import BY_KEY
from app.dependencies.database import DatabaseSession
from app.dependencies.setup import SetupAuthorised
from app.modules.registry import BY_CODE
from app.services import module_state, settings_store, setup, setup_steps

router = APIRouter(prefix="/setup", tags=["Setup"])

#: Settings a wizard step may write, by step. Declared so a step cannot reach a
#: setting it has no business touching.
STEP_SETTINGS: dict[str, tuple[str, ...]] = {
    "identity": ("HOSPITAL_NAME", "HOSPITAL_CODE", "TIME_ZONE", "DATE_FORMAT", "DATETIME_FORMAT"),
    "data": (
        "LIVE_DATA_YEARS", "ONLINE_ARCHIVE_YEARS", "COLD_ARCHIVE_YEARS",
        "AUTO_BACKUP_ENABLED", "AUTO_MAINTENANCE_ENABLED",
    ),
    "network": ("SERVER_PORT", "DISCOVERY_ENABLED", "DISCOVERY_PORT", "DISCOVERY_NAME"),
    "numbering": (),
    "money": (),
    "wards": (),
    "departments": (),
    "people": (),
    "modules": (),
    "review": (),
}


class UnlockRequest(BaseModel):
    code: str


class StepRequest(BaseModel):
    values: dict[str, Any] = {}


@router.get("/status")
async def setup_status(db: DatabaseSession) -> dict:
    """Public: whether this installation needs setting up, and which steps remain.

    Deliberately says nothing about the hospital, the database or the users. A LAN
    client learns only that the server is new.
    """

    result = await setup.status(db)
    # A GET that may have issued a code has to persist it, or the next request
    # would issue a different one and the first would never work.
    await db.commit()
    return result


@router.post("/unlock")
async def unlock(payload: UnlockRequest, db: DatabaseSession) -> dict:
    """Exchange the setup code for a short-lived setup token."""

    try:
        await setup.unlock(db, payload.code)
    except BusinessRuleException as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    await db.commit()

    token = create_access_token(
        subject="setup",
        expires_delta=timedelta(minutes=60),
        additional_claims={"scope": "setup"},
    )
    return {"token": token, "token_type": "bearer", "expires_in_minutes": 60}


@router.post("/steps/{step}")
async def apply_step(
    step: str,
    payload: StepRequest,
    db: DatabaseSession,
    _: SetupAuthorised,
) -> dict:
    """Apply one step: write its settings, enable its modules, mark it done."""

    if step not in setup.STEPS:
        raise HTTPException(status_code=404, detail=f"Unknown setup step: {step}")

    # A step either writes settings or creates rows; the two are validated
    # differently, so a step may not do both.
    handler = setup_steps.HANDLERS.get(step)
    if handler is not None:
        try:
            outcome = await handler(db, payload.values)
        except BusinessRuleException as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        await setup.mark_step(db, step)
        await db.commit()
        return {"step": step, "applied": True, **outcome, **(await setup.status(db))}

    allowed = STEP_SETTINGS.get(step, ())
    for key in payload.values:
        if key not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{key} is not part of the {step} step.",
            )

    try:
        # Validate the whole step before writing any of it, as the configuration
        # API does - a step lands or fails together.
        for key, value in payload.values.items():
            await settings_store.validate(db, key, value)
    except (BusinessRuleException, ResourceNotFoundException) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    for key, value in payload.values.items():
        await settings_store.set_value(db, key, value)

    if step == "modules":
        wanted = payload.values.get("modules")
        if not isinstance(wanted, list):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The modules step needs a list under 'modules'.",
            )
        unknown = [code for code in wanted if code not in BY_CODE]
        if unknown:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown modules: {', '.join(unknown)}",
            )
        for code in wanted:
            await module_state.enable(db, code)

    await setup.mark_step(db, step)
    await db.commit()

    return {"step": step, "applied": True, **(await setup.status(db))}


@router.get("/review")
async def review(db: DatabaseSession, _: SetupAuthorised) -> dict:
    """Every choice so far, with the mandatory steps still missing named."""

    return await setup.review(db)


@router.get("/export")
async def export_answers(db: DatabaseSession, _: SetupAuthorised) -> dict:
    """The wizard's answers as a provisioning file.

    The same shape the configuration API exports, plus the modules - which is
    everything a second installation needs to be set up identically without
    clicking through ten steps again.
    """

    from app.services import module_state, settings_store

    effective = await settings_store.effective_all(db)
    return {
        "schema": 1,
        "settings": {
            key: result.value
            for key, result in effective.items()
            if result.source == "database"
        },
        "modules": sorted(await module_state.enabled_codes(db)),
    }


@router.post("/finish")
async def finish(db: DatabaseSession, _: SetupAuthorised) -> dict:
    """Close setup. Refuses while a mandatory step is missing."""

    try:
        await setup.complete(db)
    except BusinessRuleException as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    await db.commit()

    # The network values were staged, not applied (D-032). This is where they
    # reach the environment file - the only place the server reads them from.
    from app.config.runtime_paths import application_root

    written = setup.materialise_network(str(application_root()))

    return {
        "setup_required": False,
        "restart_required": bool(written),
        "network_keys_written": written,
        "note": (
            "Restart the server so the network settings take effect."
            if written
            else "Setup is complete."
        ),
    }


__all__ = ["STEP_SETTINGS", "router"]
