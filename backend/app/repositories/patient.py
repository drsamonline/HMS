"""
HHMS Patient Repository.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.repositories.base import RepositoryBase


class PatientRepository(RepositoryBase[Patient]):
    """Persistence operations for Patient."""

    def __init__(self) -> None:
        super().__init__(Patient)

    async def get_by_id(
        self,
        db: AsyncSession,
        patient_id: int,
    ) -> Patient | None:
        return await db.get(
            Patient,
            patient_id,
        )

    async def get_by_patient_number(
        self,
        db: AsyncSession,
        *,
        patient_number: str,
    ) -> Patient | None:
        result = await db.execute(
            select(Patient).where(
                Patient.patient_number == patient_number
            )
        )

        return result.scalar_one_or_none()

    async def search(
        self,
        db: AsyncSession,
        *,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Patient]:
        statement = select(Patient)

        if search:
            term = f"%{search.strip()}%"

            statement = statement.where(
                (Patient.patient_number.ilike(term))
                | (Patient.first_name.ilike(term))
                | (Patient.last_name.ilike(term))
                | (Patient.mobile_number.ilike(term))
            )

        statement = (
            statement
            .order_by(Patient.id.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(statement)

        return list(result.scalars().all())

    async def count(
        self,
        db: AsyncSession,
    ) -> int:
        result = await db.execute(
            select(func.count(Patient.id))
        )

        return int(result.scalar_one())


patient_repository = PatientRepository()


__all__ = [
    "PatientRepository",
    "patient_repository",
]