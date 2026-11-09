"""
The wizard steps that create data rather than settings.

Four of the ten steps do not write a setting: they create the rows a hospital works
from. Wards become beds, departments become departments, and numbering becomes the
sequences every identifier is minted from.

Each handler is idempotent. A wizard is a thing people click twice, and a second
click that creates a duplicate ward or a second patient-number sequence would leave
a hospital with two numbering schemes and no way to tell which one is real.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleException
from app.models.bed import Bed
from app.models.department import Department
from app.models.number_sequence import NumberSequence
from app.services import audit

#: The sequences a hospital needs before it can register anybody.
REQUIRED_SEQUENCES = (
    ("patient_number", "P-", 6),
    ("visit_number", "V-", 6),
    ("opd_token", "T-", 4),
    ("invoice_number", "INV-", 6),
    ("receipt_number", "RCP-", 6),
    ("admission_number", "A-", 5),
)


async def apply_wards(db: AsyncSession, values: dict[str, Any]) -> dict:
    """Create beds from a ward list.

    ``values`` is ``{"wards": [{"name": "General", "beds": 10}, ...]}``. A ward is
    not a table in HHMS - beds carry a ward name - so the ward list becomes beds
    numbered within each ward.
    """

    wards = values.get("wards")
    if not isinstance(wards, list) or not wards:
        raise BusinessRuleException("The wards step needs a list of wards.")

    created = 0
    for ward in wards:
        name = str(ward.get("name", "")).strip()
        if not name:
            raise BusinessRuleException("Every ward needs a name.")
        try:
            count = int(ward.get("beds", 0))
        except (TypeError, ValueError) as exc:
            raise BusinessRuleException(f"Ward {name} needs a whole number of beds.") from exc
        if count < 0:
            raise BusinessRuleException(f"Ward {name} cannot have negative beds.")

        existing = (
            await db.execute(
                select(func.count()).select_from(Bed).where(Bed.ward == name)
            )
        ).scalar_one()

        # Idempotent by ward name: a second click tops the ward up rather than
        # creating a second ward with the same name and different numbering.
        for index in range(existing + 1, count + 1):
            now = datetime.now(UTC)
            db.add(
                Bed(
                    bed_number=f"{name[:3].upper()}-{index:02d}",
                    ward=name,
                    occupancy_status="available",
                    is_active=True,
                    # Set explicitly: the migration gives these a server default,
                    # and a schema built by create_all must not be the only place
                    # the two disagree.
                    created_at=now,
                    updated_at=now,
                )
            )
            created += 1

    await audit.record(
        db,
        activity="setup.wards",
        entity_name="Bed",
        entity_id=None,
        after={"wards": wards, "beds_created": created},
    )
    return {"beds_created": created}


async def apply_departments(db: AsyncSession, values: dict[str, Any]) -> dict:
    """Create departments from a list of names, skipping ones that exist."""

    departments = values.get("departments")
    if not isinstance(departments, list) or not departments:
        raise BusinessRuleException("The departments step needs a list of departments.")

    created: list[str] = []
    for entry in departments:
        name = str(entry).strip()
        if not name:
            raise BusinessRuleException("Every department needs a name.")
        existing = (
            await db.execute(select(Department).where(Department.name == name))
        ).scalar_one_or_none()
        if existing is not None:
            continue
        db.add(
            Department(
                code=name[:12].upper().replace(" ", "_"),
                name=name,
                department_type="clinical",
            )
        )
        created.append(name)

    await audit.record(
        db,
        activity="setup.departments",
        entity_name="Department",
        entity_id=None,
        after={"created": created},
    )
    return {"departments_created": created}


async def apply_numbering(db: AsyncSession, values: dict[str, Any]) -> dict:
    """Create the sequences identifiers are minted from.

    ``values`` may override a prefix, e.g. ``{"prefixes": {"patient_number": "HH-"}}``.
    A sequence that already exists is left alone: an installation that has been
    issuing numbers must not have its counter reset by a wizard.
    """

    prefixes = values.get("prefixes") or {}
    if not isinstance(prefixes, dict):
        raise BusinessRuleException("Prefixes must be a mapping of sequence to prefix.")

    created: list[str] = []
    for name, default_prefix, padding in REQUIRED_SEQUENCES:
        existing = (
            await db.execute(
                select(NumberSequence).where(NumberSequence.sequence_name == name)
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        db.add(
            NumberSequence(
                sequence_name=name,
                prefix=str(prefixes.get(name, default_prefix)),
                suffix="",
                current_value=0,
                padding_length=padding,
                reset_frequency="never",
                is_active=True,
            )
        )
        created.append(name)

    await audit.record(
        db,
        activity="setup.numbering",
        entity_name="NumberSequence",
        entity_id=None,
        after={"created": created, "prefixes": prefixes},
    )
    return {"sequences_created": created}


async def apply_money(db: AsyncSession, values: dict[str, Any]) -> dict:
    """Set the money-facing prefixes, on the sequences that already exist or will.

    Kept separate from numbering because it is a separate decision: a hospital
    chooses its patient-number format once, and its invoice prefix with its
    accountant.
    """

    prefixes = values.get("prefixes") or {}
    if not isinstance(prefixes, dict):
        raise BusinessRuleException("Prefixes must be a mapping of sequence to prefix.")

    allowed = {"invoice_number", "receipt_number"}
    unknown = set(prefixes) - allowed
    if unknown:
        raise BusinessRuleException(
            f"The money step sets only {', '.join(sorted(allowed))}; it was given "
            f"{', '.join(sorted(unknown))}."
        )

    updated: list[str] = []
    for name, prefix in prefixes.items():
        row = (
            await db.execute(
                select(NumberSequence).where(NumberSequence.sequence_name == name)
            )
        ).scalar_one_or_none()
        if row is None:
            continue
        before = row.prefix
        row.prefix = str(prefix)
        await audit.record(
            db,
            activity="setup.money",
            entity_name="NumberSequence",
            entity_id=row.id,
            before={"prefix": before},
            after={"prefix": row.prefix},
        )
        updated.append(name)

    return {"prefixes_updated": updated}



__all__ = [
    "HANDLERS",
    "REQUIRED_SEQUENCES",
    "apply_departments",
    "apply_money",
    "apply_network",
    "apply_numbering",
    "apply_people",
    "apply_wards",
]


# --------------------------------------------------------------- people (B24)
async def apply_people(db: AsyncSession, values: dict[str, Any]) -> dict:
    """Create the first real administrator.

    This is the handover. Until this step every write went through the setup token;
    after it there is a person who can log in, and the setup token's job is done.

    The role is the all-access ``administrator`` the catalogue seeds, so the first
    account is not accidentally crippled by a missing grant.
    """

    from app.auth.password import hash_password
    from app.models.role import Role
    from app.models.user import User
    from app.models.user_role import UserRole

    username = str(values.get("username", "")).strip()
    password = str(values.get("password", ""))
    full_name = str(values.get("full_name", "")).strip()

    if not username:
        raise BusinessRuleException("The people step needs a username.")
    if len(password) < 8:
        raise BusinessRuleException("The administrator password must be at least 8 characters.")
    if not full_name:
        raise BusinessRuleException("The people step needs the administrator's full name.")

    existing = (
        await db.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()
    if existing is not None:
        # Idempotent: a second click does not create a second administrator, and
        # does not silently reset the password of the first.
        return {"user_created": False, "username": username}

    user = User(
        username=username,
        password_hash=hash_password(password),
        full_name=full_name,
        email=str(values["email"]).strip().lower() if values.get("email") else None,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    role = (
        await db.execute(
            select(Role).where(func.lower(Role.role_name) == "administrator")
        )
    ).scalar_one_or_none()
    if role is None:
        role = Role(role_name="administrator", description="Full access")
        db.add(role)
        await db.flush()

    db.add(UserRole(user_id=user.id, role_id=role.id))

    await audit.record(
        db,
        activity="setup.administrator",
        entity_name="User",
        entity_id=user.id,
        after={"username": username, "full_name": full_name, "role": "administrator"},
    )
    return {"user_created": True, "username": username}


# -------------------------------------------------------------- network (B24)
async def apply_network(db: AsyncSession, values: dict[str, Any]) -> dict:
    """Stage the network values; they take effect after a restart.

    The port and the discovery keys are read before the database is open, so they
    cannot live in it (D-032). This step validates them and stages them for the
    restart that follows setup, rather than pretending they are already applied.
    """

    from pathlib import Path

    import json

    from app.config.runtime_paths import application_root

    staged: dict[str, Any] = {}

    if "SERVER_PORT" in values:
        try:
            port = int(values["SERVER_PORT"])
        except (TypeError, ValueError) as exc:
            raise BusinessRuleException("The server port must be a whole number.") from exc
        if not 1024 <= port <= 65535:
            raise BusinessRuleException("The server port must be between 1024 and 65535.")
        staged["SERVER_PORT"] = port

    if "DISCOVERY_ENABLED" in values:
        staged["DISCOVERY_ENABLED"] = bool(values["DISCOVERY_ENABLED"])

    if "DISCOVERY_PORT" in values:
        try:
            discovery_port = int(values["DISCOVERY_PORT"])
        except (TypeError, ValueError) as exc:
            raise BusinessRuleException("The discovery port must be a whole number.") from exc
        if not 1024 <= discovery_port <= 65535:
            raise BusinessRuleException("The discovery port must be between 1024 and 65535.")
        staged["DISCOVERY_PORT"] = discovery_port

    if "DISCOVERY_NAME" in values:
        name = str(values["DISCOVERY_NAME"]).strip()
        if not name:
            raise BusinessRuleException("The discovery name cannot be empty.")
        staged["DISCOVERY_NAME"] = name

    target = Path(application_root()) / "data" / "pending-network.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(staged, indent=2), encoding="utf-8")

    await audit.record(
        db,
        activity="setup.network",
        entity_name="SetupState",
        entity_id=None,
        after={"staged": staged, "file": str(target)},
    )
    return {
        "staged": staged,
        "restart_required": True,
        "note": (
            "These take effect when the server restarts. They are read before the "
            "database is opened, so they cannot be stored in it."
        ),
    }


HANDLERS = {
    "wards": apply_wards,
    "departments": apply_departments,
    "money": apply_money,
    "numbering": apply_numbering,
    "people": apply_people,
    "network": apply_network,
}
