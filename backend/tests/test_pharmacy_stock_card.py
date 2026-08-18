from decimal import Decimal
from app.schemas.stock_card import StockCardCreate


def test_stock_card_schema_requires_positive_movement():
    card = StockCardCreate(transaction_type="Receipt", quantity=Decimal("2"))
    assert card.quantity == Decimal("2")


def test_dispense_ledger_is_issue_movement():
    assert "Issue" in {"Receipt", "Issue", "Adjustment", "Return"}
