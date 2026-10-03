"""MRD annual lifecycle: MedicalDocument lifecycle columns and MedicalDocumentArchiveReference.

Batch 75 - MRD Document Annual Lifecycle & Rollover.

Adds operational-year lifecycle columns to MedicalDocument (document_year,
storage_tier, is_current_year), backfills document_year from the calendar year
of document_date, creates the permanent live-database
MedicalDocumentArchiveReference table so document identity survives physical
annual rollover, and completes the Batch 74 downgrade that was missing the
InvestigationResult lifecycle drops.
"""
from alembic import op
import sqlalchemy as sa

revision = "0026_mrd_operational_year_lifecycle"
down_revision = "0025_lab_operational_year_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "MedicalDocument",
        sa.Column("document_year", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "MedicalDocument",
        sa.Column(
            "storage_tier",
            sa.String(20),
            nullable=False,
            server_default="live",
        ),
    )
    op.add_column(
        "MedicalDocument",
        sa.Column(
            "is_current_year",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.create_index(
        "ix_medical_document_document_year", "MedicalDocument", ["document_year"]
    )
    op.create_index(
        "ix_medical_document_storage_tier", "MedicalDocument", ["storage_tier"]
    )
    op.create_index(
        "ix_medical_document_is_current_year", "MedicalDocument", ["is_current_year"]
    )

    # Backfill document_year from the calendar year of document_date.
    op.execute(
        "UPDATE MedicalDocument SET document_year = "
        "CAST(strftime('%Y', document_date) AS INTEGER)"
        " WHERE document_date IS NOT NULL"
    )

    op.create_table(
        "MedicalDocumentArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_document_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("visit_id", sa.Integer(), nullable=True),
        sa.Column("admission_id", sa.Integer(), nullable=True),
        sa.Column("document_number", sa.String(20), nullable=False),
        sa.Column("document_year", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_medical_document_archive_ref_manifest",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["Patient.id"],
            name="fk_medical_document_archive_ref_patient",
        ),
        sa.UniqueConstraint(
            "original_document_id",
            name="uq_medical_document_archive_ref_original_document",
        ),
    )
    op.create_index(
        "ix_medical_document_archive_ref_manifest",
        "MedicalDocumentArchiveReference",
        ["archive_manifest_id"],
    )
    op.create_index(
        "ix_medical_document_archive_ref_document",
        "MedicalDocumentArchiveReference",
        ["original_document_id"],
    )
    op.create_index(
        "ix_medical_document_archive_ref_patient",
        "MedicalDocumentArchiveReference",
        ["patient_id"],
    )
    op.create_index(
        "ix_medical_document_archive_ref_year",
        "MedicalDocumentArchiveReference",
        ["document_year"],
    )


def downgrade() -> None:
    op.drop_table("MedicalDocumentArchiveReference")
    op.drop_index("ix_medical_document_is_current_year", table_name="MedicalDocument")
    op.drop_index("ix_medical_document_storage_tier", table_name="MedicalDocument")
    op.drop_index("ix_medical_document_document_year", table_name="MedicalDocument")
    op.drop_column("MedicalDocument", "is_current_year")
    op.drop_column("MedicalDocument", "storage_tier")
    op.drop_column("MedicalDocument", "document_year")
