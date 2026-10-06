"""Encounter annual lifecycle: Visit lifecycle columns and VisitArchiveReference.

Batch 70 - Encounter Annual Lifecycle & Rollover.

Adds operational-year lifecycle columns to Visit (visit_year, storage_tier,
is_current_year), backfills visit_year from visit_datetime's calendar year,
and creates the permanent live-database VisitArchiveReference table so visit
identity survives physical annual rollover.
"""
from alembic import op
import sqlalchemy as sa

revision = "0021_visit_operational_year_lifecycle"
down_revision = "0020_case_archive_rollover_reference"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "Visit",
        sa.Column("visit_year", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "Visit",
        sa.Column(
            "storage_tier",
            sa.String(20),
            nullable=False,
            server_default="live",
        ),
    )
    op.add_column(
        "Visit",
        sa.Column(
            "is_current_year",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.create_index("ix_visit_visit_year", "Visit", ["visit_year"])
    op.create_index("ix_visit_storage_tier", "Visit", ["storage_tier"])
    op.create_index("ix_visit_is_current_year", "Visit", ["is_current_year"])

    # Backfill visit_year from the calendar year of visit_datetime.
    op.execute(
        "UPDATE Visit SET visit_year = CAST(strftime('%Y', visit_datetime) AS INTEGER)"
        " WHERE visit_datetime IS NOT NULL"
    )

    op.create_table(
        "VisitArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_visit_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("visit_number", sa.String(20), nullable=False),
        sa.Column("visit_year", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_visit_archive_ref_manifest",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["Patient.id"],
            name="fk_visit_archive_ref_patient",
        ),
        sa.UniqueConstraint(
            "original_visit_id",
            name="uq_visit_archive_ref_original_visit",
        ),
    )
    op.create_index(
        "ix_visit_archive_reference_manifest",
        "VisitArchiveReference",
        ["archive_manifest_id"],
    )
    op.create_index(
        "ix_visit_archive_reference_original_visit",
        "VisitArchiveReference",
        ["original_visit_id"],
    )
    op.create_index(
        "ix_visit_archive_reference_patient",
        "VisitArchiveReference",
        ["patient_id"],
    )
    op.create_index(
        "ix_visit_archive_reference_visit_number",
        "VisitArchiveReference",
        ["visit_number"],
    )
    op.create_index(
        "ix_visit_archive_reference_year",
        "VisitArchiveReference",
        ["visit_year"],
    )


def downgrade() -> None:
    op.drop_index("ix_visit_archive_reference_year", table_name="VisitArchiveReference")
    op.drop_index(
        "ix_visit_archive_reference_visit_number", table_name="VisitArchiveReference"
    )
    op.drop_index("ix_visit_archive_reference_patient", table_name="VisitArchiveReference")
    op.drop_index(
        "ix_visit_archive_reference_original_visit", table_name="VisitArchiveReference"
    )
    op.drop_index("ix_visit_archive_reference_manifest", table_name="VisitArchiveReference")
    op.drop_table("VisitArchiveReference")

    op.drop_index("ix_visit_is_current_year", table_name="Visit")
    op.drop_index("ix_visit_storage_tier", table_name="Visit")
    op.drop_index("ix_visit_visit_year", table_name="Visit")
    op.drop_column("Visit", "is_current_year")
    op.drop_column("Visit", "storage_tier")
    op.drop_column("Visit", "visit_year")
