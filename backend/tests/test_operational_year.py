from datetime import date
from app.services.operational_year import OperationalYearConfig, OperationalYearService

def test_calendar_year():
    c=OperationalYearConfig('calendar',4,1)
    assert OperationalYearService.current_year(date(2026,1,1),c)==2026
    assert OperationalYearService.label(date(2026,1,1),c)=='2026'

def test_financial_year_before_start():
    c=OperationalYearConfig('financial',4,1)
    assert OperationalYearService.current_year(date(2026,3,31),c)==2025
    assert OperationalYearService.label(date(2026,3,31),c)=='2025-26'

def test_financial_year_after_start():
    c=OperationalYearConfig('financial',4,1)
    assert OperationalYearService.current_year(date(2026,4,1),c)==2026
    assert OperationalYearService.label(date(2026,4,1),c)=='2026-27'
