"""HHMS IPD Assessment service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseException, DuplicateResourceException, ResourceNotFoundException
from app.models.admission import Admission
from app.models.ipd_assessment import IPDAssessment
from app.repositories.ipd_assessment import ipd_assessment_repository
from app.schemas.ipd_assessment import IPDAssessmentCreate, IPDAssessmentUpdate


class IPDAssessmentService:
    async def get(self, db: AsyncSession, object_id: int) -> IPDAssessment:
        item = await ipd_assessment_repository.get_by_id(db, object_id)
        if item is None:
            raise ResourceNotFoundException("IPD Assessment not found.")
        return item

    async def list(self, db: AsyncSession, admission_id: int, skip: int = 0, limit: int = 100) -> list[IPDAssessment]:
        admission = await db.get(Admission, admission_id)
        if admission is None:
            raise ResourceNotFoundException("Admission not found.")
        return await ipd_assessment_repository.list_by_admission(db, admission_id, skip, limit)

    async def create(self, db: AsyncSession, data: IPDAssessmentCreate) -> IPDAssessment:
        admission = await db.get(Admission, data.admission_id)
        if admission is None:
            raise ResourceNotFoundException("Admission not found.")

        existing = (await db.execute(select(IPDAssessment).where(IPDAssessment.admission_id == data.admission_id))).scalar_one_or_none()
        if existing is not None:
            raise DuplicateResourceException("An ipd assessment already exists for this admission.")

        now = datetime.now(timezone.utc)
        item = IPDAssessment(**data.model_dump(), created_at=now, updated_at=now)
        try:
            item = await ipd_assessment_repository.add(db, item)
            await db.commit()
            await db.refresh(item)
            return item
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateResourceException("Unable to create ipd assessment.") from exc
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create ipd assessment.") from exc

    async def update(self, db: AsyncSession, object_id: int, data: IPDAssessmentUpdate) -> IPDAssessment:
        item = await self.get(db, object_id)
        values = data.model_dump(exclude_unset=True)
        for field, value in values.items():
            setattr(item, field, value)
        item.updated_at = datetime.now(timezone.utc)
        try:
            await db.commit()
            await db.refresh(item)
            return item
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to update ipd assessment.") from exc


iPDAssessment_service = IPDAssessmentService()

__all__ = ["IPDAssessmentService", "iPDAssessment_service"]
