"""Seed the permission catalogue and the role templates.

Before this migration the system had a Permission table, a RolePermission table
and no rows in either: one all-powerful `admin` role and nothing else. Every
non-administrator account therefore had no permissions, which - since the client
fails closed after B05 - means no navigation at all.

The catalogue itself lives in `app.core.permissions` because a permission is a
fact about the software, not about a hospital. This migration copies it into the
database so an administrator can grant and revoke it, and so the guard in B13 has
something to check against.

Idempotent by design: re-running it on a database that already holds the rows
changes nothing, and it never removes a permission an administrator has added.

Revision ID: 0032_permission_catalogue
Revises: 0031_audit_log_hash_chain
"""

from alembic import op
import sqlalchemy as sa

revision = "0032_permission_catalogue"
down_revision = "0031_audit_log_hash_chain"
branch_labels = None
depends_on = None


# The catalogue is duplicated here rather than imported: a migration must keep
# working when the application code moves on. `test_permission_catalogue.py`
# asserts the two stay identical, so drift fails the build rather than silently
# seeding the wrong grants.
PERMISSIONS = (
    ("patients.read", "patients", "View patients", "Search and read patient demographics and history."),
    ("patients.write", "patients", "Register and edit patients", "Create a patient and edit demographics."),
    ("patients.deactivate", "patients", "Deactivate a patient", "Mark a patient inactive without deleting records."),
    ("opd.read", "opd", "View the OPD queue", "See today's tokens and queue state."),
    ("opd.write", "opd", "Issue and call tokens", "Generate, call and complete OPD tokens."),
    ("clinical.read", "clinical", "View clinical records", "Read case records, diagnoses, notes and assessments."),
    ("clinical.write", "clinical", "Record clinical notes", "Write case records, diagnoses, follow-ups and assessments."),
    ("prescriptions.read", "prescriptions", "View prescriptions", "Read prescriptions and their items."),
    ("prescriptions.write", "prescriptions", "Prescribe", "Create and amend prescriptions."),
    ("ipd.read", "ipd", "View admissions", "Read admissions, beds and discharges."),
    ("ipd.write", "ipd", "Admit and discharge", "Admit, transfer, update and discharge a patient."),
    ("investigations.read", "investigations", "View investigations", "Read investigation requests and results."),
    ("investigations.write", "investigations", "Request and report investigations", "Raise requests, enter and amend results."),
    ("pharmacy.read", "pharmacy", "View pharmacy", "Read medicines, batches and dispensing."),
    ("pharmacy.write", "pharmacy", "Dispense and maintain pharmacy", "Dispense, and maintain medicine and batch masters."),
    ("inventory.read", "inventory", "View stock", "Read stock balances, cards and transactions."),
    ("inventory.write", "inventory", "Adjust stock", "Post stock receipts and issues."),
    ("procurement.read", "procurement", "View procurement", "Read suppliers, purchase orders and goods receipts."),
    ("procurement.write", "procurement", "Raise orders and receive goods", "Create purchase orders and post goods receipts."),
    ("billing.read", "billing", "View billing", "Read invoices, payments and summaries."),
    ("billing.write", "billing", "Bill and collect", "Raise invoices, record payments and add invoice items."),
    ("billing.void", "billing", "Cancel an invoice", "Cancel an invoice or remove a line."),
    ("mrd.read", "mrd", "View medical records", "Read documents, patient files and archives."),
    ("mrd.write", "mrd", "File records", "Upload documents and manage the record archive."),
    ("reporting.read", "reporting", "View reports", "Read statistics and report envelopes."),
    ("reporting.export", "reporting", "Export reports", "Render a report to PDF or CSV."),
    ("audit.read", "audit", "Read the audit trail", "Review who did what across the hospital."),
    ("audit.export", "audit", "Export the audit trail", "Take a copy of the audit trail out of the system."),
    ("users.read", "users", "View users", "List user accounts."),
    ("users.write", "users", "Manage users", "Create, edit, deactivate and re-role users."),
    ("roles.read", "roles", "View roles", "List roles and their permissions."),
    ("roles.write", "roles", "Manage roles", "Create roles and grant permissions."),
    ("settings.read", "settings", "View settings", "Read hospital and system settings."),
    ("settings.write", "settings", "Change settings", "Change hospital and system settings and number sequences."),
    ("masters.read", "masters", "View masters", "Read departments, services, designations and ICD lookups."),
    ("masters.write", "masters", "Maintain masters", "Create and edit departments, services, designations and ICD lookups."),
    ("backup.read", "backup", "View backups", "List and download backups."),
    ("backup.write", "backup", "Back up and restore", "Create, delete and restore a backup."),
    ("maintenance.run", "maintenance", "Run maintenance", "Run archive rollover and maintenance tasks."),
    ("health.read", "health", "View system health", "Read health and operational-year status."),
)

ALL = "*"

ROLE_TEMPLATES = {
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
    "billing staff": ("patients.read", "billing.read", "billing.write", "reporting.read"),
    "medical records": (
        "patients.read", "mrd.read", "mrd.write", "ipd.read", "reporting.read",
    ),
    "store keeper": (
        "inventory.read", "inventory.write", "procurement.read", "procurement.write",
    ),
}

ROLE_DESCRIPTIONS = {
    "administrator": "Full access to every module and setting.",
    "medical superintendent": "Clinical and managerial oversight, read-mostly.",
    "auditor": "Reads and exports the audit trail and reports; changes nothing.",
    "registration desk": "Registers patients and runs the OPD queue.",
    "medical officer": "Consultations, prescriptions and investigation orders.",
    "pharmacist": "Dispensing and pharmacy stock.",
    "laboratory staff": "Investigation requests and results.",
    "billing staff": "Invoices, payments and receipts.",
    "medical records": "Medical record filing and retrieval.",
    "store keeper": "General stock and procurement.",
}


def _table(bind, name: str) -> bool:
    row = bind.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def upgrade() -> None:
    bind = op.get_bind()

    for code, module, name, description in PERMISSIONS:
        existing = bind.exec_driver_sql(
            "SELECT id FROM Permission WHERE code = ?", (code,)
        ).fetchone()
        if existing:
            continue
        bind.exec_driver_sql(
            "INSERT INTO Permission (name, code, module, description, is_active) "
            "VALUES (?, ?, ?, ?, 1)",
            (name, code, module, description),
        )

    # code -> id. Inverted the first time this was written, which meant every
    # template lookup missed and the administrator role silently received no
    # grants at all. Caught by the database-level test, not by the one that only
    # compared this file to the catalogue.
    permission_ids = {
        row[1]: row[0]
        for row in bind.exec_driver_sql("SELECT id, code FROM Permission").fetchall()
    }
    all_ids = list(permission_ids.values())

    for role_name, template in ROLE_TEMPLATES.items():
        role_row = bind.exec_driver_sql(
            "SELECT id FROM Role WHERE lower(role_name) = lower(?)", (role_name,)
        ).fetchone()
        if role_row:
            role_id = role_row[0]
        else:
            bind.exec_driver_sql(
                "INSERT INTO Role (role_name, description, is_active) VALUES (?, ?, 1)",
                (role_name, ROLE_DESCRIPTIONS.get(role_name)),
            )
            role_id = bind.exec_driver_sql(
                "SELECT id FROM Role WHERE lower(role_name) = lower(?)", (role_name,)
            ).fetchone()[0]

        wanted = all_ids if ALL in template else [
            permission_ids[code] for code in template if code in permission_ids
        ]
        for permission_id in wanted:
            already = bind.exec_driver_sql(
                "SELECT id FROM RolePermission WHERE role_id = ? AND permission_id = ?",
                (role_id, permission_id),
            ).fetchone()
            if already:
                continue
            bind.exec_driver_sql(
                "INSERT INTO RolePermission (role_id, permission_id) VALUES (?, ?)",
                (role_id, permission_id),
            )


def downgrade() -> None:
    bind = op.get_bind()

    # Remove only what this migration created: the role-permission grants it
    # made and the permissions it seeded. Roles are left in place, because a
    # hospital may have assigned people to them by the time anyone downgrades.
    for code in (row[0] for row in PERMISSIONS):
        permission = bind.exec_driver_sql(
            "SELECT id FROM Permission WHERE code = ?", (code,)
        ).fetchone()
        if not permission:
            continue
        bind.exec_driver_sql(
            "DELETE FROM RolePermission WHERE permission_id = ?", (permission[0],)
        )
        bind.exec_driver_sql("DELETE FROM Permission WHERE id = ?", (permission[0],))
