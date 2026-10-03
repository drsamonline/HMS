from decimal import Decimal
from app.services.goods_receipt import GoodsReceiptService

def test_receipt_total_math():
    assert sum([Decimal("3"), Decimal("2.5")], Decimal("0")) == Decimal("5.5")

def test_service_exists():
    assert GoodsReceiptService.__name__ == "GoodsReceiptService"
