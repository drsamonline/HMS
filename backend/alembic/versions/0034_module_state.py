"""Add the module registry state, derived from what the database already holds.

`MASTER_SPECIFICATION` 7.2 and 7.3 have always required switchable modules. This
migration adds the table that records which ones a hospital uses, and seeds it
from the data rather than from the default: an installation that has been
dispensing medicines for a year must not come back with pharmacy switched off.

The derivation is deliberately conservative - a module is enabled if the tables it
owns contain at least one row - because the failure it prevents is a hospital
losing a module it has been using.

Revision ID: 0034_module_state
Revises: 0033_all_access_roles
"""

from alembic import op
import sqlalchemy as sa

revision = "0034_module_state"
down_revision = "0033_all_access_roles"
branch_labels = None
depends_on = None


#: module code -> tables whose contents prove the module was in use.
EVIDENCE = {
    "pharmacy": ("DispenseRecord", "MedicineBatch"),
    "stock": ("InventoryItem", "StockTransaction"),
    "ipd": ("Admission", "Bed"),
    "laboratory": ("Investigation", "InvestigationResult"),
    "billing": ("Invoice", "Payment"),
    "mrd": ("MedicalDocument", "PatientFile"),
    "nabh": (),
}


def _has_rows(bind, table: str) -> bool:
    exists = bind.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    if not exists:
        return False
    return bind.exec_driver_sql(f"SELECT 1 FROM \"{table}\" LIMIT 1").fetchone() is not None


def upgrade() -> None:
    bind = op.get_bind()

    exists = bind.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='ModuleState'"
    ).fetchone()
    if not exists:
        op.create_table(
            "ModuleState",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("module_code", sa.String(40), nullable=False),
            sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("enabled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("enabled_by", sa.Integer(), nullable=True),
            sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("disabled_by", sa.Integer(), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("module_code", name="uq_module_state_module_code"),
        )
        op.create_index("ix_ModuleState_module_code", "ModuleState", ["module_code"])

    from app.modules.registry import MODULES

    for module in MODULES:
        row = bind.exec_driver_sql(
            "SELECT id FROM ModuleState WHERE module_code = ?", (module.code,)
        ).fetchone()
        if row:
            continue
        if module.is_core:
            enabled = True
        else:
            enabled = any(_has_rows(bind, table) for table in EVIDENCE.get(module.code, ()))
        bind.exec_driver_sql(
            "INSERT INTO ModuleState (module_code, is_enabled, note) VALUES (?, ?, ?)",
            (
                module.code,
                1 if enabled else 0,
                "enabled at migration: the module's tables hold records"
                if enabled and not module.is_core
                else ("core module" if module.is_core else None),
            ),
        )


def downgrade() -> None:
    op.drop_table("ModuleState")
