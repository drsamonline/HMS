"""
HHMS Visit Repository.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.visit import Visit
from app.repositories.base import RepositoryBase


class VisitRepository(RepositoryBase[Visit]):
    """Persistence operations for Visit."""

    def __init__(self) -> None:
        super().__init__(Visit)

    async def get_by_id(
        self,
        db: AsyncSession,
        visit_id: int,
    ) -> Visit | None:
        return await db.get(
            Visit,
            visit_id,
        )

    async def get_by_visit_number(
        self,
        db: AsyncSession,
        *,
        visit_number: str,
    ) -> Visit | None:
        result = await db.execute(
            select(Visit).where(
                Visit.visit_number == visit_number,
            )
        )

        return result.scalar_one_or_none()

    async def list_by_patient(
        self,
        db: AsyncSession,
        *,
        patient_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Visit]:
        result = await db.execute(
            select(Visit)
            .where(Visit.patient_id == patient_id)
            .order_by(Visit.visit_datetime.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def list_all(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Visit]:
        result = await db.execute(
            select(Visit)
            .order_by(Visit.visit_datetime.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())


visit_repository = VisitRepository()


__all__ = [
    "VisitRepository",
    "visit_repository",
]