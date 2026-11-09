"""Add the certificate register.

NCH Code of Ethics 7(1) requires a copy of every medical certificate kept for at
least three years, and 27 requires a case statement with a referral.

Revision ID: 0039_medical_certificates
Revises: 0038_adverse_events
"""

from alembic import op
import sqlalchemy as sa

revision = "0039_medical_certificates"
down_revision = "0038_adverse_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='MedicalCertificate'"
    ).fetchone():
        return

    op.create_table(
        "MedicalCertificate",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("Patient.id"), nullable=False),
        sa.Column("certificate_type", sa.String(20), nullable=False),
        sa.Column("certificate_number", sa.String(40), nullable=False, unique=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issued_by", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("case_statement", sa.Text(), nullable=True),
        sa.Column("retention_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_voided", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_MedicalCertificate_patient_id", "MedicalCertificate", ["patient_id"])
    op.create_index("ix_MedicalCertificate_type", "MedicalCertificate", ["certificate_type"])
    op.create_index("ix_MedicalCertificate_retention", "MedicalCertificate", ["retention_until"])


def downgrade() -> None:
    op.drop_table("MedicalCertificate")
