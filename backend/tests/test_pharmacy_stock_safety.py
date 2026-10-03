from datetime import date, timedelta
from types import SimpleNamespace
from app.services.stock_batch import StockBatchService


def test_expired_batch_is_classified_expired():
    batch = SimpleNamespace(is_active=True, quantity_remaining=5, expiry_date=date(2026, 8, 17))
    assert StockBatchService.expiry_status(batch, as_of=date(2026, 8, 18)) == "EXPIRED"


def test_soon_to_expire_batch_is_classified_expiring_soon():
    batch = SimpleNamespace(is_active=True, quantity_remaining=5, expiry_date=date(2026, 9, 1))
    assert StockBatchService.expiry_status(batch, as_of=date(2026, 8, 18), warning_days=30) == "EXPIRING_SOON"


def test_exhausted_batch_takes_precedence():
    batch = SimpleNamespace(is_active=True, quantity_remaining=0, expiry_date=date(2030, 1, 1))
    assert StockBatchService.expiry_status(batch, as_of=date(2026, 8, 18)) == "EXHAUSTED"
