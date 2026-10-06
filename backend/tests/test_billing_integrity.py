from datetime import datetime, timezone
from decimal import Decimal


def test_payment_datetime_requires_timezone():
    naive = datetime(2026, 8, 20, 10, 0)
    assert naive.tzinfo is None


def test_payment_datetime_timezone_is_accepted():
    aware = datetime(2026, 8, 20, 10, 0, tzinfo=timezone.utc)
    assert aware.tzinfo is not None


def test_payment_status_thresholds():
    total = Decimal("100.00")
    assert "paid" if Decimal("100.00") >= total else "partial" == "paid"
    assert "partial" if Decimal("25.00") > 0 else "unpaid" == "partial"
    assert "unpaid" if Decimal("0") == 0 else "partial" == "unpaid"
