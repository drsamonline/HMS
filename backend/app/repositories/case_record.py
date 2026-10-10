"""HHMS Case Record repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_record import CaseRecord
from app.repositories.base import RepositoryBase


class CaseRecordRepository(RepositoryBase[CaseRecord]):
    def __init__(self) -> None:
        super().__init__(CaseRecord)

    async def get_by_id(self, db: AsyncSession, case_record_id: int) -> CaseRecord | None:
        return await db.get(CaseRecord, case_record_id)

    async def list_by_patient(
        self, db: AsyncSession, patient_id: int, skip: int = 0, limit: int = 50
    ) -> list[CaseRecord]:
        result = await db.execute(
            select(CaseRecord)
            .where(CaseRecord.patient_id == patient_id)
            .order_by(CaseRecord.updated_at.desc(), CaseRecord.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


case_record_repository = CaseRecordRepository()

__all__ = ["CaseRecordRepository", "case_record_repository"]
