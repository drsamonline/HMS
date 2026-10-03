"""HHMS Case Record service."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
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

from app.services.number_sequence import number_sequence_service
from app.services.operational_year import operational_year_service


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

    async def renew_current_year(
        self, db: AsyncSession, patient_id: int, created_by: int, visit_id: int | None = None, admission_id: int | None = None
    ) -> CaseRecord:
        now = datetime.now(timezone.utc)
        op_cfg = await operational_year_service.get_config(db)
        op_year = operational_year_service.current_year(now.date(), op_cfg)
        rows = await self.repository.list_by_patient(db, patient_id, 0, 100)
        current = next((c for c in rows if c.case_year == op_year and c.is_current_year and c.storage_tier == "live"), None)
        if current is not None:
            return current
        previous = rows[0] if rows else None
        if previous is None:
            payload = CaseRecordCreate(patient_id=patient_id, visit_id=visit_id, admission_id=admission_id, case_status="draft")
            return await self.create(db, payload, created_by)
        if previous.patient_id != patient_id:
            raise BusinessRuleException("Case does not belong to patient.")
        if visit_id is not None:
            visit = await db.get(Visit, visit_id)
            if visit is None or visit.patient_id != patient_id:
                raise BusinessRuleException("Visit does not belong to the patient.")
        if admission_id is not None:
            admission = await db.get(Admission, admission_id)
            if admission is None or admission.patient_id != patient_id:
                raise BusinessRuleException("Admission does not belong to the patient.")
        for item in rows:
            item.is_current_year = False
            if item.storage_tier == "live" and item.case_year < op_year:
                item.storage_tier = "online_archive"
        baseline_fields = {
            "past_history": previous.past_history, "family_history": previous.family_history,
            "personal_history": previous.personal_history, "mental_generals": previous.mental_generals,
            "physical_generals": previous.physical_generals, "female_history": previous.female_history,
            "male_history": previous.male_history, "sexual_reproductive_history": previous.sexual_reproductive_history,
            "obstetric_history": previous.obstetric_history, "surgical_history": previous.surgical_history,
            "miasmatic_assessment": previous.miasmatic_assessment, "case_status": "draft",
            "patient_id": patient_id, "visit_id": visit_id, "admission_id": admission_id,
        }
        record = CaseRecord(
            **baseline_fields,
            case_number=await number_sequence_service.next_number(db, "case_number"),
            case_family_id=previous.case_family_id,
            case_year=op_year,
            renewed_from_case_id=previous.id,
            storage_tier="live",
            is_current_year=True,
            created_by=created_by,
            created_at=now, updated_at=now,
        )
        db.add(record)
        try:
            await db.commit(); await db.refresh(record); return record
        except SQLAlchemyError as exc:
            await db.rollback(); raise DatabaseException("Unable to renew case for current year.") from exc

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
        op_cfg = await operational_year_service.get_config(db)
        op_year = operational_year_service.current_year(now.date(), op_cfg)
        values = data.model_dump(exclude={"case_family_id"})
        record = CaseRecord(
            **values,
            case_number=await number_sequence_service.next_number(db, "case_number"),
            case_family_id=data.case_family_id or str(uuid4()),
            case_year=op_year,
            storage_tier="live",
            is_current_year=True,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

        try:
            record = await self.repository.add(db, record)
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
