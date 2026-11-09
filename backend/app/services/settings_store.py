"""
Reading and writing settings, with a stated precedence.

The rule is simple and is the whole point of this module: a value set from the
interface wins, then the environment, then the catalogue default. Every read
returns the source alongside the value, so the settings screen can say where a
number came from instead of pretending every value was chosen by the hospital.

Coercion is done from the catalogue's declared type rather than by guessing, so a
typo in the database is reported as a broken setting rather than silently becoming
a string where an integer was expected.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.exceptions import BusinessRuleException, ResourceNotFoundException
from app.core.settings_catalogue import (
    BY_KEY,
    SOURCE_DATABASE,
    SOURCE_DEFAULT,
    SOURCE_ENV,
    SettingSpec,
)
from app.models.setting_value import SettingValue
from app.services import audit


@dataclass(frozen=True)
class Effective:
    """A setting's value and where it came from."""

    spec: SettingSpec
    value: object
    source: str

    @property
    def is_default(self) -> bool:
        return self.source == SOURCE_DEFAULT


def _coerce(spec: SettingSpec, raw: str):
    """Turn stored text into the declared type, or refuse."""

    if spec.type == "integer":
        try:
            return int(raw)
        except ValueError as exc:
            raise BusinessRuleException(
                f"{spec.label} must be a whole number."
            ) from exc
    if spec.type == "boolean":
        lowered = str(raw).strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
        raise BusinessRuleException(f"{spec.label} must be true or false.")
    if spec.type == "list":
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BusinessRuleException(
                f"{spec.label} must be a list."
            ) from exc
        if not isinstance(parsed, list):
            raise BusinessRuleException(f"{spec.label} must be a list.")
        return tuple(str(item) for item in parsed)
    if spec.type == "decimal":
        try:
            return float(raw)
        except ValueError as exc:
            raise BusinessRuleException(f"{spec.label} must be a number.") from exc

    if spec.choices and str(raw) not in spec.choices:
        raise BusinessRuleException(
            f"{spec.label} must be one of: {', '.join(spec.choices)}."
        )
    return str(raw)


def _serialise(spec: SettingSpec, value) -> str | None:
    if value is None:
        return None
    if spec.type == "list":
        return json.dumps(list(value))
    if spec.type == "boolean":
        return "true" if value else "false"
    return str(value)


async def _overrides(db: AsyncSession) -> dict[str, str]:
    rows = await db.execute(select(SettingValue.setting_key, SettingValue.value_text))
    return {key: value for key, value in rows.all() if value is not None}


async def effective_all(db: AsyncSession) -> dict[str, Effective]:
    """Every setting, with its value and source."""

    overrides = await _overrides(db)
    current = get_settings()
    result: dict[str, Effective] = {}

    for spec in BY_KEY.values():
        if spec.key in overrides:
            result[spec.key] = Effective(
                spec=spec, value=_coerce(spec, overrides[spec.key]), source=SOURCE_DATABASE
            )
            continue

        field_value = getattr(current, spec.key, None)
        if field_value is not None and field_value != spec.default:
            value = tuple(field_value) if spec.type == "list" else field_value
            result[spec.key] = Effective(spec=spec, value=value, source=SOURCE_ENV)
            continue

        result[spec.key] = Effective(spec=spec, value=spec.default, source=SOURCE_DEFAULT)

    return result


async def effective(db: AsyncSession, key: str) -> Effective:
    if key not in BY_KEY:
        raise ResourceNotFoundException(f"Unknown setting: {key}")
    return (await effective_all(db))[key]


async def validate(db: AsyncSession, key: str, value) -> None:
    """Check that a value would be accepted, without storing it.

    The API validates a whole batch before writing any of it, so a wizard step
    that sets six values cannot land five and fail on the sixth.
    """

    spec = BY_KEY.get(key)
    if spec is None:
        raise ResourceNotFoundException(f"Unknown setting: {key}")
    if spec.bootstrap:
        raise BusinessRuleException(
            f"{spec.label} is read before the database is open and can only be set "
            "in the server's environment file."
        )

    text = _serialise(spec, value)
    if text is not None:
        _coerce(spec, text)


async def set_value(
    db: AsyncSession, key: str, value, *, actor_id: int | None = None
) -> Effective:
    """Store an override. Bootstrap values are refused - see D-032."""

    spec = BY_KEY.get(key)
    if spec is None:
        raise ResourceNotFoundException(f"Unknown setting: {key}")
    if spec.bootstrap:
        raise BusinessRuleException(
            f"{spec.label} is read before the database is open and can only be set "
            "in the server's environment file."
        )

    text = _serialise(spec, value)
    if text is not None:
        _coerce(spec, text)  # validate before storing

    row = (
        await db.execute(select(SettingValue).where(SettingValue.setting_key == key))
    ).scalar_one_or_none()
    if row is None:
        row = SettingValue(setting_key=key)
        db.add(row)
    before = row.value_text
    row.value_text = text
    row.updated_by = actor_id

    # A changed setting alters how the hospital runs; it belongs in the trail
    # beside any other administrative act.
    await audit.record(
        db,
        activity="setting.update",
        entity_name="SettingValue",
        entity_id=None,
        before={"key": key, "value": before},
        after={"key": key, "value": text},
    )

    await db.flush()
    return await effective(db, key)


async def reset_value(db: AsyncSession, key: str) -> Effective:
    """Remove an override, returning the setting to env or default."""

    if key not in BY_KEY:
        raise ResourceNotFoundException(f"Unknown setting: {key}")

    row = (
        await db.execute(select(SettingValue).where(SettingValue.setting_key == key))
    ).scalar_one_or_none()
    if row is not None:
        await audit.record(
            db,
            activity="setting.reset",
            entity_name="SettingValue",
            entity_id=None,
            before={"key": key, "value": row.value_text},
            after={"key": key, "value": None},
        )
        await db.delete(row)
        await db.flush()
    return await effective(db, key)




async def restart_status(db: AsyncSession) -> dict:
    """Which restart-required settings differ from what this process is running.

    A hospital changes its port in the settings screen, nothing appears to happen,
    and nobody can tell whether the change was saved or lost. This answers that:
    the values are stored, the running process still has the old ones, and the
    list names the difference.
    """

    effective = await effective_all(db)
    running = get_settings()

    pending: dict[str, dict] = {}
    for key, result in effective.items():
        if not result.spec.restart_required:
            continue
        current = getattr(running, key, None)
        if result.spec.type == "list" and current is not None:
            current = tuple(current)
        if current != result.value:
            pending[key] = {
                "stored": result.value,
                "running": current,
                "label": result.spec.label,
            }

    return {
        "restart_required": bool(pending),
        "pending": pending,
        "note": (
            "Restart the server for these to take effect."
            if pending
            else "The running process matches the stored configuration."
        ),
    }


__all__ = [
    "Effective",
    "effective",
    "effective_all",
    "reset_value",
    "restart_status",
    "set_value",
    "validate",
]
