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
    op.add_column(
        "Visit",
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "Visit",
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "Visit",
        sa.Column("case_type", sa.String(10), nullable=True),
    )
    op.create_index("ix_visit_department_id", "Visit", ["department_id"])
    op.create_index("ix_visit_service_id", "Visit", ["service_id"])
    op.create_index("ix_visit_case_type", "Visit", ["case_type"])
    op.create_foreign_key(
        "fk_visit_department", "Visit", "departments", ["department_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_visit_service", "Visit", "department_services", ["service_id"], ["id"]
    )

    op.add_column(
        "Admission",
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "Admission",
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "Admission",
        sa.Column("case_type", sa.String(10), nullable=True),
    )
    op.create_index("ix_admission_department_id", "Admission", ["department_id"])
    op.create_index("ix_admission_service_id", "Admission", ["service_id"])
    op.create_index("ix_admission_case_type", "Admission", ["case_type"])
    op.create_foreign_key(
        "fk_admission_department", "Admission", "departments", ["department_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_admission_service", "Admission", "department_services", ["service_id"], ["id"]
    )

    op.add_column(
        "Investigation",
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "Investigation",
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "Investigation",
        sa.Column("case_type", sa.String(10), nullable=True),
    )
    op.add_column(
        "Investigation",
        sa.Column("fulfillment_mode", sa.String(20), nullable=True),
    )
    op.create_index("ix_investigation_department_id", "Investigation", ["department_id"])
    op.create_index("ix_investigation_service_id", "Investigation", ["service_id"])
    op.create_index("ix_investigation_case_type", "Investigation", ["case_type"])
    op.create_index("ix_investigation_fulfillment_mode", "Investigation", ["fulfillment_mode"])
    op.create_foreign_key(
        "fk_investigation_department", "Investigation", "departments", ["department_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_investigation_service", "Investigation", "department_services", ["service_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_investigation_service", "Investigation", type_="foreignkey")
    op.drop_constraint("fk_investigation_department", "Investigation", type_="foreignkey")
    op.drop_index("ix_investigation_fulfillment_mode", table_name="Investigation")
    op.drop_index("ix_investigation_case_type", table_name="Investigation")
    op.drop_index("ix_investigation_service_id", table_name="Investigation")
    op.drop_index("ix_investigation_department_id", table_name="Investigation")
    op.drop_column("Investigation", "fulfillment_mode")
    op.drop_column("Investigation", "case_type")
    op.drop_column("Investigation", "service_id")
    op.drop_column("Investigation", "department_id")

    op.drop_constraint("fk_admission_service", "Admission", type_="foreignkey")
    op.drop_constraint("fk_admission_department", "Admission", type_="foreignkey")
    op.drop_index("ix_admission_case_type", table_name="Admission")
    op.drop_index("ix_admission_service_id", table_name="Admission")
    op.drop_index("ix_admission_department_id", table_name="Admission")
    op.drop_column("Admission", "case_type")
    op.drop_column("Admission", "service_id")
    op.drop_column("Admission", "department_id")

    op.drop_constraint("fk_visit_service", "Visit", type_="foreignkey")
    op.drop_constraint("fk_visit_department", "Visit", type_="foreignkey")
    op.drop_index("ix_visit_case_type", table_name="Visit")
    op.drop_index("ix_visit_service_id", table_name="Visit")
    op.drop_index("ix_visit_department_id", table_name="Visit")
    op.drop_column("Visit", "case_type")
    op.drop_column("Visit", "service_id")
    op.drop_column("Visit", "department_id")
