"""HHMS Diagnosis repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diagnosis import Diagnosis
from app.repositories.base import RepositoryBase


class DiagnosisRepository(RepositoryBase[Diagnosis]):
    def __init__(self) -> None:
        super().__init__(Diagnosis)

    async def get_by_id(self, db: AsyncSession, diagnosis_id: int) -> Diagnosis | None:
        return await db.get(Diagnosis, diagnosis_id)

    async def list_by_case(
        self, db: AsyncSession, case_record_id: int, skip: int = 0, limit: int = 50
    ) -> list[Diagnosis]:
        result = await db.execute(
            select(Diagnosis)
            .where(Diagnosis.case_record_id == case_record_id)
            .order_by(Diagnosis.is_primary.desc(), Diagnosis.id.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


diagnosis_repository = DiagnosisRepository()

__all__ = ["DiagnosisRepository", "diagnosis_repository"]
