"""Pharmacy annual lifecycle: DispenseRecord lifecycle columns and DispenseArchiveReference.

Batch 72 - Pharmacy Annual Lifecycle & Rollover.

Adds operational-year lifecycle columns to DispenseRecord (dispense_year,
storage_tier, is_current_year), backfills dispense_year from dispense_date's
calendar year, and creates the permanent live-database DispenseArchiveReference
table so dispensing identity survives physical annual rollover.
"""
from alembic import op
import sqlalchemy as sa

revision = "0023_pharmacy_operational_year_lifecycle"
down_revision = "0022_billing_operational_year_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "DispenseRecord",
        sa.Column("dispense_year", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "DispenseRecord",
        sa.Column(
            "storage_tier",
            sa.String(20),
            nullable=False,
            server_default="live",
        ),
    )
    op.add_column(
        "DispenseRecord",
        sa.Column(
            "is_current_year",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.create_index("ix_dispense_record_dispense_year", "DispenseRecord", ["dispense_year"])
    op.create_index("ix_dispense_record_storage_tier", "DispenseRecord", ["storage_tier"])
    op.create_index("ix_dispense_record_is_current_year", "DispenseRecord", ["is_current_year"])

    # Backfill dispense_year from the calendar year of dispense_date.
    op.execute(
        "UPDATE DispenseRecord SET dispense_year = CAST(strftime('%Y', dispense_date) AS INTEGER)"
        " WHERE dispense_date IS NOT NULL"
    )

    # Dispense rows may outlive their rolled-over prescription item; the link
    # becomes detachable during annual pharmacy rollover.
    with op.batch_alter_table("DispenseRecord") as batch_op:
        batch_op.alter_column(
            "prescription_item_id", existing_type=sa.Integer(), nullable=True
        )

    op.create_table(
        "DispenseArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_dispense_id", sa.Integer(), nullable=False),
        sa.Column("prescription_item_id", sa.Integer(), nullable=True),
        sa.Column("dispense_year", sa.Integer(), nullable=False),
        sa.Column("medicine_id", sa.Integer(), nullable=False),
        sa.Column("quantity_dispensed", sa.Numeric(10, 2), nullable=False),
        sa.Column("dispense_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_dispense_archive_ref_manifest",
        ),
        sa.UniqueConstraint(
            "original_dispense_id",
            name="uq_dispense_archive_ref_original_dispense",
        ),
    )
    op.create_index(
        "ix_dispense_archive_ref_manifest", "DispenseArchiveReference", ["archive_manifest_id"]
    )
    op.create_index(
        "ix_dispense_archive_ref_dispense", "DispenseArchiveReference", ["original_dispense_id"]
    )
    op.create_index(
        "ix_dispense_archive_ref_prescription_item",
        "DispenseArchiveReference",
        ["prescription_item_id"],
    )
    op.create_index(
        "ix_dispense_archive_ref_year", "DispenseArchiveReference", ["dispense_year"]
    )


def downgrade() -> None:
    op.drop_table("DispenseArchiveReference")
    with op.batch_alter_table("DispenseRecord") as batch_op:
        batch_op.alter_column(
            "prescription_item_id", existing_type=sa.Integer(), nullable=False
        )
    op.drop_index("ix_dispense_record_is_current_year", table_name="DispenseRecord")
    op.drop_index("ix_dispense_record_storage_tier", table_name="DispenseRecord")
    op.drop_index("ix_dispense_record_dispense_year", table_name="DispenseRecord")
    op.drop_column("DispenseRecord", "is_current_year")
    op.drop_column("DispenseRecord", "storage_tier")
    op.drop_column("DispenseRecord", "dispense_year")
