"""
HHMS Admission Repository.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admission import Admission
from app.repositories.base import RepositoryBase


class AdmissionRepository(RepositoryBase[Admission]):
    """Persistence operations for inpatient admissions."""

    def __init__(self) -> None:
        super().__init__(Admission)

    async def get_by_id(
        self,
        db: AsyncSession,
        admission_id: int,
    ) -> Admission | None:
        return await db.get(
            Admission,
            admission_id,
        )
    async def get_active_for_bed_for_update(
        self,
        db: AsyncSession,
        bed_id: int,
    ) -> Admission | None:
        result = await db.execute(
            select(Admission)
            .where(
                Admission.bed_id == bed_id,
                Admission.admission_status.in_(("admitted", "active")),
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()


    async def list_all(
        self,
        db: AsyncSession,
        *,
        status: str | None = None,
        patient_id: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Admission]:
        statement = select(Admission)

        if status is not None:
            statement = statement.where(
                Admission.admission_status == status,
            )

        if patient_id is not None:
            statement = statement.where(
                Admission.patient_id == patient_id,
            )

        result = await db.execute(
            statement
            .order_by(
                Admission.admission_datetime.desc(),
                Admission.id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())


admission_repository = AdmissionRepository()


__all__ = [
    "AdmissionRepository",
    "admission_repository",
]