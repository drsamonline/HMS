"""HHMS clinical activity classification integration."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_clinical_activity_integration"
down_revision = "0006_department_services_activity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Classification columns + foreign keys applied through batch mode so the
    # migration runs on SQLite (ALTER of constraints is unsupported outside
    # the batch copy-and-move strategy).  Replayed verbatim on PostgreSQL.
    with op.batch_alter_table("Visit") as batch_op:
        batch_op.add_column(
            sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=True)
        )
        batch_op.add_column(sa.Column("case_type", sa.String(10), nullable=True))
        batch_op.create_foreign_key(
            "fk_visit_department", "departments", ["department_id"], ["id"]
        )
        batch_op.create_foreign_key(
            "fk_visit_service", "department_services", ["service_id"], ["id"]
        )
    op.create_index("ix_visit_department_id", "Visit", ["department_id"])
    op.create_index("ix_visit_service_id", "Visit", ["service_id"])
    op.create_index("ix_visit_case_type", "Visit", ["case_type"])

    with op.batch_alter_table("Admission") as batch_op:
        batch_op.add_column(
            sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=True)
        )
        batch_op.add_column(sa.Column("case_type", sa.String(10), nullable=True))
        batch_op.create_foreign_key(
            "fk_admission_department", "departments", ["department_id"], ["id"]
        )
        batch_op.create_foreign_key(
            "fk_admission_service", "department_services", ["service_id"], ["id"]
        )
    op.create_index("ix_admission_department_id", "Admission", ["department_id"])
    op.create_index("ix_admission_service_id", "Admission", ["service_id"])
    op.create_index("ix_admission_case_type", "Admission", ["case_type"])

    with op.batch_alter_table("Investigation") as batch_op:
        batch_op.add_column(
            sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=True)
        )
        batch_op.add_column(sa.Column("case_type", sa.String(10), nullable=True))
        batch_op.add_column(
            sa.Column("fulfillment_mode", sa.String(20), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_investigation_department", "departments", ["department_id"], ["id"]
        )
        batch_op.create_foreign_key(
            "fk_investigation_service", "department_services", ["service_id"], ["id"]
        )
    op.create_index("ix_investigation_department_id", "Investigation", ["department_id"])
    op.create_index("ix_investigation_service_id", "Investigation", ["service_id"])
    op.create_index("ix_investigation_case_type", "Investigation", ["case_type"])
    op.create_index("ix_investigation_fulfillment_mode", "Investigation", ["fulfillment_mode"])


def downgrade() -> None:
    with op.batch_alter_table("Investigation") as batch_op:
        batch_op.drop_constraint("fk_investigation_service", type_="foreignkey")
        batch_op.drop_constraint("fk_investigation_department", type_="foreignkey")
        batch_op.drop_column("fulfillment_mode")
        batch_op.drop_column("case_type")
        batch_op.drop_column("service_id")
        batch_op.drop_column("department_id")
    op.drop_index("ix_investigation_fulfillment_mode", table_name="Investigation")
    op.drop_index("ix_investigation_case_type", table_name="Investigation")
    op.drop_index("ix_investigation_service_id", table_name="Investigation")
    op.drop_index("ix_investigation_department_id", table_name="Investigation")

    with op.batch_alter_table("Admission") as batch_op:
        batch_op.drop_constraint("fk_admission_service", type_="foreignkey")
        batch_op.drop_constraint("fk_admission_department", type_="foreignkey")
        batch_op.drop_column("case_type")
        batch_op.drop_column("service_id")
        batch_op.drop_column("department_id")
    op.drop_index("ix_admission_case_type", table_name="Admission")
    op.drop_index("ix_admission_service_id", table_name="Admission")
    op.drop_index("ix_admission_department_id", table_name="Admission")

    with op.batch_alter_table("Visit") as batch_op:
        batch_op.drop_constraint("fk_visit_service", type_="foreignkey")
        batch_op.drop_constraint("fk_visit_department", type_="foreignkey")
        batch_op.drop_column("case_type")
        batch_op.drop_column("service_id")
        batch_op.drop_column("department_id")
    op.drop_index("ix_visit_case_type", table_name="Visit")
    op.drop_index("ix_visit_service_id", table_name="Visit")
    op.drop_index("ix_visit_department_id", table_name="Visit")
