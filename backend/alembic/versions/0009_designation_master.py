"""Add editable designation master."""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009_designation_master"
down_revision = "0008_rbac_consistency"
branch_labels = None
depends_on = None

def upgrade() -> None:
    designation_type = sa.Enum(
        "medical", "nursing", "paramedical", "administrative", "technical", "support", "management",
        name="designation_type_enum",
    )
    designation_type.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "designations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("designation_type", designation_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id", name="pk_designations"),
        sa.UniqueConstraint("code", name="uq_designations_code"),
        sa.UniqueConstraint("name", name="uq_designations_name"),
    )
    op.create_index("ix_designations_code", "designations", ["code"])
    op.create_index("ix_designations_name", "designations", ["name"])

def downgrade() -> None:
    op.drop_index("ix_designations_name", table_name="designations")
    op.drop_index("ix_designations_code", table_name="designations")
    op.drop_table("designations")
    sa.Enum(name="designation_type_enum").drop(op.get_bind(), checkfirst=True)
