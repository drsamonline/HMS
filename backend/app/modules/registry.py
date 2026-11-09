"""
The HHMS module registry.

`MASTER_SPECIFICATION` sections 7.2 and 7.3 have always required optional modules
that a hospital switches on and off, preserving every record when one goes off.
Nothing implemented it: every module was always mounted, which is why a
twelve-bed clinic saw Procurement and System Health on the same sidebar as a
hundred-bed teaching hospital.

This module is the capability half of that requirement - what a module is, what
it depends on, what it contributes. The state half is the `ModuleState` table,
because which modules a hospital uses is data about the hospital, not about the
software.

Split deliberately: capability in code so it can be imported at startup to decide
which routers to mount (B17); state in the database so an administrator can change
it without a release.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModuleSpec:
    """One switchable module."""

    code: str
    name: str
    summary: str
    depends_on: tuple[str, ...] = ()
    recommends: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    is_core: bool = False
    field: tuple = ()


MODULES: tuple[ModuleSpec, ...] = (
    ModuleSpec(
        code="core",
        name="Core clinical",
        summary="Registration, OPD, prescriptions, security and reporting.",
        is_core=True,
        permissions=(
            "patients.read", "patients.write", "patients.deactivate",
            "opd.read", "opd.write",
            "clinical.read", "clinical.write",
            "prescriptions.read", "prescriptions.write",
            "reporting.read", "reporting.export",
        ),
    ),
    ModuleSpec(
        code="pharmacy",
        name="Pharmacy",
        summary="Dispensing, batches and expiry.",
        depends_on=("core",),
        recommends=("stock",),
        permissions=("pharmacy.read", "pharmacy.write"),
    ),
    ModuleSpec(
        code="stock",
        name="Simple stock register",
        summary="General stock, independent of pharmacy inventory.",
        depends_on=("core",),
        permissions=("inventory.read", "inventory.write"),
    ),
    ModuleSpec(
        code="ipd",
        name="Inpatient department",
        summary="Admissions, beds, assessments and discharge.",
        depends_on=("core",),
        recommends=("mrd",),
        permissions=("ipd.read", "ipd.write"),
    ),
    ModuleSpec(
        code="laboratory",
        name="Laboratory",
        summary="Investigation requests and results.",
        depends_on=("core",),
        permissions=("investigations.read", "investigations.write"),
    ),
    ModuleSpec(
        code="billing",
        name="Billing",
        summary="Invoices, payments, receipts and refunds.",
        depends_on=("core",),
        permissions=("billing.read", "billing.write", "billing.void"),
    ),
    ModuleSpec(
        code="mrd",
        name="Medical records",
        summary="Document archive, filing and retrieval.",
        depends_on=("core",),
        recommends=("ipd",),
        permissions=("mrd.read", "mrd.write"),
    ),
    ModuleSpec(
        code="nabh",
        name="NABH compliance",
        summary="Consent, indicators, incidents, infection control and the evidence pack.",
        depends_on=("core",),
        recommends=("ipd", "laboratory", "billing"),
        permissions=("audit.read", "audit.export"),
    ),
)

BY_CODE: dict[str, ModuleSpec] = {module.code: module for module in MODULES}


def depends_on(code: str) -> tuple[str, ...]:
    """The transitive dependency set of a module, core included."""

    seen: list[str] = []
    stack = list(BY_CODE[code].depends_on)
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.append(current)
        stack.extend(BY_CODE[current].depends_on)
    return tuple(seen)


def resolve(code: str, enabled: set[str]) -> set[str]:
    """Enabling one module enables its dependencies and reports the closure.

    Nothing is ever disabled as a side effect. Turning a module on may turn its
    prerequisites on; turning one off never turns another off.
    """

    if code not in BY_CODE:
        raise KeyError(code)
    return set(enabled) | {code} | set(depends_on(code))


def dependents(code: str) -> tuple[str, ...]:
    """Modules that would break if ``code`` were switched off."""

    return tuple(
        module.code
        for module in MODULES
        if code in depends_on(module.code)
    )


__all__ = [
    "BY_CODE",
    "MODULES",
    "ModuleSpec",
    "dependents",
    "depends_on",
    "resolve",
]
