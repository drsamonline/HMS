"""HHMS ArchiveRecord service."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.core.exceptions import DatabaseException, ResourceNotFoundException
from app.models.archive_record import ArchiveRecord
from app.models.patient_file import PatientFile
from app.repositories.archive_record import ArchiveRecordRepository, archive_record_repository
from app.schemas.archive_record import ArchiveRecordCreate, ArchiveRecordUpdate

class ArchiveRecordService:
    def __init__(self, repository: ArchiveRecordRepository | None = None) -> None:
        self.repository = repository or archive_record_repository

    async def get_by_id(self, db: AsyncSession, archive_id: int) -> ArchiveRecord:
        record = await self.repository.get_by_id(db, archive_id)
        if record is None:
            raise ResourceNotFoundException("Archive record not found.")
        return record

    async def list_by_patient_file(
        self, db: AsyncSession, patient_file_id: int, skip: int = 0, limit: int = 50
    ) -> list[ArchiveRecord]:
        if await db.get(PatientFile, patient_file_id) is None:
            raise ResourceNotFoundException("Patient file not found.")
        return await self.repository.list_by_patient_file(db, patient_file_id, skip, limit)

    async def create(
        self, db: AsyncSession, data: ArchiveRecordCreate
    ) -> ArchiveRecord:
        if await db.get(PatientFile, data.patient_file_id) is None:
            raise ResourceNotFoundException("Patient file not found.")
        record = ArchiveRecord(**data.model_dump())
        now = datetime.now(timezone.utc)
        record.created_at = now
        record.updated_at = now
        try:
            record = await self.repository.add(db, record)
            await db.commit()
            return record
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create archive record.") from exc

    async def update(
        self, db: AsyncSession, archive_id: int, data: ArchiveRecordUpdate
    ) -> ArchiveRecord:
        record = await self.get_by_id(db, archive_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(record, field, value)
        record.updated_at = datetime.now(timezone.utc)
        try:
            await self.repository.update(db, record)
            await db.commit()
            return record
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to update archive record.") from exc

archive_record_service = ArchiveRecordService()
__all__ = ["ArchiveRecordService", "archive_record_service"]
