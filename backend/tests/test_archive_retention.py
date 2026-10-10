from datetime import date
from app.services.operational_year import OperationalYearConfig, OperationalYearService


def _age(year: int, today: date, cfg: OperationalYearConfig) -> int:
    current = OperationalYearService.current_year(today, cfg)
    return current - year


def test_calendar_retention_boundaries():
    cfg = OperationalYearConfig("calendar", 4, 1)
    today = date(2026, 8, 18)
    assert _age(2025, today, cfg) == 1
    assert _age(2022, today, cfg) == 4
    assert _age(2020, today, cfg) == 6
    assert _age(2016, today, cfg) == 10
    assert _age(2015, today, cfg) == 11


def test_financial_year_changes_archive_age_basis():
    cfg = OperationalYearConfig("financial", 4, 1)
    assert _age(2025, date(2026, 3, 31), cfg) == 0
    assert _age(2025, date(2026, 4, 1), cfg) == 1
