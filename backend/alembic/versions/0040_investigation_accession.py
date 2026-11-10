"""Give an investigation its specimen accession.

An order becomes a sample. The laboratory writes its own identifier on the tube, and
that identifier - not the hospital's investigation number - is how a result is traced
back to what was collected, by whom, and when.

Only the identifier is added here. Sample types, collection timestamps, worklists,
analyser interfaces, QC and barcodes are the next slices, and each of them needs a
decision this revision does not make.

Revision ID: 0040_investigation_accession
Revises: 0039_medical_certificates
"""

from alembic import op
import sqlalchemy as sa

revision = "0040_investigation_accession"
down_revision = "0039_medical_certificates"
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    return any(
        row[1] == column for row in bind.exec_driver_sql(f'PRAGMA table_info("{table}")')
    )


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "Investigation", "sample_accession"):
        op.add_column(
            "Investigation", sa.Column("sample_accession", sa.String(50), nullable=True)
        )
        op.create_index(
            "ix_Investigation_sample_accession",
            "Investigation",
            ["sample_accession"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "Investigation", "sample_accession"):
        op.drop_index("ix_Investigation_sample_accession", table_name="Investigation")
        op.drop_column("Investigation", "sample_accession")
