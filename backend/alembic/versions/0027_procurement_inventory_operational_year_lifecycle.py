"""Procurement & inventory annual lifecycle: lifecycle columns and archive references.

Batch 76 - Procurement & Inventory Annual Lifecycle & Rollover.

Adds operational-year lifecycle columns to PurchaseOrder (order_year),
GoodsReceipt (receipt_year), StockTransaction (transaction_year) and
StockCard (transaction_year), backfills each year column from the calendar
year of the record's date/datetime, and creates the permanent live-database
PurchaseOrderArchiveReference, GoodsReceiptArchiveReference,
StockTransactionArchiveReference and StockCardArchiveReference tables so
procurement and stock-ledger identity survives physical annual rollover.

Master/current-balance entities (Supplier, Medicine, InventoryItem,
StockBatch) are intentionally excluded from physical rollover because they
carry live state (e.g. StockBatch.quantity_remaining) that dispensing and
stock reporting depend on.
"""
from alembic import op
import sqlalchemy as sa

revision = "0027_procurement_inventory_operational_year_lifecycle"
down_revision = "0026_mrd_operational_year_lifecycle"
branch_labels = None
depends_on = None


_LIFECYCLE_SPECS = [
    # (table, year_column, date_column)
    ("PurchaseOrder", "order_year", "order_date"),
    ("GoodsReceipt", "receipt_year", "receipt_date"),
    ("StockTransaction", "transaction_year", "transaction_datetime"),
    ("StockCard", "transaction_year", "transaction_datetime"),
]


def _add_lifecycle(table: str, year_column: str, date_column: str) -> None:
    op.add_column(
        table,
        sa.Column(year_column, sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        table,
        sa.Column(
            "storage_tier",
            sa.String(20),
            nullable=False,
            server_default="live",
        ),
    )
    op.add_column(
        table,
        sa.Column(
            "is_current_year",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    short = {
        "PurchaseOrder": "purchase_order",
        "GoodsReceipt": "goods_receipt",
        "StockTransaction": "stock_transaction",
        "StockCard": "stock_card",
    }[table]
    op.create_index(f"ix_{short}_{year_column}", table, [year_column])
    op.create_index(f"ix_{short}_storage_tier", table, ["storage_tier"])
    op.create_index(f"ix_{short}_is_current_year", table, ["is_current_year"])
    # Backfill the year column from the calendar year of the record date.
    op.execute(
        f"UPDATE {table} SET {year_column} = "
        f"CAST(strftime('%Y', {date_column}) AS INTEGER)"
        f" WHERE {date_column} IS NOT NULL"
    )


def _drop_lifecycle(table: str, year_column: str) -> None:
    short = {
        "PurchaseOrder": "purchase_order",
        "GoodsReceipt": "goods_receipt",
        "StockTransaction": "stock_transaction",
        "StockCard": "stock_card",
    }[table]
    op.drop_index(f"ix_{short}_is_current_year", table_name=table)
    op.drop_index(f"ix_{short}_storage_tier", table_name=table)
    op.drop_index(f"ix_{short}_{year_column}", table_name=table)
    op.drop_column(table, "is_current_year")
    op.drop_column(table, "storage_tier")
    op.drop_column(table, year_column)


def upgrade() -> None:
    for table, year_column, date_column in _LIFECYCLE_SPECS:
        _add_lifecycle(table, year_column, date_column)

    op.create_table(
        "PurchaseOrderArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("order_no", sa.String(40), nullable=False),
        sa.Column("order_year", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_purchase_order_archive_ref_manifest",
        ),
        sa.UniqueConstraint(
            "original_purchase_order_id",
            name="uq_purchase_order_archive_ref_original_order",
        ),
    )
    op.create_index(
        "ix_purchase_order_archive_ref_manifest",
        "PurchaseOrderArchiveReference",
        ["archive_manifest_id"],
    )
    op.create_index(
        "ix_purchase_order_archive_ref_order",
        "PurchaseOrderArchiveReference",
        ["original_purchase_order_id"],
    )
    op.create_index(
        "ix_purchase_order_archive_ref_supplier",
        "PurchaseOrderArchiveReference",
        ["supplier_id"],
    )
    op.create_index(
        "ix_purchase_order_archive_ref_year",
        "PurchaseOrderArchiveReference",
        ["order_year"],
    )

    op.create_table(
        "GoodsReceiptArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_goods_receipt_id", sa.Integer(), nullable=False),
        sa.Column("goods_receipt_no", sa.String(40), nullable=False),
        sa.Column("receipt_year", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_goods_receipt_archive_ref_manifest",
        ),
        sa.UniqueConstraint(
            "original_goods_receipt_id",
            name="uq_goods_receipt_archive_ref_original_receipt",
        ),
    )
    op.create_index(
        "ix_goods_receipt_archive_ref_manifest",
        "GoodsReceiptArchiveReference",
        ["archive_manifest_id"],
    )
    op.create_index(
        "ix_goods_receipt_archive_ref_receipt",
        "GoodsReceiptArchiveReference",
        ["original_goods_receipt_id"],
    )
    op.create_index(
        "ix_goods_receipt_archive_ref_year",
        "GoodsReceiptArchiveReference",
        ["receipt_year"],
    )

    op.create_table(
        "StockTransactionArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_stock_transaction_id", sa.Integer(), nullable=False),
        sa.Column("inventory_item_id", sa.Integer(), nullable=True),
        sa.Column("transaction_type", sa.String(30), nullable=True),
        sa.Column("reference_number", sa.String(50), nullable=True),
        sa.Column("transaction_year", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_stock_transaction_archive_ref_manifest",
        ),
        sa.UniqueConstraint(
            "original_stock_transaction_id",
            name="uq_stock_transaction_archive_ref_original_transaction",
        ),
    )
    op.create_index(
        "ix_stock_transaction_archive_ref_manifest",
        "StockTransactionArchiveReference",
        ["archive_manifest_id"],
    )
    op.create_index(
        "ix_stock_transaction_archive_ref_transaction",
        "StockTransactionArchiveReference",
        ["original_stock_transaction_id"],
    )
    op.create_index(
        "ix_stock_transaction_archive_ref_item",
        "StockTransactionArchiveReference",
        ["inventory_item_id"],
    )
    op.create_index(
        "ix_stock_transaction_archive_ref_year",
        "StockTransactionArchiveReference",
        ["transaction_year"],
    )

    op.create_table(
        "StockCardArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_stock_card_id", sa.Integer(), nullable=False),
        sa.Column("medicine_id", sa.Integer(), nullable=False),
        sa.Column("transaction_year", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_stock_card_archive_ref_manifest",
        ),
        sa.UniqueConstraint(
            "original_stock_card_id",
            name="uq_stock_card_archive_ref_original_card",
        ),
    )
    op.create_index(
        "ix_stock_card_archive_ref_manifest",
        "StockCardArchiveReference",
        ["archive_manifest_id"],
    )
    op.create_index(
        "ix_stock_card_archive_ref_card",
        "StockCardArchiveReference",
        ["original_stock_card_id"],
    )
    op.create_index(
        "ix_stock_card_archive_ref_medicine",
        "StockCardArchiveReference",
        ["medicine_id"],
    )
    op.create_index(
        "ix_stock_card_archive_ref_year",
        "StockCardArchiveReference",
        ["transaction_year"],
    )


def downgrade() -> None:
    op.drop_table("StockCardArchiveReference")
    op.drop_table("StockTransactionArchiveReference")
    op.drop_table("GoodsReceiptArchiveReference")
    op.drop_table("PurchaseOrderArchiveReference")
    for table, year_column, _date_column in reversed(_LIFECYCLE_SPECS):
        _drop_lifecycle(table, year_column)
