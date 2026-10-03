"""IPD annual lifecycle: Admission lifecycle columns and AdmissionArchiveReference.

Batch 73 - IPD Annual Lifecycle & Rollover.

Adds operational-year lifecycle columns to Admission (admission_year,
storage_tier, is_current_year), backfills admission_year from admission_datetime's
calendar year, and creates the permanent live-database AdmissionArchiveReference
table so admission identity survives physical annual rollover.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0024_ipd_operational_year_lifecycle"
down_revision = "0023_pharmacy_operational_year_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "Admission",
        sa.Column("admission_year", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "Admission",
        sa.Column(
            "storage_tier",
            sa.String(20),
            nullable=False,
            server_default="live",
        ),
    )
    op.add_column(
        "Admission",
        sa.Column(
            "is_current_year",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.create_index("ix_admission_admission_year", "Admission", ["admission_year"])
    op.create_index("ix_admission_storage_tier", "Admission", ["storage_tier"])
    op.create_index("ix_admission_is_current_year", "Admission", ["is_current_year"])

    # Backfill admission_year from the calendar year of admission_datetime.
    op.execute(
        "UPDATE Admission SET admission_year = CAST(strftime('%Y', admission_datetime) AS INTEGER)"
        " WHERE admission_datetime IS NOT NULL"
    )

    op.create_table(
        "AdmissionArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_admission_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("admission_year", sa.Integer(), nullable=False),
        sa.Column("admission_number", sa.String(20), nullable=False),
        sa.Column("admission_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("bed_id", sa.Integer(), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("case_type", sa.String(10), nullable=True),
        sa.Column("admitted_by", sa.Integer(), nullable=False),
        sa.Column("admission_status", sa.String(20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_admission_archive_ref_manifest",
        ),
        sa.UniqueConstraint(
            "original_admission_id",
            name="uq_admission_archive_ref_original_admission",
        ),
    )
    op.create_index(
        "ix_admission_archive_ref_manifest", "AdmissionArchiveReference", ["archive_manifest_id"]
    )
    op.create_index(
        "ix_admission_archive_ref_admission", "AdmissionArchiveReference", ["original_admission_id"]
    )
    op.create_index(
        "ix_admission_archive_ref_patient", "AdmissionArchiveReference", ["patient_id"]
    )
    op.create_index(
        "ix_admission_archive_ref_year", "AdmissionArchiveReference", ["admission_year"]
    )


def downgrade() -> None:
    op.drop_table("AdmissionArchiveReference")
    op.drop_index("ix_admission_is_current_year", table_name="Admission")
    op.drop_index("ix_admission_storage_tier", table_name="Admission")
    op.drop_index("ix_admission_admission_year", table_name="Admission")
    op.drop_column("Admission", "is_current_year")
    op.drop_column("Admission", "storage_tier")
    op.drop_column("Admission", "admission_year")
