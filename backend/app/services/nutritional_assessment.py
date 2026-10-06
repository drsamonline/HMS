"""HHMS Nutritional Assessment service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseException, DuplicateResourceException, ResourceNotFoundException
from app.models.admission import Admission
from app.models.nutritional_assessment import NutritionalAssessment
from app.repositories.nutritional_assessment import nutritional_assessment_repository
from app.schemas.nutritional_assessment import NutritionalAssessmentCreate, NutritionalAssessmentUpdate


class NutritionalAssessmentService:
    async def get(self, db: AsyncSession, object_id: int) -> NutritionalAssessment:
        item = await nutritional_assessment_repository.get_by_id(db, object_id)
        if item is None:
            raise ResourceNotFoundException("Nutritional Assessment not found.")
        return item

    async def list(self, db: AsyncSession, admission_id: int, skip: int = 0, limit: int = 100) -> list[NutritionalAssessment]:
        admission = await db.get(Admission, admission_id)
        if admission is None:
            raise ResourceNotFoundException("Admission not found.")
        return await nutritional_assessment_repository.list_by_admission(db, admission_id, skip, limit)

    async def create(self, db: AsyncSession, data: NutritionalAssessmentCreate) -> NutritionalAssessment:
        admission = await db.get(Admission, data.admission_id)
        if admission is None:
            raise ResourceNotFoundException("Admission not found.")

        existing = (await db.execute(select(NutritionalAssessment).where(NutritionalAssessment.admission_id == data.admission_id))).scalar_one_or_none()
        if existing is not None:
            raise DuplicateResourceException("An nutritional assessment already exists for this admission.")

        now = datetime.now(timezone.utc)
        item = NutritionalAssessment(**data.model_dump(), created_at=now, updated_at=now)
        try:
            item = await nutritional_assessment_repository.add(db, item)
            await db.commit()
            await db.refresh(item)
            return item
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateResourceException("Unable to create nutritional assessment.") from exc
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create nutritional assessment.") from exc

    async def update(self, db: AsyncSession, object_id: int, data: NutritionalAssessmentUpdate) -> NutritionalAssessment:
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
            raise DatabaseException("Unable to update nutritional assessment.") from exc


nutritionalAssessment_service = NutritionalAssessmentService()

__all__ = ["NutritionalAssessmentService", "nutritionalAssessment_service"]
