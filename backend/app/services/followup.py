"""HHMS Homoeopathic Follow-up service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseException, ResourceNotFoundException
from app.models.case_record import CaseRecord
from app.models.followup import FollowUp
from app.models.visit import Visit
from app.repositories.followup import FollowUpRepository, followup_repository
from app.schemas.followup import FollowUpCreate, FollowUpUpdate


class FollowUpService:
    def __init__(self, repository: FollowUpRepository | None = None) -> None:
        self.repository = repository or followup_repository

    async def get_by_id(self, db: AsyncSession, followup_id: int) -> FollowUp:
        record = await self.repository.get_by_id(db, followup_id)
        if record is None:
            raise ResourceNotFoundException("Follow-up not found.")
        return record

    async def list_by_case(
        self, db: AsyncSession, case_record_id: int, skip: int = 0, limit: int = 50
    ) -> list[FollowUp]:
        return await self.repository.list_by_case(db, case_record_id, skip, limit)

    async def create(
        self, db: AsyncSession, data: FollowUpCreate, recorded_by: int
    ) -> FollowUp:
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

        now = datetime.now(timezone.utc)
        record = FollowUp(
            **data.model_dump(),
            recorded_by=recorded_by,
            created_at=now,
            updated_at=now,
        )
        try:
            record = await self.repository.add(db, record)
            await db.commit()
            return record
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create follow-up.") from exc

    async def update(
        self, db: AsyncSession, followup_id: int, data: FollowUpUpdate
    ) -> FollowUp:
        record = await self.get_by_id(db, followup_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(record, field, value)
        record.updated_at = datetime.now(timezone.utc)
        try:
            await self.repository.update(db, record)
            await db.commit()
            return record
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to update follow-up.") from exc


followup_service = FollowUpService()

__all__ = ["FollowUpService", "followup_service"]
