"""HHMS Case Record service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleException,
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.models.admission import Admission
from app.models.case_record import CaseRecord
from app.models.patient import Patient
from app.models.visit import Visit
from app.repositories.case_record import CaseRecordRepository, case_record_repository
from app.schemas.case_record import CaseRecordCreate, CaseRecordUpdate


class CaseRecordService:
    def __init__(self, repository: CaseRecordRepository | None = None) -> None:
        self.repository = repository or case_record_repository

    async def get_by_id(self, db: AsyncSession, case_record_id: int) -> CaseRecord:
        record = await self.repository.get_by_id(db, case_record_id)
        if record is None:
            raise ResourceNotFoundException("Case record not found.")
        return record

    async def list_by_patient(
        self, db: AsyncSession, patient_id: int, skip: int = 0, limit: int = 50
    ) -> list[CaseRecord]:
        return await self.repository.list_by_patient(db, patient_id, skip, limit)

    async def create(
        self, db: AsyncSession, data: CaseRecordCreate, created_by: int
    ) -> CaseRecord:
        patient = await db.get(Patient, data.patient_id)
        if patient is None:
            raise ResourceNotFoundException("Patient not found.")

        if data.visit_id is not None:
            visit = await db.get(Visit, data.visit_id)
            if visit is None:
                raise ResourceNotFoundException("Visit not found.")
            if visit.patient_id != data.patient_id:
                raise BusinessRuleException("Visit does not belong to the patient.")

        if data.admission_id is not None:
            admission = await db.get(Admission, data.admission_id)
            if admission is None:
                raise ResourceNotFoundException("Admission not found.")
            if admission.patient_id != data.patient_id:
                raise BusinessRuleException("Admission does not belong to the patient.")

        now = datetime.now(timezone.utc)
        record = CaseRecord(
            **data.model_dump(),
            case_number="PENDING",
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

        try:
            record = await self.repository.add(db, record)
            record.case_number = f"CASE-{record.id:06d}"
            await self.repository.update(db, record)
            await db.commit()
            return record
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateResourceException("Unable to create case record.") from exc
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create case record.") from exc

    async def update(
        self, db: AsyncSession, case_record_id: int, data: CaseRecordUpdate
    ) -> CaseRecord:
        record = await self.get_by_id(db, case_record_id)
        values = data.model_dump(exclude_unset=True)
        if not values:
            return record

        for field, value in values.items():
            setattr(record, field, value)
        record.updated_at = datetime.now(timezone.utc)

        try:
            await self.repository.update(db, record)
            await db.commit()
            return record
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to update case record.") from exc


case_record_service = CaseRecordService()

__all__ = ["CaseRecordService", "case_record_service"]
