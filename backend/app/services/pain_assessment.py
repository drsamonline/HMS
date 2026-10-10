"""HHMS Pain Assessment service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseException, DuplicateResourceException, ResourceNotFoundException
from app.models.admission import Admission
from app.models.pain_assessment import PainAssessment
from app.repositories.pain_assessment import pain_assessment_repository
from app.schemas.pain_assessment import PainAssessmentCreate, PainAssessmentUpdate


class PainAssessmentService:
    async def get(self, db: AsyncSession, object_id: int) -> PainAssessment:
        item = await pain_assessment_repository.get_by_id(db, object_id)
        if item is None:
            raise ResourceNotFoundException("Pain Assessment not found.")
        return item

    async def list(self, db: AsyncSession, admission_id: int, skip: int = 0, limit: int = 100) -> list[PainAssessment]:
        admission = await db.get(Admission, admission_id)
        if admission is None:
            raise ResourceNotFoundException("Admission not found.")
        return await pain_assessment_repository.list_by_admission(db, admission_id, skip, limit)

    async def create(self, db: AsyncSession, data: PainAssessmentCreate) -> PainAssessment:
        admission = await db.get(Admission, data.admission_id)
        if admission is None:
            raise ResourceNotFoundException("Admission not found.")

        now = datetime.now(timezone.utc)
        item = PainAssessment(**data.model_dump(), created_at=now, updated_at=now)
        try:
            item = await pain_assessment_repository.add(db, item)
            await db.commit()
            await db.refresh(item)
            return item
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateResourceException("Unable to create pain assessment.") from exc
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create pain assessment.") from exc

    async def update(self, db: AsyncSession, object_id: int, data: PainAssessmentUpdate) -> PainAssessment:
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
            raise DatabaseException("Unable to update pain assessment.") from exc


painAssessment_service = PainAssessmentService()

__all__ = ["PainAssessmentService", "painAssessment_service"]
