"""Add the editable hospital department master."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_department_master"
down_revision = "0004_medical_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    department_type = sa.Enum(
        "clinical",
        "diagnostic",
        "administrative",
        "financial",
        "support",
        name="department_type_enum",
    )
    department_type.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("department_type", department_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id", name="pk_departments"),
        sa.UniqueConstraint("code", name="uq_departments_code"),
        sa.UniqueConstraint("name", name="uq_departments_name"),
    )
    op.create_index("ix_departments_code", "departments", ["code"])
    op.create_index("ix_departments_name", "departments", ["name"])


def downgrade() -> None:
    op.drop_index("ix_departments_name", table_name="departments")
    op.drop_index("ix_departments_code", table_name="departments")
    op.drop_table("departments")
    sa.Enum(name="department_type_enum").drop(op.get_bind(), checkfirst=True)
