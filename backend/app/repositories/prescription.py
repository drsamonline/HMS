"""
HHMS Prescription Repository.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prescription import Prescription
from app.models.prescription_item import PrescriptionItem
from app.repositories.base import RepositoryBase


class PrescriptionRepository(RepositoryBase[Prescription]):
    """Persistence operations for prescriptions."""

    def __init__(self) -> None:
        super().__init__(Prescription)

    async def get_by_id(
        self,
        db: AsyncSession,
        prescription_id: int,
    ) -> Prescription | None:
        return await db.get(
            Prescription,
            prescription_id,
        )

    async def get_by_number(
        self,
        db: AsyncSession,
        *,
        prescription_number: str,
    ) -> Prescription | None:
        result = await db.execute(
            select(Prescription).where(
                Prescription.prescription_number
                == prescription_number,
            )
        )

        return result.scalar_one_or_none()

    async def get_items(
        self,
        db: AsyncSession,
        *,
        prescription_id: int,
    ) -> list[PrescriptionItem]:
        result = await db.execute(
            select(PrescriptionItem)
            .where(
                PrescriptionItem.prescription_id
                == prescription_id,
            )
            .order_by(PrescriptionItem.id.asc())
        )

        return list(result.scalars().all())

    async def list_by_visit(
        self,
        db: AsyncSession,
        *,
        visit_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Prescription]:
        result = await db.execute(
            select(Prescription)
            .where(
                Prescription.visit_id == visit_id,
            )
            .order_by(
                Prescription.prescription_datetime.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())


prescription_repository = PrescriptionRepository()


__all__ = [
    "PrescriptionRepository",
    "prescription_repository",
]