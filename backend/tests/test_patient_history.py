from datetime import date
from app.services.operational_year import OperationalYearConfig, OperationalYearService


def test_calendar_year_history_basis():
    cfg = OperationalYearConfig("calendar", 4, 1)
    assert OperationalYearService.current_year(date(2026, 8, 18), cfg) == 2026


def test_financial_year_history_basis():
    cfg = OperationalYearConfig("financial", 4, 1)
    assert OperationalYearService.current_year(date(2026, 3, 31), cfg) == 2025
    assert OperationalYearService.current_year(date(2026, 4, 1), cfg) == 2026
