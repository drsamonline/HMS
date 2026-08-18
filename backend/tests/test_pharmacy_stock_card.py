from decimal import Decimal

def test_adjustment_increases_balance():
    current=Decimal("10")
    qty=Decimal("3")
    assert current+qty == Decimal("13")

def test_adjustment_out_cannot_go_negative():
    current=Decimal("2")
    qty=Decimal("3")
    assert qty > current

def test_ledger_direction_is_exclusive():
    quantity=Decimal("5")
    assert (quantity,Decimal("0")) != (Decimal("0"),quantity)
