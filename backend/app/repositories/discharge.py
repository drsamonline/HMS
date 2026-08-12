"""
HHMS Discharge Repository.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discharge import Discharge
from app.repositories.base import RepositoryBase


class DischargeRepository(
    RepositoryBase[Discharge],
):
    """Persistence operations for IPD discharges."""

    def __init__(self) -> None:
        super().__init__(Discharge)

    async def get_by_id(
        self,
        db: AsyncSession,
        discharge_id: int,
    ) -> Discharge | None:
        return await db.get(
            Discharge,
            discharge_id,
        )

    async def get_by_admission(
        self,
        db: AsyncSession,
        admission_id: int,
    ) -> Discharge | None:
        result = await db.execute(
            select(Discharge).where(
                Discharge.admission_id
                == admission_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_all(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Discharge]:
        result = await db.execute(
            select(Discharge)
            .order_by(
                Discharge.discharge_datetime.desc(),
                Discharge.id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )


discharge_repository = DischargeRepository()


__all__ = [
    "DischargeRepository",
    "discharge_repository",
]