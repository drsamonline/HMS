"""HHMS operational-year calculation and configuration service."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system_setting import SystemSetting

CALENDAR = "calendar"
FINANCIAL = "financial"
BASIS_KEY = "operational_year_basis"
START_MONTH_KEY = "financial_year_start_month"
START_DAY_KEY = "financial_year_start_day"

@dataclass(frozen=True)
class OperationalYearConfig:
    basis: str = CALENDAR
    start_month: int = 4
    start_day: int = 1

class OperationalYearService:
    async def get_config(self, db: AsyncSession) -> OperationalYearConfig:
        rows = await db.execute(select(SystemSetting).where(SystemSetting.setting_key.in_([BASIS_KEY, START_MONTH_KEY, START_DAY_KEY])))
        values = {row.setting_key: row.setting_value for row in rows.scalars().all()}
        basis = values.get(BASIS_KEY, CALENDAR).lower()
        if basis not in {CALENDAR, FINANCIAL}:
            basis = CALENDAR
        try:
            month = int(values.get(START_MONTH_KEY, 4))
            day = int(values.get(START_DAY_KEY, 1))
            date(2024, month, day)
        except (TypeError, ValueError):
            month, day = 4, 1
        return OperationalYearConfig(basis=basis, start_month=month, start_day=day)

    async def save_config(self, db: AsyncSession, *, basis: str, start_month: int = 4, start_day: int = 1) -> OperationalYearConfig:
        basis = basis.lower().strip()
        if basis not in {CALENDAR, FINANCIAL}:
            raise ValueError("basis must be 'calendar' or 'financial'")
        date(2024, start_month, start_day)
        desired = {
            BASIS_KEY: basis,
            START_MONTH_KEY: str(start_month),
            START_DAY_KEY: str(start_day),
        }
        for key, value in desired.items():
            row = await db.scalar(select(SystemSetting).where(SystemSetting.setting_key == key))
            if row is None:
                row = SystemSetting(setting_key=key, setting_value=value, setting_type="string", is_editable=True)
                db.add(row)
            else:
                row.setting_value = value
        await db.commit()
        return OperationalYearConfig(basis=basis, start_month=start_month, start_day=start_day)

    @staticmethod
    def current_year(today: date, config: OperationalYearConfig) -> int:
        if config.basis == CALENDAR:
            return today.year
        start = date(today.year, config.start_month, config.start_day)
        return today.year if today >= start else today.year - 1

    @staticmethod
    def label(today: date, config: OperationalYearConfig) -> str:
        year = OperationalYearService.current_year(today, config)
        if config.basis == CALENDAR:
            return str(year)
        return f"{year}-{str(year + 1)[-2:]}"

    @staticmethod
    def contains(case_year: int, today: date, config: OperationalYearConfig) -> bool:
        return case_year == OperationalYearService.current_year(today, config)

    @staticmethod
    def bounds_for_year(year: int, config: OperationalYearConfig):
        """Return an inclusive-start/exclusive-end UTC datetime window for an operational year."""
        from datetime import datetime, timezone
        if config.basis == CALENDAR:
            start = datetime(year, 1, 1, tzinfo=timezone.utc)
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            return start, end
        start = datetime(year, config.start_month, config.start_day, tzinfo=timezone.utc)
        end = datetime(year + 1, config.start_month, config.start_day, tzinfo=timezone.utc)
        return start, end


operational_year_service = OperationalYearService()
__all__ = ["OperationalYearConfig", "OperationalYearService", "operational_year_service", "CALENDAR", "FINANCIAL"]
