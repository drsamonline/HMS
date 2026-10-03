"""Batch 76 — Procurement & inventory annual lifecycle & rollover contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_procurement_inventory_lifecycle_fields_are_declared():
    from app.models.purchase_order import PurchaseOrder
    from app.models.goods_receipt import GoodsReceipt
    from app.models.stock_transaction import StockTransaction
    from app.models.stock_card import StockCard

    for model, year_attr in (
        (PurchaseOrder, "order_year"),
        (GoodsReceipt, "receipt_year"),
        (StockTransaction, "transaction_year"),
        (StockCard, "transaction_year"),
    ):
        assert hasattr(model, year_attr)
        assert hasattr(model, "storage_tier")
        assert hasattr(model, "is_current_year")


def test_procurement_archive_reference_models_and_migration_exist():
    model = ROOT / "backend" / "app" / "models" / "procurement_archive_reference.py"
    migration = (
        ROOT
        / "backend"
        / "alembic"
        / "versions"
        / "0027_procurement_inventory_operational_year_lifecycle.py"
    )
    assert model.is_file()
    assert migration.is_file()
    text = model.read_text(encoding="utf-8")
    for cls in (
        "class PurchaseOrderArchiveReference",
        "class GoodsReceiptArchiveReference",
        "class StockTransactionArchiveReference",
        "class StockCardArchiveReference",
    ):
        assert cls in text
    assert "original_purchase_order_id" in text
    assert "original_goods_receipt_id" in text
    assert "original_stock_transaction_id" in text
    assert "original_stock_card_id" in text
    assert "archive_manifest_id" in text
    migration_text = migration.read_text(encoding="utf-8")
    assert "down_revision" in migration_text
    for token in (
        "order_year",
        "receipt_year",
        "transaction_year",
        "storage_tier",
        "is_current_year",
        "PurchaseOrderArchiveReference",
        "GoodsReceiptArchiveReference",
        "StockTransactionArchiveReference",
        "StockCardArchiveReference",
    ):
        assert token in migration_text


def test_procurement_archive_references_are_registered():
    init = (ROOT / "backend" / "app" / "models" / "__init__.py").read_text(
        encoding="utf-8"
    )
    for name in (
        "PurchaseOrderArchiveReference",
        "GoodsReceiptArchiveReference",
        "StockTransactionArchiveReference",
        "StockCardArchiveReference",
    ):
        assert name in init


def test_services_derive_lifecycle_fields():
    procurement = (
        ROOT / "backend" / "app" / "services" / "procurement.py"
    ).read_text(encoding="utf-8")
    goods_receipt = (
        ROOT / "backend" / "app" / "services" / "goods_receipt.py"
    ).read_text(encoding="utf-8")
    stock_transaction = (
        ROOT / "backend" / "app" / "services" / "stock_transaction.py"
    ).read_text(encoding="utf-8")
    stock_card = (ROOT / "backend" / "app" / "services" / "stock_card.py").read_text(
        encoding="utf-8"
    )
    assert "operational_year_service" in procurement
    assert "order_year=order_year" in procurement
    assert "receipt_year=receipt_year" in procurement
    assert "receipt_year=receipt_year" in goods_receipt
    assert "transaction_year=transaction_year" in stock_transaction
    assert "transaction_year=transaction_year" in stock_card
    for service in (procurement, goods_receipt, stock_transaction, stock_card):
        assert 'storage_tier="live"' in service or "storage_tier='live'" in service


def test_read_schemas_expose_lifecycle_fields():
    procurement = (ROOT / "backend" / "app" / "schemas" / "procurement.py").read_text(
        encoding="utf-8"
    )
    goods_receipt = (ROOT / "backend" / "app" / "schemas" / "goods_receipt.py").read_text(
        encoding="utf-8"
    )
    stock_transaction = (
        ROOT / "backend" / "app" / "schemas" / "stock_transaction.py"
    ).read_text(encoding="utf-8")
    stock_card = (ROOT / "backend" / "app" / "schemas" / "stock_card.py").read_text(
        encoding="utf-8"
    )
    assert "order_year:int" in procurement.replace(" ", "")
    assert "receipt_year:int" in procurement.replace(" ", "")
    assert "receipt_year: int" in goods_receipt
    assert "transaction_year: int" in stock_transaction
    assert "transaction_year:int" in stock_card.replace(" ", "") or "transaction_year: int" in stock_transaction


def test_archive_manager_handles_procurement_rollover():
    manager = (ROOT / "backend" / "app" / "services" / "archive_manager.py").read_text(
        encoding="utf-8"
    )
    assert "PurchaseOrderArchiveReference(" in manager
    assert "GoodsReceiptArchiveReference(" in manager
    assert "StockTransactionArchiveReference(" in manager
    assert "StockCardArchiveReference(" in manager
    assert "purchase_order_count" in manager
    assert "goods_receipt_count" in manager
    assert "stock_transaction_count" in manager
    assert "stock_card_count" in manager
    assert "purchase_orders_archived" in manager
    assert "goods_receipts_archived" in manager
    assert "stock_transactions_archived" in manager
    assert "stock_cards_archived" in manager
    assert "live_purchase_order_remaining" in manager
    assert "live_goods_receipt_remaining" in manager
    assert "live_stock_transaction_remaining" in manager
    assert "live_stock_card_remaining" in manager
    # Live stock batches must survive rollover with detached receipt links.
    assert "values(goods_receipt_id=None)" in manager
    assert "delete(PurchaseOrderItem).where(" in manager
    assert "delete(PurchaseOrder).where(" in manager
    assert "delete(GoodsReceiptItem).where(" in manager
    assert "delete(GoodsReceipt).where(" in manager
    assert "delete(StockTransaction).where(" in manager
    assert "delete(StockCard).where(" in manager
    assert "async def read_purchase_orders" in manager
    assert "async def read_goods_receipts" in manager
    assert "async def read_stock_transactions" in manager
    assert "async def read_stock_cards" in manager


def test_procurement_rollover_contracts_are_exposed():
    maintenance = (
        ROOT / "backend" / "app" / "api" / "v1" / "endpoints" / "maintenance.py"
    ).read_text(encoding="utf-8")
    api = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
    for route in (
        '@router.get("/archives/{year}/purchase-orders")',
        '@router.get("/archives/{year}/goods-receipts")',
        '@router.get("/archives/{year}/stock-transactions")',
        '@router.get("/archives/{year}/stock-cards")',
    ):
        assert route in maintenance
    for call in (
        "archive_manager.read_purchase_orders",
        "archive_manager.read_goods_receipts",
        "archive_manager.read_stock_transactions",
        "archive_manager.read_stock_cards",
    ):
        assert call in maintenance
    for wrapper in (
        "getHistoricalPurchaseOrders",
        "getHistoricalGoodsReceipts",
        "getHistoricalStockTransactions",
        "getHistoricalStockCards",
    ):
        assert wrapper in api
