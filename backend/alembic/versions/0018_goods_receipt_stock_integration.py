"""Goods receipt to pharmacy stock integration.

Creates the base pharmacy tables that earlier revisions referenced but never
defined (``StockBatch``, ``PrescriptionItem``, ``DispenseRecord``).  These
were previously only materialised by ``Base.metadata.create_all`` in tests,
so a fresh packaged install upgraded through Alembic had no way to reach a
complete schema.  All FK targets (Medicine, Prescription, GoodsReceipt,
Supplier, User) exist at this point in the chain.
"""
from alembic import op
import sqlalchemy as sa

revision = "0018_goods_receipt_stock_integration"
down_revision = "0017_pharmacy_stock_card_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "StockBatch",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("medicine_id", sa.Integer(), nullable=False),
        sa.Column("batch_no", sa.String(50), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("manufacture_date", sa.Date(), nullable=True),
        sa.Column("quantity_received", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity_remaining", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=True),
        sa.Column("goods_receipt_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(["medicine_id"], ["Medicine.id"], name="fk_stock_batch_medicine"),
        sa.ForeignKeyConstraint(["supplier_id"], ["Supplier.id"], name="fk_stock_batch_supplier"),
        sa.ForeignKeyConstraint(["goods_receipt_id"], ["GoodsReceipt.id"], name="fk_stock_batch_goods_receipt"),
    )
    op.create_index("ix_stock_batch_medicine_id", "StockBatch", ["medicine_id"])
    op.create_index("ix_stock_batch_batch_no", "StockBatch", ["batch_no"])
    op.create_index("ix_stock_batch_expiry_date", "StockBatch", ["expiry_date"])
    op.create_index("ix_stock_batch_supplier_id", "StockBatch", ["supplier_id"])
    op.create_index("ix_stock_batch_goods_receipt_id", "StockBatch", ["goods_receipt_id"])

    op.create_table(
        "PrescriptionItem",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("prescription_id", sa.Integer(), nullable=False),
        sa.Column("medicine_id", sa.Integer(), nullable=False),
        sa.Column("dosage", sa.String(100), nullable=False),
        sa.Column("frequency", sa.String(100), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False),
        # NOTE: item_year / storage_tier / is_current_year lifecycle columns
        # and their indexes are introduced by revision 0028 — do not create
        # them here or the fresh-install chain hits "duplicate column".
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(["prescription_id"], ["Prescription.id"], name="fk_prescription_item_prescription"),
        sa.ForeignKeyConstraint(["medicine_id"], ["Medicine.id"], name="fk_prescription_item_medicine"),
    )
    op.create_index("ix_prescription_item_prescription_id", "PrescriptionItem", ["prescription_id"])
    op.create_index("ix_prescription_item_medicine_id", "PrescriptionItem", ["medicine_id"])

    op.create_table(
        "DispenseRecord",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("prescription_item_id", sa.Integer(), nullable=True),
        sa.Column("medicine_id", sa.Integer(), nullable=False),
        sa.Column("stock_batch_id", sa.Integer(), nullable=False),
        sa.Column("quantity_dispensed", sa.Numeric(10, 2), nullable=False),
        sa.Column("dispense_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("dispensed_by", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(["prescription_item_id"], ["PrescriptionItem.id"], name="fk_dispense_prescription_item"),
        sa.ForeignKeyConstraint(["medicine_id"], ["Medicine.id"], name="fk_dispense_medicine"),
        sa.ForeignKeyConstraint(["stock_batch_id"], ["StockBatch.id"], name="fk_dispense_stock_batch"),
        sa.ForeignKeyConstraint(["dispensed_by"], ["User.id"], name="fk_dispense_user"),
    )
    op.create_index("ix_dispense_record_prescription_item_id", "DispenseRecord", ["prescription_item_id"])
    op.create_index("ix_dispense_record_medicine_id", "DispenseRecord", ["medicine_id"])
    op.create_index("ix_dispense_record_stock_batch_id", "DispenseRecord", ["stock_batch_id"])
    op.create_index("ix_dispense_record_dispensed_by", "DispenseRecord", ["dispensed_by"])


def downgrade() -> None:
    op.drop_index("ix_dispense_record_dispensed_by", table_name="DispenseRecord")
    op.drop_index("ix_dispense_record_stock_batch_id", table_name="DispenseRecord")
    op.drop_index("ix_dispense_record_medicine_id", table_name="DispenseRecord")
    op.drop_index("ix_dispense_record_prescription_item_id", table_name="DispenseRecord")
    op.drop_table("DispenseRecord")
    op.drop_index("ix_prescription_item_medicine_id", table_name="PrescriptionItem")
    op.drop_index("ix_prescription_item_prescription_id", table_name="PrescriptionItem")
    op.drop_table("PrescriptionItem")
    op.drop_index("ix_stock_batch_goods_receipt_id", table_name="StockBatch")
    op.drop_index("ix_stock_batch_supplier_id", table_name="StockBatch")
    op.drop_index("ix_stock_batch_expiry_date", table_name="StockBatch")
    op.drop_index("ix_stock_batch_batch_no", table_name="StockBatch")
    op.drop_index("ix_stock_batch_medicine_id", table_name="StockBatch")
    op.drop_table("StockBatch")
