"""HHMS PatientFile service."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DatabaseException, DuplicateResourceException, ResourceNotFoundException
from app.models.patient import Patient
from app.models.patient_file import PatientFile
from app.repositories.patient_file import PatientFileRepository, patient_file_repository
from app.schemas.patient_file import PatientFileCreate, PatientFileUpdate

class PatientFileService:
    def __init__(self, repository: PatientFileRepository | None = None) -> None:
        self.repository = repository or patient_file_repository

    async def get_by_id(self, db: AsyncSession, patient_file_id: int) -> PatientFile:
        record = await self.repository.get_by_id(db, patient_file_id)
        if record is None:
            raise ResourceNotFoundException("Patient file not found.")
        return record

    async def list_by_patient(
        self, db: AsyncSession, patient_id: int, skip: int = 0, limit: int = 50
    ) -> list[PatientFile]:
        if await db.get(Patient, patient_id) is None:
            raise ResourceNotFoundException("Patient not found.")
        return await self.repository.list_by_patient(db, patient_id, skip, limit)

    async def create(
        self, db: AsyncSession, data: PatientFileCreate
    ) -> PatientFile:
        if await db.get(Patient, data.patient_id) is None:
            raise ResourceNotFoundException("Patient not found.")
        record = PatientFile(**data.model_dump())
        now = datetime.now(timezone.utc)
        record.created_at = now
        record.updated_at = now
        try:
            record = await self.repository.add(db, record)
            await db.commit()
            return record
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateResourceException("Patient file number already exists.") from exc
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create patient file.") from exc

    async def update(
        self, db: AsyncSession, patient_file_id: int, data: PatientFileUpdate
    ) -> PatientFile:
        record = await self.get_by_id(db, patient_file_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(record, field, value)
        record.updated_at = datetime.now(timezone.utc)
        try:
            await self.repository.update(db, record)
            await db.commit()
            return record
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to update patient file.") from exc

patient_file_service = PatientFileService()
__all__ = ["PatientFileService", "patient_file_service"]
