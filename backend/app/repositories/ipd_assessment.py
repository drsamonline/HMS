"""HHMS IPD Assessment repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ipd_assessment import IPDAssessment
from app.repositories.base import RepositoryBase


class IPDAssessmentRepository(RepositoryBase[IPDAssessment]):
    def __init__(self) -> None:
        super().__init__(IPDAssessment)

    async def get_by_id(self, db: AsyncSession, object_id: int) -> IPDAssessment | None:
        return await db.get(IPDAssessment, object_id)

    async def list_by_admission(self, db: AsyncSession, admission_id: int, skip: int = 0, limit: int = 100) -> list[IPDAssessment]:
        result = await db.execute(
            select(IPDAssessment).where(IPDAssessment.admission_id == admission_id).order_by(IPDAssessment.id.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())


ipd_assessment_repository = IPDAssessmentRepository()

__all__ = ["IPDAssessmentRepository", "ipd_assessment_repository"]
