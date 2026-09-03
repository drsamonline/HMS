"""Track case identity after physical annual archive rollover."""
from alembic import op
import sqlalchemy as sa

revision = "0020_case_archive_rollover_reference"
down_revision = "0019_ipd_active_bed_guard"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "CaseArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_case_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("case_family_id", sa.String(36), nullable=False),
        sa.Column("case_number", sa.String(20), nullable=False),
        sa.Column("archive_year", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_case_archive_ref_manifest",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["Patient.id"],
            name="fk_case_archive_ref_patient",
        ),
        sa.UniqueConstraint(
            "original_case_id",
            name="uq_case_archive_ref_original_case",
        ),
    )
    op.create_index(
        "ix_case_archive_reference_manifest",
        "CaseArchiveReference",
        ["archive_manifest_id"],
    )
    op.create_index(
        "ix_case_archive_reference_original_case",
        "CaseArchiveReference",
        ["original_case_id"],
    )
    op.create_index(
        "ix_case_archive_reference_patient",
        "CaseArchiveReference",
        ["patient_id"],
    )
    op.create_index(
        "ix_case_archive_reference_family",
        "CaseArchiveReference",
        ["case_family_id"],
    )
    op.create_index(
        "ix_case_archive_reference_case_number",
        "CaseArchiveReference",
        ["case_number"],
    )
    op.create_index(
        "ix_case_archive_reference_year",
        "CaseArchiveReference",
        ["archive_year"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_case_archive_reference_year",
        table_name="CaseArchiveReference",
    )
    op.drop_index(
        "ix_case_archive_reference_case_number",
        table_name="CaseArchiveReference",
    )
    op.drop_index(
        "ix_case_archive_reference_family",
        table_name="CaseArchiveReference",
    )
    op.drop_index(
        "ix_case_archive_reference_patient",
        table_name="CaseArchiveReference",
    )
    op.drop_index(
        "ix_case_archive_reference_original_case",
        table_name="CaseArchiveReference",
    )
    op.drop_index(
        "ix_case_archive_reference_manifest",
        table_name="CaseArchiveReference",
    )
    op.drop_table("CaseArchiveReference")
