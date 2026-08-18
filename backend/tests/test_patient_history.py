from datetime import date
from app.services.operational_year import OperationalYearConfig, OperationalYearService


def test_calendar_bounds():
    start, end = OperationalYearService.bounds_for_year(2026, OperationalYearConfig("calendar", 4, 1))
    assert start.date() == date(2026, 1, 1)
    assert end.date() == date(2027, 1, 1)


def test_financial_bounds():
    start, end = OperationalYearService.bounds_for_year(2026, OperationalYearConfig("financial", 4, 1))
    assert start.date() == date(2026, 4, 1)
    assert end.date() == date(2027, 4, 1)
