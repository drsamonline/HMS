"""HHMS configurable department services and activity ledger."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_department_services_activity"
down_revision = "0005_department_master"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "department_services",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_service_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("service_type", sa.String(30), nullable=False, server_default="service"),
        sa.Column("supports_gender_breakdown", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("supports_new_old", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("supports_fulfillment_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], name="fk_department_services_department"),
        sa.ForeignKeyConstraint(["parent_service_id"], ["department_services.id"], name="fk_department_services_parent"),
        sa.PrimaryKeyConstraint("id", name="pk_department_services"),
        sa.UniqueConstraint("department_id", "code", name="uq_department_services_department_code"),
    )
    op.create_index("ix_department_services_department_id", "department_services", ["department_id"])
    op.create_index("ix_department_services_parent_service_id", "department_services", ["parent_service_id"])
    op.create_index("ix_department_services_code", "department_services", ["code"])
    op.create_index("ix_department_services_name", "department_services", ["name"])

    op.create_table(
        "service_activities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("activity_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("case_type", sa.String(10), nullable=False, server_default="new"),
        sa.Column("fulfillment_mode", sa.String(20), nullable=True),
        sa.Column("source_type", sa.String(30), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["patient_id"], ["Patient.id"], name="fk_service_activity_patient"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], name="fk_service_activity_department"),
        sa.ForeignKeyConstraint(["service_id"], ["department_services.id"], name="fk_service_activity_service"),
        sa.PrimaryKeyConstraint("id", name="pk_service_activities"),
    )
    op.create_index("ix_service_activities_patient_id", "service_activities", ["patient_id"])
    op.create_index("ix_service_activities_department_id", "service_activities", ["department_id"])
    op.create_index("ix_service_activities_service_id", "service_activities", ["service_id"])
    op.create_index("ix_service_activities_activity_datetime", "service_activities", ["activity_datetime"])
    op.create_index("ix_service_activities_case_type", "service_activities", ["case_type"])
    op.create_index("ix_service_activities_fulfillment_mode", "service_activities", ["fulfillment_mode"])
    op.create_index("ix_service_activities_source_type", "service_activities", ["source_type"])
    op.create_index("ix_service_activities_source_id", "service_activities", ["source_id"])
    op.create_index("ix_service_activities_status", "service_activities", ["status"])


def downgrade() -> None:
    op.drop_index("ix_service_activities_status", table_name="service_activities")
    op.drop_index("ix_service_activities_source_id", table_name="service_activities")
    op.drop_index("ix_service_activities_source_type", table_name="service_activities")
    op.drop_index("ix_service_activities_fulfillment_mode", table_name="service_activities")
    op.drop_index("ix_service_activities_case_type", table_name="service_activities")
    op.drop_index("ix_service_activities_activity_datetime", table_name="service_activities")
    op.drop_index("ix_service_activities_service_id", table_name="service_activities")
    op.drop_index("ix_service_activities_department_id", table_name="service_activities")
    op.drop_index("ix_service_activities_patient_id", table_name="service_activities")
    op.drop_table("service_activities")
    op.drop_index("ix_department_services_name", table_name="department_services")
    op.drop_index("ix_department_services_code", table_name="department_services")
    op.drop_index("ix_department_services_parent_service_id", table_name="department_services")
    op.drop_index("ix_department_services_department_id", table_name="department_services")
    op.drop_table("department_services")
