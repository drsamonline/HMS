from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.number_sequence import NumberSequenceService


def test_reset_due_yearly() -> None:
    service = NumberSequenceService()
    seq = SimpleNamespace(reset_frequency="yearly", last_reset_at=datetime(2025, 12, 31, tzinfo=timezone.utc), current_value=9)
    service._reset_if_due(seq, datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert seq.current_value == 0


def test_never_does_not_reset() -> None:
    service = NumberSequenceService()
    seq = SimpleNamespace(reset_frequency="never", last_reset_at=None, current_value=9)
    service._reset_if_due(seq, datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert seq.current_value == 9
