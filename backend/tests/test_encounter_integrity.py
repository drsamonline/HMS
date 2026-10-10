from datetime import datetime, timezone


def test_timezone_aware_datetime_is_required():
    naive = datetime(2026, 8, 20)
    aware = datetime(2026, 8, 20, tzinfo=timezone.utc)
    assert naive.tzinfo is None
    assert aware.tzinfo is not None


def test_discharge_cannot_precede_admission():
    admission = datetime(2026, 8, 20, 10, tzinfo=timezone.utc)
    discharge = datetime(2026, 8, 20, 9, 59, tzinfo=timezone.utc)
    assert discharge < admission
