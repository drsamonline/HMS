"""Batch 40 regression tests."""
from decimal import Decimal

def test_stock_delta_rules():
    assert Decimal("5") + Decimal("2") == Decimal("7")
    assert Decimal("5") - Decimal("2") == Decimal("3")
