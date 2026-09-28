"""Laboratory annual lifecycle: Investigation lifecycle columns and InvestigationArchiveReference.

Batch 74 - Laboratory Annual Lifecycle & Rollover.

Adds operational-year lifecycle columns to Investigation (investigation_year,
storage_tier, is_current_year), backfills investigation_year from the calendar
year of requested_datetime, and creates the permanent live-database
InvestigationArchiveReference table so investigation identity survives
physical annual rollover.
"""
from alembic import op
import sqlalchemy as sa

revision = "0025_lab_operational_year_lifecycle"
down_revision = "0024_ipd_operational_year_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "Investigation",
        sa.Column("investigation_year", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "Investigation",
        sa.Column(
            "storage_tier",
            sa.String(20),
            nullable=False,
            server_default="live",
        ),
    )
    op.add_column(
        "Investigation",
        sa.Column(
            "is_current_year",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.create_index(
        "ix_investigation_investigation_year", "Investigation", ["investigation_year"]
    )
    op.create_index("ix_investigation_storage_tier", "Investigation", ["storage_tier"])
    op.create_index("ix_investigation_is_current_year", "Investigation", ["is_current_year"])

    # InvestigationResult lifecycle columns (result_year from result_datetime).
    op.add_column(
        "InvestigationResult",
        sa.Column("result_year", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "InvestigationResult",
        sa.Column(
            "storage_tier",
            sa.String(20),
            nullable=False,
            server_default="live",
        ),
    )
    op.add_column(
        "InvestigationResult",
        sa.Column(
            "is_current_year",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.create_index(
        "ix_investigation_result_result_year", "InvestigationResult", ["result_year"]
    )
    op.create_index(
        "ix_investigation_result_storage_tier", "InvestigationResult", ["storage_tier"]
    )
    op.create_index(
        "ix_investigation_result_is_current_year", "InvestigationResult", ["is_current_year"]
    )

    # Backfill investigation_year from the calendar year of requested_datetime.
    op.execute(
        "UPDATE Investigation SET investigation_year = "
        "CAST(strftime('%Y', requested_datetime) AS INTEGER)"
        " WHERE requested_datetime IS NOT NULL"
    )
    op.execute(
        "UPDATE InvestigationResult SET result_year = "
        "CAST(strftime('%Y', result_datetime) AS INTEGER)"
        " WHERE result_datetime IS NOT NULL"
    )

    op.create_table(
        "InvestigationArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_investigation_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("visit_id", sa.Integer(), nullable=True),
        sa.Column("admission_id", sa.Integer(), nullable=True),
        sa.Column("investigation_number", sa.String(20), nullable=False),
        sa.Column("investigation_year", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_investigation_archive_ref_manifest",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["Patient.id"],
            name="fk_investigation_archive_ref_patient",
        ),
        sa.UniqueConstraint(
            "original_investigation_id",
            name="uq_investigation_archive_ref_original_investigation",
        ),
    )
    op.create_index(
        "ix_investigation_archive_ref_manifest",
        "InvestigationArchiveReference",
        ["archive_manifest_id"],
    )
    op.create_index(
        "ix_investigation_archive_ref_investigation",
        "InvestigationArchiveReference",
        ["original_investigation_id"],
    )
    op.create_index(
        "ix_investigation_archive_ref_patient",
        "InvestigationArchiveReference",
        ["patient_id"],
    )
    op.create_index(
        "ix_investigation_archive_ref_year",
        "InvestigationArchiveReference",
        ["investigation_year"],
    )


def downgrade() -> None:
    op.drop_table("InvestigationArchiveReference")
    op.drop_index("ix_investigation_is_current_year", table_name="Investigation")
    op.drop_index("ix_investigation_storage_tier", table_name="Investigation")
    op.drop_index("ix_investigation_investigation_year", table_name="Investigation")
    op.drop_column("Investigation", "is_current_year")
    op.drop_column("Investigation", "storage_tier")
    op.drop_column("Investigation", "investigation_year")
