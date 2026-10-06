"""HHMS Follow-up repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.followup import FollowUp
from app.repositories.base import RepositoryBase


class FollowUpRepository(RepositoryBase[FollowUp]):
    def __init__(self) -> None:
        super().__init__(FollowUp)

    async def get_by_id(self, db: AsyncSession, followup_id: int) -> FollowUp | None:
        return await db.get(FollowUp, followup_id)

    async def list_by_case(
        self, db: AsyncSession, case_record_id: int, skip: int = 0, limit: int = 50
    ) -> list[FollowUp]:
        result = await db.execute(
            select(FollowUp)
            .where(FollowUp.case_record_id == case_record_id)
            .order_by(FollowUp.followup_datetime.desc(), FollowUp.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


followup_repository = FollowUpRepository()

__all__ = ["FollowUpRepository", "followup_repository"]
