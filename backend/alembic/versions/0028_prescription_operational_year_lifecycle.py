"""Prescription annual lifecycle: lifecycle columns and archive references.

Batch 77 - Prescription Annual Lifecycle & Lineage.

Adds operational-year lifecycle columns to Prescription (prescription_year)
and PrescriptionItem (item_year), backfills prescription_year from the
calendar year of prescription_datetime and item_year from the parent
prescription, makes Prescription.visit_id nullable so archived visits can be
detached safely during physical rollover (mirrors the Batch 72
DispenseRecord.prescription_item_id pattern), and creates the permanent
live-database PrescriptionArchiveReference and
PrescriptionItemArchiveReference tables so prescription identity and
dispensing lineage survive annual rollover.

This closes the integrity gap where the rollover physically deleted Visit
rows while Prescriptions still pointed at them, leaving broken clinical
lineage in archived years.
"""
from alembic import op
import sqlalchemy as sa

revision = "0028_prescription_operational_year_lifecycle"
down_revision = "0027_procurement_inventory_operational_year_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Prescription lifecycle columns -------------------------------------
    op.add_column(
        "Prescription",
        sa.Column("prescription_year", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "Prescription",
        sa.Column(
            "storage_tier",
            sa.String(20),
            nullable=False,
            server_default="live",
        ),
    )
    op.add_column(
        "Prescription",
        sa.Column(
            "is_current_year",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.create_index("ix_prescription_prescription_year", "Prescription", ["prescription_year"])
    op.create_index("ix_prescription_storage_tier", "Prescription", ["storage_tier"])
    op.create_index("ix_prescription_is_current_year", "Prescription", ["is_current_year"])
    op.execute(
        "UPDATE Prescription SET prescription_year = "
        "CAST(strftime('%Y', prescription_datetime) AS INTEGER) "
        "WHERE prescription_datetime IS NOT NULL"
    )

    # Detach-safe lineage: archived visits are physically removed by the
    # rollover, so prescriptions must tolerate a null visit pointer.
    with op.batch_alter_table("Prescription") as batch_op:
        batch_op.alter_column("visit_id", existing_type=sa.Integer(), nullable=True)

    # --- PrescriptionItem lifecycle columns ---------------------------------
    op.add_column(
        "PrescriptionItem",
        sa.Column("item_year", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "PrescriptionItem",
        sa.Column(
            "storage_tier",
            sa.String(20),
            nullable=False,
            server_default="live",
        ),
    )
    op.add_column(
        "PrescriptionItem",
        sa.Column(
            "is_current_year",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.create_index("ix_prescription_item_item_year", "PrescriptionItem", ["item_year"])
    op.create_index("ix_prescription_item_storage_tier", "PrescriptionItem", ["storage_tier"])
    op.create_index("ix_prescription_item_is_current_year", "PrescriptionItem", ["is_current_year"])
    op.execute(
        "UPDATE PrescriptionItem SET item_year = ("
        "SELECT p.prescription_year FROM Prescription p "
        "WHERE p.id = PrescriptionItem.prescription_id) "
        "WHERE item_year = 0"
    )

    # --- Archive reference tables --------------------------------------------
    op.create_table(
        "PrescriptionArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_prescription_id", sa.Integer(), nullable=False),
        sa.Column("visit_id", sa.Integer(), nullable=True),
        sa.Column("prescription_number", sa.String(20), nullable=False),
        sa.Column("prescription_year", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_prescription_archive_ref_manifest",
        ),
        sa.UniqueConstraint(
            "original_prescription_id",
            name="uq_prescription_archive_ref_original_prescription",
        ),
    )
    op.create_index(
        "ix_prescription_archive_ref_manifest",
        "PrescriptionArchiveReference",
        ["archive_manifest_id"],
    )
    op.create_index(
        "ix_prescription_archive_ref_prescription",
        "PrescriptionArchiveReference",
        ["original_prescription_id"],
    )
    op.create_index(
        "ix_prescription_archive_ref_visit",
        "PrescriptionArchiveReference",
        ["visit_id"],
    )
    op.create_index(
        "ix_prescription_archive_ref_year",
        "PrescriptionArchiveReference",
        ["prescription_year"],
    )

    op.create_table(
        "PrescriptionItemArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_item_id", sa.Integer(), nullable=False),
        sa.Column("original_prescription_id", sa.Integer(), nullable=False),
        sa.Column("medicine_id", sa.Integer(), nullable=False),
        sa.Column("item_year", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_prescription_item_archive_ref_manifest",
        ),
        sa.UniqueConstraint(
            "original_item_id",
            name="uq_prescription_item_archive_ref_original_item",
        ),
    )
    op.create_index(
        "ix_prescription_item_archive_ref_manifest",
        "PrescriptionItemArchiveReference",
        ["archive_manifest_id"],
    )
    op.create_index(
        "ix_prescription_item_archive_ref_item",
        "PrescriptionItemArchiveReference",
        ["original_item_id"],
    )
    op.create_index(
        "ix_prescription_item_archive_ref_prescription",
        "PrescriptionItemArchiveReference",
        ["original_prescription_id"],
    )
    op.create_index(
        "ix_prescription_item_archive_ref_medicine",
        "PrescriptionItemArchiveReference",
        ["medicine_id"],
    )
    op.create_index(
        "ix_prescription_item_archive_ref_year",
        "PrescriptionItemArchiveReference",
        ["item_year"],
    )


def downgrade() -> None:
    op.drop_table("PrescriptionItemArchiveReference")
    op.drop_table("PrescriptionArchiveReference")

    op.drop_index("ix_prescription_item_is_current_year", table_name="PrescriptionItem")
    op.drop_index("ix_prescription_item_storage_tier", table_name="PrescriptionItem")
    op.drop_index("ix_prescription_item_item_year", table_name="PrescriptionItem")
    op.drop_column("PrescriptionItem", "is_current_year")
    op.drop_column("PrescriptionItem", "storage_tier")
    op.drop_column("PrescriptionItem", "item_year")

    with op.batch_alter_table("Prescription") as batch_op:
        batch_op.alter_column("visit_id", existing_type=sa.Integer(), nullable=False)

    op.drop_index("ix_prescription_is_current_year", table_name="Prescription")
    op.drop_index("ix_prescription_storage_tier", table_name="Prescription")
    op.drop_index("ix_prescription_prescription_year", table_name="Prescription")
    op.drop_column("Prescription", "is_current_year")
    op.drop_column("Prescription", "storage_tier")
    op.drop_column("Prescription", "prescription_year")
