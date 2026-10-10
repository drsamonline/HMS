"""HHMS Diagnosis service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseException, ResourceNotFoundException
from app.models.case_record import CaseRecord
from app.models.visit import Visit
from app.models.diagnosis import Diagnosis
from app.repositories.diagnosis import DiagnosisRepository, diagnosis_repository
from app.schemas.diagnosis import DiagnosisCreate, DiagnosisUpdate


class DiagnosisService:
    def __init__(self, repository: DiagnosisRepository | None = None) -> None:
        self.repository = repository or diagnosis_repository

    async def get_by_id(self, db: AsyncSession, diagnosis_id: int) -> Diagnosis:
        diagnosis = await self.repository.get_by_id(db, diagnosis_id)
        if diagnosis is None:
            raise ResourceNotFoundException("Diagnosis not found.")
        return diagnosis

    async def list_by_case(
        self, db: AsyncSession, case_record_id: int, skip: int = 0, limit: int = 50
    ) -> list[Diagnosis]:
        return await self.repository.list_by_case(db, case_record_id, skip, limit)

    async def create(
        self, db: AsyncSession, data: DiagnosisCreate, created_by: int
    ) -> Diagnosis:
        case = await db.get(CaseRecord, data.case_record_id)
        if case is None:
            raise ResourceNotFoundException("Case record not found.")
        if case.patient_id != data.patient_id:
            raise ResourceNotFoundException("Patient does not match the case record.")
        if data.visit_id is not None:
            visit = await db.get(Visit, data.visit_id)
            if visit is None:
                raise ResourceNotFoundException("Visit not found.")
            if visit.patient_id != data.patient_id:
                raise ResourceNotFoundException("Visit does not belong to the patient.")

        diagnosis = Diagnosis(
            **data.model_dump(),
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        try:
            diagnosis = await self.repository.add(db, diagnosis)
            await db.commit()
            return diagnosis
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create diagnosis.") from exc

    async def update(
        self, db: AsyncSession, diagnosis_id: int, data: DiagnosisUpdate
    ) -> Diagnosis:
        diagnosis = await self.get_by_id(db, diagnosis_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(diagnosis, field, value)
        diagnosis.updated_at = datetime.now(timezone.utc)
        try:
            await self.repository.update(db, diagnosis)
            await db.commit()
            return diagnosis
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to update diagnosis.") from exc


diagnosis_service = DiagnosisService()

__all__ = ["DiagnosisService", "diagnosis_service"]
