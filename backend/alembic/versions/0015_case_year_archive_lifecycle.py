"""Add yearly case lifecycle metadata and archive manifests."""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
revision="0015_case_year_archive_lifecycle"
down_revision="0014_number_sequence_integration"
branch_labels=None
depends_on=None

def upgrade():
    # All CaseRecord column work (adds, backfill-driven nullability flips and
    # the self-referencing FK) goes through batch mode: SQLite cannot ALTER
    # columns in place or attach constraints via ALTER TABLE.
    with op.batch_alter_table("CaseRecord") as batch_op:
        batch_op.add_column(sa.Column("case_family_id", sa.String(36), nullable=True))
        batch_op.add_column(sa.Column("case_year", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("renewed_from_case_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("storage_tier", sa.String(20), nullable=False, server_default="live"))
        batch_op.add_column(sa.Column("is_current_year", sa.Boolean(), nullable=False, server_default=sa.true()))

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, created_at FROM CaseRecord")).fetchall()
    import uuid, datetime
    for rid, created_at in rows:
        year = created_at.year if hasattr(created_at, "year") else datetime.datetime.now().year
        bind.execute(
            sa.text("UPDATE CaseRecord SET case_family_id=:fid, case_year=:year WHERE id=:id"),
            {"fid": str(uuid.uuid4()), "year": year, "id": rid},
        )

    with op.batch_alter_table("CaseRecord") as batch_op:
        batch_op.alter_column("case_family_id", existing_type=sa.String(36), nullable=False)
        batch_op.alter_column("case_year", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key(
            "fk_case_record_renewed_from", "CaseRecord", ["renewed_from_case_id"], ["id"]
        )

    op.create_index("ix_case_record_family", "CaseRecord", ["case_family_id"])
    op.create_index("ix_case_record_year", "CaseRecord", ["case_year"])
    op.create_index("ix_case_record_current_year", "CaseRecord", ["is_current_year"])
    op.create_table("ArchiveManifest", sa.Column("id",sa.Integer(),primary_key=True), sa.Column("archive_year",sa.Integer(),nullable=False), sa.Column("storage_tier",sa.String(20),nullable=False), sa.Column("file_path",sa.String(500),nullable=False), sa.Column("checksum_sha256",sa.String(64),nullable=False), sa.Column("size_bytes",sa.Integer(),nullable=False), sa.Column("verified",sa.Boolean(),nullable=False,server_default=sa.true()), sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("CURRENT_TIMESTAMP")), sa.UniqueConstraint("archive_year",name="uq_archive_manifest_year"))
    op.create_index("ix_archive_manifest_year","ArchiveManifest",["archive_year"])
    op.create_index("ix_archive_manifest_tier","ArchiveManifest",["storage_tier"])

def downgrade():
    op.drop_index("ix_archive_manifest_tier",table_name="ArchiveManifest"); op.drop_index("ix_archive_manifest_year",table_name="ArchiveManifest"); op.drop_table("ArchiveManifest")
    with op.batch_alter_table("CaseRecord") as batch_op:
        batch_op.drop_constraint("fk_case_record_renewed_from", type_="foreignkey")
        batch_op.drop_column("is_current_year")
        batch_op.drop_column("storage_tier")
        batch_op.drop_column("renewed_from_case_id")
        batch_op.drop_column("case_year")
        batch_op.drop_column("case_family_id")
    op.drop_index("ix_case_record_current_year",table_name="CaseRecord"); op.drop_index("ix_case_record_year",table_name="CaseRecord"); op.drop_index("ix_case_record_family",table_name="CaseRecord")
