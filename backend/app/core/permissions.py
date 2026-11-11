"""
The HHMS permission catalogue.

One declaration, in code, of every permission the system recognises, and one
declaration of what each role is granted by default. The migration seeds the
database from this file, the guard in build plan B13 checks against it, and the
tests assert that the two never drift apart.

Why the catalogue lives in code rather than only in the database: a permission is
a fact about the software, not about a hospital. A code that no route checks is a
code an administrator can grant and nothing will happen; a route that checks a
code nobody declared is a route nobody can open. Both are caught by declaring
them here and testing against reality.

Shape of a code
---------------
``module.action``, lower case, dot separated. ``action`` is a verb, not a noun:
``patients.read``, ``billing.void``, ``audit.export``. Filtering the trail or an
administrator's screen by a verb reads correctly; by a noun it does not.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionSpec:
    """One grantable permission."""

    code: str
    module: str
    name: str
    description: str


def _p(code: str, module: str, name: str, description: str) -> PermissionSpec:
    return PermissionSpec(code=code, module=module, name=name, description=description)


#: Every permission HHMS recognises. Ordered by module so the administration
#: screen reads in a predictable sequence.
PERMISSIONS: tuple[PermissionSpec, ...] = (
    # ---------------------------------------------------------- patients
    _p("patients.read", "patients", "View patients", "Search and read patient demographics and history."),
    _p("patients.write", "patients", "Register and edit patients", "Create a patient and edit demographics."),
    _p("patients.deactivate", "patients", "Deactivate a patient", "Mark a patient inactive without deleting records."),
    # --------------------------------------------------------------- opd
    _p("opd.read", "opd", "View the OPD queue", "See today's tokens and queue state."),
    _p("opd.write", "opd", "Issue and call tokens", "Generate, call and complete OPD tokens."),
    # ----------------------------------------------------------- clinical
    _p("clinical.read", "clinical", "View clinical records", "Read case records, diagnoses, notes and assessments."),
    _p("clinical.write", "clinical", "Record clinical notes", "Write case records, diagnoses, follow-ups and assessments."),
    # ------------------------------------------------------ prescriptions
    _p("prescriptions.read", "prescriptions", "View prescriptions", "Read prescriptions and their items."),
    _p("prescriptions.write", "prescriptions", "Prescribe", "Create and amend prescriptions."),
    # --------------------------------------------------------------- ipd
    _p("ipd.read", "ipd", "View admissions", "Read admissions, beds and discharges."),
    _p("ipd.write", "ipd", "Admit and discharge", "Admit, transfer, update and discharge a patient."),
    # ----------------------------------------------------- investigations
    _p("investigations.read", "investigations", "View investigations", "Read investigation requests and results."),
    _p("investigations.write", "investigations", "Request and report investigations", "Raise requests, enter and amend results."),
    # ---------------------------------------------------------- pharmacy
    _p("pharmacy.read", "pharmacy", "View pharmacy", "Read medicines, batches and dispensing."),
    _p("pharmacy.write", "pharmacy", "Dispense and maintain pharmacy", "Dispense, and maintain medicine and batch masters."),
    # --------------------------------------------------------- inventory
    _p("inventory.read", "inventory", "View stock", "Read stock balances, cards and transactions."),
    _p("inventory.write", "inventory", "Adjust stock", "Post stock receipts and issues."),
    # ------------------------------------------------------- procurement
    _p("procurement.read", "procurement", "View procurement", "Read suppliers, purchase orders and goods receipts."),
    _p("procurement.write", "procurement", "Raise orders and receive goods", "Create purchase orders and post goods receipts."),
    # ----------------------------------------------------------- billing
    _p("billing.read", "billing", "View billing", "Read invoices, payments and summaries."),
    _p("billing.write", "billing", "Bill and collect", "Raise invoices, record payments and add invoice items."),
    _p("billing.void", "billing", "Cancel an invoice", "Cancel an invoice or remove a line. Separated from billing.write because it is the permission an auditor asks about."),
    # --------------------------------------------------------------- mrd
    _p("mrd.read", "mrd", "View medical records", "Read documents, patient files and archives."),
    _p("mrd.write", "mrd", "File records", "Upload documents and manage the record archive."),
    # --------------------------------------------------------- reporting
    _p("reporting.read", "reporting", "View reports", "Read statistics and report envelopes."),
    _p("reporting.export", "reporting", "Export reports", "Render a report to PDF or CSV."),
    # ------------------------------------------------------------ audit
    _p("audit.read", "audit", "Read the audit trail", "Review who did what across the hospital."),
    _p("audit.export", "audit", "Export the audit trail", "Take a copy of the audit trail out of the system."),
    # --------------------------------------------------- administration
    _p("users.read", "users", "View users", "List user accounts."),
    _p("users.write", "users", "Manage users", "Create, edit, deactivate and re-role users."),
    _p("roles.read", "roles", "View roles", "List roles and their permissions."),
    _p("roles.write", "roles", "Manage roles", "Create roles and grant permissions."),
    _p("settings.read", "settings", "View settings", "Read hospital and system settings."),
    _p("settings.write", "settings", "Change settings", "Change hospital and system settings and number sequences."),
    _p("masters.read", "masters", "View masters", "Read departments, services, designations and ICD lookups."),
    _p("masters.write", "masters", "Maintain masters", "Create and edit departments, services, designations and ICD lookups."),
    # ------------------------------------------------------------ system
    _p("backup.read", "backup", "View backups", "List and download backups."),
    _p("backup.write", "backup", "Back up and restore", "Create, delete and restore a backup. Restore overwrites live data."),
    _p("maintenance.run", "maintenance", "Run maintenance", "Run archive rollover and maintenance tasks."),
    _p("health.read", "health", "View system health", "Read health and operational-year status."),
)


#: Every valid code, for O(1) membership checks by the guard and the tests.
CODES: frozenset[str] = frozenset(spec.code for spec in PERMISSIONS)

#: Code to specification, for seeding and for error messages.
BY_CODE: dict[str, PermissionSpec] = {spec.code: spec for spec in PERMISSIONS}

#: The wildcard used by a role template that holds everything.
ALL = "*"

#: Role names the client already treats as all-access (frontend/js/rbac.js).
#: Kept here so the server and the client agree about what "admin" means; the
#: migration grants these roles every code so the data says the same thing.
ALL_ACCESS_ROLE_NAMES = frozenset(
    {
        "admin",
        "administrator",
        "hospital administrator",
        "super administrator",
    }
)


#: Default grants for the eight roles named in MASTER_SPECIFICATION section 6,
#: plus an auditor and a medical superintendent because B11's review screen and
#: an assessment both need a role that can read without being able to change.
#:
#: These are starting points an administrator edits, not a policy. The point is
#: that a new installation has usable roles on day one instead of one
#: all-powerful account and seven empty ones.
ROLE_TEMPLATES: dict[str, tuple[str, ...]] = {
    "administrator": (ALL,),
    "medical superintendent": (
        "patients.read", "opd.read", "clinical.read", "prescriptions.read",
        "ipd.read", "investigations.read", "pharmacy.read", "inventory.read",
        "procurement.read", "billing.read", "mrd.read", "reporting.read",
        "reporting.export", "audit.read", "audit.export", "users.read",
        "roles.read", "settings.read", "health.read",
    ),
    "auditor": (
        "audit.read", "audit.export", "reporting.read", "reporting.export",
        "patients.read", "billing.read",
    ),
    "registration desk": (
        "patients.read", "patients.write", "opd.read", "opd.write", "masters.read",
    ),
    "medical officer": (
        "patients.read", "opd.read", "clinical.read", "clinical.write",
        "prescriptions.read", "prescriptions.write", "investigations.read",
        "investigations.write", "ipd.read", "reporting.read", "masters.read",
    ),
    "pharmacist": (
        "patients.read", "pharmacy.read", "pharmacy.write", "inventory.read",
        "prescriptions.read",
    ),
    "laboratory staff": (
        "patients.read", "investigations.read", "investigations.write",
        "reporting.read",
    ),
    "billing staff": (
        "patients.read", "billing.read", "billing.write", "reporting.read",
    ),
    "medical records": (
        "patients.read", "mrd.read", "mrd.write", "ipd.read", "reporting.read",
    ),
    "store keeper": (
        "inventory.read", "inventory.write", "procurement.read",
        "procurement.write",
    ),
}


def expand(template: tuple[str, ...]) -> frozenset[str]:
    """Resolve a role template to concrete codes."""

    if ALL in template:
        return CODES
    return frozenset(template)


def unknown_codes(template: tuple[str, ...]) -> frozenset[str]:
    """Codes in a template that the catalogue does not declare."""

    if ALL in template:
        return frozenset()
    return frozenset(code for code in template if code not in CODES)


__all__ = [
    "ALL",
    "ALL_ACCESS_ROLE_NAMES",
    "BY_CODE",
    "CODES",
    "PERMISSIONS",
    "PermissionSpec",
    "ROLE_TEMPLATES",
    "expand",
    "unknown_codes",
]
