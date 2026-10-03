"""HHMS ArchiveRecord repository."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.archive_record import ArchiveRecord
from app.repositories.base import RepositoryBase

class ArchiveRecordRepository(RepositoryBase[ArchiveRecord]):
    def __init__(self) -> None:
        super().__init__(ArchiveRecord)

    async def get_by_id(self, db: AsyncSession, archive_id: int) -> ArchiveRecord | None:
        return await db.get(ArchiveRecord, archive_id)

    async def list_by_patient_file(
        self, db: AsyncSession, patient_file_id: int, skip: int = 0, limit: int = 50
    ) -> list[ArchiveRecord]:
        result = await db.execute(
            select(ArchiveRecord)
            .where(ArchiveRecord.patient_file_id == patient_file_id)
            .order_by(ArchiveRecord.id.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

archive_record_repository = ArchiveRecordRepository()
__all__ = ["ArchiveRecordRepository", "archive_record_repository"]
