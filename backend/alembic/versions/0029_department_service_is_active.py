"""Add missing is_active column to department_services.

The DepartmentService ORM model inherits AuditMixin, which includes the
``is_active`` flag (mirroring the departments and designations masters that
ship it via migrations 0005 and 0009), but migration 0006 created the
``department_services`` table without the column. Any INSERT through the
service layer therefore fails with
``OperationalError: table department_services has no column named is_active``.

Tests never caught this because they build their ephemeral databases from
``Base.metadata.create_all`` (ORM-derived schema), not from Alembic. This
migration realigns the Alembic schema with the ORM for fresh installs and
existing operational databases alike.
"""
from alembic import op
import sqlalchemy as sa

revision = "0029_department_service_is_active"
down_revision = "0028_prescription_operational_year_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Guarded so databases created via metadata.create_all (which already
    # include the column) are unaffected.
    bind = op.get_bind()
    existing = {
        row[1]
        for row in bind.exec_driver_sql("PRAGMA table_info(department_services)")
    }
    if "is_active" not in existing:
        op.add_column(
            "department_services",
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
        )


def downgrade() -> None:
    with op.batch_alter_table("department_services") as batch_op:
        batch_op.drop_column("is_active")
