from decimal import Decimal

def test_invoice_item_total_is_decimal_calculation():
    quantity = Decimal("2.50")
    unit_price = Decimal("100.00")
    assert (quantity * unit_price).quantize(Decimal("0.01")) == Decimal("250.00")
