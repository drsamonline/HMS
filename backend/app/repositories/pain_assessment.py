"""HHMS Pain Assessment repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pain_assessment import PainAssessment
from app.repositories.base import RepositoryBase


class PainAssessmentRepository(RepositoryBase[PainAssessment]):
    def __init__(self) -> None:
        super().__init__(PainAssessment)

    async def get_by_id(self, db: AsyncSession, object_id: int) -> PainAssessment | None:
        return await db.get(PainAssessment, object_id)

    async def list_by_admission(self, db: AsyncSession, admission_id: int, skip: int = 0, limit: int = 100) -> list[PainAssessment]:
        result = await db.execute(
            select(PainAssessment).where(PainAssessment.admission_id == admission_id).order_by(PainAssessment.id.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())


pain_assessment_repository = PainAssessmentRepository()

__all__ = ["PainAssessmentRepository", "pain_assessment_repository"]
