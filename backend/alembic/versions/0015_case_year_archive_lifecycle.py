"""Add yearly case lifecycle metadata and archive manifests."""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
revision="0015_case_year_archive_lifecycle"
down_revision="0014_number_sequence_integration"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("CaseRecord", sa.Column("case_family_id", sa.String(36), nullable=True))
    op.add_column("CaseRecord", sa.Column("case_year", sa.Integer(), nullable=True))
    op.add_column("CaseRecord", sa.Column("renewed_from_case_id", sa.Integer(), nullable=True))
    op.add_column("CaseRecord", sa.Column("storage_tier", sa.String(20), nullable=False, server_default="live"))
    op.add_column("CaseRecord", sa.Column("is_current_year", sa.Boolean(), nullable=False, server_default=sa.true()))
    bind=op.get_bind()
    rows=bind.execute(sa.text("SELECT id, created_at FROM CaseRecord")).fetchall()
    import uuid, datetime
    for rid, created_at in rows:
        year=created_at.year if hasattr(created_at,"year") else datetime.datetime.now().year
        bind.execute(sa.text("UPDATE CaseRecord SET case_family_id=:fid, case_year=:year WHERE id=:id"), {"fid":str(uuid.uuid4()),"year":year,"id":rid})
    op.alter_column("CaseRecord","case_family_id",nullable=False)
    op.alter_column("CaseRecord","case_year",nullable=False)
    op.create_index("ix_case_record_family","CaseRecord",["case_family_id"])
    op.create_index("ix_case_record_year","CaseRecord",["case_year"])
    op.create_index("ix_case_record_current_year","CaseRecord",["is_current_year"])
    op.create_foreign_key("fk_case_record_renewed_from","CaseRecord","CaseRecord",["renewed_from_case_id"],["id"])
    op.create_table("ArchiveManifest", sa.Column("id",sa.Integer(),primary_key=True), sa.Column("archive_year",sa.Integer(),nullable=False), sa.Column("storage_tier",sa.String(20),nullable=False), sa.Column("file_path",sa.String(500),nullable=False), sa.Column("checksum_sha256",sa.String(64),nullable=False), sa.Column("size_bytes",sa.Integer(),nullable=False), sa.Column("verified",sa.Boolean(),nullable=False,server_default=sa.true()), sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("CURRENT_TIMESTAMP")), sa.UniqueConstraint("archive_year",name="uq_archive_manifest_year"))
    op.create_index("ix_archive_manifest_year","ArchiveManifest",["archive_year"])
    op.create_index("ix_archive_manifest_tier","ArchiveManifest",["storage_tier"])

def downgrade():
    op.drop_index("ix_archive_manifest_tier",table_name="ArchiveManifest"); op.drop_index("ix_archive_manifest_year",table_name="ArchiveManifest"); op.drop_table("ArchiveManifest")
    op.drop_constraint("fk_case_record_renewed_from","CaseRecord",type_="foreignkey")
    op.drop_index("ix_case_record_current_year",table_name="CaseRecord"); op.drop_index("ix_case_record_year",table_name="CaseRecord"); op.drop_index("ix_case_record_family",table_name="CaseRecord")
    op.drop_column("CaseRecord","is_current_year"); op.drop_column("CaseRecord","storage_tier"); op.drop_column("CaseRecord","renewed_from_case_id"); op.drop_column("CaseRecord","case_year"); op.drop_column("CaseRecord","case_family_id")
