"""HHMS MRD patient files and archive records."""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "0004_medical_records"
down_revision = "0003_ipd_clinical"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "PatientFile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("file_no", sa.String(50), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("shelf_no", sa.String(50), nullable=True),
        sa.Column("rack_no", sa.String(50), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["patient_id"], ["Patient.id"], name="fk_patient_file_patient"),
        sa.UniqueConstraint("file_no", name="uq_patient_file_file_no"),
    )
    op.create_index("ix_patient_file_patient_id", "PatientFile", ["patient_id"])
    op.create_index("ix_patient_file_file_no", "PatientFile", ["file_no"])
    op.create_index("ix_patient_file_file_type", "PatientFile", ["file_type"])
    op.create_index("ix_patient_file_status", "PatientFile", ["status"])

    op.create_table(
        "ArchiveRecord",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_file_id", sa.Integer(), nullable=False),
        sa.Column("archive_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archive_location", sa.String(200), nullable=True),
        sa.Column("box_no", sa.String(50), nullable=True),
        sa.Column("retention_period", sa.String(100), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["patient_file_id"], ["PatientFile.id"], name="fk_archive_record_patient_file"
        ),
    )
    op.create_index(
        "ix_archive_record_patient_file_id", "ArchiveRecord", ["patient_file_id"]
    )
    op.create_index("ix_archive_record_status", "ArchiveRecord", ["status"])

def downgrade() -> None:
    op.drop_index("ix_archive_record_status", table_name="ArchiveRecord")
    op.drop_index("ix_archive_record_patient_file_id", table_name="ArchiveRecord")
    op.drop_table("ArchiveRecord")
    op.drop_index("ix_patient_file_status", table_name="PatientFile")
    op.drop_index("ix_patient_file_file_type", table_name="PatientFile")
    op.drop_index("ix_patient_file_file_no", table_name="PatientFile")
    op.drop_index("ix_patient_file_patient_id", table_name="PatientFile")
    op.drop_table("PatientFile")
