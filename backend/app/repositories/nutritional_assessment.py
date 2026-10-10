"""HHMS Nutritional Assessment repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.nutritional_assessment import NutritionalAssessment
from app.repositories.base import RepositoryBase


class NutritionalAssessmentRepository(RepositoryBase[NutritionalAssessment]):
    def __init__(self) -> None:
        super().__init__(NutritionalAssessment)

    async def get_by_id(self, db: AsyncSession, object_id: int) -> NutritionalAssessment | None:
        return await db.get(NutritionalAssessment, object_id)

    async def list_by_admission(self, db: AsyncSession, admission_id: int, skip: int = 0, limit: int = 100) -> list[NutritionalAssessment]:
        result = await db.execute(
            select(NutritionalAssessment).where(NutritionalAssessment.admission_id == admission_id).order_by(NutritionalAssessment.id.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())


nutritional_assessment_repository = NutritionalAssessmentRepository()

__all__ = ["NutritionalAssessmentRepository", "nutritional_assessment_repository"]
